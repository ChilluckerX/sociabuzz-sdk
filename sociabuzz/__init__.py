"""
SociaBuzz SDK
=============

Reverse-engineered Python SDK for `SociaBuzz <https://sociabuzz.com>`_
donations.  18 countries supported.

Quick start::

    from sociabuzz import SociaBuzz

    sb = SociaBuzz()
    donation = await sb.donate(
        username="creator", amount=5.0, country="Malaysia",
        fullname="John", email="john@test.com",
    )
    methods = await donation.get_payment_methods()
    payment = await donation.create_payment("my_touchngo")
    print(payment.payment_url)
"""

from .client import Donation, Payment, SociaBuzz
from .constants import SUPPORTED_COUNTRIES
from .exceptions import (
    DonationError,
    PaymentError,
    SessionExpiredError,
    SociaBuzzError,
    UnsupportedCountryError,
)
from .fees import FeeCalculator, FeeEstimate
from .models import FeeInfo, PaymentMethod

__all__ = [
    "SociaBuzz",
    "Donation",
    "Payment",
    "FeeCalculator",
    "FeeEstimate",
    "FeeInfo",
    "PaymentMethod",
    "SUPPORTED_COUNTRIES",
    "SociaBuzzError",
    "UnsupportedCountryError",
    "DonationError",
    "PaymentError",
    "SessionExpiredError",
]
