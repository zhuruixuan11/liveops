from datetime import datetime, timedelta, date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.all import SalesOrder, Store, RevenueDaily, LiveSession
from app.schemas.all import SalesDashboardOut, SalesSummary, StoreAnomaly, StoreRankItem

router = APIRouter()


def _previous_window(from_d: date, to_d: date):
    span = (to_d - from_d).days + 1
    prev_to = from_d - timedelta(days=1)
    prev_from = prev_to - timedelta(days=span - 1)
    return prev_from, prev_to


def _build_summary(db, store_id, start_dt, end_dt):
    conds = [SalesOrder.status == "02", SalesOrder.create_time >= start_dt, SalesOrder.create_time <= end_dt]
    if store_id:
        conds.append(SalesOrder.store_id == store_id)

    total_revenue = db.execute(
        select(func.coalesce(func.sum(SalesOrder.pay_amount), 0)).where(and_(*conds))
    ).scalar_one()
    total_orders = db.scalar(
        select(func.count()).select_from(SalesOrder).where(and_(*conds))
    ) or 0
    avg_ticket = total_revenue / total_orders if total_orders else 0

    viewer_conds = [LiveSession.start_time >= start_dt, LiveSession.start_time <= end_dt]
    if store_id:
        viewer_conds.append(LiveSession.store_id == store_id)
    total_viewers = db.execute(
        select(func.coalesce(func.sum(LiveSession.viewer_count), 0)).where(and_(*viewer_conds))
    ).scalar_one()
    conv_rate = round(total_orders / total_viewers * 100, 4) if total_viewers else 0.0

    # 同窗口开播场次
    session_cnt = db.scalar(
        select(func.count()).select_from(LiveSession).where(and_(*viewer_conds))
    ) or 0

    return SalesSummary(
        store_id=store_id,
        date_from=start_dt.date(),
        date_to=end_dt.date(),
        revenue=total_revenue,
        orders=total_orders,
        avg_ticket=avg_ticket,
        conversion_rate=conv_rate,
        gmv=total_revenue,
        aov=avg_ticket,
        sessions=session_cnt,
    )


@router.get("/home")
def home_overview(db: Session = Depends(get_db)):
    """首页概览：门店数、直播中场次、近 7 天 GMV / 订单、当前在线人数"""
    date_from = date.today() - timedelta(days=6)
    start_dt = datetime.combine(date_from, datetime.min.time())
    end_dt = datetime.combine(date.today(), datetime.max.time())

    store_count = db.scalar(
        select(func.count()).select_from(Store).where(Store.status == 1)
    ) or 0

    living = db.scalars(select(LiveSession).where(LiveSession.status == "living")).all()
    living_count = len(living)
    online_viewers = sum(s.viewer_count or 0 for s in living)

    paid_conds = [
        SalesOrder.status == "02",
        SalesOrder.create_time >= start_dt,
        SalesOrder.create_time <= end_dt,
    ]
    gmv_7d = db.execute(
        select(func.coalesce(func.sum(SalesOrder.pay_amount), 0)).where(and_(*paid_conds))
    ).scalar_one()
    orders_7d = db.scalar(
        select(func.count()).select_from(SalesOrder).where(and_(*paid_conds))
    ) or 0

    return {
        "store_count": store_count,
        "living_count": living_count,
        "online_viewers": online_viewers,
        "gmv_7d": float(gmv_7d or 0),
        "orders_7d": orders_7d,
    }


@router.get("/intraday")
def intraday(db: Session = Depends(get_db)):
    """今日按小时成交趋势（数据来自已支付订单的支付时间，无支付则为 0）"""
    start_dt = datetime.combine(date.today(), datetime.min.time())
    rows = db.execute(
        select(SalesOrder.pay_time, SalesOrder.create_time, SalesOrder.pay_amount).where(
            SalesOrder.status == "02",
            SalesOrder.create_time >= start_dt,
        )
    ).all()

    gmv = [0.0] * 24
    orders = [0] * 24
    for pay_time, create_time, amount in rows:
        hour = (pay_time or create_time or datetime.now()).hour
        gmv[hour] += float(amount or 0)
        orders[hour] += 1

    return {
        "date": date.today().isoformat(),
        "hours": [f"{h:02d}:00" for h in range(24)],
        "gmv": [round(v, 2) for v in gmv],
        "orders": orders,
        "total_gmv": round(sum(gmv), 2),
        "total_orders": sum(orders),
    }


