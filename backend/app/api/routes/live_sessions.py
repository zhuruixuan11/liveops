import random
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, update
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, scope_staff_id
from app.models.all import LiveSession, LiveProduct, Store, Staff, Product, SalesOrder, CouponIssue, SkuInfo
from app.schemas.all import (
    LiveSessionCreate, LiveSessionUpdate, StatusUpdate,
    LiveSessionOut, LiveSessionDetailOut, LiveProductOut, DashboardOut, PageResp,
)

router = APIRouter()


def _attach_store_host(session_out: dict, session: LiveSession, db: Session) -> dict:
    if session.store_id:
        store = db.scalar(select(Store).where(Store.store_id == session.store_id))
        session_out["store_name"] = store.name if store else None
    if session.host_id:
        host = db.scalar(select(Staff).where(Staff.staff_id == session.host_id))
        session_out["host_name"] = host.name if host else None
    return session_out


@router.get("", response_model=PageResp[LiveSessionOut])
def list_sessions(
    store_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    host_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    host_scope = scope_staff_id(user, db)
    if host_scope is not None:
        host_id = host_scope
    stmt = select(LiveSession)
    if store_id:
        stmt = stmt.where(LiveSession.store_id == store_id)
    if status:
        stmt = stmt.where(LiveSession.status == status)
    if host_id:
        stmt = stmt.where(LiveSession.host_id == host_id)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(
        stmt.order_by(LiveSession.session_id.desc()).offset((page - 1) * size).limit(size)
    ).all()

    out_items = []
    for s in items:
        d = LiveSessionOut.model_validate(s).model_dump()
        d = _attach_store_host(d, s, db)
        # GMV
        gmv = db.execute(
            select(func.coalesce(func.sum(SalesOrder.pay_amount), 0)).where(
                SalesOrder.session_id == s.session_id, SalesOrder.status == "02"
            )
        ).scalar_one()
        d["gmv"] = gmv
        out_items.append(d)

    return PageResp(total=total or 0, items=out_items, page=page, size=size)


@router.post("", response_model=LiveSessionOut)
def create_session(payload: LiveSessionCreate, db: Session = Depends(get_db)):
    session = LiveSession(
        store_id=payload.store_id,
        host_id=payload.host_id,
        title=payload.title,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status=payload.status or "planned",
    )
    db.add(session)
    db.flush()

    for lp in payload.live_products or []:
        db.add(LiveProduct(
            session_id=session.session_id,
            product_id=lp.product_id,
            sku_id=lp.sku_id,
            is_focus=lp.is_focus,
        ))

    db.commit()
    db.refresh(session)
    return session


@router.put("/{session_id}", response_model=LiveSessionOut)
def update_session(session_id: int, payload: LiveSessionUpdate, db: Session = Depends(get_db)):
    session = db.scalar(select(LiveSession).where(LiveSession.session_id == session_id))
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(session, k, v)
    db.commit()
    db.refresh(session)
    return session


@router.put("/{session_id}/status", response_model=LiveSessionOut)
def update_status(session_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    session = db.scalar(select(LiveSession).where(LiveSession.session_id == session_id))
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    old_status = session.status
    session.status = payload.status
    if old_status != "living" and payload.status == "living":
        session.viewer_count = random.randint(800, 5000)
        session.peak_viewer = session.viewer_count
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}", response_model=LiveSessionDetailOut)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.scalar(select(LiveSession).where(LiveSession.session_id == session_id))
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    out = LiveSessionOut.model_validate(session).model_dump()
    out = _attach_store_host(out, session, db)

    live_products = db.scalars(
        select(LiveProduct).where(LiveProduct.session_id == session_id).order_by(LiveProduct.id)
    ).all()

    lps_out = []
    for lp in live_products:
        lp_dict = LiveProductOut.model_validate(lp).model_dump()
        product = db.scalar(select(Product).where(Product.product_id == lp.product_id))
        if product:
            lp_dict["product_name"] = product.product_name
            if lp.sku_id:
                sku = db.scalar(select(SkuInfo).where(SkuInfo.sku_id == lp.sku_id))
                if sku:
                    lp_dict["spec"] = sku.spec
                    lp_dict["price"] = sku.price
                    lp_dict["stock"] = sku.stock
        lps_out.append(lp_dict)

    out["live_products"] = lps_out
    return LiveSessionDetailOut(**out)


@router.get("/{session_id}/dashboard", response_model=DashboardOut)
def session_dashboard(session_id: int, db: Session = Depends(get_db)):
    session = db.scalar(select(LiveSession).where(LiveSession.session_id == session_id))
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    coupon_issued = db.scalar(
        select(func.count()).select_from(CouponIssue).where(CouponIssue.session_id == session_id)
    ) or 0

    gmv_row = db.execute(
        select(func.coalesce(func.sum(SalesOrder.pay_amount), 0)).where(
            SalesOrder.session_id == session_id, SalesOrder.status == "02"
        )
    ).scalar_one()

    orders = db.scalar(
        select(func.count()).select_from(SalesOrder).where(
            SalesOrder.session_id == session_id, SalesOrder.status == "02"
        )
    ) or 0

    conv_rate = 0.0
    if session.viewer_count and session.viewer_count > 0:
        conv_rate = round(orders / session.viewer_count * 100, 4)

    return DashboardOut(
        session_id=session_id,
        viewer_count=session.viewer_count,
        peak_viewer=session.peak_viewer,
        coupon_issued_count=coupon_issued,
        gmv=gmv_row,
        orders=orders,
        conversion_rate=conv_rate,
    )
