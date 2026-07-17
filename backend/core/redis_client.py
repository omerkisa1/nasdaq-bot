import redis.asyncio as redis

from config import settings

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def _cooldown_key(symbol: str) -> str:
    return f"gemini_cooldown:{symbol}"


async def is_on_cooldown(symbol: str) -> bool:
    return await get_redis().exists(_cooldown_key(symbol)) > 0


async def set_cooldown(symbol: str, ttl_sec: int) -> None:
    await get_redis().set(_cooldown_key(symbol), "1", ex=ttl_sec)
