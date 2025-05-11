# app/core/redis.py

import redis.asyncio as redis
from app.core.configuration import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True
)