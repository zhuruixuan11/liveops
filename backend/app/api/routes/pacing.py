"""直播节奏指挥台

把一场直播拆成 5 个阶段，按开播时长自动推进，并结合实时弹幕/成交/库存给出
「现在该做什么、还剩多久、哪里出问题了」。

- 节奏时钟默认取场次开播时间；若开播已超过计划时长（如外部同步进来的老场次），
  自动从当前时刻重新计时，避免一进直播间就是"超时"。
- 人工跳阶段/重置计时写入 Redis（Redis 不可用时仅保留自动推进）。
"""
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.redis_client import get_sync_redis
from app.models.all import (
    Coupon, Danmaku, LiveProduct, LiveSession, Product, SalesOrder, SkuInfo,
)

router = APIRouter()

PAID = "02"

PHASES = [
    {
        "name": "暖场留人",
        "ratio": (0.00, 0.10),
        "action": "先发券再讲品：报本场最低价 + 券倒计时，把前 3 分钟的人留住",
        "tips": ["口播本场福利清单", "引导点关注/加粉丝团", "用福袋拉停留"],
    },
    {
        "name": "主推讲解",
        "ratio": (0.10, 0.45),
        "action": "主推款五步讲法：痛点 → 成分/参数 → 实拍演示 → 到手价对比 → 引导下单",
        "tips": ["每款讲 8-10 分钟，别拖堂", "讲完立刻报库存", "把链接重复挂 3 次"],
    },
    {
        "name": "福利逼单",
        "ratio": (0.45, 0.70),
        "action": "限时限量逼单：报库存、报倒计时、报已付款人数，每 3 分钟提醒一次",
        "tips": ["库存少的主推款优先逼单", "搭配组合优惠提高客单价", "强调券即将发完"],
    },
    {
        "name": "异议答疑",
        "ratio": (0.70, 0.85),
        "action": "集中回答高频问题（价格/物流/售后），把犹豫用户拉回购物车",
        "tips": ["挑弹幕里重复最多的问题统一回答", "售后问题当场给处理方案", "安排客服私信跟进"],
    },
    {
        "name": "返场收尾",
        "ratio": (0.85, 1.00),
        "action": "返场 2 款 + 组合优惠，预告下一场福利，引导关注",
        "tips": ["返场只讲成交最好的 1-2 款", "预告下一场开播时间", "下播前 1 小时做复盘"],
    },
]

INTENT_LABEL = {
    "faq_product": "商品咨询", "faq_policy": "活动规则", "ask_price": "价格咨询",
    "ask_coupon": "求优惠券", "ask_stock": "问库存", "logistics": "物流咨询",
    "aftersale": "售后问题", "complaint": "投诉", "spam": "广告刷屏", "general": "闲聊互动",
}


def _money(v: Any) -> float:
    return float(Decimal(str(v or 0)))


def _focus_product(db: Session, session_id: int) -> Dict[str, Any]:
    lp = db.scalar(
        select(LiveProduct).where(
            LiveProduct.session_id == session_id, LiveProduct.is_focus == 1
        ).order_by(LiveProduct.id)
    )
    if not lp:
        return {"name": "门店主推款", "stock": None, "price": None}
    product = db.scalar(select(Product).where(Product.product_id == lp.product_id))
    sku = db.scalar(select(SkuInfo).where(SkuInfo.sku_id == lp.sku_id)) if lp.sku_id else None
    return {
        "name": product.product_name if product else f"商品#{lp.product_id}",
        "stock": int(sku.stock) if sku and sku.stock is not None else None,
        "price": _money(sku.price) if sku else None,
    }


def _phase_plan(duration: int, focus_name: str) -> List[Dict[str, Any]]:
    plan: List[Dict[str, Any]] = []
    for i, p in enumerate(PHASES):
        start = int(round(duration * p["ratio"][0]))
        end = duration if i == len(PHASES) - 1 else int(round(duration * p["ratio"][1]))
        action = p["action"]
        if p["name"] == "主推讲解":
            action = f"主推「{focus_name}」：" + action
        plan.append({
            "index": i,
            "name": p["name"],
            "start_min": start,
            "end_min": end,
            "action": action,
            "tips": p["tips"],
        })
    return plan