@router.get("/sales", response_model=SalesDashboardOut)
def sales_dashboard(
    store_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    if not date_from:
        date_from = date.today() - timedelta(days=6)
    if not date_to:
        date_to = date.today()

    start_dt = datetime.combine(date_from, datetime.min.time())
    end_dt = datetime.combine(date_to, datetime.max.time())

    summary = _build_summary(db, store_id, start_dt, end_dt)

    # Anomaly：对比前一周期 revenue 下滑 > 30% 的门店
    prev_from, prev_to = _previous_window(date_from, date_to)
    prev_start = datetime.combine(prev_from, datetime.min.time())
    prev_end = datetime.combine(prev_to, datetime.max.time())

    stores = db.scalars(select(Store).where(Store.status == 1)).all()
    anomalies: list[StoreAnomaly] = []
    for s in stores:
        cur_rev = db.execute(
            select(func.coalesce(func.sum(SalesOrder.pay_amount), 0)).where(
                SalesOrder.status == "02",
                SalesOrder.store_id == s.store_id,
                SalesOrder.create_time >= start_dt,
                SalesOrder.create_time <= end_dt,
            )
        ).scalar_one()
        prev_rev = db.execute(
            select(func.coalesce(func.sum(SalesOrder.pay_amount), 0)).where(
                SalesOrder.status == "02",
                SalesOrder.store_id == s.store_id,
                SalesOrder.create_time >= prev_start,
                SalesOrder.create_time <= prev_end,
            )
        ).scalar_one()
        if prev_rev and prev_rev > 0:
            drop = (prev_rev - cur_rev) / prev_rev
            if drop > 0.30:
                anomalies.append(StoreAnomaly(
                    store_id=s.store_id,
                    current_revenue=cur_rev,
                    previous_revenue=prev_rev,
                    drop_percent=round(drop * 100, 2),
                ))

    return SalesDashboardOut(summary=summary, anomalies=anomalies)


@router.get("/store-rank")
def store_rank(
    topN: int = Query(10, ge=1, le=50),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    if not date_from:
        date_from = date.today() - timedelta(days=6)
    if not date_to:
        date_to = date.today()
    start_dt = datetime.combine(date_from, datetime.min.time())
    end_dt = datetime.combine(date_to, datetime.max.time())

    rows = db.execute(
        select(
            SalesOrder.store_id,
            func.coalesce(func.sum(SalesOrder.pay_amount), 0).label("gmv"),
            func.count().label("orders"),
        ).where(
            SalesOrder.status == "02",
            SalesOrder.create_time >= start_dt,
            SalesOrder.create_time <= end_dt,
        ).group_by(SalesOrder.store_id)
    ).all()

    items = []
    for store_id, gmv, orders in rows:
        store = db.scalar(select(Store).where(Store.store_id == store_id))
        items.append(StoreRankItem(
            store_id=store_id,
            store_name=store.name if store else f"门店#{store_id}",
            gmv=gmv,
            orders=orders,
            city=store.city if store else None,
        ))
    items.sort(key=lambda x: -float(x.gmv))
    return {"items": items[:topN]}


@router.get("/anomalies")
def anomalies(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    if not date_from:
        date_from = date.today() - timedelta(days=6)
    if not date_to:
        date_to = date.today()
    start_dt = datetime.combine(date_from, datetime.min.time())
    end_dt = datetime.combine(date_to, datetime.max.time())
    prev_from, prev_to = _previous_window(date_from, date_to)
    prev_start = datetime.combine(prev_from, datetime.min.time())
    prev_end = datetime.combine(prev_to, datetime.max.time())

    stores = db.scalars(select(Store).where(Store.status == 1)).all()
    result = []
    for s in stores:
        cur_rev = db.execute(
            select(func.coalesce(func.sum(SalesOrder.pay_amount), 0)).where(
                SalesOrder.status == "02", SalesOrder.store_id == s.store_id,
                SalesOrder.create_time >= start_dt, SalesOrder.create_time <= end_dt,
            )
        ).scalar_one()
        prev_rev = db.execute(
            select(func.coalesce(func.sum(SalesOrder.pay_amount), 0)).where(
                SalesOrder.status == "02", SalesOrder.store_id == s.store_id,
                SalesOrder.create_time >= prev_start, SalesOrder.create_time <= prev_end,
            )
        ).scalar_one()
        if prev_rev and prev_rev > 0:
            drop = (prev_rev - cur_rev) / prev_rev
            if drop > 0.30:
                result.append(StoreAnomaly(
                    store_id=s.store_id, current_revenue=cur_rev,
                    previous_revenue=prev_rev, drop_percent=round(drop * 100, 2),
                ))
    return {"items": result}
