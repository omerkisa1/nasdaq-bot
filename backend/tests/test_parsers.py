import pytest

from core.parsers import parse_date, parse_price, parse_range, parse_volume


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("$4.24", 4.24),
        ("+11.29%", 11.29),
        ("+0.43", 0.43),
        ("-1.20", -1.20),
        ("$1,234.56", 1234.56),
        ("--", 0.0),
        (4.24, 4.24),
    ],
)
def test_parse_price(raw, expected):
    assert parse_price(raw) == pytest.approx(expected)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("107,909,204", 107_909_204),
        ("0", 0),
        ("1,000", 1000),
        ("--", 0),
        (500, 500),
    ],
)
def test_parse_volume(raw, expected):
    assert parse_volume(raw) == expected


def test_parse_date():
    assert parse_date("06/18/2026") == "2026-06-18"
    assert parse_date("01/01/2025") == "2025-01-01"


def test_parse_range_with_dollar_signs():
    assert parse_range("$4.10-$4.60") == pytest.approx((4.10, 4.60))


def test_parse_range_with_spaces():
    assert parse_range("4.10 - 4.60") == pytest.approx((4.10, 4.60))


def test_parse_range_invalid_returns_none():
    assert parse_range("N/A") is None
    assert parse_range("") is None
