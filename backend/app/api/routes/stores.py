from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.all import Store, LiveSession, Staff
from app.schemas.all import (
    StoreCreate, StoreUpdate, StoreOut, StoreDetailOut, PageResp,
)

router = APIRouter()


@router.get("", response_model=PageResp[StoreOut])
def list_stores(
    city: Optional[str] = Query(None),
    status: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(Store)
    if city:
        stmt = stmt.where(Store.city == city)
    if status is not None:
        stmt = stmt.where(Store.status == status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(stmt.offset((page - 1) * size).limit(size)).all()
    return PageResp(total=total or 0, items=items, page=page, size=size)


@router.get("/{store_id}", response_model=StoreDetailOut)
def get_store(store_id: int, db: Session = Depends(get_db)):
    store = db.scalar(select(Store).where(Store.store_id == store_id))
    if not store:
        raise HTTPException(status_code=404, detail="store not found")
    live_count = db.scalar(
        select(func.count()).select_from(LiveSession).where(LiveSession.store_id == store_id)
    ) or 0
    staff_count = db.scalar(
        select(func.count()).select_from(Staff).where(Staff.store_id == store_id)
    ) or 0
    data = StoreOut.model_validate(store).model_dump()
    return StoreDetailOut(**data, live_session_count=live_count, staff_count=staff_count)


@router.post("", response_model=StoreOut)
def create_store(payload: StoreCreate, db: Session = Depends(get_db)):
    store = Store(**payload.model_dump())
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


@router.put("/{store_id}", response_model=StoreOut)
def update_store(store_id: int, payload: StoreUpdate, db: Session = Depends(get_db)):
    store = db.scalar(select(Store).where(Store.store_id == store_id))
    if not store:
        raise HTTPException(status_code=404, detail="store not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(store, k, v)
    db.commit()
    db.refresh(store)
    return store
