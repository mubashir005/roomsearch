"""Run history + logging API (task sections 7, 20)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SearchRun
from app.schemas import SearchRunOut

router = APIRouter(prefix="/api/run-history", tags=["run-history"])


@router.get("", response_model=list[SearchRunOut])
def list_runs(db: Session = Depends(get_db), limit: int = 50):
    stmt = select(SearchRun).order_by(SearchRun.started_at.desc()).limit(limit)
    return list(db.execute(stmt).scalars().all())


@router.get("/{run_id}", response_model=SearchRunOut)
def get_run(run_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException

    run = db.get(SearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
