"""
Unit tests for domain.conflicts - spec.md SS3.5/R4, risk item SS5.2.

domain.conflicts is a pure time-range overlap test; it has no notion of room or status
(same-room and active-only filtering happens in the caller, G5). Those two cases are covered
at the API level instead, in test_api_bookings.py.
"""

from datetime import datetime, timedelta

from app.domain import conflicts

BASE = datetime(2026, 7, 6, 9, 0, 0)


def test_identical_ranges_conflict():
    start, end = BASE, BASE + timedelta(minutes=30)
    assert conflicts(start, end, start, end)


def test_partial_overlap_conflicts_both_directions():
    a_start, a_end = BASE, BASE + timedelta(minutes=30)
    b_start, b_end = BASE + timedelta(minutes=15), BASE + timedelta(minutes=45)
    assert conflicts(a_start, a_end, b_start, b_end)
    assert conflicts(b_start, b_end, a_start, a_end)


def test_one_range_fully_contains_the_other_conflicts():
    outer_start, outer_end = BASE, BASE + timedelta(hours=2)
    inner_start, inner_end = BASE + timedelta(minutes=30), BASE + timedelta(minutes=45)
    assert conflicts(outer_start, outer_end, inner_start, inner_end)


def test_back_to_back_existing_ends_when_new_starts_is_not_a_conflict():
    existing_start, existing_end = BASE, BASE + timedelta(hours=1)
    new_start, new_end = existing_end, existing_end + timedelta(hours=1)
    assert not conflicts(existing_start, existing_end, new_start, new_end)


def test_back_to_back_new_ends_when_existing_starts_is_not_a_conflict():
    new_start, new_end = BASE, BASE + timedelta(hours=1)
    existing_start, existing_end = new_end, new_end + timedelta(hours=1)
    assert not conflicts(new_start, new_end, existing_start, existing_end)


def test_smallest_possible_overlap_conflicts():
    existing_start, existing_end = BASE, BASE + timedelta(hours=1)
    new_start, new_end = existing_end - timedelta(minutes=1), existing_end + timedelta(minutes=30)
    assert conflicts(existing_start, existing_end, new_start, new_end)
