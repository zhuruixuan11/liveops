from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.all import Coupon, CouponIssue
from app.schemas.all import CouponCreate, CouponOut, CouponIssueOut, CouponDetailOut

router = APIRouter()


@router.get("/", response_model=list[CouponOut])
def list_coupons(
    session_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    stmt = select(Coupon)
    if session_id:
        stmt = stmt.where(Coupon.session_id == session_id)
    return db.scalars(stmt.order_by(Coupon.coupon_id.desc())).all()


@router.post("/", response_model=CouponOut)
def create_coupon(payload: CouponCreate, db: Session = Depends(get_db)):
    coupon = Coupon(**payload.model_dump())
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.post("/issue", response_model=CouponIssueOut)
def issue_coupon(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    coupon_id = payload.get("coupon_id")
    session_id = payload.get("session_id")
    if not coupon_id:
        raise HTTPException(status_code=400, detail="coupon_id required")
    coupon = db.scalar(select(Coupon).where(Coupon.coupon_id == coupon_id))
    if not coupon:
        raise HTTPException(status_code=404, detail="coupon not found")
    if coupon.stock and coupon.stock <= coupon.issued:
        raise HTTPException(status_code=400, detail="coupon out of stock")
    coupon.issued += 1
    issue = CouponIssue(
        coupon_id=coupon.coupon_id,
        session_id=session_id or coupon.session_id,
        user_id=int(current_user["sub"]),
        issued_by="MANUAL",
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue


@router.get("/stats")
def coupon_stats(db: Session = Depends(get_db)):
    """优惠券运营看板：状态、发放进度、剩余、到期与 AI/人工发放来源。"""
    coupons = db.scalars(select(Coupon).order_by(Coupon.coupon_id.desc())).all()
    agg = db.execute(
        select(CouponIssue.coupon_id, CouponIssue.issued_by, func.count())
        .group_by(CouponIssue.coupon_id, CouponIssue.issued_by)
    ).all()
    by_coupon: dict[int, dict] = {}
    for cid, issued_by, cnt in agg:
        item = by_coupon.setdefault(cid, {"AGENT": 0, "MANUAL": 0})
        if issued_by in item:
            item[issued_by] = cnt

    now = datetime.now()
    items = []
    for c in coupons:
        remain = max(0, (c.stock or 0) - (c.issued or 0))
        expire_days = (c.valid_end - now).days if c.valid_end else None
        if c.valid_start and now < c.valid_start:
            status = "upcoming"
        elif c.valid_end and now > c.valid_end:
            status = "expired"
        elif remain <= 0:
            status = "sold_out"
        else:
            status = "active"
        items.append({
            "coupon_id": c.coupon_id,
            "session_id": c.session_id,
            "type": c.type,
            "threshold": float(c.threshold or 0),
            "discount": float(c.discount or 0),
            "stock": c.stock or 0,
            "issued": c.issued or 0,
            "remain": remain,
            "valid_start": c.valid_start,
            "valid_end": c.valid_end,
            "expire_days": expire_days,
            "status": status,
            "issued_agent": by_coupon.get(c.coupon_id, {}).get("AGENT", 0),
            "issued_manual": by_coupon.get(c.coupon_id, {}).get("MANUAL", 0),
        })

    total_stock = sum(c.stock or 0 for c in coupons)
    total_issued = sum(c.issued or 0 for c in coupons)
    return {
        "total": len(coupons),
        "total_stock": total_stock,
        "total_issued": total_issued,
        "total_remain": max(0, total_stock - total_issued),
        "expiring_7d": sum(1 for i in items if i["expire_days"] is not None and 0 <= i["expire_days"] <= 7),
        "agent_issued": sum(v["AGENT"] for v in by_coupon.values()),
        "items": items,
    }


@router.get("/{coupon_id}", response_model=CouponDetailOut)
def get_coupon(coupon_id: int, db: Session = Depends(get_db)):
    coupon = db.scalar(select(Coupon).where(Coupon.coupon_id == coupon_id))
    if not coupon:
        raise HTTPException(status_code=404, detail="coupon not found")
    issues = db.scalars(
        select(CouponIssue).where(CouponIssue.coupon_id == coupon_id).order_by(CouponIssue.issue_id.desc())
    ).all()
    return CouponDetailOut(
        **CouponOut.model_validate(coupon).model_dump(),
        issues=[CouponIssueOut.model_validate(i) for i in issues],
    )
