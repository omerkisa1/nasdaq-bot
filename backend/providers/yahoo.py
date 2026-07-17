"""Nasdaq 403/429 verirse fallback candle kaynağı."""
from core.http import get_client, with_retry

BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"


@with_retry()
async def _get(url: str, params: dict):
    client = get_client()
    return await client.get(url, params=params)


async def get_candles(symbol: str, range_: str = "3mo", interval: str = "1d") -> list[dict]:
    resp = await _get(f"{BASE_URL}/{symbol}", params={"range": range_, "interval": interval})
    resp.raise_for_status()
    payload = resp.json()
    result = payload["chart"]["result"][0]
    timestamps = result["timestamp"]
    quote = result["indicators"]["quote"][0]

    candles = []
    for i, ts in enumerate(timestamps):
        if quote["close"][i] is None:
            continue
        candles.append(
            {
                "timestamp": ts,
                "open": quote["open"][i],
                "high": quote["high"][i],
                "low": quote["low"][i],
                "close": quote["close"][i],
                "volume": quote["volume"][i] or 0,
            }
        )
    return candles
