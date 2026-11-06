from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, Numeric, DateTime, SmallInteger,
    ForeignKey, UniqueConstraint, Index, JSON, text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Store(Base):
    __tablename__ = "store"
    store_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)
    city = Column(String(32), nullable=False)
    address = Column(String(255))
    manager = Column(String(64))
    status = Column(SmallInteger, default=1)
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class AuthUser(Base):
    __tablename__ = "auth_user"
    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(32))
    role = Column(String(16), default="CUSTOMER")
    status = Column(SmallInteger, default=1)
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class Staff(Base):
    __tablename__ = "staff"
    staff_id = Column(BigInteger, primary_key=True, autoincrement=True)
    store_id = Column(BigInteger, ForeignKey("store.store_id"))
    user_id = Column(BigInteger, ForeignKey("auth_user.user_id"), unique=True)
    name = Column(String(64), nullable=False)
    role = Column(String(16), nullable=False)  # MANAGER/HOST/OPERATOR
    availability = Column(String(255))
    status = Column(String(16), default="online")
    max_concurrent = Column(Integer, default=5)


class ProductCategory(Base):
    __tablename__ = "product_category"
    category_id = Column(BigInteger, primary_key=True, autoincrement=True)
    parent_id = Column(BigInteger)
    name = Column(String(64), nullable=False)
    level = Column(Integer, default=1)
    sort_order = Column(Integer, default=0)
    is_show = Column(SmallInteger, default=1)


class Product(Base):
    __tablename__ = "product"
    product_id = Column(BigInteger, primary_key=True, autoincrement=True)
    category_id = Column(BigInteger, ForeignKey("product_category.category_id"))
    product_name = Column(String(128), nullable=False)
    subtitle = Column(String(255))
    brand = Column(String(64))
    main_image = Column(String(255))
    description = Column(Text)
    status = Column(SmallInteger, default=1)
    sales_count = Column(Integer, default=0)
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    skus = relationship("SkuInfo", backref="product")


class SkuInfo(Base):
    __tablename__ = "sku_info"
    sku_id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey("product.product_id"))
    sku_code = Column(String(64), unique=True, nullable=False)
    spec = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2))
    stock = Column(Integer, default=0)
    image = Column(String(255))


class LiveSession(Base):
    __tablename__ = "live_session"
    session_id = Column(BigInteger, primary_key=True, autoincrement=True)
    store_id = Column(BigInteger, ForeignKey("store.store_id"))
    host_id = Column(BigInteger, ForeignKey("staff.staff_id"))
    title = Column(String(128), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    status = Column(String(16), default="planned")
    viewer_count = Column(Integer, default=0)
    peak_viewer = Column(Integer, default=0)
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class LiveProduct(Base):
    __tablename__ = "live_product"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, ForeignKey("live_session.session_id"))
    product_id = Column(BigInteger, ForeignKey("product.product_id"))
    sku_id = Column(BigInteger, ForeignKey("sku_info.sku_id"))
    explain_status = Column(String(16), default="pending")
    order_in_session = Column(Integer, default=0)
    is_focus = Column(SmallInteger, default=0)


class StoreProduct(Base):
    __tablename__ = "store_product"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    store_id = Column(BigInteger, ForeignKey("store.store_id"), nullable=False)
    product_id = Column(BigInteger, ForeignKey("product.product_id"), nullable=False)
    stock = Column(Integer, default=0)

    __table_args__ = (UniqueConstraint("store_id", "product_id", name="uk_store_product"),)


class Coupon(Base):
    __tablename__ = "coupon"
    coupon_id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, ForeignKey("live_session.session_id"))
    type = Column(String(16), nullable=False)  # discount/percent/shipping
    threshold = Column(Numeric(10, 2), default=0)
    discount = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    issued = Column(Integer, default=0)
    valid_start = Column(DateTime)
    valid_end = Column(DateTime)
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class CouponIssue(Base):
    __tablename__ = "coupon_issue"
    issue_id = Column(BigInteger, primary_key=True, autoincrement=True)
    coupon_id = Column(BigInteger, ForeignKey("coupon.coupon_id"))
    session_id = Column(BigInteger, ForeignKey("live_session.session_id"))
    user_id = Column(BigInteger)
    issued_by = Column(String(16), nullable=False)  # MANUAL / AGENT
    amount_cost = Column(Numeric(10, 2), default=0)
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class Danmaku(Base):
    __tablename__ = "danmaku"
    msg_id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, ForeignKey("live_session.session_id"))
    user_id = Column(BigInteger)
    nickname = Column(String(64))
    content = Column(Text, nullable=False)
    intent = Column(String(32))
    priority = Column(SmallInteger, default=3)
    handled_by = Column(String(16), default="PENDING")
    confidence = Column(Numeric(3, 2), default=0)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (Index("idx_danmaku_session", "session_id", "created_at"),)


