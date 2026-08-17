"""Search profile CRUD (task section 12)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SearchProfile
from app.schemas import SearchProfileIn, SearchProfileOut

router = APIRouter(prefix="/api/search-profiles", tags=["search-profiles"])


@router.get("", response_model=list[SearchProfileOut])
def list_profiles(db: Session = Depends(get_db)):
    return list(db.execute(select(SearchProfile)).scalars().all())


@router.post("", response_model=SearchProfileOut)
def create_profile(payload: SearchProfileIn, db: Session = Depends(get_db)):
    profile = SearchProfile(**payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.put("/{profile_id}", response_model=SearchProfileOut)
def update_profile(profile_id: int, payload: SearchProfileIn, db: Session = Depends(get_db)):
    profile = db.get(SearchProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/{profile_id}")
def delete_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.get(SearchProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(profile)
    db.commit()
    return {"deleted": True}
