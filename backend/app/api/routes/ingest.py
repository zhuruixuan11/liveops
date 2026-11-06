"""直播弹幕采集接入

外部采集器（抖音/快手抓取进程、开源 WebFetcher、演示脚本）把进入直播间拉到的弹幕
批量推到这里，服务端统一做：意图识别 → 落库 → 推 Redis Stream（场控/Agent 自动消费）。

鉴权：请求头 X-Ingest-Token 或 body.token，需与 settings.ingest_token 一致。
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agent.classifier import classify_by_rules
from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.redis_client import get_sync_redis
from app.models.all import Danmaku, LiveSession

router = APIRouter()

settings = get_settings()

INTENT_LABEL = {
    "faq_product": "商品咨询", "faq_policy": "活动规则", "ask_price": "价格咨询",
    "ask_coupon": "求优惠券", "ask_stock": "问库存", "logistics": "物流咨询",
    "aftersale": "售后问题", "complaint": "投诉", "spam": "广告刷屏", "general": "闲聊互动",
}

# 意图 -> 处理优先级（1 最高）
PRIORITY = {
    "complaint": 1, "aftersale": 1,
    "ask_coupon": 2, "ask_stock": 2, "ask_price": 2,
    "logistics": 3, "faq_product": 3, "faq_policy": 3,
    "general": 4, "spam": 5,
}


class DanmakuItem(BaseModel):
    nickname: Optional[str] = None
    content: str
    user_id: Optional[int] = None
    ts: Optional[Any] = None          # ISO 字符串 / 秒级或毫秒级时间戳，可空


class IngestIn(BaseModel):
    session_id: int
    token: Optional[str] = None
    source: str = "collector"         # collector / douyin / kuaishou / manual
    room_id: Optional[str] = None
    items: List[DanmakuItem] = Field(default_factory=list)


class HeartbeatIn(BaseModel):
    session_id: int
    token: Optional[str] = None
    source: str = "collector"
    room_id: Optional[str] = None
    collected: int = 0
    note: Optional[str] = None


def _check_token(token: Optional[str], header_token: Optional[str]) -> None:
    expected = settings.ingest_token
    got = token or header_token
    if not expected or got != expected:
        raise HTTPException(status_code=401, detail="invalid ingest token")


def _parse_ts(value: Any, now: datetime) -> datetime:
    if value is None:
        return now
    try:
        if isinstance(value, (int, float)):
            v = float(value)
            if v > 1e12:      # 毫秒
                v /= 1000
            dt = datetime.utcfromtimestamp(v)
        else:
            s = str(value).strip().replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            if dt.tzinfo:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        if dt > now + timedelta(minutes=5):
            return now
        return dt
    except Exception:
        return now


def _redis_state(session_id: int, accepted: int, filtered: int,
                 source: str, now: datetime) -> None:
    try:
        r = get_sync_redis()
        key = f"ingest:state:{session_id}"
        r.hincrby(key, "accepted", accepted)
        r.hincrby(key, "filtered", filtered)
        r.hset(key, mapping={"last_at": now.isoformat(), "source": source})
        r.expire(key, 60 * 60 * 24 * 7)
    except Exception:
        pass


@router.get("/config")
def ingest_config():
    """给前端展示用：只暴露是否配置了 token，不返回 token 本身。"""
    return {
        "enabled": bool(settings.ingest_token),
        "endpoint": "/api/v1/ingest/danmaku",
        "heartbeat": "/api/v1/ingest/heartbeat",
        "modes": ["mock", "file", "ws"],
    }


@router.post("/danmaku")
def ingest_danmaku(payload: IngestIn,
                   x_ingest_token: Optional[str] = Header(None, alias="X-Ingest-Token"),
                   db: Session = Depends(get_db)):
    _check_token(payload.token, x_ingest_token)

    if not payload.items:
        return {"accepted": 0, "filtered": 0, "skipped": 0, "intents": {}}
    if len(payload.items) > 200:
        raise HTTPException(status_code=400, detail="单批最多 200 条弹幕")

    session = db.scalar(select(LiveSession).where(LiveSession.session_id == payload.session_id))
    if not session:
        raise HTTPException(status_code=404, detail="session not found")

    now = datetime.utcnow()
    seen = set()
    rows: List[Danmaku] = []
    filtered = 0
    skipped = 0
    intents: Dict[str, int] = {}

    for item in payload.items:
        content = (item.content or "").strip()
        if not content:
            skipped += 1
            continue
        nickname = (item.nickname or "观众").strip()[:64]
        key = (nickname, content)
        if key in seen:
            skipped += 1
            continue
        seen.add(key)

        intent, confidence = classify_by_rules(content)
        intents[intent] = intents.get(intent, 0) + 1
        handled_by = "FILTERED" if intent == "spam" else "PENDING"
        if intent == "spam":
            filtered += 1

        rows.append(Danmaku(
            session_id=payload.session_id,
            user_id=item.user_id,
            nickname=nickname,
            content=content[:2000],
            intent=intent,
            priority=PRIORITY.get(intent, 3),
            confidence=confidence,
            handled_by=handled_by,
            created_at=_parse_ts(item.ts, now),
        ))

    if rows:
        db.add_all(rows)
        db.commit()

        # 非垃圾弹幕推到 Redis Stream，场控 Agent 自动消费
        try:
            r = get_sync_redis()
            for dm in rows:
                if dm.handled_by == "FILTERED":
                    continue
                r.xadd(
                    f"danmaku:{payload.session_id}",
                    {
                        "msg_id": str(dm.msg_id),
                        "nickname": dm.nickname or "",
                        "content": dm.content or "",
                        "intent": dm.intent or "",
                        "ts": (dm.created_at or now).isoformat(),
                    },
                    maxlen=1000,
                )
        except Exception:
            pass

    _redis_state(payload.session_id, len(rows) - filtered, filtered, payload.source, now)

    return {
        "session_id": payload.session_id,
        "accepted": len(rows) - filtered,
        "filtered": filtered,
        "skipped": skipped,
        "intents": intents,
    }


@router.post("/heartbeat")
def ingest_heartbeat(payload: HeartbeatIn,
                     x_ingest_token: Optional[str] = Header(None, alias="X-Ingest-Token")):
    _check_token(payload.token, x_ingest_token)
    now = datetime.utcnow()
    try:
        r = get_sync_redis()
        key = f"ingest:heart:{payload.session_id}"
        r.hset(key, mapping={
            "source": payload.source,
            "room_id": payload.room_id or "",
            "collected": payload.collected,
            "note": payload.note or "",
            "ts": now.isoformat(),
        })
        r.expire(key, 600)
    except Exception:
        raise HTTPException(status_code=503, detail="redis unavailable")
    return {"ok": True, "server_time": now.isoformat()}


@router.get("/status")
def ingest_status(session_id: int = Query(..., ge=1),
                  db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    today_count = db.scalar(
        select(func.count()).select_from(Danmaku).where(
            Danmaku.session_id == session_id, Danmaku.created_at >= today
        )
    ) or 0
    total_count = db.scalar(
        select(func.count()).select_from(Danmaku).where(Danmaku.session_id == session_id)
    ) or 0
    filtered_count = db.scalar(
        select(func.count()).select_from(Danmaku).where(
            Danmaku.session_id == session_id, Danmaku.handled_by == "FILTERED"
        )
    ) or 0
    last_at = db.scalar(
        select(func.max(Danmaku.created_at)).where(Danmaku.session_id == session_id)
    )

    since_24h = datetime.utcnow() - timedelta(hours=24)
    intent_rows = db.execute(
        select(Danmaku.intent, func.count(Danmaku.msg_id))
        .where(Danmaku.session_id == session_id, Danmaku.created_at >= since_24h)
        .group_by(Danmaku.intent).order_by(func.count(Danmaku.msg_id).desc())
    ).all()

    heart: Dict[str, Any] = {}
    connected = False
    heartbeat_age = None
    try:
        r = get_sync_redis()
        heart = r.hgetall(f"ingest:heart:{session_id}") or {}
        state = r.hgetall(f"ingest:state:{session_id}") or {}
        if heart:
            heart["accepted_total"] = state.get("accepted", "0")
            heart["filtered_total"] = state.get("filtered", "0")
            ts = datetime.fromisoformat(heart["ts"]) if heart.get("ts") else None
            if ts:
                heartbeat_age = int((datetime.utcnow() - ts).total_seconds())
                connected = heartbeat_age < 90
    except Exception:
        pass

    return {
        "session_id": session_id,
        "connected": connected,
        "heartbeat_age_seconds": heartbeat_age,
        "source": heart.get("source") or "-",
        "room_id": heart.get("room_id") or "",
        "collector_note": heart.get("note") or "",
        "collected_reported": int(heart.get("collected") or 0),
        "today_count": today_count,
        "total_count": total_count,
        "filtered_count": filtered_count,
        "last_received_at": last_at.isoformat() if last_at else None,
        "intents": [
            {"intent": INTENT_LABEL.get(k or "general", k or "general"), "count": int(v)}
            for k, v in intent_rows
        ],
    }
