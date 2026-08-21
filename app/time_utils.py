"""
Naive-local timestamp handling - enforces that every timestamp in this codebase is naive (G1).
"""

from __future__ import annotations

from datetime import datetime


def parse_naive_iso(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid ISO datetime: {value!r}") from exc
    if dt.tzinfo is not None:
        raise ValueError(f"datetime must be naive, no timezone/offset allowed: {value!r}")
    return dt


def format_naive_iso(dt: datetime) -> str:
    assert dt.tzinfo is None, "cannot format a timezone-aware datetime"
    return dt.isoformat()
