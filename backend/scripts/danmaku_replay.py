"""历史弹幕按时间戳灌入 Redis Stream，驱动场控 Agent 演示。

用法（容器内）:
    python -m scripts.danmaku_replay --session 1 --speed 5 --limit 100
    --session  指定直播场次 ID（默认 1）
    --speed    回放倍速（默认 5，即真实时间的 5 倍速）
    --limit    最多回放条数（默认 0 = 全部）
    --loop     循环回放（默认 False）
"""
from __future__ import annotations

import argparse
import asyncio
import time
from datetime import datetime

import redis.asyncio as redis
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.all import Danmaku

settings = get_settings()


async def replay(session_id: int, speed: float, limit: int, loop: bool) -> None:
    r = redis.from_url(settings.redis_url)
    stream_key = f"danmaku:{session_id}"

    with SessionLocal() as db:
        stmt = select(Danmaku).where(Danmaku.session_id == session_id).order_by(Danmaku.created_at)
        if limit > 0:
            stmt = stmt.limit(limit)
        rows = db.execute(stmt).scalars().all()

    if not rows:
        print(f"[replay] session {session_id} 无历史弹幕")
        return

    print(f"[replay] 共 {len(rows)} 条弹幕，{speed}x 倍速，{'循环' if loop else '单次'}")
    round_no = 0
    while True:
        round_no += 1
        prev_ts: datetime | None = None
        for i, dm in enumerate(rows, 1):
            if prev_ts and dm.created_at:
                delta = (dm.created_at - prev_ts).total_seconds()
                await asyncio.sleep(max(0.05, delta / speed))
            prev_ts = dm.created_at

            fields = {
                "msg_id": str(dm.msg_id),
                "session_id": str(dm.session_id),
                "nickname": dm.nickname or "观众",
                "content": dm.content[:500],
                "user_id": str(dm.user_id or 0),
            }
            await r.xadd(stream_key, fields, maxlen=10000)
            print(f"  [{round_no}-{i}/{len(rows)}] {dm.nickname}: {dm.content[:40]}")

        if not loop:
            break
        await asyncio.sleep(2)

    await r.aclose()
    print(f"[replay] 第 {round_no} 轮回放结束")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=int, default=1, help="直播场次 ID")
    parser.add_argument("--speed", type=float, default=5.0, help="回放倍速")
    parser.add_argument("--limit", type=int, default=0, help="最多回放条数 (0=全部)")
    parser.add_argument("--loop", action="store_true", help="循环回放")
    args = parser.parse_args()
    asyncio.run(replay(args.session, args.speed, args.limit, args.loop))
