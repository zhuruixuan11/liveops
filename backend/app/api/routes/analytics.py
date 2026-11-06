"""直播流量分析 / 场次复盘 / 主播绩效

数据全部来自本平台已有表：弹幕时间分布、订单时间分布、监控事件、场次快照。
在线人数为按互动热度折算的估算值（平台不提供逐秒曲线），字段名与说明均标注"估算"。
"""
from collections import defaultdict
import math
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, scope_staff_id
from app.models.all import (
    LiveSession, Danmaku, SalesOrder, MonitorEvent, Staff, Store,
)

router = APIRouter()

INTENT_LABEL = {
    "faq_product": "商品咨询",
    "ask_price": "价格咨询",
    "ask_coupon": "求优惠券",
    "ask_stock": "问库存",
    "logistics": "物流咨询",
    "aftersale": "售后问题",
    "complaint": "投诉",
    "spam": "广告刷屏",
    "general": "闲聊互动",
}

INTENT_ADVICE = {
    "ask_coupon": "求券密集，建议把发券节奏前置到讲解开场，并设置“券倒计时”口播",
    "ask_stock": "库存疑问集中，建议开场先讲备货量、补货节奏，降低犹豫",
    "faq_product": "商品疑问多，建议固定 3 分钟一次“成分/适用人群”快答环节",
    "ask_price": "价格敏感度高，建议增加“专柜价 vs 直播价”对比板",
    "logistics": "物流咨询多，建议在讲解间隙统一口播发货时效与快递",
    "aftersale": "售后问题偏多，建议开播前集中处理历史工单，避免占用直播间",
    "spam": "广告刷屏较多，建议开启关键词过滤并安排管理员盯屏",
    "general": "互动氛围不错，可穿插抽奖/口令保持热度",
    "complaint": "存在投诉情绪，建议安排专人优先响应并私信安抚",
}

BUCKET_MINUTES = 5


