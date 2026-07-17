from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from db import repo
from engine.stats import compute_stats

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
async def get_stats():
    cards = await repo.get_resolved_cards(limit=5000)
    overall = compute_stats(cards)

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    last_30d_cards = [c for c in cards if _created_at(c) >= cutoff]
    overall["last_30d"] = compute_stats(last_30d_cards)
    return overall


def _created_at(card: dict) -> datetime:
    value = card["created_at"]
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value
