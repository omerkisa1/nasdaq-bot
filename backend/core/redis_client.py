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


NEWS_SEEN_TTL_SEC = 7 * 24 * 3600


def _news_seen_key(symbol: str, external_id: str) -> str:
    return f"news_seen:{symbol}:{external_id}"


async def is_news_seen(symbol: str, external_id: str) -> bool:
    return await get_redis().exists(_news_seen_key(symbol, external_id)) > 0


async def mark_news_seen(symbol: str, external_id: str) -> None:
    await get_redis().set(_news_seen_key(symbol, external_id), "1", ex=NEWS_SEEN_TTL_SEC)


def _manual_cooldown_key(symbol: str) -> str:
    return f"manual_cooldown:{symbol}"


async def is_on_manual_cooldown(symbol: str) -> bool:
    return await get_redis().exists(_manual_cooldown_key(symbol)) > 0


async def set_manual_cooldown(symbol: str, ttl_sec: int) -> None:
    await get_redis().set(_manual_cooldown_key(symbol), "1", ex=ttl_sec)


def _news_gemini_budget_key() -> str:
    import time

    hour_bucket = int(time.time() // 3600)
    return f"news_gemini_budget:{hour_bucket}"


async def get_news_gemini_budget_used() -> int:
    value = await get_redis().get(_news_gemini_budget_key())
    return int(value) if value else 0


async def increment_news_gemini_budget() -> int:
    key = _news_gemini_budget_key()
    redis_conn = get_redis()
    count = await redis_conn.incr(key)
    if count == 1:
        await redis_conn.expire(key, 3600)
    return count


def _article_cache_key(external_id: str) -> str:
    return f"article_content:{external_id}"


async def get_cached_article(external_id: str) -> str | None:
    return await get_redis().get(_article_cache_key(external_id))


async def cache_article(external_id: str, content: str, ttl_sec: int = 24 * 3600) -> None:
    await get_redis().set(_article_cache_key(external_id), content, ex=ttl_sec)
