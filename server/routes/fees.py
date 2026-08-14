"""Fees — POST /api/fees and GET /api/fees/countries"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from config import settings
from server.auth import verify_api_key
from server.schemas import FeeMethodItem, FeesRequest, FeesResponse
from sociabuzz import FeeCalculator
from sociabuzz.constants import SUPPORTED_COUNTRIES
from sociabuzz.exceptions import DonationError, UnsupportedCountryError

router = APIRouter(prefix="/api/fees")


@router.post("", response_model=FeesResponse, dependencies=[Depends(verify_api_key)])
async def get_fees(req: FeesRequest):
    """List every payment method's fee/tax for a given country + amount.

    No donation is created and nothing is charged — this runs a lightweight
    donate → settings flow and returns the live fee table.
    """
    info = SUPPORTED_COUNTRIES.get(req.country)
    if not info:
        raise HTTPException(400, f"Unsupported country '{req.country}'.")

    username = req.username or settings.DEFAULT_CREATOR
    if not username:
        raise HTTPException(
            400,
            "No creator username supplied and DEFAULT_CREATOR is not set.",
        )

    calc = FeeCalculator(base_url=settings.BASE_URL, username=username)
    try:
        estimates = await calc.estimate(country=req.country, amount=req.amount)
    except UnsupportedCountryError as exc:
        raise HTTPException(400, str(exc))
    except DonationError as exc:
        if exc.errors:
            raise HTTPException(400, {"message": str(exc), "errors": exc.errors})
        raise HTTPException(502, str(exc))
    except Exception as exc:
        raise HTTPException(502, f"Failed to fetch fees: {exc}")
    finally:
        await calc.close()

    return FeesResponse(
        success=True,
        country=req.country,
        currency=info["currency"],
        amount=req.amount,
        methods=[FeeMethodItem(**e.as_dict()) for e in estimates],
        total=len(estimates),
    )


@router.get("/countries", dependencies=[Depends(verify_api_key)])
async def list_countries():
    """List every supported country with its currency and ISO code."""
    return {
        "success": True,
        "total": len(SUPPORTED_COUNTRIES),
        "countries": [
            {"country": name, "currency": data["currency"], "iso2": data["iso2"]}
            for name, data in SUPPORTED_COUNTRIES.items()
        ],
    }
