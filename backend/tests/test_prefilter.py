from engine.prefilter import has_recent_trade, passes_mechanical_filter, prefilter_universe


def make_candidate(**overrides):
    base = {"symbol": "ABCD", "close": 5.0, "volume": 200_000, "change_pct": 5.0, "rvol": 3.0}
    base.update(overrides)
    return base


def test_passes_with_strong_gain_and_rvol():
    assert passes_mechanical_filter(make_candidate()) is True


def test_passes_with_strong_drop():
    assert passes_mechanical_filter(make_candidate(change_pct=-6.0)) is True


def test_fails_low_rvol():
    assert passes_mechanical_filter(make_candidate(rvol=1.5)) is False


def test_fails_flat_change():
    assert passes_mechanical_filter(make_candidate(change_pct=1.0)) is False


def test_fails_price_out_of_range():
    assert passes_mechanical_filter(make_candidate(close=25.0)) is False
    assert passes_mechanical_filter(make_candidate(close=0.1)) is False


def test_prefilter_universe_filters_list():
    candidates = [make_candidate(symbol="A"), make_candidate(symbol="B", rvol=1.0)]
    result = prefilter_universe(candidates)
    assert [c["symbol"] for c in result] == ["A"]


def test_has_recent_trade_true_within_window():
    now_ms = 1_000_000_000
    chart = [{"ts_ms": now_ms - 10 * 60_000, "price": 5.0}]
    assert has_recent_trade(chart, within_minutes=30, now_ms=now_ms) is True


def test_has_recent_trade_false_stale():
    now_ms = 1_000_000_000
    chart = [{"ts_ms": now_ms - 60 * 60_000, "price": 5.0}]
    assert has_recent_trade(chart, within_minutes=30, now_ms=now_ms) is False


def test_has_recent_trade_empty_chart():
    assert has_recent_trade([], within_minutes=30) is False
