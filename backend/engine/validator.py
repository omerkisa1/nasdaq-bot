from dataclasses import dataclass


@dataclass
class ValidationResult:
    valid: bool
    reason: str
    position_size: int = 0
    risk_amount: float = 0.0


def validate_card(
    card: dict,
    current_price: float,
    avg_daily_volume: float,
    account_size: float,
    risk_percent: float,
    liquidity_cap_pct: float,
) -> ValidationResult:
    entry_low = card["entry_zone_low"]
    entry_high = card["entry_zone_high"]
    stop = card["stop"]
    target_1 = card["target_1"]
    target_2 = card["target_2"]

    if not (stop < entry_low < entry_high < target_1 < target_2):
        return ValidationResult(False, "geçersiz seviye sıralaması")

    stop_distance_pct = (entry_low - stop) / entry_low * 100
    if not (2.0 <= stop_distance_pct <= 15.0):
        return ValidationResult(False, f"stop mesafesi aralık dışı: %{stop_distance_pct:.1f}")

    risk = entry_low - stop
    reward = target_1 - entry_low
    rr = reward / risk if risk > 0 else 0
    if rr < 1.2:
        return ValidationResult(False, f"R/R yetersiz: {rr:.2f}")

    entry_mid = (entry_low + entry_high) / 2
    drift_pct = abs(current_price - entry_mid) / current_price * 100
    if drift_pct > 5.0:
        return ValidationResult(False, f"bayat kart: fiyat giriş bölgesinden %{drift_pct:.1f} uzak")

    risk_amount = account_size * risk_percent / 100
    position_size_risk = risk_amount / risk
    position_size_liquidity = avg_daily_volume * liquidity_cap_pct / 100
    position_size = int(min(position_size_risk, position_size_liquidity))

    if position_size < 1:
        return ValidationResult(False, "pozisyon boyutu 0 (risk/likidite limiti çok düşük)")

    return ValidationResult(True, "ok", position_size=position_size, risk_amount=risk_amount)
