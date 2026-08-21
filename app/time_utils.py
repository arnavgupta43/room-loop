"""
Naive-local timestamp handling.

Implemented so far: parse_naive_iso / format_naive_iso, used at the schemas.py boundary to
enforce that every timestamp in this codebase is naive (G1).

Not yet implemented: now_in_office(office) - the per-office "now" helper needed by series
cancellation's future/past cutoff (SS3.4/SS3.7/G6). It is the only place zoneinfo is meant to be
used, and stays out of this module until series cancellation is built.
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
