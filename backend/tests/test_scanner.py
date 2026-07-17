from engine.scanner import filter_candidates_for_processing


def make_candidates(symbols):
    return [{"symbol": s} for s in symbols]


def test_skips_active_symbols():
    result = filter_candidates_for_processing(
        make_candidates(["A", "B", "C"]), active_symbols={"B"}, cooldown_symbols=set(), max_count=10
    )
    assert [c["symbol"] for c in result] == ["A", "C"]


def test_skips_cooldown_symbols():
    result = filter_candidates_for_processing(
        make_candidates(["A", "B", "C"]), active_symbols=set(), cooldown_symbols={"A", "C"}, max_count=10
    )
    assert [c["symbol"] for c in result] == ["B"]


def test_respects_max_count_budget():
    result = filter_candidates_for_processing(
        make_candidates(["A", "B", "C", "D"]), active_symbols=set(), cooldown_symbols=set(), max_count=2
    )
    assert [c["symbol"] for c in result] == ["A", "B"]


def test_zero_budget_returns_empty():
    result = filter_candidates_for_processing(
        make_candidates(["A", "B"]), active_symbols=set(), cooldown_symbols=set(), max_count=0
    )
    assert result == []
