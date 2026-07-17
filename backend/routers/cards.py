from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.ws_manager import ws_manager
from db import repo

router = APIRouter(prefix="/api/cards", tags=["cards"])


class CardPatch(BaseModel):
    status: str


@router.get("")
async def list_cards(status: str | None = None, limit: int = 20):
    if status:
        return await repo.get_cards(status=status, limit=limit)
    active = await repo.get_cards(status="ACTIVE", limit=100)
    closed = await repo.get_resolved_cards(limit=limit)
    return active + closed


@router.get("/{card_id}")
async def get_card(card_id: int):
    card = await repo.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="kart bulunamadı")
    return card


@router.patch("/{card_id}")
async def cancel_card(card_id: int, patch: CardPatch):
    if patch.status != "CANCELLED":
        raise HTTPException(status_code=400, detail="sadece CANCELLED durumuna geçilebilir")
    updated = await repo.update_card(
        card_id, {"status": "CANCELLED", "resolved_at": datetime.now(timezone.utc).isoformat()}
    )
    await ws_manager.broadcast({"type": "card_updated", "data": updated})
    return updated
