"""Data models shared between the SDK and the API server."""

from __future__ import annotations

from pydantic import BaseModel


class FeeInfo(BaseModel):
    """Fee breakdown for a payment method."""

    fee_type: str = ""
    fee_rate: float = 0
    fee_fixed: float = 0
    total_fee: str = "0"
    total_pay: str = "0"
    min_amount: float = 0
    max_amount: float = 0


class PaymentMethod(BaseModel):
    """A single available payment method."""

    id: int
    name: str
    label: str
    group: str
    gateway: str
    fee: FeeInfo
