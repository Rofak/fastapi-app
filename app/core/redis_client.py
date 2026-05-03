from redis import asyncio as aioredis

_redis = None

async def get_redis():
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            "redis://localhost:6379",
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=1,  # 👈 important
            socket_timeout=1
        )
    return _redis