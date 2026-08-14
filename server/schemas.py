"""Pydantic request / response schemas for the REST API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from sociabuzz.models import FeeInfo, PaymentMethod

# ── Step 1 ────────────────────────────────────────────────────────────


class DonateRequest(BaseModel):
    username: str = Field(
        default="",
        description="Creator's SociaBuzz username (falls back to DEFAULT_CREATOR env var)",
        examples=["your_creator_username"],
    )
    amount: float = Field(
        ...,
        gt=0,
        description="Donation amount in the chosen currency",
        examples=[5.0, 10000],
    )
    country: str = Field(
        default="Malaysia",
        description="Country name — currency is auto-detected",
        examples=["Malaysia", "Indonesia", "Singapore", "Philippines", "Thailand", "United States"],
    )
    fullname: str = Field(
        ...,
        min_length=1,
        description="Donor's display name",
        examples=["John Doe"],
    )
    email: str = Field(
        ...,
        description="Donor's email address",
        examples=["john@example.com"],
    )
    note: str = Field(
        default="",
        description="Optional message to the creator",
        examples=["Keep it up!"],
    )
    callback_url: str = Field(
        default="",
        description=(
            "Merchant webhook URL — gateway will POST the payment result here when status changes"
        ),
        examples=["https://yourapp.com/webhooks/sociabuzz"],
    )


class DonateResponse(BaseModel):
    success: bool
    token: str = Field(..., description="Payment token — use in all subsequent calls")
    country: str
    currency: str
    amount: float = Field(..., description="Actual donation amount (after unit-price rounding)")
    redirect_url: str = Field(..., description="SociaBuzz payment page (for reference)")
    expires_in: int = Field(..., description="Token expiry in seconds")


# ── Step 2 ────────────────────────────────────────────────────────────


class PaymentMethodsRequest(BaseModel):
    token: str = Field(..., description="Token from Step 1")


class PaymentMethodsResponse(BaseModel):
    success: bool
    token: str
    country: str
    currency: str
    amount: float
    methods: list[PaymentMethod]
    total: int = Field(..., description="Number of available methods")


# ── Step 3 ────────────────────────────────────────────────────────────


class CreatePaymentRequest(BaseModel):
    token: str = Field(..., description="Token from Step 1")
    payment_method: str = Field(
        ...,
        description="Method 'name' from Step 2 (e.g. gopay, my_touchngo, qris)",
        examples=["my_touchngo", "gopay", "qris", "bri"],
    )


class CreatePaymentResponse(BaseModel):
    success: bool
    payment_method: str
    label: str
    gateway: str
    fee: FeeInfo
    payment_url: str | None = Field(None, description="URL / deeplink to complete payment")
    qr_string: str | None = Field(None, description="QR code string (for QRIS)")
    token: str
    inv_id: str | None = Field(None, description="Invoice ID — use in Step 4")


# ── Step 4 ────────────────────────────────────────────────────────────


class PaymentStatusRequest(BaseModel):
    token: str = Field(..., description="Token from Step 1")
    inv_id: str = Field(..., description="Invoice ID from Step 3")
    payment_method: str = Field(
        ...,
        description="Payment method used in Step 3",
        examples=["my_touchngo", "gopay"],
    )


class PaymentStatusResponse(BaseModel):
    success: bool
    token: str
    status: str = Field(..., description="pending | paid | expired | failed")


# ── Fees ───────────────────────────────────────────────────────────────


class FeesRequest(BaseModel):
    country: str = Field(
        default="Malaysia",
        description="Country name — currency is auto-detected",
        examples=["Malaysia", "Indonesia", "Thailand", "United States"],
    )
    amount: float = Field(
        ...,
        gt=0,
        description="Donation amount in the country's local currency",
        examples=[5.0, 10000],
    )
    username: str = Field(
        default="",
        description="Creator's SociaBuzz username (falls back to DEFAULT_CREATOR env var)",
    )


class FeeMethodItem(BaseModel):
    id: int
    name: str
    label: str
    group: str
    gateway: str
    currency: str
    amount: float
    fee: FeeInfo


class FeesResponse(BaseModel):
    success: bool
    country: str
    currency: str
    amount: float
    methods: list[FeeMethodItem]
    total: int
