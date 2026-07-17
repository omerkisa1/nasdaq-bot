from datetime import datetime, timezone

_state = {"last_scan_at": None, "scan_in_progress": False, "top_symbols": []}


def set_scan_in_progress(value: bool) -> None:
    _state["scan_in_progress"] = value


def set_last_scan_now() -> None:
    _state["last_scan_at"] = datetime.now(timezone.utc).isoformat()


def set_top_symbols(symbols: list[str]) -> None:
    _state["top_symbols"] = symbols


def get_top_symbols() -> list[str]:
    return list(_state["top_symbols"])


def get_state() -> dict:
    return dict(_state)
