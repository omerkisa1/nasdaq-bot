import asyncio
import logging
import random

from config import settings
from core import redis_client, state
from core.market_hours import is_market_open
from core.ws_manager import ws_manager
from db import repo
from engine.card_pipeline import build_card_row, evaluate_candidate
from providers.quotes import get_quote_with_fallback

logger = logging.getLogger(__name__)


def get_watchlist_symbols(top_symbols: list[str], active_symbols: set[str], max_n: int) -> list[str]:
    combined = list(dict.fromkeys([*top_symbols, *active_symbols]))
    return combined[:max_n]


def compute_price_change_pct(price_at_detection: float, current_price: float) -> float:
    if not price_at_detection:
        return 0.0
    return (current_price - price_at_detection) / price_at_detection * 100


def is_volume_accelerating(volume_samples: list[float]) -> bool:
    """volume_samples: kümülatif günlük hacim, zaman sırasıyla. İkinci yarının ortalama artış
    hızı ilk yarıdan büyükse hacim akışı hızlanıyor demektir."""
    if len(volume_samples) < 3:
        return False
    deltas = [b - a for a, b in zip(volume_samples, volume_samples[1:])]
    mid = len(deltas) // 2
    first_half, second_half = deltas[:mid], deltas[mid:]
    if not first_half or not second_half:
        return False
    return (sum(second_half) / len(second_half)) > (sum(first_half) / len(first_half))


def evaluate_reaction(price_change_pct: float, volume_accelerating: bool, min_pct: float) -> bool:
    return abs(price_change_pct) >= min_pct and volume_accelerating


async def run_news_watch_cycle() -> None:
    if not is_market_open():
        return

    from engine import scanner  # döngüsel import'tan kaçınmak için burada

    active_symbols = await repo.get_active_card_symbols()
    top_symbols = state.get_top_symbols()
    symbols = get_watchlist_symbols(top_symbols, active_symbols, settings.news_watch_top_n)

    for symbol in symbols:
        await asyncio.sleep(random.uniform(0.1, 0.3))
        try:
            await _check_symbol_news(symbol, scanner.news_provider)
        except Exception:
            logger.exception("Haber kontrolü başarısız: %s", symbol)


async def _check_symbol_news(symbol: str, news_provider) -> None:
    items = await news_provider.get_news(symbol, limit=5)
    for item in items:
        if not item.external_id:
            continue
        if await redis_client.is_news_seen(symbol, item.external_id):
            continue
        await redis_client.mark_news_seen(symbol, item.external_id)

        event = await repo.insert_news_event(
            {
                "symbol": symbol,
                "external_id": item.external_id,
                "headline": item.headline,
                "description": item.summary,
                "source": item.source,
                "url": item.url,
            }
        )
        if event is None:
            continue
        asyncio.create_task(_process_news_event(symbol, item, event))


async def _process_news_event(symbol: str, item, event: dict) -> None:
    quote = await get_quote_with_fallback(symbol)
    if quote is None:
        await repo.update_news_event(event["id"], {"reaction": "no_reaction"})
        return

    price_at_detection = quote["last_sale_price"]
    price_samples = [price_at_detection]
    volume_samples = [quote["volume"]]

    elapsed = 0
    interval = 15
    while elapsed < settings.news_reaction_window_sec:
        await asyncio.sleep(interval)
        elapsed += interval
        sample = await get_quote_with_fallback(symbol)
        if sample is None:
            continue
        price_samples.append(sample["last_sale_price"])
        volume_samples.append(sample["volume"])

    price_change_pct = compute_price_change_pct(price_at_detection, price_samples[-1])
    accelerating = is_volume_accelerating(volume_samples)
    confirmed = evaluate_reaction(price_change_pct, accelerating, settings.news_reaction_min_pct)

    await repo.update_news_event(
        event["id"],
        {
            "reaction": "confirmed" if confirmed else "no_reaction",
            "price_at_detection": price_at_detection,
            "price_change_pct": round(price_change_pct, 2),
        },
    )
    if not confirmed:
        return

    await _try_create_news_card(symbol, item, event)


async def _try_create_news_card(symbol: str, item, event: dict) -> None:
    from engine import scanner  # döngüsel import'tan kaçınmak için burada

    used = await redis_client.increment_news_gemini_budget()
    if used > settings.news_gemini_max_per_hour:
        logger.info("Haber Gemini bütçesi doldu, %s atlandı", symbol)
        return

    settings_dict = await repo.get_settings()
    active_symbols = await repo.get_active_card_symbols()
    if symbol in active_symbols:
        return
    max_active = int(settings_dict.get("max_active_cards", settings.max_active_cards))
    if len(active_symbols) >= max_active:
        return

    snapshot = await scanner.build_snapshot(symbol)
    if snapshot is None:
        return
    snapshot["news_trigger"] = {"headline": item.headline, "summary": item.summary, "source": item.source}

    evaluation = await evaluate_candidate(symbol, snapshot, settings_dict, trigger_source="news")
    if not evaluation.attempted_gemini or not evaluation.has_setup:
        return

    row = build_card_row(symbol, evaluation.card_data, evaluation.validation, snapshot, trigger_source="news")
    inserted = await repo.insert_card(row)
    await repo.update_news_event(event["id"], {"card_id": inserted["id"]})
    await ws_manager.broadcast({"type": "card_created", "data": inserted})
