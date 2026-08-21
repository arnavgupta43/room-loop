"""
Reusable test data (spec.md §5's "behavior most at risk of being wrong"), shared by
tests/test_domain_*.py and tests/test_api_*.py so boundary values aren't redefined per file.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from app.domain import ALLOWED_DURATIONS

# Deliberately non-aligned between offices - that mismatch is why per-office recurrence matters.
DENVER_DST_2026_SPRING_FORWARD = date(2026, 3, 8)  # 2am -> 3am, MST -> MDT
DENVER_DST_2026_FALL_BACK = date(2026, 11, 1)  # 2am -> 1am, MDT -> MST
BERLIN_DST_2026_SPRING_FORWARD = date(2026, 3, 29)  # 2am -> 3am, CET -> CEST
BERLIN_DST_2026_FALL_BACK = date(2026, 10, 25)  # 3am -> 2am, CEST -> CET

_DEFAULT_DURATION = timedelta(minutes=30)


def weekly_series_spanning(
    start_date: date, weeks: int, time_of_day: time, room_id: int, user: str
) -> dict:
    """A recurring-booking request spanning `weeks` occurrences from `start_date`."""
    start = datetime.combine(start_date, time_of_day)
    return {
        "room_id": room_id,
        "start": start,
        "end": start + _DEFAULT_DURATION,
        "user": user,
        "repeat_until": start_date + timedelta(weeks=weeks - 1),
    }


def overlapping_pair() -> tuple[tuple[datetime, datetime], tuple[datetime, datetime]]:
    """Canonical (existing, new) time ranges that partially overlap."""
    base = datetime(2026, 7, 6, 9, 0, 0)
    existing = (base, base + timedelta(minutes=30))
    new = (base + timedelta(minutes=15), base + timedelta(minutes=45))
    return existing, new


def back_to_back_pair() -> tuple[tuple[datetime, datetime], tuple[datetime, datetime]]:
    """Canonical (existing, new) time ranges that touch at one boundary - not a conflict (§3.5)."""
    base = datetime(2026, 7, 6, 9, 0, 0)
    existing = (base, base + timedelta(hours=1))
    new = (existing[1], existing[1] + timedelta(hours=1))
    return existing, new


def duration_boundary_cases() -> list[tuple[timedelta, bool]]:
    """(duration, expected_valid) pairs covering every allowed duration plus the §5.6 edge cases."""
    cases = [(duration, True) for duration in sorted(ALLOWED_DURATIONS)]
    cases += [
        (timedelta(minutes=14, seconds=59), False),  # just under the floor
        (timedelta(hours=4, seconds=1), False),  # just over the ceiling
        (timedelta(minutes=20), False),  # in-between, not in the allowed set
        (timedelta(minutes=50), False),  # in-between, not in the allowed set
    ]
    return cases
