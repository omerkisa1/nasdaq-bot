import logging
import time
from datetime import date, timedelta

from config import settings
from core import redis_client, state
from core.market_hours import is_market_open
from core.ws_manager import ws_manager
from db import repo
from engine import metrics, prefilter
from engine.card_pipeline import build_card_row, evaluate_candidate
from providers import nasdaq, tradingview, yahoo
from providers.quotes import get_quote_with_fallback
from providers.news.article_content import get_full_content
from providers.news.chain import ChainedNewsProvider
from providers.news.finnhub import FinnhubNewsProvider
from providers.news.nasdaq_news import NasdaqNewsProvider

logger = logging.getLogger(__name__)

news_provider = ChainedNewsProvider([NasdaqNewsProvider(), FinnhubNewsProvider()])


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

    if news_items:
        try:
            news_items[0].summary = await get_full_content(news_items[0])
        except Exception:
            logger.warning("Makale tam içeriği alınamadı, özetle devam: %s", symbol)

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

    evaluation = await evaluate_candidate(symbol, snapshot, settings_dict, trigger_source="scan")
    await redis_client.set_cooldown(symbol, settings.gemini_symbol_cooldown_sec)

    if not evaluation.attempted_gemini:
        return False, False
    if not evaluation.has_setup:
        return True, False

    row = build_card_row(
        symbol, evaluation.card_data, evaluation.validation, snapshot,
        company_name=candidate.get("description"), trigger_source="scan",
    )
    inserted = await repo.insert_card(row)
    await ws_manager.broadcast({"type": "card_created", "data": inserted})
    return True, True


async def run_scan(force: bool = False) -> dict:
    started = time.monotonic()
    settings_dict = await repo.get_settings()

    if not force and (not settings_dict.get("scan_enabled", True) or not is_market_open()):
        return {"skipped": True}

    universe = await tradingview.scan_universe(limit=200)
    state.set_top_symbols([c["symbol"] for c in universe[: settings.news_watch_top_n]])
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
