import asyncio
from datetime import datetime, timezone

from config import settings
from db.supabase_client import get_supabase

DEFAULT_SETTINGS = {
    "account_size": settings.default_account_size,
    "risk_percent": settings.default_risk_percent,
    "max_active_cards": settings.max_active_cards,
    "paper_mode": True,
    "min_confidence": 0.5,
    "scan_enabled": True,
}


async def _run(fn):
    return await asyncio.to_thread(fn)


async def get_settings() -> dict:
    def _query():
        return get_supabase().table("system_settings").select("key,value").execute()

    resp = await _run(_query)
    result = dict(DEFAULT_SETTINGS)
    for row in resp.data:
        result[row["key"]] = row["value"]
    return result


async def update_settings(patch: dict) -> None:
    def _query():
        client = get_supabase()
        now = datetime.now(timezone.utc).isoformat()
        for key, value in patch.items():
            client.table("system_settings").upsert(
                {"key": key, "value": value, "updated_at": now}
            ).execute()

    await _run(_query)


async def count_active_cards() -> int:
    def _query():
        return (
            get_supabase()
            .table("trade_cards")
            .select("id", count="exact")
            .eq("status", "ACTIVE")
            .execute()
        )

    resp = await _run(_query)
    return resp.count or 0


async def get_active_card_symbols() -> set[str]:
    def _query():
        return get_supabase().table("trade_cards").select("symbol").eq("status", "ACTIVE").execute()

    resp = await _run(_query)
    return {row["symbol"] for row in resp.data}


async def insert_card(card: dict) -> dict:
    def _query():
        return get_supabase().table("trade_cards").insert(card).execute()

    resp = await _run(_query)
    return resp.data[0]


async def update_card(card_id: int, patch: dict) -> dict:
    def _query():
        return get_supabase().table("trade_cards").update(patch).eq("id", card_id).execute()

    resp = await _run(_query)
    return resp.data[0]


async def get_cards(status: str | None = None, limit: int = 20) -> list[dict]:
    def _query():
        query = get_supabase().table("trade_cards").select("*").order("created_at", desc=True).limit(limit)
        if status:
            query = query.eq("status", status)
        return query.execute()

    resp = await _run(_query)
    return resp.data


async def get_resolved_cards(limit: int = 1000) -> list[dict]:
    def _query():
        return (
            get_supabase()
            .table("trade_cards")
            .select("*")
            .neq("status", "ACTIVE")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

    resp = await _run(_query)
    return resp.data


async def get_card(card_id: int) -> dict | None:
    def _query():
        return get_supabase().table("trade_cards").select("*").eq("id", card_id).limit(1).execute()

    resp = await _run(_query)
    return resp.data[0] if resp.data else None


async def insert_scan_run(run: dict) -> dict:
    def _query():
        return get_supabase().table("scan_runs").insert(run).execute()

    resp = await _run(_query)
    return resp.data[0]


async def get_scan_runs(limit: int = 20) -> list[dict]:
    def _query():
        return (
            get_supabase()
            .table("scan_runs")
            .select("*")
            .order("ran_at", desc=True)
            .limit(limit)
            .execute()
        )

    resp = await _run(_query)
    return resp.data


async def insert_news_event(event: dict) -> dict | None:
    """symbol+external_id çakışırsa (dup) sessizce atlar."""

    def _query():
        return (
            get_supabase()
            .table("news_events")
            .upsert(event, on_conflict="symbol,external_id", ignore_duplicates=True)
            .execute()
        )

    resp = await _run(_query)
    return resp.data[0] if resp.data else None


async def update_news_event(event_id: int, patch: dict) -> dict:
    def _query():
        return get_supabase().table("news_events").update(patch).eq("id", event_id).execute()

    resp = await _run(_query)
    return resp.data[0]
