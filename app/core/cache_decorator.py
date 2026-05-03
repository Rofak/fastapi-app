import json
import functools
import hashlib
from typing import Callable
from pydantic import BaseModel
from app.core.redis_client import get_redis


def serialize(data):
    if isinstance(data, BaseModel):
        return data.model_dump()
    if isinstance(data, list):
        return [serialize(item) for item in data]
    if isinstance(data, dict):
        return {k: serialize(v) for k, v in data.items()}
    return data


def redis_cache(expire: int = 60, key_builder=None):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):

            try:
                redis = await get_redis()

                key = key_builder(*args, **kwargs) if key_builder else func.__name__

                # 👉 CACHE READ
                try:
                    cached = await redis.get(key)
                    if cached:
                        return json.loads(cached)
                except Exception as e:
                    print("Redis GET failed:", e)

                # 👉 EXECUTE FUNCTION
                result = await func(*args, **kwargs)

                # 👉 CACHE WRITE (non-blocking)
                try:
                    serialized=serialize(result)
                    await redis.set(key, json.dumps(serialized), ex=expire)
                except Exception as e:
                    print("Redis SET failed:", e)

                return result

            except Exception as e:
                # 🔥 TOTAL FAILSAFE: Redis completely down
                print("Redis unavailable, bypassing cache:", e)
                return await func(*args, **kwargs)

        return wrapper
    return decorator