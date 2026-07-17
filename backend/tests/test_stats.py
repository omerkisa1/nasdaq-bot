from engine.stats import compute_stats


def make_card(status, horizon="1d", realized_r=None):
    return {"status": status, "horizon": horizon, "realized_r": realized_r}


def test_empty_cards():
    result = compute_stats([])
    assert result["total"] == 0
    assert result["win_rate"] == 0.0
    assert result["avg_r"] == 0.0


def test_win_rate_excludes_expired_and_no_fill():
    cards = [
        make_card("TARGET_HIT", realized_r=2.0),
        make_card("TARGET_HIT", realized_r=1.5),
        make_card("STOP_HIT", realized_r=-1.0),
        make_card("EXPIRED", realized_r=0.3),
        make_card("NO_FILL"),
    ]
    result = compute_stats(cards)
    assert result["total"] == 5
    assert result["wins"] == 2
    assert result["losses"] == 1
    assert result["expired"] == 1
    assert result["no_fill"] == 1
    assert result["win_rate"] == round(2 / 3, 4)
    assert result["total_r"] == 2.8
    assert result["avg_r"] == 0.7


def test_by_horizon_breakdown():
    cards = [
        make_card("TARGET_HIT", horizon="30m", realized_r=2.0),
        make_card("STOP_HIT", horizon="1d", realized_r=-1.0),
    ]
    result = compute_stats(cards)
    assert result["by_horizon"]["30m"] == {"count": 1, "wins": 1, "total_r": 2.0}
    assert result["by_horizon"]["1d"] == {"count": 1, "wins": 0, "total_r": -1.0}
