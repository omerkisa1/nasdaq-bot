import logging
import time
from datetime import date, timedelta

from config import settings
from core import redis_client
from core.market_hours import can_open_horizon, horizon_to_expires_at, is_market_open
from core.ws_manager import ws_manager
from db import repo
from engine import card_generator, metrics, prefilter, validator
from providers import nasdaq, tradingview, yahoo
from providers.quotes import get_quote_with_fallback
from providers.news.finnhub import FinnhubNewsProvider

logger = logging.getLogger(__name__)

news_provider = FinnhubNewsProvider()


def filter_candidates_for_processing(
    prefiltered: list[dict],
    active_symbols: set[str],
    cooldown_symbols: set[str],
    max_count: int,
) -> list[dict]:
    result = []
    for candidate in prefiltered:
        if len(result) >= max_count:
            break
        if candidate["symbol"] in active_symbols or candidate["symbol"] in cooldown_symbols:
            continue
        result.append(candidate)
    return result


async def build_snapshot(symbol: str) -> dict | None:
    from_date = (date.today() - timedelta(days=90)).isoformat()

    try:
        historical = await nasdaq.get_historical(symbol, from_date)
    except Exception:
        logger.warning("Nasdaq historical başarısız, Yahoo fallback: %s", symbol)
        candles = await yahoo.get_candles(symbol, range_="3mo", interval="1d")
        historical = [
            {"date": None, "open": c["open"], "high": c["high"], "low": c["low"],
             "close": c["close"], "volume": c["volume"]}
            for c in candles
        ]

    if len(historical) < 20:
        return None

    try:
        intraday = await nasdaq.get_intraday_chart(symbol)
    except Exception:
        intraday = []

    if not prefilter.has_recent_trade(intraday, within_minutes=30):
        return None

    quote = await get_quote_with_fallback(symbol)
    if quote is None:
        return None

    recent_volumes = [c["volume"] for c in historical[-20:]]
    avg_daily_volume = sum(recent_volumes) / len(recent_volumes)

    closes = [c["close"] for c in historical]
    intraday_vwap = metrics.vwap([{"price": p["price"], "volume": 1} for p in intraday]) if intraday else quote["last_sale_price"]

    try:
        news_items = await news_provider.get_news(symbol, hours_back=48)
    except Exception:
        news_items = []

    return {
        "quote": quote,
        "avg_daily_volume": avg_daily_volume,
        "atr_14": metrics.atr(historical, period=14),
        "rsi_14": metrics.rsi(closes, period=14),
        "ema_9": metrics.ema(closes, period=9),
        "ema_21": metrics.ema(closes, period=21),
        "vwap_today": intraday_vwap,
        "levels": metrics.support_resistance(historical[-60:]),
        "news": [
            {"headline": n.headline, "summary": n.summary, "source": n.source, "datetime": n.datetime}
            for n in news_items
        ],
    }


async def _process_candidate(candidate: dict, settings_dict: dict) -> tuple[bool, bool]:
    """Returns (attempted_gemini_call, card_created)."""
    symbol = candidate["symbol"]

    snapshot = await build_snapshot(symbol)
    if snapshot is None:
        return False, False

    gemini_result = await card_generator.generate_card(symbol, snapshot)
    await redis_client.set_cooldown(symbol, settings.gemini_symbol_cooldown_sec)

    if gemini_result is None or not gemini_result.get("has_setup"):
        return True, False

    card_data = gemini_result["card"]
    if card_data.get("confidence", 0) < settings_dict.get("min_confidence", 0.5):
        return True, False
    if not can_open_horizon(card_data["horizon"]):
        return True, False

    result = validator.validate_card(
        card_data,
        current_price=snapshot["quote"]["last_sale_price"],
        avg_daily_volume=snapshot["avg_daily_volume"],
        account_size=settings_dict.get("account_size", settings.default_account_size),
        risk_percent=settings_dict.get("risk_percent", settings.default_risk_percent),
        liquidity_cap_pct=settings.liquidity_cap_pct,
    )
    if not result.valid:
        logger.info("Kart reddedildi %s: %s", symbol, result.reason)
        return True, False

    expires_at = horizon_to_expires_at(card_data["horizon"])
    row = {
        "symbol": symbol,
        "company_name": candidate.get("description"),
        "direction": card_data.get("direction", "long"),
        "entry_zone_low": card_data["entry_zone_low"],
        "entry_zone_high": card_data["entry_zone_high"],
        "stop": card_data["stop"],
        "target_1": card_data["target_1"],
        "target_2": card_data["target_2"],
        "horizon": card_data["horizon"],
        "expires_at": expires_at.isoformat(),
        "confidence": card_data["confidence"],
        "position_size": result.position_size,
        "risk_amount": result.risk_amount,
        "reasoning": card_data.get("reasoning"),
        "invalidation": card_data.get("invalidation"),
        "catalyst": card_data.get("catalyst"),
        "news_context": snapshot["news"],
        "snapshot": snapshot,
        "price_at_creation": snapshot["quote"]["last_sale_price"],
    }
    inserted = await repo.insert_card(row)
    await ws_manager.broadcast({"type": "card_created", "data": inserted})
    return True, True


async def run_scan(force: bool = False) -> dict:
    started = time.monotonic()
    settings_dict = await repo.get_settings()

    if not force and (not settings_dict.get("scan_enabled", True) or not is_market_open()):
        return {"skipped": True}

    universe = await tradingview.scan_universe(limit=200)
    prefiltered = prefilter.prefilter_universe(universe)

    active_symbols = await repo.get_active_card_symbols()
    active_count = len(active_symbols)
    max_active = int(settings_dict.get("max_active_cards", settings.max_active_cards))
    slots = max(0, max_active - active_count)

    cooldown_symbols = {
        c["symbol"] for c in prefiltered if await redis_client.is_on_cooldown(c["symbol"])
    }
    budget = min(slots, settings.gemini_max_calls_per_scan)
    candidates = filter_candidates_for_processing(prefiltered, active_symbols, cooldown_symbols, budget)

    gemini_calls = 0
    cards_created = 0
    cards_rejected = 0

    for candidate in candidates:
        if slots <= 0 or gemini_calls >= settings.gemini_max_calls_per_scan:
            break
        attempted, created = await _process_candidate(candidate, settings_dict)
        if attempted:
            gemini_calls += 1
        if created:
            cards_created += 1
            slots -= 1
        elif attempted:
            cards_rejected += 1

    duration_ms = int((time.monotonic() - started) * 1000)
    run_row = {
        "universe_size": len(universe),
        "prefiltered_count": len(prefiltered),
        "gemini_calls": gemini_calls,
        "cards_created": cards_created,
        "cards_rejected": cards_rejected,
        "duration_ms": duration_ms,
    }
    inserted_run = await repo.insert_scan_run(run_row)
    await ws_manager.broadcast({"type": "scan_completed", "data": inserted_run})
    return inserted_run
