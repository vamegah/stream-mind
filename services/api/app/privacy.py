import redis.asyncio as redis
from fastapi import HTTPException, Depends
import os

redis_client = None


async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = await redis.from_url("redis://redis:6379", decode_responses=True)
    return redis_client


EPSILON_PER_QUERY = float(os.getenv("PRIVACY_EPSILON_PER_QUERY", "0.1"))
DAILY_BUDGET = float(os.getenv("PRIVACY_DAILY_BUDGET", "1.0"))


async def check_privacy_budget(user_token: str) -> bool:
    """
    Check if user has enough budget left.
    If yes, consume epsilon and return True.
    Else return False.
    """
    r = await get_redis()
    key = f"privacy:budget:{user_token}"
    # Get current remaining budget (default to DAILY_BUDGET)
    remaining = await r.get(key)
    if remaining is None:
        remaining = DAILY_BUDGET
        await r.setex(key, 86400, remaining)  # 24h TTL
    else:
        remaining = float(remaining)
    if remaining >= EPSILON_PER_QUERY:
        new_remaining = remaining - EPSILON_PER_QUERY
        await r.setex(key, 86400, new_remaining)
        return True
    return False


async def get_remaining_budget(user_token: str) -> float:
    r = await get_redis()
    remaining = await r.get(f"privacy:budget:{user_token}")
    if remaining is None:
        return DAILY_BUDGET
    return float(remaining)
