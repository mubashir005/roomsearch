"""Manual search trigger: the "Search Now" button (task section 14)."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.pipeline import run_search
from app.schemas import SearchRunOut

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/run", response_model=SearchRunOut)
def trigger_manual_search(db: Session = Depends(get_db)):
    run = asyncio.run(run_search(db, trigger="manual"))
    return run
