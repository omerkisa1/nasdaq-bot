from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)

HORIZON_MINUTES = {"30m": 30, "2h": 120}
HORIZON_TRADING_DAYS = {"1d": 1, "2d": 2, "3d": 3}


def now_et() -> datetime:
    return datetime.now(ET)


def is_trading_day(dt: datetime) -> bool:
    return dt.weekday() < 5


def is_market_open(dt: datetime | None = None) -> bool:
    dt = (dt or now_et()).astimezone(ET)
    if not is_trading_day(dt):
        return False
    return MARKET_OPEN <= dt.time() < MARKET_CLOSE


def minutes_to_close(dt: datetime | None = None) -> float:
    dt = (dt or now_et()).astimezone(ET)
    close = dt.replace(hour=MARKET_CLOSE.hour, minute=MARKET_CLOSE.minute, second=0, microsecond=0)
    return (close - dt).total_seconds() / 60


def next_trading_day(d: datetime) -> datetime:
    current = d
    while True:
        current = current + timedelta(days=1)
        if is_trading_day(current):
            return current


def can_open_horizon(horizon: str, dt: datetime | None = None) -> bool:
    """Piyasa kapanışına horizon süresinden az kaldıysa 30m/2h kart açılmaz."""
    dt = (dt or now_et()).astimezone(ET)
    if horizon in HORIZON_MINUTES:
        return minutes_to_close(dt) >= HORIZON_MINUTES[horizon]
    return True


def horizon_to_expires_at(horizon: str, created_at: datetime | None = None) -> datetime:
    created_at = (created_at or now_et()).astimezone(ET)

    if horizon in HORIZON_MINUTES:
        return created_at + timedelta(minutes=HORIZON_MINUTES[horizon])

    if horizon in HORIZON_TRADING_DAYS:
        expiry_day = created_at
        for _ in range(HORIZON_TRADING_DAYS[horizon]):
            expiry_day = next_trading_day(expiry_day)
        return expiry_day.replace(
            hour=MARKET_CLOSE.hour, minute=MARKET_CLOSE.minute, second=0, microsecond=0
        )

    raise ValueError(f"unknown horizon: {horizon}")
