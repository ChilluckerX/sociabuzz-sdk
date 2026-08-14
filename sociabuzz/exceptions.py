"""Custom exceptions for the SociaBuzz SDK."""

from __future__ import annotations


class SociaBuzzError(Exception):
    """Base exception for all SociaBuzz SDK errors."""


class UnsupportedCountryError(SociaBuzzError):
    """Raised when a country is not in the supported list."""

    def __init__(self, country: str, supported: list[str]):
        self.country = country
        self.supported = supported
        super().__init__(f"Unsupported country '{country}'. Choose from: {', '.join(supported)}")


class DonationError(SociaBuzzError):
    """Raised when donation submission fails."""

    def __init__(self, message: str, errors: list | None = None):
        self.errors = errors or []
        super().__init__(message)


class PaymentError(SociaBuzzError):
    """Raised when payment creation or status check fails."""


class SessionExpiredError(SociaBuzzError):
    """Raised when a donation token is not found or has expired."""

    def __init__(self, token: str):
        self.token = token
        super().__init__(f"Session not found for token '{token}'")
