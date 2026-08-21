"""
Naive-local timestamp handling - enforces that every timestamp in this codebase is naive (G1).
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

_OFFICE_ZONES = {
    "Berlin": ZoneInfo("Europe/Berlin"),
    "Denver": ZoneInfo("America/Denver"),
}


def parse_naive_iso(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid ISO datetime: {value!r}") from exc
    if dt.tzinfo is not None:
        raise ValueError(f"datetime must be naive, no timezone/offset allowed: {value!r}")
    if dt.microsecond != 0:
        raise ValueError(f"datetime must have second precision, no fractional seconds: {value!r}")
    return dt


def format_naive_iso(dt: datetime) -> str:
    assert dt.tzinfo is None, "cannot format a timezone-aware datetime"
    return dt.isoformat()


def now_in_office(office: str) -> datetime:
    """The only place allowed to touch zoneinfo (G1, G6) - strips tzinfo before returning."""
    aware_now = datetime.now(_OFFICE_ZONES[office])
    return aware_now.replace(tzinfo=None)
