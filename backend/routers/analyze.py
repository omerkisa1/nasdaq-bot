from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from config import settings
from core import redis_client
from core.ws_manager import ws_manager
from db import repo
from engine import validator
from engine.analysis import build_context_summary
from engine.card_pipeline import build_card_row, evaluate_candidate

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


@router.post("/{symbol}")
async def analyze_symbol(symbol: str):
    symbol = symbol.upper()

    if await redis_client.is_on_manual_cooldown(symbol):
        raise HTTPException(
            status_code=429, detail=f"{symbol} için birkaç dakika sonra tekrar analiz edilebilir"
        )
    await redis_client.set_manual_cooldown(symbol, settings.manual_analysis_cooldown_sec)

    from engine import scanner  # döngüsel import'tan kaçınmak için burada

    snapshot = await scanner.build_snapshot(symbol)
    if snapshot is None:
        return {
            "symbol": symbol,
            "verdict": "no_setup",
            "skip_reason": "yeterli veri alınamadı (sembol yanlış olabilir ya da işlem görmüyor)",
            "card_draft": None,
            "context_summary": None,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    settings_dict = await repo.get_settings()
    evaluation = await evaluate_candidate(symbol, snapshot, settings_dict, trigger_source="manual")
    context_summary = build_context_summary(snapshot, settings.prefilter_min_rvol)

    card_draft = None
    verdict = "no_setup"
    skip_reason = evaluation.skip_reason
    if evaluation.has_setup:
        verdict = "setup"
        skip_reason = None
        card_draft = build_card_row(
            symbol, evaluation.card_data, evaluation.validation, snapshot, trigger_source="manual"
        )

    return {
        "symbol": symbol,
        "verdict": verdict,
        "skip_reason": skip_reason,
        "card_draft": card_draft,
        "context_summary": context_summary,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/{symbol}/accept")
async def accept_card_draft(symbol: str, card_draft: dict):
    symbol = symbol.upper()

    from providers.quotes import get_quote_with_fallback

    quote = await get_quote_with_fallback(symbol)
    if quote is None:
        raise HTTPException(status_code=502, detail="fiyat verisi alınamadı")

    settings_dict = await repo.get_settings()
    snapshot = card_draft.get("snapshot") or {}
    avg_daily_volume = snapshot.get("avg_daily_volume", 0)

    result = validator.validate_card(
        card_draft,
        current_price=quote["last_sale_price"],
        avg_daily_volume=avg_daily_volume,
        account_size=settings_dict.get("account_size", settings.default_account_size),
        risk_percent=settings_dict.get("risk_percent", settings.default_risk_percent),
        liquidity_cap_pct=settings.liquidity_cap_pct,
    )
    if not result.valid:
        raise HTTPException(status_code=409, detail=f"kart bayatladı, tekrar analiz et: {result.reason}")

    active_symbols = await repo.get_active_card_symbols()
    max_active = int(settings_dict.get("max_active_cards", settings.max_active_cards))
    if len(active_symbols) >= max_active:
        raise HTTPException(status_code=409, detail="aktif kart limiti dolu")

    row = build_card_row(symbol, card_draft, result, snapshot, trigger_source="manual")
    row["price_at_creation"] = quote["last_sale_price"]

    inserted = await repo.insert_card(row)
    await ws_manager.broadcast({"type": "card_created", "data": inserted})
    return inserted