class IntentLabel(Base):
    __tablename__ = "intent_label"
    intent = Column(String(32), primary_key=True)
    label_name = Column(String(64), nullable=False)
    route_to = Column(String(16), nullable=False)
    need_hitl = Column(SmallInteger, default=0)


class AgentAction(Base):
    __tablename__ = "agent_action"
    action_id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, ForeignKey("live_session.session_id"))
    msg_id = Column(BigInteger, ForeignKey("danmaku.msg_id"))
    tool_name = Column(String(64), nullable=False)
    tool_args = Column(JSON)
    tool_result = Column(Text)
    decision_reason = Column(String(255))
    latency_ms = Column(Integer)
    model_used = Column(String(64))
    token_cost = Column(Integer, default=0)
    operator_id = Column(BigInteger)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (Index("idx_action_session_time", "session_id", "created_at"),)


class MonitorEvent(Base):
    __tablename__ = "monitor_event"
    event_id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, ForeignKey("live_session.session_id"))
    event_type = Column(String(32), nullable=False)
    metric_value = Column(Numeric(12, 2))
    threshold = Column(Numeric(12, 2))
    agent_response = Column(String(500))
    status = Column(String(16), default="notified")
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class SalesOrder(Base):
    __tablename__ = "sales_order"
    order_id = Column(String(32), primary_key=True)
    session_id = Column(BigInteger, ForeignKey("live_session.session_id"))
    store_id = Column(BigInteger, ForeignKey("store.store_id"))
    user_id = Column(BigInteger)
    coupon_id = Column(BigInteger)
    total_amount = Column(Numeric(10, 2), nullable=False)
    pay_amount = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0)
    status = Column(String(4), default="01")
    channel = Column(String(16), default="LIVE")
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    pay_time = Column(DateTime)


class SalesOrderDetail(Base):
    __tablename__ = "sales_order_detail"
    detail_id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(String(32), ForeignKey("sales_order.order_id"))
    sku_id = Column(BigInteger)
    product_name = Column(String(128))
    spec = Column(String(255))
    price = Column(Numeric(10, 2))
    qty = Column(Integer)
    subtotal = Column(Numeric(10, 2))
    coupon_applied = Column(SmallInteger, default=0)


class PaymentRecord(Base):
    __tablename__ = "payment_record"
    pay_id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(String(32), ForeignKey("sales_order.order_id"))
    amount = Column(Numeric(10, 2))
    channel = Column(String(32))
    status = Column(String(16), default="success")
    pay_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class RevenueDaily(Base):
    __tablename__ = "revenue_daily"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    store_id = Column(BigInteger)
    session_id = Column(BigInteger)
    date = Column(DateTime, nullable=False)
    revenue = Column(Numeric(12, 2), default=0)
    orders = Column(Integer, default=0)
    avg_ticket = Column(Numeric(10, 2), default=0)
    conversion_rate = Column(Numeric(5, 4), default=0)

    __table_args__ = (UniqueConstraint("date", "store_id", "session_id", name="uk_date_store_session"),)


class KbDoc(Base):
    __tablename__ = "kb_doc"
    doc_id = Column(BigInteger, primary_key=True, autoincrement=True)
    category = Column(String(32), nullable=False)
    chunk_text = Column(Text, nullable=False)
    source = Column(String(255))
    milvus_id = Column(String(64))
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class PlatformAccount(Base):
    """外部直播平台（抖音小店/快手等）授权账号"""
    __tablename__ = "platform_account"
    account_id = Column(BigInteger, primary_key=True, autoincrement=True)
    platform = Column(String(16), nullable=False)          # DOUYIN / KUAISHOU / WECHAT_CHANNEL
    account_name = Column(String(64), nullable=False)
    shop_id = Column(String(64))
    app_key = Column(String(64))
    app_secret = Column(String(255))
    access_token = Column(String(500))
    refresh_token = Column(String(500))
    token_expire = Column(DateTime)
    bind_mode = Column(String(8), default="MOCK")          # REAL / MOCK
    status = Column(String(16), default="CONNECTED")       # CONNECTED / EXPIRED / DISCONNECTED
    last_sync_at = Column(DateTime)
    store_id = Column(BigInteger)                          # 映射到本平台门店
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    update_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class PlatformSyncLog(Base):
    """外部平台数据同步日志"""
    __tablename__ = "platform_sync_log"
    log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    account_id = Column(BigInteger, nullable=False)
    sync_type = Column(String(16), nullable=False)         # ORDER / PRODUCT / SESSION
    bind_mode = Column(String(8), default="MOCK")
    status = Column(String(16), default="SUCCESS")         # SUCCESS / FAILED
    fetched = Column(Integer, default=0)
    created_count = Column(Integer, default=0)
    updated_count = Column(Integer, default=0)
    message = Column(String(500))
    started_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    finished_at = Column(DateTime)

    __table_args__ = (Index("idx_synclog_account_time", "account_id", "started_at"),)
