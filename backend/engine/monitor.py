import asyncio
import random
from datetime import datetime, timezone

from core.market_hours import is_market_open
from core.ws_manager import ws_manager
from db import repo
from providers.quotes import get_quote_with_fallback


async def _fetch_quote_staggered(symbol: str, index: int) -> dict | None:
    await asyncio.sleep(index * 0.05 + random.uniform(0, 0.02))
    return await get_quote_with_fallback(symbol)


def _compute_r(entry_low: float, stop: float, resolved_price: float) -> float:
    risk = entry_low - stop
    if risk <= 0:
        return 0.0
    return round((resolved_price - entry_low) / risk, 2)


def evaluate_card(card: dict, price: float, now: datetime | None = None) -> dict:
    """Pure decision logic for one card given the latest price. Returns a dict describing
    what changed (patch for DB, tick info for the price_tick websocket message)."""
    now = now or datetime.now(timezone.utc)
    entry_low = float(card["entry_zone_low"])
    entry_high = float(card["entry_zone_high"])
    stop = float(card["stop"])
    target_1 = float(card["target_1"])
    target_2 = float(card["target_2"])
    snapshot = card.get("snapshot") or {}
    entered = bool(snapshot.get("entered", False))
    t1_hit = bool(card.get("t1_hit", False))
    expires_at = card["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))

    patch: dict = {}
    status = "ACTIVE"

    if not entered and entry_low <= price <= entry_high:
        entered = True
        patch["snapshot"] = {**snapshot, "entered": True}

    if entered and price <= stop:
        status = "STOP_HIT"
        patch.update(status="STOP_HIT", resolved_price=stop, realized_r=-1.0,
                     resolved_at=now.isoformat())
    elif entered and price >= target_2:
        status = "TARGET_HIT"
        patch.update(status="TARGET_HIT", resolved_price=price,
                     realized_r=_compute_r(entry_low, stop, price),
                     resolved_at=now.isoformat(), t1_hit=True)
    elif entered and not t1_hit and price >= target_1:
        t1_hit = True
        patch["t1_hit"] = True
    elif now >= expires_at:
        if entered:
            status = "EXPIRED"
            patch.update(status="EXPIRED", resolved_price=price,
                         realized_r=_compute_r(entry_low, stop, price),
                         resolved_at=now.isoformat())
        else:
            status = "NO_FILL"
            patch.update(status="NO_FILL", resolved_at=now.isoformat())

    pct_to_target = (target_1 - price) / price * 100 if price else 0.0
    pct_to_stop = (price - stop) / price * 100 if price else 0.0

    return {
        "patch": patch,
        "status": status,
        "tick": {
            "id": card["id"],
            "symbol": card["symbol"],
            "price": price,
            "pct_to_target": round(pct_to_target, 2),
            "pct_to_stop": round(pct_to_stop, 2),
        },
    }


async def run_monitor_cycle() -> None:
    if not is_market_open():
        return

    cards = await repo.get_cards(status="ACTIVE", limit=200)
    if not cards:
        return

    quotes = await asyncio.gather(
        *[_fetch_quote_staggered(c["symbol"], i) for i, c in enumerate(cards)]
    )

    tick_payload = []
    for card, quote in zip(cards, quotes):
        if quote is None:
            continue
        result = evaluate_card(card, quote["last_sale_price"])
        tick_payload.append(result["tick"])

        if result["patch"]:
            updated = await repo.update_card(card["id"], result["patch"])
            if result["status"] != "ACTIVE" or "t1_hit" in result["patch"]:
                await ws_manager.broadcast({"type": "card_updated", "data": updated})

    if tick_payload:
        await ws_manager.broadcast({"type": "price_tick", "data": {"cards": tick_payload}})
