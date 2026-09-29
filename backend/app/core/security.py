"""
Security utilities: optional API-key middleware, secret masking, CORS helpers.
"""

from __future__ import annotations

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(_api_key_header),
) -> str | None:
    """Validate the API key if one is configured."""
    settings = get_settings()
    if not settings.API_KEY:
        # No key configured → allow all requests
        return None
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key


def mask_secret(value: str, visible: int = 4) -> str:
    """Return a masked version of a secret string for safe logging."""
    if len(value) <= visible:
        return "****"
    return value[:visible] + "*" * (len(value) - visible)
