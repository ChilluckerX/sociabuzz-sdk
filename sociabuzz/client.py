"""
High-level SociaBuzz SDK — OOP donation flow.

Classes
-------
SociaBuzz
    Entry point.  Call ``donate()`` to start a flow.
Donation
    Active donation session; list methods, create payments, check status.
Payment
    A created payment with URL / QR code; poll ``check_status()``.
"""

from __future__ import annotations

from ._http import SociaBuzzHTTP
from .constants import GROUP_LABELS, SUPPORTED_COUNTRIES
from .exceptions import DonationError, PaymentError, UnsupportedCountryError
from .models import FeeInfo, PaymentMethod

# =====================================================================
# Public SDK classes
# =====================================================================


class SociaBuzz:
    """SociaBuzz donation SDK.

    Example::

        sb = SociaBuzz()
        donation = await sb.donate(
            username="creator", amount=5.0, country="Malaysia",
            fullname="John", email="john@test.com",
        )
        methods = await donation.get_payment_methods()
        payment = await donation.create_payment("my_touchngo")
        print(payment.payment_url)
        status = await payment.check_status()
        await donation.close()
    """

    def __init__(self, base_url: str = "https://sociabuzz.com"):
        self.base_url = base_url.rstrip("/")

    async def donate(
        self,
        username: str,
        amount: float,
        country: str,
        fullname: str,
        email: str,
        note: str = "",
    ) -> Donation:
        """Submit a donation and return a :class:`Donation` for the rest of the flow."""
        info = SUPPORTED_COUNTRIES.get(country)
        if not info:
            raise UnsupportedCountryError(country, list(SUPPORTED_COUNTRIES))

        currency = info["currency"]
        http = SociaBuzzHTTP(self.base_url)

        try:
            await http.init_session(username)
            result = await http.submit_donation(
                username=username,
                amount=amount,
                currency=currency,
                fullname=fullname,
                email=email,
                note=note,
            )
        except Exception as exc:
            await http.close()
            raise DonationError(f"SociaBuzz request failed: {exc}") from exc

        success = result.get("success")
        if success != "true" and success is not True:
            await http.close()
            raise DonationError(
                "Donation validation failed",
                errors=result.get("validates", []),
            )

        content = result.get("content", {})
        redirect_url = content.get("redirect", "")
        token = redirect_url.rstrip("/").split("/")[-1] if redirect_url else ""

        if not token:
            await http.close()
            raise DonationError("Failed to obtain payment token")

        return Donation(
            http=http,
            token=token,
            country=country,
            currency=currency,
            amount=result.get("_actual_amount", amount),
            redirect_url=redirect_url,
            expires_in=content.get("expired_at", 3600),
        )

    # Async context-manager (convenience) ---------------------------------

    async def __aenter__(self) -> SociaBuzz:
        return self

    async def __aexit__(self, *exc: object) -> None:
        pass  # SociaBuzz itself is stateless; Donation owns the HTTP session


