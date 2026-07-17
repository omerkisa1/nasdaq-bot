from engine.validator import validate_card


def make_card(**overrides):
    base = {
        "entry_zone_low": 4.40,
        "entry_zone_high": 4.55,
        "stop": 4.18,
        "target_1": 4.90,
        "target_2": 5.30,
    }
    base.update(overrides)
    return base


def test_valid_card_passes():
    result = validate_card(
        make_card(),
        current_price=4.50,
        avg_daily_volume=1_000_000,
        account_size=1000,
        risk_percent=1.0,
        liquidity_cap_pct=2.0,
    )
    assert result.valid is True
    assert result.risk_amount == 10.0
    assert result.position_size >= 1


def test_bad_level_ordering_rejected():
    card = make_card(target_1=4.30)  # target_1 below entry_high
    result = validate_card(card, 4.50, 1_000_000, 1000, 1.0, 2.0)
    assert result.valid is False
    assert "sıralaması" in result.reason


def test_stop_too_far_rejected():
    card = make_card(stop=3.50)  # >15% away from entry_low 4.40
    result = validate_card(card, 4.50, 1_000_000, 1000, 1.0, 2.0)
    assert result.valid is False
    assert "stop mesafesi" in result.reason


def test_stop_too_close_rejected():
    card = make_card(stop=4.35)  # <2% away from entry_low 4.40
    result = validate_card(card, 4.50, 1_000_000, 1000, 1.0, 2.0)
    assert result.valid is False
    assert "stop mesafesi" in result.reason


def test_poor_rr_rejected():
    card = make_card(stop=4.00, target_1=4.60)  # risk 0.40, reward 0.20
    result = validate_card(card, 4.50, 1_000_000, 1000, 1.0, 2.0)
    assert result.valid is False
    assert "R/R" in result.reason


def test_stale_entry_zone_rejected():
    result = validate_card(make_card(), current_price=5.50, avg_daily_volume=1_000_000,
                            account_size=1000, risk_percent=1.0, liquidity_cap_pct=2.0)
    assert result.valid is False
    assert "bayat kart" in result.reason


def test_liquidity_cap_limits_position_size():
    result = validate_card(
        make_card(),
        current_price=4.50,
        avg_daily_volume=40,  # tiny volume -> liquidity cap binds
        account_size=1000,
        risk_percent=1.0,
        liquidity_cap_pct=2.0,
    )
    assert result.valid is False
    assert "pozisyon boyutu" in result.reason


def test_position_size_uses_min_of_risk_and_liquidity():
    result = validate_card(
        make_card(),
        current_price=4.50,
        avg_daily_volume=1_000_000,
        account_size=1_000_000,  # large account -> risk-based size huge
        risk_percent=1.0,
        liquidity_cap_pct=2.0,
    )
    assert result.valid is True
    # liquidity cap = 1_000_000 * 0.02 = 20_000, should bind vs risk-based size
    assert result.position_size == 20_000
