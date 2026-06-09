"""Shared Redis client.

Used for rate-limit counters, alert dedup, AI health/degradation state, and
chat session cache (Architecture 2).
"""
from __future__ import annotations

import redis.asyncio as aioredis

from app.config import settings

redis_client: aioredis.Redis = aioredis.from_url(  # type: ignore[no-untyped-call]
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
    socket_connect_timeout=5,
    health_check_interval=30,
)


async def close_redis() -> None:
    await redis_client.aclose()
