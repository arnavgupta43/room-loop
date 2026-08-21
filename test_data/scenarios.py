"""
Reusable test data - the brief's requested "test data that demonstrates the behavior most at
risk of being wrong" (spec.md §5), as importable constants/builder functions rather than values
buried inline in individual test files. Both tests/test_domain_*.py and tests/test_api_*.py
import from here rather than re-deriving these dates by hand.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from app.domain import ALLOWED_DURATIONS

# DST transition dates for 2026, deliberately non-aligned between the two offices - that
# mismatch is the whole reason a per-office, DST-proof recurrence rule matters (spec.md §3.7).
DENVER_DST_2026_SPRING_FORWARD = date(2026, 3, 8)  # clocks jump 2am -> 3am, MST -> MDT
DENVER_DST_2026_FALL_BACK = date(2026, 11, 1)  # clocks fall 2am -> 1am, MDT -> MST
BERLIN_DST_2026_SPRING_FORWARD = date(2026, 3, 29)  # clocks jump 2am -> 3am, CET -> CEST
BERLIN_DST_2026_FALL_BACK = date(2026, 10, 25)  # clocks fall 3am -> 2am, CEST -> CET

_DEFAULT_DURATION = timedelta(minutes=30)


def weekly_series_spanning(
    start_date: date, weeks: int, time_of_day: time, room_id: int, user: str
) -> dict:
    """A recurring-booking request spanning `weeks` weekly occurrences starting on `start_date`,
    for feeding into either domain.generate_weekly_instances or a POST /bookings/recurring call
    (format start/end/repeat_until with time_utils.format_naive_iso/isoformat for the latter)."""
    start = datetime.combine(start_date, time_of_day)
    return {
        "room_id": room_id,
        "start": start,
        "end": start + _DEFAULT_DURATION,
        "user": user,
        "repeat_until": start_date + timedelta(weeks=weeks - 1),
    }


def overlapping_pair() -> tuple[tuple[datetime, datetime], tuple[datetime, datetime]]:
    """Canonical (existing, new) time ranges that partially overlap - the smallest meaningful
    overlap plus some margin, used to keep conflict-boundary tests in sync across files."""
    base = datetime(2026, 7, 6, 9, 0, 0)
    existing = (base, base + timedelta(minutes=30))
    new = (base + timedelta(minutes=15), base + timedelta(minutes=45))
    return existing, new


def back_to_back_pair() -> tuple[tuple[datetime, datetime], tuple[datetime, datetime]]:
    """Canonical (existing, new) time ranges that touch at exactly one boundary - existing ends
    the instant new starts. Must NOT be treated as a conflict (strict overlap test, spec.md §3.5)."""
    base = datetime(2026, 7, 6, 9, 0, 0)
    existing = (base, base + timedelta(hours=1))
    new = (existing[1], existing[1] + timedelta(hours=1))
    return existing, new


def duration_boundary_cases() -> list[tuple[timedelta, bool]]:
    """(duration, expected_valid) pairs covering every allowed duration (spec.md §3.1) plus the
    just-under/just-over/in-between cases from spec.md §5.6."""
    cases = [(duration, True) for duration in sorted(ALLOWED_DURATIONS)]
    cases += [
        (timedelta(minutes=14, seconds=59), False),  # just under the floor
        (timedelta(hours=4, seconds=1), False),  # just over the ceiling
        (timedelta(minutes=20), False),  # in-between, not in the allowed set
        (timedelta(minutes=50), False),  # in-between, not in the allowed set
    ]
    return cases
