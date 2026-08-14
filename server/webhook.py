"""Webhook dispatcher + background status polling.

When a payment is created with a ``callback_url``, the gateway polls
SociaBuzz for the payment status.  Once the status reaches a terminal
state (``paid`` / ``expired`` / ``failed``) a webhook is POSTed to the
merchant's callback URL with the result.

Configuration (see ``config.py``):

- ``WEBHOOK_ENABLED`` — master switch (default true)
- ``WEBHOOK_POLL_INTERVAL`` — seconds between polls (default 5)
- ``WEBHOOK_TIMEOUT`` — max seconds to poll before giving up (default 3600)
- ``WEBHOOK_SECRET`` — sent as ``X-Webhook-Secret`` header to the merchant
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import time
from typing import TYPE_CHECKING

import httpx

from config import settings

if TYPE_CHECKING:
    from server.session import SQLiteSessionStore

logger = logging.getLogger("sociabuzz.webhook")

TERMINAL_STATUSES = {"paid", "expired", "failed"}


class WebhookDispatcher:
    """Background task that polls pending payments and fires webhooks."""

    def __init__(self, store: SQLiteSessionStore) -> None:
        self._store = store
        self._task: asyncio.Task | None = None
        self._polling: set[str] = set()  # inv_ids currently being polled
        self._http = httpx.AsyncClient(timeout=15.0)

    # ── Lifecycle ──────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background poller (idempotent)."""
        if not settings.WEBHOOK_ENABLED:
            logger.info("Webhook dispatcher disabled via WEBHOOK_ENABLED=false")
            return
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run_loop())
            logger.info("Webhook dispatcher started")

    async def stop(self) -> None:
        """Stop the background poller and close the HTTP client."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._http.aclose()
        logger.info("Webhook dispatcher stopped")

    # ── Registration ───────────────────────────────────────────────

    async def track(
        self,
        token: str,
        inv_id: str,
        payment_method: str,
        base_url: str,
    ) -> None:
        """Register a payment for background polling.

        Spawns a per-payment polling coroutine that runs until the status
        reaches a terminal state or the timeout expires.
        """
        if not settings.WEBHOOK_ENABLED:
            return
        if inv_id in self._polling:
            return
        self._polling.add(inv_id)
        asyncio.create_task(self._poll_payment(token, inv_id, payment_method, base_url))

    # ── Internal: per-payment poll loop ────────────────────────────

    async def _poll_payment(
        self, token: str, inv_id: str, payment_method: str, base_url: str
    ) -> None:
        deadline = time.time() + settings.WEBHOOK_TIMEOUT
        try:
            while time.time() < deadline:
                try:
                    donation = self._store.get(token, base_url)
                    status = await donation.check_payment_status(payment_method, inv_id)
                except Exception as exc:
                    logger.warning("Poll error for inv_id=%s: %s", inv_id, exc)
                    status = "pending"

                if status in TERMINAL_STATUSES:
                    await self._fire_webhook(token, inv_id, payment_method, status, base_url)
                    return

                await asyncio.sleep(settings.WEBHOOK_POLL_INTERVAL)

            # Timed out
            logger.info("Webhook poll timed out for inv_id=%s", inv_id)
            await self._fire_webhook(token, inv_id, payment_method, "expired", base_url)
        finally:
            self._polling.discard(inv_id)

    # ── Internal: webhook delivery ─────────────────────────────────

    async def _fire_webhook(
        self,
        token: str,
        inv_id: str,
        payment_method: str,
        status: str,
        base_url: str,
    ) -> None:
        callback_url = self._store.get_callback_url(token)
        if not callback_url:
            # No callback registered — just mark as sent so we stop polling.
            self._store.mark_webhook_sent(inv_id, success=True)
            return

        payload = {
            "event": f"payment.{status}",
            "token": token,
            "inv_id": inv_id,
            "payment_method": payment_method,
            "status": status,
            "timestamp": int(time.time()),
        }

        headers = {"Content-Type": "application/json"}
        if settings.WEBHOOK_SECRET:
            headers["X-Webhook-Secret"] = settings.WEBHOOK_SECRET
            # Also provide an HMAC signature of the body.
            body_bytes = json.dumps(payload, separators=(",", ":")).encode()
            sig = hmac.new(settings.WEBHOOK_SECRET.encode(), body_bytes, hashlib.sha256).hexdigest()
            headers["X-Webhook-Signature"] = sig

        for attempt in range(3):
            try:
                resp = await self._http.post(callback_url, json=payload, headers=headers)
                if 200 <= resp.status_code < 300:
                    self._store.mark_webhook_sent(inv_id, success=True)
                    logger.info(
                        "Webhook delivered to %s for inv_id=%s status=%s",
                        callback_url,
                        inv_id,
                        status,
                    )
                    return
                logger.warning(
                    "Webhook attempt %d to %s returned HTTP %s",
                    attempt + 1,
                    callback_url,
                    resp.status_code,
                )
            except Exception as exc:
                logger.warning(
                    "Webhook attempt %d to %s failed: %s", attempt + 1, callback_url, exc
                )

            await asyncio.sleep(2)

        self._store.mark_webhook_sent(inv_id, success=False)
        logger.error("Webhook delivery failed after 3 attempts for inv_id=%s", inv_id)

    # ── Internal: recovery loop (resume polling after restart) ─────

    async def _run_loop(self) -> None:
        """Periodically resume polling for payments left pending across restarts."""
        await asyncio.sleep(3)  # initial delay to let server bind
        while True:
            try:
                await self._resume_pending()
            except Exception as exc:
                logger.warning("Resume loop error: %s", exc)
            await asyncio.sleep(30)

    async def _resume_pending(self) -> None:
        """Find payments not yet webhook-delivered and resume polling."""
        from config import settings as cfg

        pending = self._store.list_pending_payments()
        for p in pending:
            inv_id = p["inv_id"]
            if inv_id in self._polling:
                continue
            self._polling.add(inv_id)
            asyncio.create_task(
                self._poll_payment(p["token"], inv_id, p["payment_method"], cfg.BASE_URL)
            )


# Module-level singleton.
# Only created for SQLite-backed stores (memory store has no payment table).
from server.session import session_store  # noqa: E402

webhook_dispatcher: WebhookDispatcher | None = None
if isinstance(session_store, type(None)) is False and hasattr(
    session_store, "list_pending_payments"
):
    webhook_dispatcher = WebhookDispatcher(session_store)  # type: ignore[arg-type]
