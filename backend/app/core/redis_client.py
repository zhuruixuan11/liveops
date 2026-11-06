from typing import Optional

import redis.asyncio as aioredis
import redis as sync_redis

from app.core.config import get_settings

settings = get_settings()


async def get_redis():
    return aioredis.from_url(settings.redis_url, decode_responses=True)


def get_sync_redis():
    return sync_redis.from_url(settings.redis_url, decode_responses=True)
