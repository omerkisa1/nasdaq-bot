def compute_stats(cards: list[dict]) -> dict:
    total = len(cards)
    wins = sum(1 for c in cards if c["status"] == "TARGET_HIT")
    losses = sum(1 for c in cards if c["status"] == "STOP_HIT")
    expired = sum(1 for c in cards if c["status"] == "EXPIRED")
    no_fill = sum(1 for c in cards if c["status"] == "NO_FILL")

    resolved_r_cards = [c for c in cards if c.get("realized_r") is not None]
    total_r = sum(c["realized_r"] for c in resolved_r_cards)
    avg_r = total_r / len(resolved_r_cards) if resolved_r_cards else 0.0

    decided = wins + losses
    win_rate = wins / decided if decided else 0.0

    by_horizon: dict[str, dict] = {}
    for c in cards:
        h = c["horizon"]
        bucket = by_horizon.setdefault(h, {"count": 0, "wins": 0, "total_r": 0.0})
        bucket["count"] += 1
        if c["status"] == "TARGET_HIT":
            bucket["wins"] += 1
        if c.get("realized_r") is not None:
            bucket["total_r"] += c["realized_r"]

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "expired": expired,
        "no_fill": no_fill,
        "win_rate": round(win_rate, 4),
        "avg_r": round(avg_r, 4),
        "total_r": round(total_r, 4),
        "by_horizon": by_horizon,
    }
