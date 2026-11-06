"""MCP 标准工具实现，由 LangGraph Worker Function Calling 调用。"""
from datetime import datetime

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.config import get_settings
from app.agent import replies
from app.models.all import (
    Coupon, CouponIssue, SkuInfo, Product, Danmaku, AgentAction,
    LiveProduct, SalesOrder, SalesOrderDetail,
)

settings = get_settings()


def _record(session_id: int, msg_id: int | None, tool_name: str, tool_args: dict,
            tool_result: str, latency_ms: int, model_used: str = "rule", operator_id: int | None = None):
    with SessionLocal() as db:
        action = AgentAction(
            session_id=session_id, msg_id=msg_id, tool_name=tool_name,
            tool_args=tool_args, tool_result=tool_result, latency_ms=latency_ms,
            model_used=model_used, operator_id=operator_id,
        )
        db.add(action)
        db.commit()


def query_stock(sku_id: int, nickname: str | None = None) -> str:
    with SessionLocal() as db:
        sku = db.get(SkuInfo, sku_id)
        if not sku:
            return f"SKU {sku_id} 不存在"
        product = db.get(Product, sku.product_id)
    return replies.stock_reply(
        product.product_name if product else "商品",
        sku.spec, sku.stock, sku.price, name=nickname,
    )


def query_product_faq(product_id: int, user_question: str, nickname: str | None = None) -> str:
    with SessionLocal() as db:
        p = db.get(Product, product_id)
        if not p:
            return "未找到该商品"
        skus = db.execute(select(SkuInfo).where(SkuInfo.product_id == product_id)).scalars().all()
        sku_text = "; ".join(f"{s.spec}(库存{s.stock},¥{s.price})" for s in skus)
        desc = p.description or "无详细描述"
    suffix = replies.product_faq_suffix(nickname)
    return f"商品：{p.product_name}。{desc}。可选规格：{sku_text}。{suffix}"


def issue_coupon(session_id: int, coupon_id: int, amount: float, issued_by: str = "AGENT",
                 msg_id: int | None = None, operator_id: int | None = None) -> str:
    with SessionLocal() as db:
        coupon = db.get(Coupon, coupon_id)
        if not coupon or coupon.stock <= coupon.issued:
            return "券已发完或不存在"
        from sqlalchemy import func as sa_func
        today_cost = db.execute(
            select(sa_func.sum(CouponIssue.amount_cost)).where(
                CouponIssue.session_id == session_id,
                CouponIssue.create_time >= datetime.now().date(),
            )
        ).scalar() or 0
        if float(today_cost) + amount > settings.coupon_daily_budget and issued_by == "AGENT":
            return f"超预算：当日已发 {today_cost:.2f}，预算 {settings.coupon_daily_budget:.2f}，自动发券转人工"
        issue = CouponIssue(
            coupon_id=coupon_id, session_id=session_id,
            issued_by=issued_by, amount_cost=amount,
        )
        db.add(issue)
        coupon.issued += 1
        db.commit()
        return f"已发券：{coupon.type}-{coupon.discount}，面额/成本 {amount:.2f}，剩余 {coupon.stock - coupon.issued}"


def set_focus_product(session_id: int, product_id: int, sku_id: int | None = None) -> str:
    with SessionLocal() as db:
        db.execute(select(LiveProduct).where(LiveProduct.session_id == session_id)).scalars().all()
        lp_list = db.execute(select(LiveProduct).where(LiveProduct.session_id == session_id)).scalars().all()
        for lp in lp_list:
            lp.is_focus = 1 if (lp.product_id == product_id and (sku_id is None or lp.sku_id == sku_id)) else 0
        db.commit()
        return f"已切主推到商品 {product_id}"


def create_human_ticket(msg_id: int, reason: str) -> str:
    with SessionLocal() as db:
        dm = db.get(Danmaku, msg_id)
        if dm:
            dm.handled_by = "PENDING"
        action = AgentAction(
            session_id=dm.session_id if dm else 0, msg_id=msg_id,
            tool_name="create_human_ticket", tool_args={"reason": reason},
            tool_result=f"转人工待办：{reason}", decision_reason=reason,
            latency_ms=0, model_used="rule",
        )
        db.add(action)
        db.commit()
        return f"已转人工：{reason}"


def send_danmaku_reply(session_id: int, content: str, msg_id: int | None = None) -> str:
    """产出 AI 回复：既记 AgentAction，也落一条 Danmaku 让 WS 自动推到前端弹幕流。"""
    with SessionLocal() as db:
        action = AgentAction(
            session_id=session_id, msg_id=msg_id,
            tool_name="send_danmaku_reply", tool_args={"content": content},
            tool_result=f"AI回复：{content}", latency_ms=0, model_used="rule",
        )
        db.add(action)
        # 同时落库一条 AI 回复弹幕（nickname 带 AI 标识，前端可特殊渲染）
        db.add(Danmaku(
            session_id=session_id,
            nickname="🤖 AI助理",
            content=content,
            intent="ai_reply",
            priority=3,
            handled_by="AI",   # enum('AI','HUMAN','PENDING','FILTERED')
        ))
        db.commit()
    return content


def query_order(order_id: str) -> str:
    with SessionLocal() as db:
        o = db.get(SalesOrder, order_id)
        if not o:
            return f"订单 {order_id} 不存在"
        details = db.execute(select(SalesOrderDetail).where(SalesOrderDetail.order_id == order_id)).scalars().all()
        dtext = "; ".join(f"{d.product_name}×{d.qty} ¥{d.subtotal}" for d in details)
        status_map = {"01": "待支付", "02": "已支付", "03": "已取消", "07": "退款中"}
        return f"订单 {order_id}：{dtext}，合计 ¥{o.pay_amount:.2f}，状态{status_map.get(o.status,o.status)}"


def adjust_price(session_id: int, sku_id: int, new_price: float, msg_id: int | None = None) -> str:
    with SessionLocal() as db:
        sku = db.get(SkuInfo, sku_id)
        if not sku:
            return "SKU 不存在"
        old = sku.price
        sku.price = new_price
        db.commit()
        return f"改价完成：{sku.sku_code} ¥{old} → ¥{new_price}"
