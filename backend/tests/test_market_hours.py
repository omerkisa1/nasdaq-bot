from datetime import datetime

from core.market_hours import (
    ET,
    can_open_horizon,
    horizon_to_expires_at,
    is_market_open,
    minutes_to_close,
)


def test_is_market_open_during_session():
    dt = datetime(2026, 6, 17, 10, 0, tzinfo=ET)  # Wednesday
    assert is_market_open(dt) is True


def test_is_market_open_before_open():
    dt = datetime(2026, 6, 17, 9, 0, tzinfo=ET)
    assert is_market_open(dt) is False


def test_is_market_open_weekend():
    dt = datetime(2026, 6, 20, 10, 0, tzinfo=ET)  # Saturday
    assert is_market_open(dt) is False


def test_minutes_to_close():
    dt = datetime(2026, 6, 17, 15, 45, tzinfo=ET)
    assert minutes_to_close(dt) == 15


def test_can_open_horizon_blocks_near_close():
    dt = datetime(2026, 6, 17, 15, 45, tzinfo=ET)
    assert can_open_horizon("2h", dt) is False
    assert can_open_horizon("30m", dt) is False
    assert can_open_horizon("1d", dt) is True


def test_can_open_horizon_allows_midday():
    dt = datetime(2026, 6, 17, 11, 0, tzinfo=ET)
    assert can_open_horizon("2h", dt) is True
    assert can_open_horizon("30m", dt) is True


def test_horizon_to_expires_at_intraday():
    created = datetime(2026, 6, 17, 11, 0, tzinfo=ET)
    expires = horizon_to_expires_at("30m", created)
    assert expires == datetime(2026, 6, 17, 11, 30, tzinfo=ET)


def test_horizon_to_expires_at_1d_skips_weekend():
    created = datetime(2026, 6, 19, 11, 0, tzinfo=ET)  # Friday
    expires = horizon_to_expires_at("1d", created)
    assert expires.date() == datetime(2026, 6, 22).date()  # Monday
    assert expires.time().hour == 16


def test_horizon_to_expires_at_3d():
    created = datetime(2026, 6, 17, 11, 0, tzinfo=ET)  # Wednesday
    expires = horizon_to_expires_at("3d", created)
    assert expires.date() == datetime(2026, 6, 22).date()  # Monday (Thu, Fri, Mon)
