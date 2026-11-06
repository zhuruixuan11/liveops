"""外部平台数据同步：把抖音/快手等平台的订单、商品、直播场次映射进本平台表结构"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.database import engine
from app.models.all import (
    PlatformAccount, PlatformSyncLog, SalesOrder, SalesOrderDetail,
    Product, SkuInfo, ProductCategory, LiveSession, Store, Staff,
)
from app.integrations.douyin_client import (
    DouyinOpenClient, DouyinApiError,
    mock_orders, mock_products, mock_live_rooms,
)

# 外部订单状态 -> 本平台状态（01 待支付 / 02 已支付 / 03 已取消）
ORDER_STATUS_MAP = {1: "01", 2: "02", 3: "02", 4: "02", 5: "03"}


def ensure_tables() -> None:
    """首次启动时自动建表（老库无需手动迁移）"""
    PlatformAccount.__table__.create(bind=engine, checkfirst=True)
    PlatformSyncLog.__table__.create(bind=engine, checkfirst=True)
    # 扩展订单来源枚举，支持外部平台渠道
    try:
        with engine.begin() as conn:
            conn.execute(text(
                "ALTER TABLE sales_order MODIFY channel "
                "ENUM('LIVE','STORE_PICKUP','DOUYIN','KUAISHOU','WECHAT_CHANNEL') DEFAULT 'LIVE'"
            ))
    except Exception:  # noqa: BLE001
        pass


PLATFORM_LABEL = {"DOUYIN": "抖音", "KUAISHOU": "快手", "WECHAT_CHANNEL": "视频号"}


def _client(account: PlatformAccount) -> DouyinOpenClient:
    return DouyinOpenClient(
        app_key=account.app_key or "",
        app_secret=account.app_secret or "",
        access_token=account.access_token,
    )


def _resolve_store(db: Session, account: PlatformAccount) -> int:
    if account.store_id:
        return int(account.store_id)
    store = db.scalar(select(Store).order_by(Store.store_id))
    return int(store.store_id) if store else 1


def _resolve_host(db: Session, store_id: int):
    """live_session.host_id 非空：外部场次挂到该门店主播，没有则取任一主播"""
    host = db.scalar(
        select(Staff).where(Staff.store_id == store_id, Staff.role == "HOST")
        .order_by(Staff.staff_id)
    )
    if not host:
        host = db.scalar(select(Staff).where(Staff.role == "HOST").order_by(Staff.staff_id))
    return host.staff_id if host else None


def _resolve_session(db: Session, account: PlatformAccount, store_id: int) -> int:
    """外部订单必须挂到一场场次上：优先取该门店正在播的场次，没有再建一个外部同步场次"""
    session = db.scalar(
        select(LiveSession)
        .where(LiveSession.store_id == store_id, LiveSession.status == "living")
        .order_by(LiveSession.session_id.desc())
    )
    if session:
        return int(session.session_id)

    label = PLATFORM_LABEL.get(account.platform, account.platform)
    title = f"{label}直播 · {account.account_name}"[:128]
    session = db.scalar(
        select(LiveSession).where(LiveSession.title == title, LiveSession.store_id == store_id)
    )
    if not session:
        session = LiveSession(
            store_id=store_id,
            host_id=_resolve_host(db, store_id),
            title=title,
            start_time=datetime.utcnow(),
            status="living",
            viewer_count=0,
            peak_viewer=0,
        )
        db.add(session)
        db.flush()
    return int(session.session_id)


# ---------------- 订单 ----------------
def _fetch_orders(account: PlatformAccount) -> List[Dict[str, Any]]:
    if account.bind_mode == "MOCK":
        return mock_orders()
    return _client(account).fetch_orders(page=0, size=50)


def sync_orders(db: Session, account: PlatformAccount) -> PlatformSyncLog:
    log = PlatformSyncLog(
        account_id=account.account_id, sync_type="ORDER",
        bind_mode=account.bind_mode, status="SUCCESS",
    )
    store_id = _resolve_store(db, account)
    session_id = _resolve_session(db, account, store_id)
    created = updated = 0
    try:
        rows = _fetch_orders(account)
        log.fetched = len(rows)
        for ext in rows:
            ext_id = str(ext.get("order_id") or "")
            if not ext_id:
                continue
            prefix = "DY" if account.platform == "DOUYIN" else "EXT"
            order_id = (ext_id if ext_id.startswith(prefix) else f"{prefix}{ext_id}")[:32]
            exists = db.scalar(select(SalesOrder).where(SalesOrder.order_id == order_id))
            items = ext.get("items") or []
            gross = sum(Decimal(str(i.get("price", 0))) * int(i.get("qty", 1)) for i in items)
            pay = Decimal(str(ext.get("pay_amount") or gross or 0))
            status = ORDER_STATUS_MAP.get(int(ext.get("order_status") or 2), "02")

            if exists:
                exists.status = status
                exists.pay_amount = pay
                updated += 1
                continue

            order = SalesOrder(
                order_id=order_id,
                session_id=session_id,
                store_id=store_id,
                user_id=None,
                total_amount=gross or pay,
                pay_amount=pay,
                discount_amount=max(Decimal("0"), (gross or pay) - pay),
                status=status,
                channel="DOUYIN" if account.platform == "DOUYIN" else "KUAISHOU",
                create_time=_parse_time(ext.get("create_time")),
                pay_time=_parse_time(ext.get("pay_time")),
            )
            db.add(order)
            for it in items:
                price = Decimal(str(it.get("price", 0)))
                qty = int(it.get("qty", 1))
                db.add(SalesOrderDetail(
                    order_id=order_id,
                    sku_id=None,
                    product_name=str(it.get("product_name", ""))[:128],
                    spec=str(it.get("spec", ""))[:255],
                    price=price,
                    qty=qty,
                    subtotal=price * qty,
                ))
            created += 1
        account.last_sync_at = datetime.utcnow()
        log.created_count, log.updated_count = created, updated
        log.message = f"拉取 {log.fetched} 单，新增 {created}，更新 {updated}"
    except DouyinApiError as e:
        log.status = "FAILED"
        log.message = str(e)[:480]
    except Exception as e:  # noqa: BLE001
        log.status = "FAILED"
        log.message = f"同步异常: {e}"[:480]
    log.finished_at = datetime.utcnow()
    db.add(log)
    db.commit()
    return log


# ---------------- 商品 ----------------
def _fetch_products(account: PlatformAccount) -> List[Dict[str, Any]]:
    if account.bind_mode == "MOCK":
        return mock_products()
    return _client(account).fetch_products(page=0, size=50)


def sync_products(db: Session, account: PlatformAccount) -> PlatformSyncLog:
    log = PlatformSyncLog(
        account_id=account.account_id, sync_type="PRODUCT",
        bind_mode=account.bind_mode, status="SUCCESS",
    )
    created = updated = 0
    try:
        rows = _fetch_products(account)
        log.fetched = len(rows)
        category = db.scalar(select(ProductCategory).order_by(ProductCategory.category_id))
        if not category:
            category = ProductCategory(name="抖音同步", level=1)
            db.add(category)
            db.flush()

        for ext in rows:
            name = str(ext.get("name") or ext.get("product_name") or "").strip()
            if not name:
                continue
            product = db.scalar(select(Product).where(Product.product_name == name))
            if not product:
                product = Product(
                    category_id=category.category_id,
                    product_name=name[:128],
                    subtitle="同步自抖音小店",
                    brand="DOUYIN",
                    status=1,
                )
                db.add(product)
                db.flush()
                created += 1
            else:
                updated += 1

            for sku in ext.get("skus") or []:
                code = str(sku.get("code") or sku.get("sku_id") or "")
                if not code:
                    continue
                exist_sku = db.scalar(select(SkuInfo).where(SkuInfo.sku_code == code[:64]))
                price = Decimal(str(sku.get("price", 0)))
                stock = int(sku.get("stock", 0))
                if exist_sku:
                    exist_sku.price = price
                    exist_sku.stock = stock
                else:
                    db.add(SkuInfo(
                        product_id=product.product_id,
                        sku_code=code[:64],
                        spec=str(sku.get("spec", ""))[:128],
                        price=price,
                        stock=stock,
                    ))
        account.last_sync_at = datetime.utcnow()
        log.created_count, log.updated_count = created, updated
        log.message = f"拉取 {log.fetched} 个商品，新增 {created}，更新 {updated}"
    except DouyinApiError as e:
        log.status = "FAILED"
        log.message = str(e)[:480]
    except Exception as e:  # noqa: BLE001
        log.status = "FAILED"
        log.message = f"同步异常: {e}"[:480]
    log.finished_at = datetime.utcnow()
    db.add(log)
    db.commit()
    return log


# ---------------- 直播场次 ----------------
def _fetch_rooms(account: PlatformAccount) -> List[Dict[str, Any]]:
    if account.bind_mode == "MOCK":
        return mock_live_rooms()
    return _client(account).fetch_live_rooms()


def sync_sessions(db: Session, account: PlatformAccount) -> PlatformSyncLog:
    log = PlatformSyncLog(
        account_id=account.account_id, sync_type="SESSION",
        bind_mode=account.bind_mode, status="SUCCESS",
    )
    store_id = _resolve_store(db, account)
    created = updated = 0
    try:
        rows = _fetch_rooms(account)
        log.fetched = len(rows)
        for ext in rows:
            title = str(ext.get("title") or "抖音直播场次")[:128]
            session = db.scalar(
                select(LiveSession)
                .where(LiveSession.title == title)
                .where(LiveSession.store_id == store_id)
            )
            status = "living" if int(ext.get("status") or 2) == 2 else "ended"
            viewer = int(ext.get("online_count") or 0)
            if session:
                session.status = status
                session.viewer_count = viewer
                session.peak_viewer = max(session.peak_viewer or 0, viewer)
                updated += 1
            else:
                db.add(LiveSession(
                    store_id=store_id,
                    host_id=_resolve_host(db, store_id),
                    title=title,
                    start_time=_parse_time(ext.get("start_time")) or datetime.utcnow(),
                    status=status,
                    viewer_count=viewer,
                    peak_viewer=viewer,
                ))
                created += 1
        account.last_sync_at = datetime.utcnow()
        log.created_count, log.updated_count = created, updated
        log.message = f"拉取 {log.fetched} 个直播间，新增 {created}，更新 {updated}"
    except DouyinApiError as e:
        log.status = "FAILED"
        log.message = str(e)[:480]
    except Exception as e:  # noqa: BLE001
        log.status = "FAILED"
        log.message = f"同步异常: {e}"[:480]
    log.finished_at = datetime.utcnow()
    db.add(log)
    db.commit()
    return log


def _parse_time(value: Any):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.strptime(str(value)[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


SYNC_DISPATCH = {
    "ORDER": sync_orders,
    "PRODUCT": sync_products,
    "SESSION": sync_sessions,
}


def run_sync(db: Session, account: PlatformAccount, sync_type: str) -> PlatformSyncLog:
    fn = SYNC_DISPATCH.get(sync_type.upper())
    if not fn:
        raise ValueError(f"不支持的同步类型: {sync_type}")
    return fn(db, account)
