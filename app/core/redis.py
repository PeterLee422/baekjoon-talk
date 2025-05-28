# app/core/redis.py

# import redis.asyncio as redis
from redis.asyncio import Redis
from app.core.configuration import settings
from functools import lru_cache

@lru_cache()
def get_redis_client() -> Redis:
    return Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True
    )


# redis_client = redis.Redis(
#     host=settings.REDIS_HOST,
#     port=settings.REDIS_PORT,
#     db=0,
#     decode_responses=True
# )