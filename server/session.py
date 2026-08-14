"""Persistent donation session store.

Supports two backends controlled by ``settings.SESSION_BACKEND``:

- ``sqlite`` (default) — survives restarts, works across workers.
- ``memory`` — legacy in-memory dict (single-process only, dev use).

Each stored donation is serialised to its cookies + CSRF state so the
:class:`~sociabuzz.client.Donation` object can be fully rebuilt on demand.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from typing import Protocol

from sociabuzz._http import SociaBuzzHTTP
from sociabuzz.client import Donation
from sociabuzz.exceptions import SessionExpiredError


class SessionBackend(Protocol):
    """Interface implemented by every session store backend."""

    def get(self, token: str, base_url: str) -> Donation: ...
    def store(self, donation: Donation) -> None: ...
    def delete(self, token: str) -> None: ...
    async def close_all(self) -> None: ...
    @property
    def count(self) -> int: ...


# ── In-memory backend (legacy / dev) ──────────────────────────────────


class MemorySessionStore:
    """In-memory store — single process, lost on restart."""

    def __init__(self) -> None:
        self._sessions: dict[str, Donation] = {}

    def get(self, token: str, base_url: str = "") -> Donation:
        donation = self._sessions.get(token)
        if not donation:
            raise SessionExpiredError(token)
        return donation

    def store(self, donation: Donation) -> None:
        self._sessions[donation.token] = donation

    def delete(self, token: str) -> None:
        self._sessions.pop(token, None)

    async def close_all(self) -> None:
        for d in self._sessions.values():
            await d.close()
        self._sessions.clear()

    @property
    def count(self) -> int:
        return len(self._sessions)


# ── SQLite backend (default, production-ready) ───────────────────────


_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    token        TEXT PRIMARY KEY,
    country      TEXT NOT NULL DEFAULT '',
    currency     TEXT NOT NULL DEFAULT '',
    amount       REAL NOT NULL DEFAULT 0,
    redirect_url TEXT NOT NULL DEFAULT '',
    expires_in   INTEGER NOT NULL DEFAULT 3600,
    csrf         TEXT NOT NULL DEFAULT '',
    callback_url TEXT NOT NULL DEFAULT '',
    cookies      TEXT NOT NULL DEFAULT '{}',
    created_at   REAL NOT NULL,
    updated_at   REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS payments (
    inv_id        TEXT PRIMARY KEY,
    token         TEXT NOT NULL,
    payment_method TEXT NOT NULL DEFAULT '',
    label         TEXT NOT NULL DEFAULT '',
    gateway       TEXT NOT NULL DEFAULT '',
    payment_url   TEXT,
    qr_string     TEXT,
    fee_json      TEXT NOT NULL DEFAULT '{}',
    webhook_sent  INTEGER NOT NULL DEFAULT 0,
    webhook_attempts INTEGER NOT NULL DEFAULT 0,
    created_at    REAL NOT NULL,
    FOREIGN KEY (token) REFERENCES sessions(token)
);
CREATE INDEX IF NOT EXISTS idx_payments_token ON payments(token);
"""


