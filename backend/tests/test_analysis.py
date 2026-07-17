from engine.analysis import build_context_summary, classify_headline


def test_classify_headline_negative():
    assert classify_headline("CEO Insider Sale Reported This Week") == "negatif"


def test_classify_headline_positive():
    assert classify_headline("Company Announces FDA Approval for Drug") == "pozitif"


def test_classify_headline_neutral():
    assert classify_headline("Analyst Comments on Sector Outlook") == "nötr"


def make_snapshot(**overrides):
    base = {
        "quote": {"last_sale_price": 4.24, "volume": 5_000_000, "day_range": "$4.10-$5.00"},
        "avg_daily_volume": 1_000_000,
        "atr_14": 0.31,
        "levels": {"support": [3.85, 4.00], "resistance": [4.65, 5.20]},
        "news": [{"headline": "Insider Sale Reported", "source": "Nasdaq"}],
    }
    base.update(overrides)
    return base


def test_context_summary_computes_rvol_and_levels():
    summary = build_context_summary(make_snapshot(), min_rvol=2.0)
    assert summary["rvol"] == 5.0
    assert summary["key_levels"]["support"] == 4.00
    assert summary["key_levels"]["resistance"] == 4.65
    assert summary["news"][0]["classification"] == "negatif"


def test_context_summary_warns_when_far_from_day_high():
    summary = build_context_summary(make_snapshot(), min_rvol=2.0)
    assert any("zirveden" in w for w in summary["warnings"])


def test_context_summary_warns_low_rvol():
    snapshot = make_snapshot(quote={"last_sale_price": 4.24, "volume": 500_000, "day_range": "$4.10-$4.30"})
    summary = build_context_summary(snapshot, min_rvol=2.0)
    assert any("RVOL" in w for w in summary["warnings"])
