"""Optional API-key gate. A no-op when API_KEY is unset (local/self-hosted
use), and required on every request when it is set (public deployments)."""
from __future__ import annotations

from fastapi import Header, HTTPException

from app.config import get_settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not settings.API_KEY:
        return
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Missing or invalid API key")
