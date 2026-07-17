from core.http import get_client, with_retry
from providers.news.base import NewsItem, NewsProvider

BASE_URL = "https://www.nasdaq.com/api/news/topic/articlebysymbol"
SITE_URL = "https://www.nasdaq.com"


def map_row_to_newsitem(row: dict) -> NewsItem:
    url = row.get("url") or ""
    absolute_url = url if url.startswith("http") else f"{SITE_URL}{url}"
    return NewsItem(
        headline=row.get("title", ""),
        summary=row.get("description", ""),
        source=row.get("publisher", "") or "Nasdaq",
        url=absolute_url,
        datetime=0,
        external_id=str(row["id"]) if row.get("id") is not None else None,
    )


class NasdaqNewsProvider(NewsProvider):
    @with_retry()
    async def _get(self, params: dict):
        client = get_client()
        return await client.get(BASE_URL, params=params)

    async def get_news(self, symbol: str, hours_back: int = 48, limit: int = 10) -> list[NewsItem]:
        resp = await self._get(
            {"q": f"{symbol.upper()}|STOCKS", "offset": 0, "limit": limit, "fallback": "true"}
        )
        resp.raise_for_status()
        payload = resp.json()
        rows = ((payload.get("data") or {}).get("rows")) or []
        return [map_row_to_newsitem(row) for row in rows if row.get("id") is not None]
