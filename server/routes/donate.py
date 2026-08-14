"""Step 1 — POST /api/donate"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from config import settings
from server.auth import verify_api_key
from server.schemas import DonateRequest, DonateResponse
from server.session import session_store
from sociabuzz import SociaBuzz
from sociabuzz.exceptions import DonationError, UnsupportedCountryError

router = APIRouter()


@router.post("/api/donate", response_model=DonateResponse, dependencies=[Depends(verify_api_key)])
async def donate(req: DonateRequest):
    """Submit a donation — returns a **token** for all subsequent steps."""
    username = req.username or settings.DEFAULT_CREATOR
    if not username:
        raise HTTPException(
            400,
            "No creator username supplied and DEFAULT_CREATOR is not set. "
            "Provide 'username' in the request or set SOCIABUZZ_USERNAME / DEFAULT_CREATOR in .env",
        )

    sb = SociaBuzz(base_url=settings.BASE_URL)

    try:
        donation = await sb.donate(
            username=username,
            amount=req.amount,
            country=req.country,
            fullname=req.fullname,
            email=req.email,
            note=req.note,
        )
    except UnsupportedCountryError as exc:
        raise HTTPException(400, str(exc))
    except DonationError as exc:
        if exc.errors:
            raise HTTPException(400, {"message": str(exc), "errors": exc.errors})
        raise HTTPException(502, str(exc))

    donation.callback_url = req.callback_url
    session_store.store(donation)

    return DonateResponse(
        success=True,
        token=donation.token,
        country=donation.country,
        currency=donation.currency,
        amount=donation.amount,
        redirect_url=donation.redirect_url,
        expires_in=donation.expires_in,
    )