def _resolve_base(session: LiveSession, duration: int, now: datetime) -> Tuple[datetime, Optional[str]]:
    """节奏时钟起点：优先 Redis 人工设定，其次开播时间。"""
    base = session.start_time or now
    note = None
    key = f"pacing:{session.session_id}"
    try:
        r = get_sync_redis()
        saved = r.hget(key, "base_ts")
        if saved:
            base = datetime.fromisoformat(saved)
        else:
            elapsed = (now - base).total_seconds() / 60
            if session.status == "living" and elapsed > duration:
                base = now
                note = "该场次开播时间较早，节奏计时已从当前时刻重新开始"
            r.hset(key, "base_ts", base.isoformat())
            r.expire(key, 60 * 60 * 24 * 3)
    except Exception:
        pass
    return base, note


def _build_state(db: Session, session: LiveSession, duration: int, now: datetime) -> Dict[str, Any]:
    focus = _focus_product(db, session.session_id)
    plan = _phase_plan(duration, focus["name"])
    base, clock_note = _resolve_base(session, duration, now)
    elapsed = max(0.0, (now - base).total_seconds() / 60)

    idx = 0
    for i, p in enumerate(plan):
        if elapsed >= p["start_min"]:
            idx = i
    current = plan[idx]
    overtime = max(0.0, elapsed - duration)
    remaining = max(0.0, current["end_min"] - elapsed)
    next_phase = plan[idx + 1] if idx + 1 < len(plan) else None

    # ---- 实时信号：近 20 分钟弹幕，近 10 分钟成交 ----
    since_20 = now - timedelta(minutes=20)
    danmakus = db.scalars(
        select(Danmaku).where(
            Danmaku.session_id == session.session_id, Danmaku.created_at >= since_20
        )
    ).all()
    recent_5 = sum(1 for d in danmakus if d.created_at >= now - timedelta(minutes=5))
    prev_5 = sum(
        1 for d in danmakus
        if now - timedelta(minutes=10) <= d.created_at < now - timedelta(minutes=5)
    )
    trend = "flat"
    if prev_5 >= 5:
        if recent_5 >= prev_5 * 1.2:
            trend = "up"
        elif recent_5 <= prev_5 * 0.7:
            trend = "down"

    since_10 = now - timedelta(minutes=10)
    orders_10 = db.scalars(
        select(SalesOrder).where(
            SalesOrder.session_id == session.session_id,
            SalesOrder.status == PAID, SalesOrder.create_time >= since_10,
        )
    ).all()
    order_gmv_10 = sum(_money(o.pay_amount) for o in orders_10)

    intent_cnt: Dict[str, int] = defaultdict(int)
    for d in danmakus:
        if d.created_at >= since_10 and d.intent:
            intent_cnt[d.intent] += 1
    top_intents = sorted(intent_cnt.items(), key=lambda x: -x[1])[:3]

    all_paid = db.scalars(
        select(SalesOrder).where(
            SalesOrder.session_id == session.session_id, SalesOrder.status == PAID
        )
    ).all()

    # ---- 告警 ----
    alerts: List[Dict[str, str]] = []
    if session.status != "living":
        alerts.append({
            "level": "info", "title": "场次未在直播中",
            "action": "当前节奏建议仅供参考，开播后会自动按真实时长推进",
        })
    if overtime > 0:
        alerts.append({
            "level": "warning", "title": f"已超出计划时长 {int(overtime)} 分钟",
            "action": "建议立刻进入返场收尾：返场 2 款 + 预告下一场，避免拖堂掉粉",
        })
    if trend == "down":
        drop = int((1 - recent_5 / max(prev_5, 1)) * 100)
        alerts.append({
            "level": "warning", "title": f"近 5 分钟互动量下滑 {drop}%",
            "action": "立刻发券或上福袋，并抛一个二选一问题把评论区拉回来",
        })
    if elapsed > 15 and not orders_10 and session.status == "living":
        alerts.append({
            "level": "warning", "title": "近 10 分钟没有成交",
            "action": "切回爆款，报库存 + 报倒计时，用限时价逼单",
        })
    if focus["stock"] is not None and focus["stock"] < 10:
        alerts.append({
            "level": "error", "title": f"主推「{focus['name']}」仅剩 {focus['stock']} 件",
            "action": "改为限量开抢口播，或切预售款，避免拍下无货",
        })
    if intent_cnt.get("ask_coupon", 0) >= 3:
        alerts.append({
            "level": "info", "title": f"近 10 分钟 {intent_cnt['ask_coupon']} 条求券弹幕",
            "action": "先放券再讲解，券的发放节奏需要前置",
        })
    if intent_cnt.get("complaint", 0) >= 1:
        alerts.append({
            "level": "error", "title": "弹幕里出现投诉情绪",
            "action": "安排客服优先私信跟进，主播口播安抚一句即可，别纠缠",
        })

    # ---- 实时福利决策 ----
    coupons = db.scalars(
        select(Coupon).where(Coupon.session_id == session.session_id)
    ).all()
    coupon_pool = [c for c in coupons if int(c.stock or 0) > int(c.issued or 0)]
    if not coupon_pool:
        # 本场没配券时，退而使用平台内有库存的券，保证一键发券可用
        coupon_pool = [
            c for c in db.scalars(select(Coupon).order_by(Coupon.coupon_id.asc())).all()
            if int(c.stock or 0) > int(c.issued or 0)
        ]
    best_coupon = coupon_pool[0] if coupon_pool else None

    score = 0
    if current["name"] == "福利逼单":
        score += 15
    elif elapsed >= duration * 0.2:
        score += 5
    if trend == "down":
        score += 10
    if elapsed >= 10 and not orders_10:
        score += 10
    if intent_cnt.get("ask_coupon", 0) >= 3:
        score += 10
    if recent_5 < 3 and elapsed >= 5:
        score += 5
    should_send = score >= 20

    if intent_cnt.get("ask_coupon", 0) >= 3:
        wtype, wtitle = "coupon", "观众在求券，建议立刻放券"
    elif trend == "down":
        wtype, wtitle = "lucky_bag", "互动下滑，建议上福袋把停留拉回来"
    elif elapsed >= 10 and not orders_10:
        wtype, wtitle = "price", "近 10 分钟无成交，建议报限时价逼单"
    else:
        wtype, wtitle = "coupon", "节奏平稳，可按计划放券"

    w_reason = (f"当前处于「{current['name']}」，近 5 分钟弹幕 {recent_5} 条"
                f"（上一段 {prev_5} 条），近 10 分钟成交 {len(orders_10)} 单")
    if intent_cnt.get("ask_coupon", 0):
        w_reason += f"，求券弹幕 {intent_cnt['ask_coupon']} 条"
    w_reason += f"；福利决策分 {score}（≥20 建议发）。"

    coupon_out = None
    if best_coupon:
        thr = int(_money(best_coupon.threshold))
        if best_coupon.type == "discount":
            label = f"满 {thr} 减 {int(_money(best_coupon.discount))}" if thr else f"立减 {int(_money(best_coupon.discount))} 元"
        elif best_coupon.type == "percent":
            rate = float(_money(best_coupon.discount))
            if 0 < rate <= 1:
                label = f"立减 {round(rate * 100)}%"
            else:
                label = f"{rate:g} 折"
            if thr:
                label = f"满 {thr} {label}"
        else:
            label = "包邮券"
        coupon_out = {
            "coupon_id": best_coupon.coupon_id,
            "label": label,
            "stock_left": int(best_coupon.stock or 0) - int(best_coupon.issued or 0),
        }

    welfare = {
        "should_send": should_send,
        "score": score,
        "type": wtype,
        "title": wtitle if should_send else "暂不需要额外发福利",
        "reason": w_reason,
        "coupon": coupon_out,
        "action": ("一键发券" if coupon_out else "先到优惠券页创建本场券"),
    }

    if not alerts:
        alerts.append({
            "level": "success", "title": "节奏平稳",
            "action": f"保持当前节奏，按「{current['name']}」的动作继续执行",
        })

    # ---- 现在该做什么 ----
    next_actions = [current["action"]]
    if trend == "down":
        next_actions.append("互动下滑：3 分钟内安排一次福袋/抽奖，把停留拉回来")
    if top_intents and top_intents[0][0] == "ask_coupon":
        next_actions.append(f"求券 {top_intents[0][1]} 条：先口播券规则，再引导点小黄车")
    if top_intents and top_intents[0][0] == "ask_stock":
        next_actions.append(f"问库存 {top_intents[0][1]} 条：逐款报剩余数量，降低犹豫")
    if next_phase:
        next_actions.append(
            f"{int(remaining)} 分钟后进入「{next_phase['name']}」，提前准备对应话术"
        )

    phases_out = []
    for p in plan:
        status = "done" if p["index"] < idx else ("current" if p["index"] == idx else "next")
        if overtime > 0 and p["index"] == idx:
            status = "current"
        phases_out.append({**p, "status": status})

    progress = round(min(100.0, elapsed / duration * 100), 1) if duration else 0.0

    return {
        "session_id": session.session_id,
        "title": session.title,
        "status": session.status,
        "duration_minutes": duration,
        "elapsed_minutes": round(elapsed, 1),
        "remaining_minutes": round(remaining, 1),
        "countdown_seconds": int(remaining * 60),
        "progress_pct": progress,
        "overtime_minutes": int(overtime),
        "clock_note": clock_note,
        "focus_product": focus,
        "phase": current,
        "next_phase": next_phase,
        "phases": phases_out,
        "next_actions": next_actions,
        "alerts": alerts,
        "welfare": welfare,
        "heat": {
            "danmaku_5m": recent_5,
            "danmaku_prev_5m": prev_5,
            "trend": trend,
            "orders_10m": len(orders_10),
            "gmv_10m": round(order_gmv_10, 2),
            "paid_orders_total": len(all_paid),
            "gmv_total": round(sum(_money(o.pay_amount) for o in all_paid), 2),
            "top_intents": [
                {"intent": INTENT_LABEL.get(k, k), "count": v} for k, v in top_intents
            ],
        },
    }