class Donation:
    """An active donation session.

    Created by :meth:`SociaBuzz.donate`.  Use to list methods, create
    payments, and check status.
    """

    def __init__(
        self,
        http: SociaBuzzHTTP,
        token: str,
        country: str,
        currency: str,
        amount: float,
        redirect_url: str,
        expires_in: int,
    ):
        self._http = http
        self.token = token
        self.country = country
        self.currency = currency
        self.amount = amount
        self.redirect_url = redirect_url
        self.expires_in = expires_in
        self._csrf: str = ""
        self._settings_cache: dict | None = None
        self.callback_url: str = ""

    # ── Step 2: list payment methods ──────────────────────────────

    async def get_payment_methods(self) -> list[PaymentMethod]:
        """Return every active payment method with fee details."""
        await self._ensure_csrf()
        raw_settings = await self._fetch_settings()

        methods: list[PaymentMethod] = []
        counter = 0
        for group in raw_settings.get("payment_channel", []):
            raw_group = group.get("name", "")
            for m in group.get("available", []):
                if not m.get("active", False):
                    continue
                counter += 1
                methods.append(
                    PaymentMethod(
                        id=counter,
                        name=m["name"],
                        label=m.get("alias", m["name"]),
                        group=GROUP_LABELS.get(raw_group, raw_group),
                        gateway=m.get("source", ""),
                        fee=_build_fee(m),
                    )
                )
        return methods

    # ── Step 3: create payment ────────────────────────────────────

    async def create_payment(self, method_name: str) -> Payment:
        """Create a payment and return a :class:`Payment` object."""
        await self._ensure_csrf()
        raw_settings = await self._fetch_settings()

        method_info, raw_group = self._find_method(raw_settings, method_name)
        if not method_info:
            raise PaymentError(
                f"Payment method '{method_name}' not available. "
                "Call get_payment_methods() to see valid options."
            )

        final_currency = self.currency
        if method_name == "qris":
            final_currency = "IDR"
        if method_info.get("source") == "2c2p" and raw_group == "credit_card":
            final_currency = "IDR"

        country_info = SUPPORTED_COUNTRIES.get(self.country, {})
        iso2 = country_info.get("iso2", self.country[:2].upper())

        result = await self._http.create_payment(
            token=self.token,
            csrf_token=self._csrf,
            payment_method=method_name,
            type_payment=raw_group,
            source_payment=method_info.get("source", "xendit"),
            currency=final_currency,
            country_iso2=iso2,
            country_name=self.country,
        )

        payment_url, qr_string, inv_id = None, None, None
        if isinstance(result, dict):
            inv_id = result.get("inv_id")
            data = result.get("data")
            if isinstance(data, dict):
                payment_url = data.get("payment_link") or data.get("redirect_url")
                qr_string = data.get("qr_string")
            if not payment_url and isinstance(result.get("redirect"), str):
                payment_url = result["redirect"]

        return Payment(
            http=self._http,
            token=self.token,
            method=method_name,
            label=method_info.get("alias", method_name),
            gateway=method_info.get("source", ""),
            fee=_build_fee(method_info),
            payment_url=payment_url,
            qr_string=qr_string,
            inv_id=inv_id,
        )

    # ── Step 4 (convenience) ──────────────────────────────────────

    async def check_payment_status(self, payment_method: str, inv_id: str) -> str:
        """Check payment status directly from the donation object.

        Returns ``'pending'``, ``'paid'``, ``'expired'``, or ``'failed'``.
        """
        result = await self._http.check_payment_status(
            token=self.token,
            payment_method=payment_method,
            inv_id=inv_id,
        )
        return result.get("status", "unknown")

    # ── Lifecycle ─────────────────────────────────────────────────

    async def close(self) -> None:
        """Close the underlying HTTP session."""
        await self._http.close()

    async def __aenter__(self) -> Donation:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    # ── Persistence (for SQLite session store) ─────────────────────

    def serialize(self) -> dict:
        """Snapshot the donation state so it can be persisted and rebuilt."""
        return {
            "token": self.token,
            "country": self.country,
            "currency": self.currency,
            "amount": self.amount,
            "redirect_url": self.redirect_url,
            "expires_in": self.expires_in,
            "csrf": self._csrf,
            "callback_url": self.callback_url,
            "cookies": self._http.serialize_cookies(),
        }

    @classmethod
    def restore(cls, http: SociaBuzzHTTP, data: dict) -> Donation:
        """Rebuild a :class:`Donation` from a previously serialised snapshot."""
        cookies = data.get("cookies") or {}
        if cookies:
            http.restore_cookies(cookies)
        donation = cls(
            http=http,
            token=data["token"],
            country=data.get("country", ""),
            currency=data.get("currency", ""),
            amount=data.get("amount", 0.0),
            redirect_url=data.get("redirect_url", ""),
            expires_in=data.get("expires_in", 3600),
        )
        donation._csrf = data.get("csrf", "")
        donation.callback_url = data.get("callback_url", "")
        return donation

    # ── Internal helpers ──────────────────────────────────────────

    async def _ensure_csrf(self) -> None:
        if not self._csrf:
            self._csrf = await self._http.visit_payment_page(self.token)

    async def _fetch_settings(self) -> dict:
        if self._settings_cache is None:
            self._settings_cache = await self._http.get_payment_settings(
                token=self.token,
                amount=self.amount,
                currency=self.currency,
                country=self.country,
            )
        return self._settings_cache

    @staticmethod
    def _find_method(settings: dict, name: str) -> tuple[dict | None, str]:
        for group in settings.get("payment_channel", []):
            for m in group.get("available", []):
                if m.get("name") == name:
                    return m, group.get("name", "")
        return None, ""


class Payment:
    """A created payment — redirect the user to :attr:`payment_url`
    or display :attr:`qr_string`, then poll :meth:`check_status`."""

    def __init__(
        self,
        http: SociaBuzzHTTP,
        token: str,
        method: str,
        label: str,
        gateway: str,
        fee: FeeInfo,
        payment_url: str | None,
        qr_string: str | None,
        inv_id: str | None,
    ):
        self._http = http
        self.token = token
        self.method = method
        self.label = label
        self.gateway = gateway
        self.fee = fee
        self.payment_url = payment_url
        self.qr_string = qr_string
        self.inv_id = inv_id

    async def check_status(self) -> str:
        """Poll payment status.

        Returns ``'pending'``, ``'paid'``, ``'expired'``, or ``'failed'``.
        """
        result = await self._http.check_payment_status(
            token=self.token,
            payment_method=self.method,
            inv_id=self.inv_id or self.token,
        )
        return result.get("status", "unknown")


# ── Module-level helper ──────────────────────────────────────────────


def _build_fee(raw: dict) -> FeeInfo:
    """Convert a raw SociaBuzz method dict to a :class:`FeeInfo`."""
    return FeeInfo(
        fee_type=raw.get("fee_type", ""),
        fee_rate=raw.get("fee", 0),
        fee_fixed=raw.get("fee_amount", 0),
        total_fee=str(raw.get("total_fee", "0")),
        total_pay=str(raw.get("total_pay", "0")),
        min_amount=raw.get("min_amount", 0),
        max_amount=raw.get("max_amount", 0),
    )