class SQLiteSessionStore:
    """SQLite-backed session store — survives restarts, multi-worker safe.

    Donations are serialised (cookies + CSRF) into a row.  On ``get`` the
    :class:`Donation` is rebuilt with a fresh :class:`SociaBuzzHTTP`
    instance and its cookies restored.
    """

    def __init__(self, db_path: str = "sociabuzz_sessions.db") -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock, self._conn() as conn:
            conn.executescript(_SCHEMA)
            conn.commit()

    # ── Sessions ───────────────────────────────────────────────────

    def get(self, token: str, base_url: str = "https://sociabuzz.com") -> Donation:
        with self._lock, self._conn() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE token = ?", (token,)).fetchone()

        if not row:
            raise SessionExpiredError(token)

        http = SociaBuzzHTTP(base_url)
        data = {
            "token": row["token"],
            "country": row["country"],
            "currency": row["currency"],
            "amount": row["amount"],
            "redirect_url": row["redirect_url"],
            "expires_in": row["expires_in"],
            "csrf": row["csrf"],
            "callback_url": row["callback_url"],
            "cookies": json.loads(row["cookies"] or "{}"),
        }
        return Donation.restore(http, data)

    def store(self, donation: Donation) -> None:
        data = donation.serialize()
        now = time.time()
        with self._lock, self._conn() as conn:
            conn.execute(
                """
                INSERT INTO sessions
                    (token, country, currency, amount, redirect_url, expires_in,
                     csrf, callback_url, cookies, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(token) DO UPDATE SET
                    csrf = excluded.csrf,
                    callback_url = excluded.callback_url,
                    cookies = excluded.cookies,
                    updated_at = excluded.updated_at
                """,
                (
                    data["token"],
                    data["country"],
                    data["currency"],
                    data["amount"],
                    data["redirect_url"],
                    data["expires_in"],
                    data["csrf"],
                    data["callback_url"],
                    json.dumps(data["cookies"]),
                    now,
                    now,
                ),
            )
            conn.commit()

    def update_csrf(self, token: str, csrf: str, cookies: dict[str, str]) -> None:
        """Persist refreshed CSRF + cookies after a settings fetch."""
        with self._lock, self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET csrf = ?, cookies = ?, updated_at = ? WHERE token = ?",
                (csrf, json.dumps(cookies), time.time(), token),
            )
            conn.commit()

    def get_callback_url(self, token: str) -> str:
        with self._lock, self._conn() as conn:
            row = conn.execute(
                "SELECT callback_url FROM sessions WHERE token = ?", (token,)
            ).fetchone()
        return row["callback_url"] if row else ""

    def delete(self, token: str) -> None:
        with self._lock, self._conn() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.execute("DELETE FROM payments WHERE token = ?", (token,))
            conn.commit()

    # ── Payments (for webhook tracking) ────────────────────────────

    def store_payment(
        self,
        token: str,
        inv_id: str,
        payment_method: str,
        label: str,
        gateway: str,
        payment_url: str | None,
        qr_string: str | None,
        fee: dict,
    ) -> None:
        now = time.time()
        with self._lock, self._conn() as conn:
            conn.execute(
                """
                INSERT INTO payments
                    (inv_id, token, payment_method, label, gateway,
                     payment_url, qr_string, fee_json, webhook_sent,
                     webhook_attempts, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)
                ON CONFLICT(inv_id) DO UPDATE SET
                    payment_url = excluded.payment_url,
                    qr_string = excluded.qr_string
                """,
                (
                    inv_id,
                    token,
                    payment_method,
                    label,
                    gateway,
                    payment_url,
                    qr_string,
                    json.dumps(fee),
                    now,
                ),
            )
            conn.commit()

    def list_pending_payments(self) -> list[dict]:
        """Return payments not yet webhook-delivered and not expired."""
        with self._lock, self._conn() as conn:
            rows = conn.execute("SELECT * FROM payments WHERE webhook_sent = 0").fetchall()
        return [dict(r) for r in rows]

    def mark_webhook_sent(self, inv_id: str, success: bool) -> None:
        with self._lock, self._conn() as conn:
            if success:
                conn.execute(
                    "UPDATE payments SET webhook_sent = 1, updated_at = ? WHERE inv_id = ?",
                    (time.time(), inv_id),
                )
            else:
                conn.execute(
                    "UPDATE payments SET webhook_attempts = webhook_attempts + 1 WHERE inv_id = ?",
                    (inv_id,),
                )
            conn.commit()

    # ── Lifecycle ──────────────────────────────────────────────────

    async def close_all(self) -> None:
        # SQLite has no long-lived async client to close.
        # Optionally purge old sessions here if needed.
        pass

    @property
    def count(self) -> int:
        with self._lock, self._conn() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM sessions").fetchone()
        return row["c"] if row else 0


# ── Factory ───────────────────────────────────────────────────────────


def create_session_store() -> SessionBackend:
    """Build the configured session store based on ``settings.SESSION_BACKEND``."""
    from config import settings

    backend = settings.SESSION_BACKEND
    if backend == "memory":
        return MemorySessionStore()
    # default: sqlite
    return SQLiteSessionStore(settings.SESSION_DB_PATH)


# Module-level singleton — imported by routes and app lifecycle.
session_store = create_session_store()
