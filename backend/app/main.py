"""FastAPI application entrypoint."""
from __future__ import annotations

import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import require_api_key
from app.config import get_settings
from app.routers import (
    dashboard,
    listings,
    notifications,
    quick_add,
    run_history,
    search,
    search_profiles,
    settings as settings_router,
    sources,
)

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(title="RoomSearch Hannover", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# /api/health stays open (used for uptime checks); everything else is gated
# behind require_api_key, which is a no-op unless API_KEY is set.
_protected = [Depends(require_api_key)]
app.include_router(listings.router, dependencies=_protected)
app.include_router(sources.router, dependencies=_protected)
app.include_router(search_profiles.router, dependencies=_protected)
app.include_router(notifications.router, dependencies=_protected)
app.include_router(settings_router.router, dependencies=_protected)
app.include_router(run_history.router, dependencies=_protected)
app.include_router(search.router, dependencies=_protected)
app.include_router(dashboard.router, dependencies=_protected)
app.include_router(quick_add.router, dependencies=_protected)


@app.get("/api/health")
def health():
    return {"status": "ok"}
