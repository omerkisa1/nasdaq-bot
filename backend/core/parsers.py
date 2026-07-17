from datetime import datetime


def parse_price(s: str | float | int) -> float:
    """"$4.24" / "+11.29%" / "+0.43" / "-1.20" -> float"""
    if isinstance(s, (int, float)):
        return float(s)
    cleaned = s.strip().replace("$", "").replace("%", "").replace(",", "")
    if cleaned in ("", "N/A", "NA", "--"):
        return 0.0
    return float(cleaned)


def parse_volume(s: str | int) -> int:
    """"107,909,204" -> int"""
    if isinstance(s, int):
        return s
    cleaned = s.strip().replace(",", "")
    if cleaned in ("", "N/A", "NA", "--"):
        return 0
    return int(float(cleaned))


def parse_date(s: str) -> str:
    """"06/18/2026" -> "2026-06-18" """
    return datetime.strptime(s.strip(), "%m/%d/%Y").strftime("%Y-%m-%d")


def parse_range(s: str) -> tuple[float, float] | None:
    """"$4.10-$4.60" / "4.10 - 4.60" -> (4.10, 4.60)"""
    if not s:
        return None
    parts = s.replace("$", "").replace(",", "").split("-")
    if len(parts) != 2:
        return None
    try:
        return float(parts[0].strip()), float(parts[1].strip())
    except ValueError:
        return None
