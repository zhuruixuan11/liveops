"""SSE / WS 实时推送层：给前端场控三栏界面喂数据。

简易实现：维护一个全局订阅者集合，agent_action 写入时自动 broadcast。
"""
from __future__ import annotations

import asyncio
import json
from typing import Set

SUBSCRIBERS: Set[asyncio.Queue] = set()


async def broadcast(event: str, data: dict, session_id: int | None = None):
    payload = json.dumps({"event": event, "session_id": session_id, "data": data}, default=str, ensure_ascii=False)
    dead = set()
    for q in SUBSCRIBERS:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            dead.add(q)
    SUBSCRIBERS -= dead


def register_subscriber() -> asyncio.Queue:
    q = asyncio.Queue(maxsize=1000)
    SUBSCRIBERS.add(q)
    return q


def unregister_subscriber(q: asyncio.Queue):
    SUBSCRIBERS.discard(q)
