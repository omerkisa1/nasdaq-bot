import logging

from providers import nasdaq, yahoo

logger = logging.getLogger(__name__)


async def get_quote_with_fallback(symbol: str) -> dict | None:
    try:
        return await nasdaq.get_quote(symbol)
    except Exception as exc:
        logger.warning("Nasdaq quote başarısız, Yahoo fallback: %s (%s)", symbol, exc)

    try:
        candles = await yahoo.get_candles(symbol, range_="5d", interval="1d")
    except Exception as exc:
        logger.error("Yahoo fallback de başarısız: %s (%s)", symbol, exc)
        return None

    if not candles:
        return None

    last = candles[-1]
    return {
        "symbol": symbol,
        "company_name": None,
        "last_sale_price": last["close"],
        "net_change": None,
        "pct_change": None,
        "volume": last["volume"],
        "market_status": None,
        "day_range": None,
        "fifty_two_week_range": None,
    }