@router.get("/{session_id}")
def pacing_state(session_id: int,
                 duration: int = Query(60, ge=10, le=240),
                 db: Session = Depends(get_db),
                 _: dict = Depends(get_current_user)):
    session = db.scalar(select(LiveSession).where(LiveSession.session_id == session_id))
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    return _build_state(db, session, duration, datetime.now())


@router.post("/{session_id}/advance")
def pacing_advance(session_id: int, duration: int = Query(60, ge=10, le=240),
                   db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    """人工跳到下一阶段（以当前时刻作为该阶段起点）。"""
    session = db.scalar(select(LiveSession).where(LiveSession.session_id == session_id))
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    state = _build_state(db, session, duration, datetime.now())
    plan = state["phases"]
    next_idx = min(state["phase"]["index"] + 1, len(plan) - 1)
    base = datetime.now() - timedelta(minutes=plan[next_idx]["start_min"])
    try:
        r = get_sync_redis()
        r.hset(f"pacing:{session_id}", "base_ts", base.isoformat())
    except Exception:
        raise HTTPException(status_code=503, detail="节奏状态存储不可用，请稍后重试")
    return {"ok": True, "phase_index": next_idx, "phase_name": plan[next_idx]["name"]}


@router.post("/{session_id}/reset")
def pacing_reset(session_id: int,
                 db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    """重置节奏计时，从暖场阶段重新开始。"""
    session = db.scalar(select(LiveSession).where(LiveSession.session_id == session_id))
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    try:
        r = get_sync_redis()
        r.hset(f"pacing:{session_id}", "base_ts", datetime.now().isoformat())
    except Exception:
        raise HTTPException(status_code=503, detail="节奏状态存储不可用，请稍后重试")
    return {"ok": True, "phase_index": 0, "phase_name": PHASES[0]["name"]}
