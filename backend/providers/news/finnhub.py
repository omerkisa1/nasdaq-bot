import time
from datetime import datetime, timedelta

from config import settings
from core.http import get_client, with_retry
from providers.news.base import NewsItem, NewsProvider

BASE_URL = "https://finnhub.io/api/v1/company-news"


class FinnhubNewsProvider(NewsProvider):
    @with_retry()
    async def _get(self, params: dict):
        client = get_client()
        return await client.get(BASE_URL, params=params)

    async def get_news(self, symbol: str, hours_back: int = 48) -> list[NewsItem]:
        now = datetime.utcnow()
        frm = (now - timedelta(hours=hours_back)).strftime("%Y-%m-%d")
        to = now.strftime("%Y-%m-%d")

        resp = await self._get(
            {"symbol": symbol, "from": frm, "to": to, "token": settings.finnhub_api_key}
        )
        resp.raise_for_status()
        cutoff = time.time() - hours_back * 3600

        items = []
        for entry in resp.json():
            if entry.get("datetime", 0) < cutoff:
                continue
            items.append(
                NewsItem(
                    headline=entry.get("headline", ""),
                    summary=entry.get("summary", ""),
                    source=entry.get("source", ""),
                    url=entry.get("url", ""),
                    datetime=entry.get("datetime", 0),
                )
            )
        return items
