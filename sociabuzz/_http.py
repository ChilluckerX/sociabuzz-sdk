"""
Internal HTTP client for the SociaBuzz backend.

This module is **not** part of the public SDK surface — import from
``sociabuzz`` (the package) instead.
"""

from __future__ import annotations

import json
import re

import httpx


class SociaBuzzHTTP:
    """Low-level async HTTP client that manages cookies, CSRF tokens,
    and the full SociaBuzz request lifecycle."""

    COMMON_HEADERS = {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/146.0.0.0 Safari/537.36"
        ),
        "accept-language": "en-US,en;q=0.9",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    def __init__(self, base_url: str = "https://sociabuzz.com"):
        self.base_url = base_url.rstrip("/")
        self._http: httpx.AsyncClient | None = None

    # ── HTTP session management ───────────────────────────────────

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                follow_redirects=True,
                timeout=30.0,
                headers=self.COMMON_HEADERS,
            )
        return self._http

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()

    # ── Cookie persistence ─────────────────────────────────────────

    def serialize_cookies(self) -> dict[str, str]:
        """Snapshot the current cookie jar as a plain dict.

        Returns an empty dict if no client exists yet.

        If duplicate cookie names exist (e.g. after a session refresh),
        the last value wins — this matches SociaBuzz's cookie behaviour.
        """
        client = self._http
        if client is None or client.is_closed:
            return {}
        result: dict[str, str] = {}
        for cookie in client.cookies.jar:
            result[cookie.name] = cookie.value or ""
        return result

    def restore_cookies(self, cookies: dict[str, str]) -> None:
        """Restore a previously serialised cookie jar into the client.

        Creates the client if necessary.  Safe to call before
        :meth:`init_session` — the restored cookies will be merged with
        any new ones set by SociaBuzz.
        """
        if not cookies:
            return
        client = self._http
        if client is None or client.is_closed:
            # Build client synchronously (no I/O needed for cookie set)
            self._http = httpx.AsyncClient(
                follow_redirects=True,
                timeout=30.0,
                headers=self.COMMON_HEADERS,
                cookies=cookies,
            )
        else:
            # Delete any existing duplicates first, then set fresh values.
            for name in cookies:
                client.cookies.delete(name)
            for name, value in cookies.items():
                client.cookies.set(name, value)

    # ── Step 0: seed session cookies ──────────────────────────────

    async def init_session(self, username: str) -> dict:
        """GET /{username}/tribe — seeds ci_session + CSRF cookies."""
        client = await self._client()
        resp = await client.get(
            f"{self.base_url}/{username}/tribe",
            headers={
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "sec-fetch-site": "none",
                "sec-fetch-mode": "navigate",
                "sec-fetch-dest": "document",
            },
        )
        resp.raise_for_status()

        cookies = {k: v for k, v in client.cookies.items()}
        csrf_token = cookies.get("sociabuzz_sb_cookie_csrf", cookies.get("csrf_cookie_name", ""))
        return {"cookies": cookies, "csrf_token": csrf_token}

    # ── Step 0.5: fetch creator config (TRAKTIR_PRICE) ────────────

    async def get_creator_config(self, username: str, currency: str = "MYR") -> dict:
        """GET /{username}/donate/queue — extracts the ``client`` config JSON."""
        client = await self._client()
        resp = await client.get(
            f"{self.base_url}/{username}/donate/queue",
            params={"type": "buyme", "currency": currency, "message": ""},
            headers={
                "accept": "*/*",
                "x-requested-with": "XMLHttpRequest",
                "referer": f"{self.base_url}/{username}/tribe",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
            },
        )
        resp.raise_for_status()

        match = re.search(r"var\s+client\s*=\s*(\{[^;]+\})\s*;", resp.text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return {}

    # ── Step 1: submit donation form ──────────────────────────────

    async def submit_donation(
        self,
        username: str,
        amount: float,
        currency: str,
        fullname: str,
        email: str,
        note: str = "",
    ) -> dict:
        """POST /{username}/donate/get-form-queue?buyme=1

        Auto-fetches the creator's unit price (TRAKTIR_PRICE) and
        calculates the correct qty so the server-side validation passes.
        """
        client = await self._client()

        # Ensure CSRF cookie exists
        csrf_token = ""
        for k, v in client.cookies.items():
            if k in ("sociabuzz_sb_cookie_csrf", "csrf_cookie_name"):
                csrf_token = v
                break
        if not csrf_token:
            session_info = await self.init_session(username)
            csrf_token = session_info["csrf_token"]

        # Unit-price calculation
        config = await self.get_creator_config(username, currency)
        traktir_price = float(config.get("TRAKTIR_PRICE", "1"))
        if traktir_price <= 0:
            traktir_price = 1.0

        calculated_qty = max(1, round(amount / traktir_price))
        actual_amount = traktir_price * calculated_qty

        form_data = {
            "sb_token_csrf": csrf_token,
            "currency": currency,
            "amount": (
                str(int(actual_amount))
                if actual_amount == int(actual_amount)
                else str(actual_amount)
            ),
            "qty": str(calculated_qty),
            "support_duration": "30",
            "note": note,
            "fullname": fullname,
            "email": email,
            "is_agree": "1",
            "years18": "1",
            "is_vote": "0",
            "is_voice": "0",
            "is_mediashare": "0",
            "is_gif": "0",
            "is_sound": "0",
            "vote_id": "",
            "ms_maxtime": "",
            "start_from": "0",
            "ms_starthour": "0",
            "ms_startminute": "0",
            "ms_startsecond": "0",
            "spin_check": "0",
            "prev_url": f"{self.base_url}/{username}/tribe?",
            "hide_email": "0",
            "is_tiktok": "0",
            "tiktok_duration": "0",
            "is_instagram": "0",
            "instagram_duration": "0",
            "wishlist_id": "",
            "quickpay": "0",
        }

        resp = await client.post(
            f"{self.base_url}/{username}/donate/get-form-queue?buyme=1",
            data=form_data,
            headers={
                "accept": "application/json, text/javascript, */*; q=0.01",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "x-requested-with": "XMLHttpRequest",
                "origin": self.base_url,
                "referer": f"{self.base_url}/{username}/tribe?",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
            },
        )
        resp.raise_for_status()
        result = resp.json()
        result["_actual_amount"] = actual_amount
        result["_traktir_price"] = traktir_price
        result["_qty"] = calculated_qty
        return result

    # ── Step 2: payment settings (available methods + fees) ───────

    async def get_payment_settings(
        self,
        token: str,
        amount: float,
        currency: str = "MYR",
        country: str = "Malaysia",
    ) -> dict:
        """GET /payment/pay/setting — returns payment channels with fee info."""
        client = await self._client()

        params = {
            "amount": str(amount),
            "currency": currency,
            "base_amount": str(amount),
            "base_currency": currency,
            "currency_def": currency,
            "convertion": currency,
            "country": country,
            "feature": "TRIBE",
            "is_borne_fee": "1",
            "risk": "",
            "message": "",
            "direct": "",
            "service_fee": "0",
            "token": token,
            "country_account": "",
        }

        resp = await client.get(
            f"{self.base_url}/payment/pay/setting",
            params=params,
            headers={
                "accept": "application/json, text/plain, */*",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
                "referer": f"{self.base_url}/payment/x/{token}",
            },
        )
        resp.raise_for_status()
        return resp.json()

    # ── Step 2.5: visit payment page → extract page CSRF ─────────

    async def visit_payment_page(self, token: str) -> str:
        """GET /payment/x/{token} — seeds cookies and returns CSRF token."""
        client = await self._client()
        resp = await client.get(
            f"{self.base_url}/payment/x/{token}",
            headers={
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "navigate",
                "sec-fetch-dest": "document",
                "referer": f"{self.base_url}/payment/x/{token}",
            },
        )
        resp.raise_for_status()

        match = re.search(r'name=["\']sb_token_csrf["\']\s+value=["\']([^"\']*)["\']', resp.text)
        if match:
            return match.group(1)

        for k, v in client.cookies.items():
            if k in ("sociabuzz_sb_cookie_csrf", "csrf_cookie_name"):
                return v
        return ""

    # ── Step 3: create payment ────────────────────────────────────

    async def create_payment(
        self,
        token: str,
        csrf_token: str,
        payment_method: str = "my_touchngo",
        type_payment: str = "ewallet",
        source_payment: str = "xendit",
        currency: str = "MYR",
        country_iso2: str = "MY",
        country_name: str = "Malaysia",
    ) -> dict:
        """POST /payment/send/create (JSON body) — returns payment URL / QR."""
        client = await self._client()

        resp = await client.post(
            f"{self.base_url}/payment/send/create",
            json={
                "sb_token_csrf": csrf_token,
                "order_id": token,
                "final_currency": currency,
                "currency_def": currency,
                "payment_method": payment_method,
                "type_payment": type_payment,
                "source_payment": source_payment,
                "country": country_iso2,
                "country_pay": country_name,
            },
            headers={
                "accept": "application/json, text/javascript, */*; q=0.01",
                "x-requested-with": "XMLHttpRequest",
                "origin": self.base_url,
                "referer": f"{self.base_url}/payment/x/{token}",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "cors",
                "sec-fetch-dest": "empty",
            },
        )
        resp.raise_for_status()
        return resp.json()

    # ── Step 4: check payment status ──────────────────────────────

    async def check_payment_status(
        self, token: str, payment_method: str = "my_touchngo", inv_id: str = ""
    ) -> dict:
        """GET /payment/pending — parses HTML to detect paid/expired/failed."""
        client = await self._client()

        resp = await client.get(
            f"{self.base_url}/payment/pending",
            params={"type": payment_method, "inv_id": inv_id or token},
            headers={
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "sec-fetch-site": "same-origin",
                "sec-fetch-mode": "navigate",
                "sec-fetch-dest": "document",
                "referer": f"{self.base_url}/payment/x/{token}",
            },
        )
        resp.raise_for_status()

        html_lower = resp.text.lower()
        if (
            "payment successful" in html_lower
            or "payment success" in html_lower
            or "terima kasih" in html_lower
        ):
            status = "paid"
        elif "expired" in html_lower and "payment expired" in html_lower:
            status = "expired"
        elif "payment failed" in html_lower:
            status = "failed"
        else:
            status = "pending"

        return {"status": status, "url": str(resp.url)}
