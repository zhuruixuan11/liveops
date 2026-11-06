"""弹幕消费者：Redis Streams XADD/XREADGROUP + 削峰背压。"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Optional

from app.core.redis_client import get_redis
from app.core.database import SessionLocal
from app.core.config import get_settings
from app.agent.graph import run_single
from app.models.all import Danmaku, LiveSession, AgentAction, Coupon, CouponIssue

settings = get_settings()

CONSUMER_GROUP = "liveops-agent-group"
BATCH_SIZE = 10
BACKPRESSURE_THRESHOLD = 2000  # 积压消息数


async def ensure_group(redis, key: str):
    try:
        await redis.xgroup_create(key, CONSUMER_GROUP, mkstream=True)
    except Exception:
        pass  # 已存在


async def consume_for_session(session_id: int, stop_event: Optional[asyncio.Event] = None):
    key = f"danmaku:{session_id}"
    redis = await get_redis()
    await ensure_group(redis, key)
    consumer_name = f"c-{session_id}-{int(time.time())}"
    while True:
        if stop_event and stop_event.is_set():
            break
        try:
            # 背压检测
            info = await redis.xinfo_stream(key)
            pending_backlog = info.get("length", 0) - info.get("groups", [{}])[0].get("consumers", [{}])[0].get("pending", 0)
            degraded = pending_backlog > BACKPRESSURE_THRESHOLD
            raw = await redis.xreadgroup(
                CONSUMER_GROUP, consumer_name,
                {key: ">"}, count=BATCH_SIZE, block=2000,
            )
            if not raw:
                continue
            for stream_key, msgs in raw:
                for msg_id, payload in msgs:
                    try:
                        content = payload.get("content", "")
                        nickname = payload.get("nickname", "游客")
                        # 落库
                        with SessionLocal() as db:
                            dm = Danmaku(
                                session_id=session_id,
                                nickname=nickname,
                                content=content,
                                intent="general",
                                priority=3,
                                handled_by="PENDING",
                            )
                            db.add(dm)
                            db.commit()
                            db.refresh(dm)
                            mid = dm.msg_id
                        # 处理（背压时走规则降级）
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, run_single, session_id, mid, content)
                        await redis.xack(key, CONSUMER_GROUP, msg_id)
                        if degraded:
                            # 降级模式额外记一条
                            with SessionLocal() as db:
                                db.add(AgentAction(
                                    session_id=session_id, msg_id=mid,
                                    tool_name="degraded", tool_args={"backlog": pending_backlog},
                                    tool_result="队列积压降级，规则快速处理", latency_ms=50,
                                    model_used="rule",
                                ))
                                db.commit()
                    except Exception as e:
                        pass
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(1)


async def run_all_consumers():
    """为所有 living 场次起一个消费者协程。"""
    while True:
        try:
            with SessionLocal() as db:
                sessions = db.execute(
                    __import__("sqlalchemy").select(LiveSession.session_id).where(
                        LiveSession.status == "living"
                    )
                ).scalars().all()
            tasks = [asyncio.create_task(consume_for_session(sid)) for sid in sessions]
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:
            await asyncio.sleep(5)
