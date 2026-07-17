import time

from config import settings


def passes_mechanical_filter(candidate: dict) -> bool:
    price = candidate["close"]
    rvol = candidate["rvol"] or 0
    change_pct = candidate["change_pct"] or 0

    if not (settings.universe_price_min <= price <= settings.universe_price_max):
        return False
    if rvol < settings.prefilter_min_rvol:
        return False
    if not (change_pct >= 3.0 or change_pct <= -5.0):
        return False
    return True


def has_recent_trade(intraday_chart: list[dict], within_minutes: int = 30, now_ms: int | None = None) -> bool:
    if not intraday_chart:
        return False
    now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
    last_ts = max(point["ts_ms"] for point in intraday_chart)
    return (now_ms - last_ts) <= within_minutes * 60_000


def prefilter_universe(candidates: list[dict]) -> list[dict]:
    return [c for c in candidates if passes_mechanical_filter(c)]
