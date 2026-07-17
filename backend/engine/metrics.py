import numpy as np


def ema(values: list[float], period: int) -> float:
    arr = np.asarray(values, dtype=float)
    if len(arr) < period:
        raise ValueError("not enough values for ema period")
    alpha = 2 / (period + 1)
    result = arr[:period].mean()
    for value in arr[period:]:
        result = value * alpha + result * (1 - alpha)
    return float(result)


def rsi(closes: list[float], period: int = 14) -> float:
    arr = np.asarray(closes, dtype=float)
    if len(arr) < period + 1:
        raise ValueError("not enough values for rsi period")
    changes = np.diff(arr)
    gains = np.where(changes > 0, changes, 0.0)
    losses = np.where(changes < 0, -changes, 0.0)

    avg_gain = gains[:period].mean()
    avg_loss = losses[:period].mean()
    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return float(100 - 100 / (1 + rs))


def atr(candles: list[dict], period: int = 14) -> float:
    if len(candles) < period + 1:
        raise ValueError("not enough candles for atr period")

    true_ranges = [candles[0]["high"] - candles[0]["low"]]
    for prev, cur in zip(candles, candles[1:]):
        tr = max(
            cur["high"] - cur["low"],
            abs(cur["high"] - prev["close"]),
            abs(cur["low"] - prev["close"]),
        )
        true_ranges.append(tr)

    tr_arr = np.asarray(true_ranges, dtype=float)
    result = tr_arr[:period].mean()
    for tr in tr_arr[period:]:
        result = (result * (period - 1) + tr) / period
    return float(result)


def vwap(ticks: list[dict]) -> float:
    """ticks: [{"price": float, "volume": float}, ...]"""
    total_volume = sum(t["volume"] for t in ticks)
    if total_volume == 0:
        return 0.0
    total_value = sum(t["price"] * t["volume"] for t in ticks)
    return total_value / total_volume


def find_swing_lows(lows: list[float], window: int = 3) -> list[float]:
    points = []
    for i in range(window, len(lows) - window):
        segment = lows[i - window : i + window + 1]
        if lows[i] == min(segment):
            points.append(lows[i])
    return points


def find_swing_highs(highs: list[float], window: int = 3) -> list[float]:
    points = []
    for i in range(window, len(highs) - window):
        segment = highs[i - window : i + window + 1]
        if highs[i] == max(segment):
            points.append(highs[i])
    return points


def cluster_levels(levels: list[float], tolerance_pct: float = 1.0) -> list[float]:
    if not levels:
        return []
    ordered = sorted(levels)
    clusters: list[list[float]] = [[ordered[0]]]
    for level in ordered[1:]:
        cluster_avg = sum(clusters[-1]) / len(clusters[-1])
        if abs(level - cluster_avg) / cluster_avg * 100 <= tolerance_pct:
            clusters[-1].append(level)
        else:
            clusters.append([level])
    return [sum(c) / len(c) for c in clusters]


def support_resistance(candles: list[dict], window: int = 3, tolerance_pct: float = 1.0) -> dict:
    lows = [c["low"] for c in candles]
    highs = [c["high"] for c in candles]
    support = cluster_levels(find_swing_lows(lows, window), tolerance_pct)
    resistance = cluster_levels(find_swing_highs(highs, window), tolerance_pct)
    return {"support": support, "resistance": resistance}
