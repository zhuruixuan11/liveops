from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict


T = TypeVar("T")


# ---------- 通用 ----------
class PageResp(BaseModel, Generic[T]):
    total: int
    items: List[T]
    page: int
    size: int


# ---------- Auth ----------
class LoginIn(BaseModel):
    username: str
    password: str


class RegisterIn(BaseModel):
    username: str
    password: str
    phone: Optional[str] = None
    role: Optional[str] = "CUSTOMER"


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeOut(BaseModel):
    user_id: int
    username: str
    phone: Optional[str] = None
    role: str
    status: int
    staff_id: Optional[int] = None
    store_id: Optional[int] = None
    create_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------- Store ----------
class StoreBase(BaseModel):
    name: str
    city: str
    address: Optional[str] = None
    manager: Optional[str] = None
    status: int = 1


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    manager: Optional[str] = None
    status: Optional[int] = None


class StoreOut(StoreBase):
    store_id: int
    create_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StoreDetailOut(StoreOut):
    live_session_count: int = 0
    staff_count: int = 0


# ---------- Product ----------
class SkuInfoOut(BaseModel):
    sku_id: int
    sku_code: str
    spec: str
    price: Decimal
    original_price: Optional[Decimal] = None
    stock: int
    image: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CategoryOut(BaseModel):
    category_id: int
    parent_id: Optional[int] = None
    name: str
    level: int
    sort_order: int = 0
    is_show: int = 1
    children: List["CategoryOut"] = []

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    category_id: int
    product_name: str
    subtitle: Optional[str] = None
    brand: Optional[str] = None
    main_image: Optional[str] = None
    description: Optional[str] = None
    status: int = 1


class ProductCreate(ProductBase):
    skus: Optional[List[SkuInfoOut]] = None


class ProductUpdate(BaseModel):
    category_id: Optional[int] = None
    product_name: Optional[str] = None
    subtitle: Optional[str] = None
    brand: Optional[str] = None
    main_image: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None


class ProductOut(ProductBase):
    product_id: int
    sales_count: int = 0
    create_time: Optional[datetime] = None
    skus: List[SkuInfoOut] = []

    model_config = ConfigDict(from_attributes=True)


CategoryOut.model_rebuild()


# ---------- Live Session ----------
class LiveProductIn(BaseModel):
    product_id: int
    sku_id: Optional[int] = None
    is_focus: int = 0


class LiveProductOut(BaseModel):
    id: int
    session_id: int
    product_id: int
    sku_id: Optional[int] = None
    explain_status: str = "pending"
    order_in_session: int = 0
    is_focus: int = 0
    product_name: Optional[str] = None
    spec: Optional[str] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class LiveSessionBase(BaseModel):
    store_id: int
    host_id: Optional[int] = None
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "planned"


class LiveSessionCreate(BaseModel):
    store_id: int
    host_id: Optional[int] = None
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "planned"
    live_products: Optional[List[LiveProductIn]] = None


class LiveSessionUpdate(BaseModel):
    title: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    host_id: Optional[int] = None


class StatusUpdate(BaseModel):
    status: str


class LiveSessionOut(LiveSessionBase):
    session_id: int
    viewer_count: int = 0
    peak_viewer: int = 0
    create_time: Optional[datetime] = None
    # 列表展示附加字段
    store_name: Optional[str] = None
    host_name: Optional[str] = None
    gmv: Optional[float] = 0

    model_config = ConfigDict(from_attributes=True)


class LiveSessionDetailOut(LiveSessionOut):
    store_name: Optional[str] = None
    host_name: Optional[str] = None
    live_products: List[LiveProductOut] = []


class DashboardOut(BaseModel):
    session_id: int
    viewer_count: int = 0
    peak_viewer: int = 0
    coupon_issued_count: int = 0
    gmv: Decimal = Decimal("0")
    orders: int = 0
    conversion_rate: float = 0.0