def _bucket_index(base: datetime, t: datetime, bucket_minutes: int = BUCKET_MINUTES) -> int:
    delta = (t - base).total_seconds()
    return max(0, int(delta // (bucket_minutes * 60)))


def _money(v: Any) -> float:
    return float(Decimal(str(v or 0)))


@router.get("/sessions/{session_id}/traffic")
def session_traffic(session_id: int, db: Session = Depends(get_db),
                    _: dict = Depends(get_current_user)):
    session = db.scalar(select(LiveSession).where(LiveSession.session_id == session_id))
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    base = session.start_time or datetime.now()
    danmakus = db.scalars(select(Danmaku).where(Danmaku.session_id == session_id)).all()
    orders = db.scalars(select(SalesOrder).where(SalesOrder.session_id == session_id)).all()

    # 时间范围：开播 -> 结束或最后一条动态
    activity = [t for t in
                [d.created_at for d in danmakus] + [o.create_time for o in orders] if t]
    start = session.start_time or datetime.now()
    end = session.end_time or (max(activity) if activity else start)
    if end <= start:
        end = start + timedelta(minutes=BUCKET_MINUTES * 6)

    # 场次跨度太长（如跨天）时，改用「有效活动窗口」，避免曲线被大量空白段稀释
    if activity and (end - start) > timedelta(hours=8):
        start, end = min(activity), max(activity)
        if end <= start:
            end = start + timedelta(minutes=BUCKET_MINUTES * 6)

    base = start
    # 自适应粒度：长场次放大统计间隔，保证曲线不超过 48 个点
    span_minutes = max(1, (end - base).total_seconds() / 60)
    bucket_minutes = max(BUCKET_MINUTES, math.ceil(span_minutes / 48))
    total_buckets = max(1, int(math.ceil(span_minutes / bucket_minutes)))

    interactions = defaultdict(int)
    order_cnt = defaultdict(int)
    order_gmv = defaultdict(float)
    buyer_nicks = set()

    for d in danmakus:
        if d.created_at:
            idx = min(_bucket_index(base, d.created_at, bucket_minutes), total_buckets - 1)
            interactions[idx] += 1
        if d.nickname:
            buyer_nicks.add(d.nickname)
    for o in orders:
        idx = (min(_bucket_index(base, o.create_time, bucket_minutes), total_buckets - 1)
               if o.create_time else 0)
        order_cnt[idx] += 1
        if o.status == "02":
            order_gmv[idx] += _money(o.pay_amount)

    max_inter = max(interactions.values()) if interactions else 0
    peak_viewer = max(session.peak_viewer or 0, session.viewer_count or 0)

    buckets = []
    for i in range(total_buckets):
        inter = interactions.get(i, 0)
        # 在线人数估算：以峰值在线为上限，按各时段互动量做平滑折算
        ratio = (inter / max_inter) if max_inter else 0
        online = int(round(peak_viewer * (0.35 + 0.65 * ratio))) if peak_viewer else inter * 3
        buckets.append({
            "index": i,
            "time": (base + timedelta(minutes=bucket_minutes * i)).strftime("%H:%M"),
            "interactions": inter,
            "orders": order_cnt.get(i, 0),
            "gmv": round(order_gmv.get(i, 0), 2),
            "online_est": online,
        })

    paid_orders = [o for o in orders if o.status == "02"]
    peak_bucket = max(buckets, key=lambda b: b["online_est"]) if buckets else None
    quiet = [b for b in buckets if b["interactions"] == 0 and peak_viewer]

    viewer = max(session.viewer_count or 0, 1)
    funnel = [
        {"stage": "峰值在线（估算）", "value": peak_viewer},
        {"stage": "互动观众", "value": len(buyer_nicks)},
        {"stage": "下单笔数", "value": len(orders)},
        {"stage": "支付成交", "value": len(paid_orders)},
    ]

    return {
        "session_id": session_id,
        "title": session.title,
        "status": session.status,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "bucket_minutes": bucket_minutes,
        "buckets": buckets,
        "funnel": funnel,
        "summary": {
            "peak_viewer": peak_viewer,
            "peak_time": peak_bucket["time"] if peak_bucket else None,
            "interactions": len(danmakus),
            "unique_nicknames": len(buyer_nicks),
            "orders": len(orders),
            "paid_orders": len(paid_orders),
            "gmv": round(sum(_money(o.pay_amount) for o in paid_orders), 2),
            "conversion_rate": round(len(paid_orders) / viewer * 100, 2),
            "quiet_bucket_count": len(quiet),
            "online_note": "在线人数曲线为按互动热度估算，峰值取自场次快照",
        },
    }


@router.get("/sessions/{session_id}/review")
def session_review(session_id: int, db: Session = Depends(get_db),
                   _: dict = Depends(get_current_user)):
    session = db.scalar(select(LiveSession).where(LiveSession.session_id == session_id))
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    traffic = session_traffic(session_id, db, _)
    summary = traffic["summary"]
    buckets = traffic["buckets"]

    danmakus = db.scalars(select(Danmaku).where(Danmaku.session_id == session_id)).all()
    orders = db.scalars(select(SalesOrder).where(SalesOrder.session_id == session_id)).all()
    events = db.scalars(select(MonitorEvent).where(MonitorEvent.session_id == session_id)).all()

    intent_cnt = defaultdict(int)
    handled = defaultdict(int)
    for d in danmakus:
        if d.intent:
            intent_cnt[d.intent] += 1
        handled[d.handled_by or "AI"] += 1

    top_intents = sorted(intent_cnt.items(), key=lambda x: -x[1])[:3]
    lulls = [b for b in buckets if b["interactions"] == 0]
    lull_text = "、".join(f"{b['time']}" for b in lulls[:4])

    highlights, risks, suggestions = [], [], []

    if summary["paid_orders"]:
        highlights.append(
            f"本场成交 {summary['paid_orders']} 单，GMV ¥{summary['gmv']:.2f}，"
            f"峰值在线 {summary['peak_viewer']} 人（{summary['peak_time'] or '-'} 达到峰值）"
        )
    else:
        risks.append("本场暂无支付订单，需重点排查价格吸引力与购物车引导")

    if summary["conversion_rate"] >= 3:
        highlights.append(f"转化率 {summary['conversion_rate']}%，高于门店直播均值 3%")
    elif summary["conversion_rate"] >= 1.5:
        highlights.append(f"转化率 {summary['conversion_rate']}%，处于正常区间")
    else:
        risks.append(
            f"转化率仅 {summary['conversion_rate']}%，低于 1.5% 健康线："
            "建议压缩单品讲解时长、增加“限时限量”逼单话术"
        )

    if summary["unique_nicknames"] >= 10:
        highlights.append(f"{summary['unique_nicknames']} 位观众参与互动，互动氛围良好")
    if lull_text:
        risks.append(f"存在 {len(lulls)} 个 5 分钟零互动冷场段（{lull_text}…），建议插入福袋或提问互动")
    if len(danmakus) and handled.get("HUMAN", 0) / max(len(danmakus), 1) > 0.3:
        risks.append("转人工比例超过 30%，AI 自动处理能力偏弱，建议补充 FAQ 知识库")

    for intent, cnt in top_intents:
        label = INTENT_LABEL.get(intent, intent)
        suggestions.append(f"{label} 共 {cnt} 条：{INTENT_ADVICE.get(intent, '建议完善标准回复话术')}")

    for ev in events[:3]:
        if ev.event_type == "stock_alert":
            suggestions.append(
                f"库存告警（{int(ev.metric_value or 0)} 件）：下一场提前备货，并把预售话术前置"
            )
        elif ev.event_type == "viewer_drop":
            suggestions.append("出现掉线高峰：下一场把福利环节放在开播 5 分钟内，稳住前段留存")
        elif ev.event_type == "low_conversion":
            suggestions.append("转化低迷时段：建议调整商品顺序，先讲爆款拉成交信心")

    # 下一场规划
    best_time = summary["peak_time"] or "开播后 20 分钟"
    paid_count = len([o for o in orders if o.status == "02"])

    next_plan = {
        "suggested_start": "20:00-21:00 黄金档" if not summary["peak_time"] else f"沿用本场峰值时段（{best_time} 前后）",
        "structure": [
            "0-5 分钟：福利开场 + 券倒计时，抢住前段留存",
            f"5-25 分钟：主推 1-2 款（本场成交 {paid_count} 单的爆款优先）+ 库存口播",
            "25-40 分钟：异议答疑（成分/物流/售后三类高频问题集中回答）",
            "40-55 分钟：返场逼单 + 组合优惠",
            "最后 5 分钟：预告下一场福利，引导关注",
        ],
        "focus_intents": [INTENT_LABEL.get(i, i) for i, _ in top_intents],
    }

    # 综合评分
    score = 60
    score += min(20, summary["conversion_rate"] * 4)
    score += min(10, summary["unique_nicknames"] / 3)
    score += 10 if summary["paid_orders"] else 0
    score -= min(15, len(lulls) * 2)
    score = int(max(0, min(100, score)))

    return {
        "session_id": session_id,
        "title": session.title,
        "score": score,
        "summary": summary,
        "highlights": highlights,
        "risks": risks,
        "suggestions": suggestions,
        "intent_distribution": [
            {"intent": INTENT_LABEL.get(k, k), "count": v}
            for k, v in sorted(intent_cnt.items(), key=lambda x: -x[1])
        ],
        "next_plan": next_plan,
    }


@router.get("/hosts/rank")
def host_rank(days: int = Query(30, ge=1, le=365),
              db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    since = datetime.now() - timedelta(days=days)
    sessions = db.scalars(
        select(LiveSession).where(LiveSession.start_time >= since)
    ).all()
    staff_map = {s.staff_id: s for s in db.scalars(select(Staff)).all()}
    store_map = {s.store_id: s.name for s in db.scalars(select(Store)).all()}

    agg: Dict[int, Dict[str, Any]] = {}
    for s in sessions:
        if not s.host_id:
            continue
        row = agg.setdefault(s.host_id, {
            "host_id": s.host_id, "sessions": 0, "orders": 0, "gmv": 0.0,
            "peak_viewer": 0, "viewer_sum": 0,
        })
        row["sessions"] += 1
        row["peak_viewer"] = max(row["peak_viewer"], s.peak_viewer or 0)
        row["viewer_sum"] += s.viewer_count or 0

        orders = db.scalars(
            select(SalesOrder).where(
                SalesOrder.session_id == s.session_id, SalesOrder.status == "02"
            )
        ).all()
        row["orders"] += len(orders)
        row["gmv"] += sum(_money(o.pay_amount) for o in orders)

    result = []
    for host_id, row in agg.items():
        staff = staff_map.get(host_id)
        avg_viewer = round(row["viewer_sum"] / row["sessions"], 1) if row["sessions"] else 0
        conv = round(row["orders"] / row["viewer_sum"] * 100, 2) if row["viewer_sum"] else 0
        result.append({
            "host_id": host_id,
            "host_name": staff.name if staff else f"主播#{host_id}",
            "store_name": store_map.get(staff.store_id if staff else 0, "-"),
            "sessions": row["sessions"],
            "orders": row["orders"],
            "gmv": round(row["gmv"], 2),
            "avg_viewer": avg_viewer,
            "peak_viewer": row["peak_viewer"],
            "conversion_rate": conv,
            "avg_ticket": round(row["gmv"] / row["orders"], 2) if row["orders"] else 0,
        })
    scope = scope_staff_id(user, db)
    if scope is not None:
        result = [r for r in result if r["host_id"] == scope]
    result.sort(key=lambda x: -x["gmv"])
    for i, r in enumerate(result, start=1):
        r["rank"] = i
    return {"days": days, "items": result}
