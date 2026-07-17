import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from config import settings
from core import state
from core.http import close_client
from core.market_hours import is_market_open
from core.redis_client import close_redis
from core.ws_manager import ws_manager
from db import repo
from engine.monitor import run_monitor_cycle
from engine.scanner import run_scan
from routers import cards, quote, scan, settings as settings_router, stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _scheduled_scan() -> None:
    state.set_scan_in_progress(True)
    try:
        await run_scan()
    except Exception:
        logger.exception("Tarama döngüsü hata verdi")
    finally:
        state.set_scan_in_progress(False)
        state.set_last_scan_now()


async def _scheduled_monitor() -> None:
    try:
        await run_monitor_cycle()
    except Exception:
        logger.exception("İzleme döngüsü hata verdi")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(_scheduled_scan, "interval", seconds=settings.scan_interval_sec, id="scan")
    scheduler.add_job(_scheduled_monitor, "interval", seconds=settings.monitor_interval_sec, id="monitor")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)
    await close_client()
    await close_redis()


app = FastAPI(title="Otonom Trade Kartı Sistemi", lifespan=lifespan)

app.include_router(cards.router)
app.include_router(stats.router)
app.include_router(settings_router.router)
app.include_router(scan.router)
app.include_router(quote.router)


@app.get("/api/health")
async def health():
    current_state = state.get_state()
    active_cards = await repo.count_active_cards()
    return {
        "status": "ok",
        "market_open": is_market_open(),
        "scanner_running": current_state["scan_in_progress"],
        "last_scan": current_state["last_scan_at"],
        "active_cards": active_cards,
    }


@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
