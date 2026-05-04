from redis import asyncio as aioredis
from app.core.config import settings

_redis = None

async def get_redis():
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=1,  # 👈 important
            socket_timeout=1
        )
    return _redis