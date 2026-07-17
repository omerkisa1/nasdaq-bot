import pytest

from core.parsers import parse_date, parse_price, parse_volume


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