# ---------- Coupon ----------
class CouponCreate(BaseModel):
    session_id: int
    type: str
    threshold: Decimal = Decimal("0")
    discount: Decimal
    stock: int = 0
    valid_start: Optional[datetime] = None
    valid_end: Optional[datetime] = None


class CouponOut(BaseModel):
    coupon_id: int
    session_id: int
    type: str
    threshold: Decimal
    discount: Decimal
    stock: int
    issued: int
    valid_start: Optional[datetime] = None
    valid_end: Optional[datetime] = None
    create_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CouponIssueOut(BaseModel):
    issue_id: int
    coupon_id: int
    session_id: int
    user_id: Optional[int] = None
    issued_by: str
    amount_cost: Decimal = Decimal("0")
    create_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CouponDetailOut(CouponOut):
    issues: List[CouponIssueOut] = []


# ---------- Order ----------
class OrderOut(BaseModel):
    order_id: str
    session_id: Optional[int] = None
    store_id: Optional[int] = None
    user_id: Optional[int] = None
    coupon_id: Optional[int] = None
    total_amount: Decimal
    pay_amount: Decimal
    discount_amount: Decimal
    status: str
    channel: str
    create_time: Optional[datetime] = None
    pay_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrderDetailOut(OrderOut):
    details: List[Any] = []


class PayRequest(BaseModel):
    channel: Optional[str] = "LIVE_PAY"


class OrderItemIn(BaseModel):
    sku_id: int
    qty: int = 1


class OrderCreate(BaseModel):
    session_id: int
    store_id: int
    items: List[OrderItemIn]
    coupon_id: Optional[int] = None
    channel: Optional[str] = "LIVE"


# ---------- Sales ----------
class SalesSummary(BaseModel):
    store_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    revenue: Decimal = Decimal("0")
    orders: int = 0
    avg_ticket: Decimal = Decimal("0")
    conversion_rate: float = 0.0
    # 前端兼容字段
    gmv: Decimal = Decimal("0")
    aov: Decimal = Decimal("0")
    sessions: int = 0


class StoreRankItem(BaseModel):
    store_id: int
    store_name: str
    gmv: Decimal = Decimal("0")
    orders: int = 0
    city: Optional[str] = None


class StoreAnomaly(BaseModel):
    store_id: int
    current_revenue: Decimal
    previous_revenue: Decimal
    drop_percent: float


class SalesDashboardOut(BaseModel):
    summary: SalesSummary
    anomalies: List[StoreAnomaly] = []


# ---------- Danmaku ----------
class DanmakuIn(BaseModel):
    session_id: Optional[int] = None
    user_id: Optional[int] = None
    nickname: Optional[str] = None
    content: str


class DanmakuOut(BaseModel):
    msg_id: int
    session_id: int
    user_id: Optional[int] = None
    nickname: Optional[str] = None
    content: str
    intent: Optional[str] = None
    priority: int = 3
    handled_by: str = "PENDING"
    confidence: Optional[Decimal] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------- Agent ----------
class AgentActionOut(BaseModel):
    action_id: int
    session_id: Optional[int] = None
    msg_id: Optional[int] = None
    tool_name: str
    tool_args: Optional[Any] = None
    tool_result: Optional[str] = None
    decision_reason: Optional[str] = None
    latency_ms: Optional[int] = None
    model_used: Optional[str] = None
    token_cost: int = 0
    operator_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------- Monitor ----------
class MonitorEventOut(BaseModel):
    event_id: int
    session_id: Optional[int] = None
    event_type: str
    metric_value: Optional[Decimal] = None
    threshold: Optional[Decimal] = None
    agent_response: Optional[str] = None
    status: str = "notified"
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------- Operator ----------
class OperatorTicketOut(BaseModel):
    msg_id: int
    session_id: Optional[int] = None
    nickname: Optional[str] = None
    content: str
    intent: Optional[str] = None
    handled_by: str = "PENDING"
    confidence: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    agent_actions: List[AgentActionOut] = []


class ResolveRequest(BaseModel):
    reply: str
