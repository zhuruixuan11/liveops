import random
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, scope_staff_id
from app.models.all import SalesOrder, SalesOrderDetail, LiveSession, PaymentRecord, SkuInfo, Product, Coupon
from app.schemas.all import OrderOut, OrderDetailOut, PayRequest, OrderCreate, PageResp

router = APIRouter()


@router.post("", response_model=OrderOut)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="items required")

    user_id = int(current_user["sub"])
    total_amount = Decimal("0")
    details = []

    for item in payload.items:
        sku = db.scalar(select(SkuInfo).where(SkuInfo.sku_id == item.sku_id))
        if not sku:
            raise HTTPException(status_code=400, detail=f"sku {item.sku_id} not found")
        if sku.stock < item.qty:
            raise HTTPException(status_code=400, detail=f"sku {item.sku_id} out of stock")
        sku.stock -= item.qty

        product = db.scalar(select(Product).where(Product.product_id == sku.product_id))
        subtotal = Decimal(sku.price) * item.qty
        total_amount += subtotal

        details.append({
            "sku_id": sku.sku_id,
            "product_name": product.product_name if product else "",
            "spec": sku.spec,
            "price": sku.price,
            "qty": item.qty,
            "subtotal": subtotal,
            "coupon_applied": 0,
        })

    discount_amount = Decimal("0")
    coupon_id = None
    if payload.coupon_id:
        coupon = db.scalar(select(Coupon).where(Coupon.coupon_id == payload.coupon_id))
        if not coupon:
            raise HTTPException(status_code=400, detail="coupon not found")
        if coupon.session_id and coupon.session_id != payload.session_id:
            raise HTTPException(status_code=400, detail="coupon not for this session")
        if total_amount < Decimal(coupon.threshold):
            raise HTTPException(status_code=400, detail=f"need {coupon.threshold} to use coupon")
        if coupon.type == "discount":
            discount_amount = Decimal(coupon.discount)
        elif coupon.type == "percent":
            discount_amount = (total_amount * (Decimal("1") - Decimal(coupon.discount))).quantize(Decimal("0.01"))
        if discount_amount > total_amount:
            discount_amount = total_amount
        coupon_id = coupon.coupon_id

    pay_amount = total_amount - discount_amount
    order_id = "SO" + datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))

    order = SalesOrder(
        order_id=order_id,
        session_id=payload.session_id,
        store_id=payload.store_id,
        user_id=user_id,
        coupon_id=coupon_id,
        total_amount=total_amount,
        pay_amount=pay_amount,
        discount_amount=discount_amount,
        status="01",
        channel=payload.channel or "LIVE",
    )
    db.add(order)
    for d in details:
        db.add(SalesOrderDetail(order_id=order_id, **d))

    db.commit()
    db.refresh(order)
    return order


@router.get("", response_model=PageResp[OrderOut])
def list_orders(
    session_id: Optional[int] = Query(None),
    store_id: Optional[int] = Query(None),
    host_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    host_scope = scope_staff_id(user, db)
    if host_scope is not None:
        host_id = host_scope
    stmt = select(SalesOrder)
    if session_id:
        stmt = stmt.where(SalesOrder.session_id == session_id)
    if store_id:
        stmt = stmt.where(SalesOrder.store_id == store_id)
    if host_id:
        stmt = stmt.join(LiveSession, LiveSession.session_id == SalesOrder.session_id).where(
            LiveSession.host_id == host_id
        )
    if status:
        stmt = stmt.where(SalesOrder.status == status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(
        stmt.order_by(SalesOrder.order_id.desc()).offset((page - 1) * size).limit(size)
    ).all()
    return PageResp(total=total or 0, items=items, page=page, size=size)


@router.get("/{order_id}", response_model=OrderDetailOut)
def get_order(order_id: str, db: Session = Depends(get_db)):
    order = db.scalar(select(SalesOrder).where(SalesOrder.order_id == order_id))
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    details = db.scalars(
        select(SalesOrderDetail).where(SalesOrderDetail.order_id == order_id).order_by(SalesOrderDetail.detail_id)
    ).all()
    return OrderDetailOut(
        **OrderOut.model_validate(order).model_dump(),
        details=[
            {
                "detail_id": d.detail_id,
                "sku_id": d.sku_id,
                "product_name": d.product_name,
                "spec": d.spec,
                "price": float(d.price or 0),
                "qty": d.qty,
                "subtotal": float(d.subtotal or 0),
            }
            for d in details
        ],
    )


@router.post("/{order_id}/pay", response_model=OrderOut)
def pay_order(order_id: str, payload: PayRequest, db: Session = Depends(get_db)):
    order = db.scalar(select(SalesOrder).where(SalesOrder.order_id == order_id))
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    if order.status == "02":
        raise HTTPException(status_code=400, detail="already paid")

    order.status = "02"
    order.pay_time = datetime.now()

    rec = PaymentRecord(
        order_id=order.order_id,
        amount=order.pay_amount,
        channel=payload.channel or "LIVE_PAY",
        status="success",
        pay_time=order.pay_time,
    )
    db.add(rec)
    db.commit()
    db.refresh(order)
    return order
