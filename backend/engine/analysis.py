from core.parsers import parse_range

POSITIVE_KEYWORDS = [
    "fda approval", "approved", "phase 2", "phase 3", "acquisition", "acquire",
    "contract", "beats estimates", "upgrade", "partnership", "merger",
]
NEGATIVE_KEYWORDS = [
    "insider sale", "insider sold", "offering", "dilution", "s-1", "424b5",
    "investigation", "delisting", "downgrade", "lawsuit", "going concern",
]


def classify_headline(headline: str) -> str:
    lowered = headline.lower()
    if any(k in lowered for k in NEGATIVE_KEYWORDS):
        return "negatif"
    if any(k in lowered for k in POSITIVE_KEYWORDS):
        return "pozitif"
    return "nötr"


def build_context_summary(snapshot: dict, min_rvol: float) -> dict:
    quote = snapshot["quote"]
    price = quote["last_sale_price"]
    avg_daily_volume = snapshot["avg_daily_volume"]
    rvol = round(quote["volume"] / avg_daily_volume, 2) if avg_daily_volume else 0.0

    levels = snapshot["levels"]
    supports_below = [s for s in levels["support"] if s < price]
    resistances_above = [r for r in levels["resistance"] if r > price]
    support = max(supports_below) if supports_below else None
    resistance = min(resistances_above) if resistances_above else None

    warnings = []
    day_range = parse_range(quote.get("day_range") or "")
    if day_range:
        _, day_high = day_range
        if day_high > 0 and price < day_high:
            pct_from_high = (day_high - price) / day_high * 100
            if pct_from_high > 10:
                warnings.append(f"zirveden %{pct_from_high:.0f} uzakta")
    if rvol < min_rvol:
        warnings.append(f"RVOL düşük ({rvol:.1f}x)")

    news = [
        {
            "headline": n["headline"],
            "source": n["source"],
            "classification": classify_headline(n["headline"]),
        }
        for n in snapshot.get("news", [])
    ]

    return {
        "price": price,
        "rvol": rvol,
        "atr": snapshot["atr_14"],
        "key_levels": {"support": support, "resistance": resistance},
        "news": news,
        "warnings": warnings,
    }
