from fastapi import APIRouter

from core import state
from db import repo
from engine.scanner import run_scan

router = APIRouter(prefix="/api/scan", tags=["scan"])


@router.post("/trigger")
async def trigger_scan():
    state.set_scan_in_progress(True)
    try:
        result = await run_scan(force=True)
    finally:
        state.set_scan_in_progress(False)
        state.set_last_scan_now()
    return result


@router.get("/runs")
async def scan_runs(limit: int = 20):
    return await repo.get_scan_runs(limit=limit)
