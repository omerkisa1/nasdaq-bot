import logging
from dataclasses import dataclass

from config import settings
from core.market_hours import can_open_horizon, horizon_to_expires_at
from engine import card_generator, validator

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    attempted_gemini: bool
    has_setup: bool
    card_data: dict | None
    validation: validator.ValidationResult | None
    skip_reason: str | None = None


async def evaluate_candidate(symbol: str, snapshot: dict, settings_dict: dict, trigger_source: str = "scan") -> EvaluationResult:
    gemini_result = await card_generator.generate_card(symbol, snapshot, trigger=trigger_source)
    if gemini_result is None:
        return EvaluationResult(False, False, None, None, "Gemini yanıt vermedi")

    if not gemini_result.get("has_setup"):
        return EvaluationResult(True, False, None, None, gemini_result.get("skip_reason", "setup yok"))

    card_data = gemini_result["card"]
    if card_data.get("confidence", 0) < settings_dict.get("min_confidence", 0.5):
        return EvaluationResult(True, False, card_data, None, "güven eşiği altında")
    if not can_open_horizon(card_data["horizon"]):
        return EvaluationResult(True, False, card_data, None, "kapanışa çok az kaldı")

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
        return EvaluationResult(True, False, card_data, result, result.reason)

    return EvaluationResult(True, True, card_data, result, None)


def build_card_row(
    symbol: str,
    card_data: dict,
    validation: validator.ValidationResult,
    snapshot: dict,
    company_name: str | None = None,
    trigger_source: str = "scan",
) -> dict:
    expires_at = horizon_to_expires_at(card_data["horizon"])
    return {
        "symbol": symbol,
        "company_name": company_name,
        "direction": card_data.get("direction", "long"),
        "entry_zone_low": card_data["entry_zone_low"],
        "entry_zone_high": card_data["entry_zone_high"],
        "stop": card_data["stop"],
        "target_1": card_data["target_1"],
        "target_2": card_data["target_2"],
        "horizon": card_data["horizon"],
        "expires_at": expires_at.isoformat(),
        "confidence": card_data["confidence"],
        "position_size": validation.position_size,
        "risk_amount": validation.risk_amount,
        "reasoning": card_data.get("reasoning"),
        "invalidation": card_data.get("invalidation"),
        "catalyst": card_data.get("catalyst"),
        "news_context": snapshot.get("news"),
        "snapshot": snapshot,
        "price_at_creation": snapshot["quote"]["last_sale_price"],
        "trigger_source": trigger_source,
    }
