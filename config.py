"""Centralised application settings (env-driven).

All runtime configuration is read from environment variables (or a ``.env``
file).  No secrets are hard-coded anywhere in the SDK.

Required for production
-----------------------
- ``API_KEY`` — secret key clients must send to access the gateway.
- ``DEFAULT_CREATOR`` — SociaBuzz username used when none is supplied.

Optional
--------
- ``SESSION_BACKEND`` — ``sqlite`` (default, file-based) or ``memory``.
- ``SESSION_DB_PATH`` — SQLite path (default: ``./sociabuzz_sessions.db``).
- ``WEBHOOK_TIMEOUT`` — per-payment poll timeout in seconds.
- ``WEBHOOK_POLL_INTERVAL`` — seconds between status polls.
- ``WEBHOOK_SECRET`` — optional shared secret sent in webhook ``X-Webhook-Secret``.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool) -> bool:
    val = os.getenv(name, str(default)).strip().lower()
    return val in ("1", "true", "yes", "on")


class Settings:
    """Read-only settings populated from environment variables."""

    # ── SociaBuzz backend ──────────────────────────────────────────
    BASE_URL: str = os.getenv("SOCIABUZZ_BASE_URL", "https://sociabuzz.com")
    DEFAULT_CREATOR: str = os.getenv("SOCIABUZZ_USERNAME", os.getenv("DEFAULT_CREATOR", ""))

    # ── Gateway server ─────────────────────────────────────────────
    HOST: str = os.getenv("API_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("API_PORT", "8000"))

    # ── Authentication ─────────────────────────────────────────────
    # If empty, auth is DISABLED (dev only — never leave empty in prod).
    API_KEY: str = os.getenv("API_KEY", "")
    # Comma-separated extra keys (rotation).
    API_KEYS: list[str] = [k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()]

    @property
    def ALL_KEYS(self) -> set[str]:
        keys: set[str] = set()
        if self.API_KEY:
            keys.add(self.API_KEY)
        keys.update(self.API_KEYS)
        return keys

    @property
    def AUTH_ENABLED(self) -> bool:
        return len(self.ALL_KEYS) > 0

    # ── Session persistence ────────────────────────────────────────
    SESSION_BACKEND: str = os.getenv("SESSION_BACKEND", "sqlite").lower()
    SESSION_DB_PATH: str = os.getenv("SESSION_DB_PATH", "sociabuzz_sessions.db")

    # ── Webhook / callback ─────────────────────────────────────────
    WEBHOOK_ENABLED: bool = _bool("WEBHOOK_ENABLED", True)
    WEBHOOK_POLL_INTERVAL: float = float(os.getenv("WEBHOOK_POLL_INTERVAL", "5"))
    WEBHOOK_TIMEOUT: float = float(os.getenv("WEBHOOK_TIMEOUT", "3600"))
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")


settings = Settings()
