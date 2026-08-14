"""Steps 2–4 — /api/payment/*"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from config import settings
from server.auth import verify_api_key
from server.schemas import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    PaymentMethodsRequest,
    PaymentMethodsResponse,
    PaymentStatusRequest,
    PaymentStatusResponse,
)
from server.session import SQLiteSessionStore, session_store
from sociabuzz.exceptions import PaymentError, SessionExpiredError

router = APIRouter(prefix="/api/payment")


# ── Step 2 — list methods ────────────────────────────────────────────


@router.post(
    "/methods", response_model=PaymentMethodsResponse, dependencies=[Depends(verify_api_key)]
)
async def list_methods(req: PaymentMethodsRequest):
    """List every available payment method (numbered) with fee details."""
    try:
        donation = session_store.get(req.token, settings.BASE_URL)
    except SessionExpiredError as exc:
        raise HTTPException(400, str(exc))

    try:
        methods = await donation.get_payment_methods()
    except Exception as exc:
        raise HTTPException(502, f"Failed to fetch payment methods: {exc}")

    # Persist refreshed CSRF + cookies back to the store (if SQLite).
    if isinstance(session_store, SQLiteSessionStore):
        session_store.update_csrf(req.token, donation._csrf, donation._http.serialize_cookies())

    return PaymentMethodsResponse(
        success=True,
        token=req.token,
        country=donation.country,
        currency=donation.currency,
        amount=donation.amount,
        methods=methods,
        total=len(methods),
    )


# ── Step 3 — create payment ──────────────────────────────────────────


@router.post(
    "/create", response_model=CreatePaymentResponse, dependencies=[Depends(verify_api_key)]
)
async def create_payment(req: CreatePaymentRequest):
    """Pick a method and get a payment URL (or QR string) to redirect the user."""
    try:
        donation = session_store.get(req.token, settings.BASE_URL)
    except SessionExpiredError as exc:
        raise HTTPException(400, str(exc))

    try:
        payment = await donation.create_payment(req.payment_method)
    except PaymentError as exc:
        raise HTTPException(404, str(exc))
    except Exception as exc:
        raise HTTPException(502, f"Failed to create payment: {exc}")

    # Persist CSRF/cookies after create.
    if isinstance(session_store, SQLiteSessionStore):
        session_store.update_csrf(req.token, donation._csrf, donation._http.serialize_cookies())
        # Track for webhook polling.
        session_store.store_payment(
            token=req.token,
            inv_id=payment.inv_id or "",
            payment_method=payment.method,
            label=payment.label,
            gateway=payment.gateway,
            payment_url=payment.payment_url,
            qr_string=payment.qr_string,
            fee=payment.fee.model_dump(),
        )

    # Register with webhook dispatcher for background polling.
    from server.webhook import webhook_dispatcher

    if webhook_dispatcher and payment.inv_id:
        await webhook_dispatcher.track(
            token=req.token,
            inv_id=payment.inv_id,
            payment_method=payment.method,
            base_url=settings.BASE_URL,
        )

    return CreatePaymentResponse(
        success=True,
        payment_method=payment.method,
        label=payment.label,
        gateway=payment.gateway,
        fee=payment.fee,
        payment_url=payment.payment_url,
        qr_string=payment.qr_string,
        token=payment.token,
        inv_id=payment.inv_id,
    )


# ── Step 4 — check status ────────────────────────────────────────────


@router.post(
    "/status", response_model=PaymentStatusResponse, dependencies=[Depends(verify_api_key)]
)
async def check_status(req: PaymentStatusRequest):
    """Poll until the payment is ``paid``, ``expired``, or ``failed``."""
    try:
        donation = session_store.get(req.token, settings.BASE_URL)
    except SessionExpiredError as exc:
        raise HTTPException(400, str(exc))

    try:
        status = await donation.check_payment_status(req.payment_method, req.inv_id)
    except Exception as exc:
        raise HTTPException(502, f"Failed to check status: {exc}")

    return PaymentStatusResponse(
        success=True,
        token=req.token,
        status=status,
    )
