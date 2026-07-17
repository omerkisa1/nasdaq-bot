import pytest

from engine.metrics import atr, cluster_levels, ema, rsi, support_resistance, vwap


def test_ema_known_values():
    assert ema([1, 2, 3, 4, 5], period=3) == pytest.approx(4.0)


def test_rsi_known_values():
    prices = [10, 12, 11, 13, 15]
    assert rsi(prices, period=3) == pytest.approx(87.5, abs=1e-4)


def test_rsi_all_gains_is_100():
    prices = [10, 11, 12, 13, 14]
    assert rsi(prices, period=3) == pytest.approx(100.0)


def test_atr_known_values():
    candles = [
        {"high": 10, "low": 8, "close": 9},
        {"high": 13, "low": 9, "close": 12},
        {"high": 13, "low": 11, "close": 12},
        {"high": 18, "low": 12, "close": 17},
    ]
    assert atr(candles, period=3) == pytest.approx(3.7778, abs=1e-3)


def test_vwap_known_values():
    ticks = [
        {"price": 10, "volume": 100},
        {"price": 11, "volume": 200},
        {"price": 12, "volume": 100},
    ]
    assert vwap(ticks) == pytest.approx(11.0)


def test_cluster_levels_groups_close_values():
    levels = [10.0, 10.05, 15.0, 15.1, 20.0]
    clustered = cluster_levels(levels, tolerance_pct=1.0)
    assert len(clustered) == 3


def test_support_resistance_finds_swing_points():
    candles = [
        {"high": 10, "low": 5},
        {"high": 11, "low": 4},
        {"high": 12, "low": 3},
        {"high": 11, "low": 4},
        {"high": 10, "low": 5},
    ]
    result = support_resistance(candles, window=2, tolerance_pct=1.0)
    assert result["support"] == pytest.approx([3.0])
    assert result["resistance"] == pytest.approx([12.0])
