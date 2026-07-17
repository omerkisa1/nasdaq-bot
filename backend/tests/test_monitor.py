from datetime import datetime, timedelta, timezone

from engine.monitor import evaluate_card


def make_card(**overrides):
    base = {
        "id": 1,
        "symbol": "ABCD",
        "entry_zone_low": 4.40,
        "entry_zone_high": 4.55,
        "stop": 4.18,
        "target_1": 4.90,
        "target_2": 5.30,
        "t1_hit": False,
        "snapshot": {},
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    }
    base.update(overrides)
    return base


def test_price_outside_zone_stays_active_not_entered():
    result = evaluate_card(make_card(), price=4.60)
    assert result["status"] == "ACTIVE"
    assert result["patch"] == {}


def test_price_enters_zone_marks_entered():
    result = evaluate_card(make_card(), price=4.45)
    assert result["status"] == "ACTIVE"
    assert result["patch"]["snapshot"]["entered"] is True


def test_stop_hit_only_after_entered():
    card = make_card(snapshot={"entered": True})
    result = evaluate_card(card, price=4.10)
    assert result["status"] == "STOP_HIT"
    assert result["patch"]["realized_r"] == -1.0


def test_stop_touch_without_entry_ignored():
    card = make_card()  # never entered
    result = evaluate_card(card, price=4.10)
    assert result["status"] == "ACTIVE"
    assert result["patch"] == {}


def test_target_1_hit_stays_active_marks_flag():
    card = make_card(snapshot={"entered": True})
    result = evaluate_card(card, price=4.95)
    assert result["status"] == "ACTIVE"
    assert result["patch"]["t1_hit"] is True


def test_target_2_hit_closes_win():
    card = make_card(snapshot={"entered": True})
    result = evaluate_card(card, price=5.40)
    assert result["status"] == "TARGET_HIT"
    assert result["patch"]["t1_hit"] is True
    assert result["patch"]["realized_r"] > 0


def test_expired_after_entry_computes_r():
    expired_card = make_card(
        snapshot={"entered": True},
        expires_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
    )
    result = evaluate_card(expired_card, price=4.60)
    assert result["status"] == "EXPIRED"
    assert result["patch"]["realized_r"] == pytest_approx(0.91)


def test_expired_without_entry_is_no_fill():
    expired_card = make_card(
        expires_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
    )
    result = evaluate_card(expired_card, price=4.20)
    assert result["status"] == "NO_FILL"
    assert "realized_r" not in result["patch"]


def pytest_approx(value):
    import pytest

    return pytest.approx(value, abs=1e-2)
