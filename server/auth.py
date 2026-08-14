"""API key authentication middleware.

When ``settings.AUTH_ENABLED`` is true, every ``/api/*`` request must
include a valid key via one of:

- ``Authorization: Bearer <key>``
- ``X-API-Key: <key>``
- ``?api_key=<key>`` query parameter

If no ``API_KEY`` / ``API_KEYS`` are configured, auth is disabled
(dev only — **never leave empty in production**).
"""

from __future__ import annotations

from fastapi import HTTPException, Request

from config import settings

# Paths that never require auth.
_PUBLIC_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"}


async def verify_api_key(request: Request) -> None:
    """Dependency that validates the API key on protected endpoints."""
    if not settings.AUTH_ENABLED:
        return  # dev mode — no keys configured

    path = request.url.path
    if path in _PUBLIC_PATHS or not path.startswith("/api"):
        return

    key = _extract_key(request)
    if key not in settings.ALL_KEYS:
        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid or missing API key. Provide via "
                "'Authorization: Bearer <key>' or 'X-API-Key'."
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )


def _extract_key(request: Request) -> str:
    """Pull the API key from header, bearer token, or query string."""
    # 1. X-API-Key header
    xkey = request.headers.get("x-api-key", "")
    if xkey:
        return xkey.strip()

    # 2. Authorization: Bearer <key>
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()

    # 3. ?api_key=<key> query param
    qkey = request.query_params.get("api_key", "")
    if qkey:
        return qkey.strip()

    return ""
