import logging

from providers.news.base import NewsItem, NewsProvider

logger = logging.getLogger(__name__)


def dedup_news_items(items: list[NewsItem]) -> list[NewsItem]:
    seen: set[str] = set()
    result = []
    for item in items:
        key = item.external_id or item.url or item.headline
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


class ChainedNewsProvider(NewsProvider):
    """Birden fazla NewsProvider'ı sırayla sorgular, sonuçları external_id/url bazlı dedup eder."""

    def __init__(self, providers: list[NewsProvider]) -> None:
        self.providers = providers

    async def get_news(self, symbol: str, hours_back: int = 48, limit: int = 10) -> list[NewsItem]:
        combined: list[NewsItem] = []
        for provider in self.providers:
            try:
                items = await provider.get_news(symbol, hours_back=hours_back, limit=limit)
                combined.extend(items)
            except Exception as exc:
                logger.warning("Haber kaynağı başarısız (%s): %s", type(provider).__name__, exc)
        return dedup_news_items(combined)
