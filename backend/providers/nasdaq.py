import logging

from cachetools import TTLCache

from core.http import get_client, with_retry
from core.parsers import parse_date, parse_price, parse_volume

logger = logging.getLogger(__name__)

BASE_URL = "https://api.nasdaq.com/api/quote"

_quote_cache: TTLCache = TTLCache(maxsize=256, ttl=5)
_historical_cache: TTLCache = TTLCache(maxsize=256, ttl=3600)


@with_retry()
async def _get(url: str, params: dict | None = None):
    client = get_client()
    return await client.get(url, params=params)


async def get_quote(symbol: str) -> dict:
    """Anlık fiyat + hacim. Nasdaq quote/info endpoint."""
    cache_key = f"quote:{symbol}"
    if cache_key in _quote_cache:
        return _quote_cache[cache_key]

    resp = await _get(f"{BASE_URL}/{symbol}/info", params={"assetclass": "stocks"})
    resp.raise_for_status()
    payload = resp.json()
    data = payload.get("data") or {}
    primary = data.get("primaryData") or {}
    key_stats = data.get("keyStats") or {}

    result = {
        "symbol": symbol,
        "company_name": data.get("companyName"),
        "last_sale_price": parse_price(primary.get("lastSalePrice", "0")),
        "net_change": parse_price(primary.get("netChange", "0")),
        "pct_change": parse_price(primary.get("percentageChange", "0")),
        "volume": parse_volume(primary.get("volume", "0")),
        "market_status": data.get("marketStatus"),
        "day_range": key_stats.get("dayrange", {}).get("value"),
        "fifty_two_week_range": key_stats.get("fiftyTwoWeekHighLow", {}).get("value"),
    }
    _quote_cache[cache_key] = result
    return result


async def get_intraday_chart(symbol: str) -> list[dict]:
    """Gün içi dakika verisi."""
    resp = await _get(f"{BASE_URL}/{symbol}/chart", params={"assetclass": "stocks"})
    resp.raise_for_status()
    payload = resp.json()
    chart = (payload.get("data") or {}).get("chart") or []
    return [{"ts_ms": point["x"], "price": float(point["y"])} for point in chart if point.get("y") is not None]


async def get_historical(symbol: str, from_date: str, limit: int = 9999) -> list[dict]:
    """Günlük OHLCV. from_date formatı YYYY-MM-DD."""
    cache_key = f"historical:{symbol}:{from_date}:{limit}"
    if cache_key in _historical_cache:
        return _historical_cache[cache_key]

    resp = await _get(
        f"{BASE_URL}/{symbol}/historical",
        params={"assetclass": "stocks", "fromdate": from_date, "limit": limit},
    )
    resp.raise_for_status()
    payload = resp.json()
    rows = ((payload.get("data") or {}).get("tradesTable") or {}).get("rows") or []

    result = []
    for row in rows:
        result.append(
            {
                "date": parse_date(row["date"]),
                "open": parse_price(row["open"]),
                "high": parse_price(row["high"]),
                "low": parse_price(row["low"]),
                "close": parse_price(row["close"]),
                "volume": parse_volume(row["volume"]),
            }
        )
    _historical_cache[cache_key] = result
    return result
