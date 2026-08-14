"""
Fee calculation utilities for the SociaBuzz SDK.

Provides :class:`FeeCalculator` — a standalone helper that fetches live
payment-method fees for a given country + amount **without** requiring
the caller to manage tokens, CSRF, or HTTP sessions manually.

Typical use::

    from sociabuzz import FeeCalculator

    calc = FeeCalculator(username="creator_username")
    estimates = await calc.estimate(country="Malaysia", amount=5.0)
    for e in estimates:
        print(f"{e.label:<20} fee={e.fee.total_fee}  pay={e.fee.total_pay}")
    await calc.close()

The calculator runs the minimal donate → settings flow internally and
returns a list of :class:`FeeEstimate` objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._http import SociaBuzzHTTP
from .client import _build_fee
from .constants import GROUP_LABELS, SUPPORTED_COUNTRIES
from .exceptions import DonationError, UnsupportedCountryError
from .models import FeeInfo


@dataclass
class FeeEstimate:
    """Fee quote for one payment method at a given amount."""

    id: int
    name: str
    label: str
    group: str
    gateway: str
    fee: FeeInfo
    currency: str
    amount: float

    def as_dict(self) -> dict:
        """Return a plain-dict representation (JSON-serialisable)."""
        return {
            "id": self.id,
            "name": self.name,
            "label": self.label,
            "group": self.group,
            "gateway": self.gateway,
            "currency": self.currency,
            "amount": self.amount,
            "fee": self.fee.model_dump(),
        }


class FeeCalculator:
    """Fetch live fee estimates for a country + amount.

    This runs a lightweight donate flow against SociaBuzz (init session,
    submit donation, fetch payment settings) and returns the per-method
    fee breakdown.  No payment is created, so nothing is charged.

    Args:
        base_url: SociaBuzz base URL.
        username: Creator username whose donation page is used for the
            estimate. Required — SociaBuzz's fee data is scoped per
            creator, so there is no universal default.
    """

    def __init__(self, base_url: str = "https://sociabuzz.com", *, username: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self._http = SociaBuzzHTTP(self.base_url)

    async def estimate(
        self,
        country: str,
        amount: float,
        username: str | None = None,
    ) -> list[FeeEstimate]:
        """Return fee estimates for every active method in *country*.

        Args:
            country: Full country name (see :data:`~sociabuzz.constants.SUPPORTED_COUNTRIES`).
            amount: Donation amount in the country's local currency.
            username: Override the creator username for this call.

        Returns:
            List of :class:`FeeEstimate`, one per active payment method.

        Raises:
            UnsupportedCountryError: If *country* is not supported.
            DonationError: If SociaBuzz rejects the donation form.
        """
        info = SUPPORTED_COUNTRIES.get(country)
        if not info:
            raise UnsupportedCountryError(country, list(SUPPORTED_COUNTRIES))

        currency = info["currency"]
        uname = username or self.username

        await self._http.init_session(uname)
        result = await self._http.submit_donation(
            username=uname,
            amount=amount,
            currency=currency,
            fullname="Fee Estimate",
            email="noreply@sociabuzz-sdk.local",
            note="",
        )

        success = result.get("success")
        if success != "true" and success is not True:
            raise DonationError(
                "Donation validation failed during fee estimate",
                errors=result.get("validates", []),
            )

        content = result.get("content", {})
        redirect_url = content.get("redirect", "")
        token = redirect_url.rstrip("/").split("/")[-1] if redirect_url else ""
        if not token:
            raise DonationError("Failed to obtain payment token for fee estimate")

        actual_amount = result.get("_actual_amount", amount)

        await self._http.visit_payment_page(token)
        settings = await self._http.get_payment_settings(
            token=token,
            amount=actual_amount,
            currency=currency,
            country=country,
        )

        return self._parse_settings(settings, currency, actual_amount)

    async def estimate_all(
        self,
        amount_by_currency: dict[str, float] | None = None,
        username: str | None = None,
    ) -> dict[str, list[FeeEstimate]]:
        """Estimate fees for **every** supported country.

        Args:
            amount_by_currency: Optional mapping of currency → amount.
                Countries whose currency is absent use a sensible default
                per currency (see :attr:`DEFAULT_AMOUNTS`).
            username: Override the creator username.

        Returns:
            Mapping of country name → list of fee estimates.
        """
        amounts = {**self.DEFAULT_AMOUNTS, **(amount_by_currency or {})}
        results: dict[str, list[FeeEstimate]] = {}
        uname = username or self.username

        for country, info in SUPPORTED_COUNTRIES.items():
            currency = info["currency"]
            amount = amounts.get(currency, 5.0)
            try:
                results[country] = await self.estimate(country, amount, uname)
            except Exception:
                results[country] = []

        return results

    async def close(self) -> None:
        """Close the underlying HTTP session."""
        await self._http.close()

    async def __aenter__(self) -> FeeCalculator:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    # ── Internal ──────────────────────────────────────────────────

    DEFAULT_AMOUNTS: dict[str, float] = {
        "MYR": 5.0,
        "IDR": 10000.0,
        "SGD": 5.0,
        "PHP": 100.0,
        "THB": 100.0,
        "PKR": 500.0,
        "BDT": 500.0,
        "LKR": 1000.0,
        "AED": 20.0,
        "SAR": 20.0,
        "QAR": 20.0,
        "NGN": 2000.0,
        "ZAR": 50.0,
        "GBP": 5.0,
        "DKK": 50.0,
        "AUD": 5.0,
        "NZD": 5.0,
        "USD": 5.0,
    }

    @staticmethod
    def _parse_settings(settings: dict, currency: str, amount: float) -> list[FeeEstimate]:
        estimates: list[FeeEstimate] = []
        counter = 0
        for group in settings.get("payment_channel", []):
            raw_group = group.get("name", "")
            for m in group.get("available", []):
                if not m.get("active", False):
                    continue
                counter += 1
                estimates.append(
                    FeeEstimate(
                        id=counter,
                        name=m["name"],
                        label=m.get("alias", m["name"]),
                        group=GROUP_LABELS.get(raw_group, raw_group),
                        gateway=m.get("source", ""),
                        fee=_build_fee(m),
                        currency=currency,
                        amount=amount,
                    )
                )
        return estimates
