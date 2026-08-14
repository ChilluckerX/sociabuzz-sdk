"""FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings
from server.routes import router
from server.session import session_store

logger = logging.getLogger("sociabuzz")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.AUTH_ENABLED:
        logger.info("API key authentication: ENABLED (%d key(s))", len(settings.ALL_KEYS))
    else:
        logger.warning("API key authentication: DISABLED — set API_KEY in .env for production!")

    from server.webhook import webhook_dispatcher

    if webhook_dispatcher:
        webhook_dispatcher.start()

    yield

    # Shutdown
    if webhook_dispatcher:
        await webhook_dispatcher.stop()
    await session_store.close_all()


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application."""
    app = FastAPI(
        title="SociaBuzz Payment Gateway",
        description=(
            "Reverse-engineered wrapper for SociaBuzz donations.\n\n"
            "**18 countries supported** — from Malaysia/Indonesia to US/UK/Australia.\n\n"
            "Flow: check fees → donate → list methods → create payment → "
            "check status / webhook.\n\n"
            "Auth: send `Authorization: Bearer <API_KEY>` or `X-API-Key` header."
        ),
        version="3.0.0",
        lifespan=lifespan,
    )
    app.include_router(router)

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "active_sessions": session_store.count,
            "auth_enabled": settings.AUTH_ENABLED,
            "webhook_enabled": settings.WEBHOOK_ENABLED,
        }

    return app
