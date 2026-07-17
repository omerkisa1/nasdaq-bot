import asyncio
import logging

import trafilatura

from core import redis_client
from core.http import get_client
from providers.news.base import NewsItem

logger = logging.getLogger(__name__)

MIN_SUFFICIENT_LENGTH = 120
SCRAPE_TIMEOUT_SEC = 8.0


def is_description_insufficient(description: str) -> bool:
    if not description:
        return True
    stripped = description.strip()
    if len(stripped) < MIN_SUFFICIENT_LENGTH:
        return True
    if stripped.endswith("...") or stripped.endswith(","):
        return True
    if stripped[-1] not in ".!?\"'”":
        return True
    return False


async def _scrape(url: str) -> str | None:
    client = get_client()
    resp = await client.get(url)
    resp.raise_for_status()
    return trafilatura.extract(resp.text)


async def get_full_content(item: NewsItem) -> str:
    """description yetersizse tam makale metnini getirmeyi dener. Redis'te 24h cache'lenir.
    Başarısız olursa description ile devam edilir, pipeline durmaz."""
    if not is_description_insufficient(item.summary):
        return item.summary

    if item.external_id:
        cached = await redis_client.get_cached_article(item.external_id)
        if cached is not None:
            return cached

    try:
        content = await asyncio.wait_for(_scrape(item.url), timeout=SCRAPE_TIMEOUT_SEC)
    except Exception as exc:
        logger.warning("Makale scrape başarısız %s: %s", item.url, exc)
        return item.summary

    if not content:
        return item.summary

    if item.external_id:
        await redis_client.cache_article(item.external_id, content)
    return content
