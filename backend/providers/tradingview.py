from cachetools import TTLCache

from config import settings
from core.http import get_client, with_retry

SCAN_URL = "https://scanner.tradingview.com/america/scan"

_scan_cache: TTLCache = TTLCache(maxsize=4, ttl=60)


@with_retry()
async def _post(url: str, json: dict):
    client = get_client()
    return await client.post(url, json=json, headers={"Content-Type": "application/json"})


async def scan_universe(limit: int = 200) -> list[dict]:
    """Penny hisse evrenini RVOL sıralı tarar."""
    cache_key = f"scan:{limit}"
    if cache_key in _scan_cache:
        return _scan_cache[cache_key]

    body = {
        "filter": [
            {"left": "close", "operation": "in_range", "right": [settings.universe_price_min, settings.universe_price_max]},
            {"left": "volume", "operation": "greater", "right": settings.universe_min_vol},
            {"left": "exchange", "operation": "in_range", "right": ["NASDAQ"]},
        ],
        "columns": [
            "name",
            "description",
            "close",
            "volume",
            "change",
            "relative_volume_10d_calc",
            "float_shares_outstanding",
            "market_cap_basic",
        ],
        "sort": {"sortBy": "relative_volume_10d_calc", "sortOrder": "desc"},
        "range": [0, limit],
    }
    resp = await _post(SCAN_URL, json=body)
    resp.raise_for_status()
    payload = resp.json()

    columns = body["columns"]
    result = []
    for row in payload.get("data", []):
        values = dict(zip(columns, row["d"]))
        result.append(
            {
                "symbol": values["name"],
                "description": values["description"],
                "close": values["close"],
                "volume": values["volume"],
                "change_pct": values["change"],
                "rvol": values["relative_volume_10d_calc"],
                "float_shares": values["float_shares_outstanding"],
                "market_cap": values["market_cap_basic"],
            }
        )
    _scan_cache[cache_key] = result
    return result
