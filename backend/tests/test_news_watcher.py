import pytest

from engine.news_watcher import (
    compute_price_change_pct,
    evaluate_reaction,
    get_watchlist_symbols,
    is_volume_accelerating,
)


def test_watchlist_combines_and_dedups_preserving_order():
    result = get_watchlist_symbols(["A", "B", "C"], {"B", "D"}, max_n=10)
    assert result[:3] == ["A", "B", "C"]
    assert "D" in result


def test_watchlist_respects_max_n():
    result = get_watchlist_symbols(["A", "B", "C", "D"], set(), max_n=2)
    assert result == ["A", "B"]


def test_price_change_pct_positive():
    assert compute_price_change_pct(4.0, 4.4) == pytest.approx(10.0)


def test_price_change_pct_zero_baseline():
    assert compute_price_change_pct(0, 5.0) == 0.0


def test_volume_accelerating_true_when_deltas_increase():
    # deltas: 100,100,100,500,600  -> second half avg >> first half avg
    samples = [1000, 1100, 1200, 1300, 1800, 2400]
    assert is_volume_accelerating(samples) is True


def test_volume_accelerating_false_when_flat():
    samples = [1000, 1100, 1200, 1300, 1400, 1500]
    assert is_volume_accelerating(samples) is False


def test_volume_accelerating_false_with_too_few_samples():
    assert is_volume_accelerating([1000, 1100]) is False


def test_evaluate_reaction_requires_both_conditions():
    assert evaluate_reaction(3.0, True, min_pct=2.0) is True
    assert evaluate_reaction(1.0, True, min_pct=2.0) is False
    assert evaluate_reaction(3.0, False, min_pct=2.0) is False
