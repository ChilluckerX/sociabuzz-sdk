"""Route aggregation — combines all API routers into one."""

from fastapi import APIRouter

from .donate import router as donate_router
from .fees import router as fees_router
from .payment import router as payment_router

router = APIRouter()
router.include_router(donate_router)
router.include_router(payment_router)
router.include_router(fees_router)
