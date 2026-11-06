"""LangGraph 组装：Supervisor 路由 → 意图分类 → Worker 分流。

降级友好：LLM API Key 缺失时走 classifier.classify_by_rules。
"""
from __future__ import annotations

import json
import time
from typing import TypedDict, Any, Optional

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.llm_client import get_llm
from app.core.config import get_settings
from app.agent.classifier import classify_by_rules, classify_by_llm
from app.agent import replies
from app.tools.live_tools import (
    query_stock, query_product_faq, issue_coupon,
    create_human_ticket, send_danmaku_reply, set_focus_product,
    adjust_price, _record,
)
from app.models.all import Danmaku, AgentAction, Coupon, LiveProduct

settings = get_settings()


class AgentState(TypedDict):
    session_id: int
    msg_id: int
    content: str
    nickname: Optional[str]
    intent: str
    confidence: float
    route_to: str
    need_hitl: bool
    reply: str | None
    tool_logs: list[dict]
    start_ts: float


def build_intent_route(intent: str) -> tuple[str, bool]:
    routing = {
        "faq_product": ("FAQ", False),
        "faq_policy": ("FAQ", False),
        "general": ("FAQ", False),
        "ask_price": ("COUPON", True),
        "ask_coupon": ("COUPON", True),
        "ask_stock": ("STOCK", False),
        "logistics": ("FAQ", False),
        "aftersale": ("HUMAN", True),
        "complaint": ("HUMAN", True),
        "spam": ("FILTER", False),
    }
    return routing.get(intent, ("FAQ", False))


def classify(state: AgentState) -> AgentState:
    llm = get_llm()
    intent, conf = classify_by_llm(state["content"], llm, settings.llm_light_model)
    route, hitl = build_intent_route(intent)
    return {**state, "intent": intent, "confidence": conf, "route_to": route, "need_hitl": hitl}


def route_node(state: AgentState) -> str:
    return state["route_to"]


def faq_node(state: AgentState) -> AgentState:
    try:
        llm = get_llm()
    except Exception:
        llm = None
    reply = ""
    if state["intent"] in ("faq_product",):
        with SessionLocal() as db:
            lp = db.execute(select(LiveProduct).where(
                LiveProduct.session_id == state["session_id"], LiveProduct.is_focus == 1
            )).scalars().first()
            pid = lp.product_id if lp else None
            if pid:
                reply = query_product_faq(pid, state["content"], state.get("nickname"))
    elif state["intent"] in ("logistics", "faq_policy"):
        reply = replies.logistics_reply(state.get("nickname"))
    else:
        try:
            resp = llm.chat(settings.llm_light_model, [
                {"role": "system", "content": "你是直播间场控助手，语气活泼友好，一句话回复，不超过 50 字。"},
                {"role": "user", "content": state["content"]}
            ]) if llm else {}
            reply = resp.get("content") or ""
        except Exception:
            # 大模型超时/额度用尽时降级为模板话术，避免观众弹幕石沉大海
            reply = ""
    if not reply:
        reply = replies.general_fallback(state.get("nickname"))
    send_danmaku_reply(state["session_id"], reply, state["msg_id"])
    return {**state, "reply": reply}


def coupon_node(state: AgentState) -> AgentState:
    with SessionLocal() as db:
        coupon = db.execute(select(Coupon).where(
            Coupon.session_id == state["session_id"], Coupon.stock > Coupon.issued
        ).order_by(Coupon.discount.desc())).scalars().first()
    if not coupon:
        reply = replies.no_coupon_reply(state.get("nickname"))
        send_danmaku_reply(state["session_id"], reply, state["msg_id"])
        return {**state, "reply": reply}
    # 超预算降级走规则：如果预算已超限，自动发券转人工
    if state["need_hitl"]:
        create_human_ticket(state["msg_id"], f"用户索要优惠券超预算阈值：intent={state['intent']}")
        return {**state, "reply": replies.human_reply(state.get("nickname"))}
    res = issue_coupon(state["session_id"], coupon.coupon_id, float(coupon.discount),
                      issued_by="AGENT", msg_id=state["msg_id"])
    reply = replies.coupon_issued_reply(coupon, state.get("nickname"))
    send_danmaku_reply(state["session_id"], reply, state["msg_id"])
    return {**state, "reply": reply}


def stock_node(state: AgentState) -> AgentState:
    with SessionLocal() as db:
        lp = db.execute(select(LiveProduct).where(
            LiveProduct.session_id == state["session_id"], LiveProduct.is_focus == 1
        )).scalars().first()
    if not lp or not lp.sku_id:
        reply = replies.no_sku_reply(state.get("nickname"))
    else:
        reply = query_stock(lp.sku_id, state.get("nickname"))
    send_danmaku_reply(state["session_id"], reply, state["msg_id"])
    return {**state, "reply": reply}


def human_node(state: AgentState) -> AgentState:
    reason = f"意图 {state['intent']} 需人工处理"
    create_human_ticket(state["msg_id"], reason)
    reply = replies.human_reply(state.get("nickname"))
    send_danmaku_reply(state["session_id"], reply, state["msg_id"])
    return {**state, "reply": reply}


def filter_node(state: AgentState) -> AgentState:
    with SessionLocal() as db:
        dm = db.get(Danmaku, state["msg_id"])
        if dm:
            dm.handled_by = "FILTERED"
        db.commit()
    return {**state, "reply": None}


def run_single(session_id: int, msg_id: int, content: str) -> AgentState:
    """同步执行单条弹幕的完整处理链路（用于 debug + 后端路由触发）。"""
    start = time.time()
    nickname = None
    with SessionLocal() as db:
        dm = db.get(Danmaku, msg_id)
        if dm:
            nickname = dm.nickname
    state: AgentState = {
        "session_id": session_id, "msg_id": msg_id, "content": content,
        "nickname": nickname,
        "intent": "", "confidence": 0.0, "route_to": "FAQ", "need_hitl": False,
        "reply": None, "tool_logs": [], "start_ts": start,
    }
    state = classify(state)
    route = state["route_to"]
    if route == "FAQ":
        state = faq_node(state)
    elif route == "COUPON":
        state = coupon_node(state)
    elif route == "STOCK":
        state = stock_node(state)
    elif route == "HUMAN":
        state = human_node(state)
    elif route == "FILTER":
        state = filter_node(state)
    latency = int((time.time() - start) * 1000)
    # 更新 danmaku 最终状态
    with SessionLocal() as db:
        dm = db.get(Danmaku, msg_id)
        if dm:
            dm.intent = state["intent"]
            dm.confidence = state["confidence"]
            if route == "FILTER":
                dm.handled_by = "FILTERED"
            elif state["need_hitl"]:
                dm.handled_by = "PENDING"
            else:
                dm.handled_by = "AI"
        db.commit()
    _record(session_id, msg_id, "intent_classify",
            {"content": content[:120]}, f"intent={state['intent']} route={route}",
            latency_ms=latency, model_used=settings.llm_light_model)
    return state
