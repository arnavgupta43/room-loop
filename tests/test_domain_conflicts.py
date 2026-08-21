"""
Unit tests for domain.conflicts - spec.md SS3.5/R4, risk item SS5.2.

domain.conflicts is a pure time-range overlap test; it has no notion of room or status
(same-room and active-only filtering happens in the caller, G5). Those two cases are covered
at the API level instead, in test_api_bookings.py.
"""

from datetime import datetime, timedelta

from app.domain import conflicts
from test_data.scenarios import back_to_back_pair, overlapping_pair

BASE = datetime(2026, 7, 6, 9, 0, 0)


def test_identical_ranges_conflict():
    start, end = BASE, BASE + timedelta(minutes=30)
    assert conflicts(start, end, start, end)


def test_overlapping_pair_conflicts_both_directions():
    existing, new = overlapping_pair()
    assert conflicts(*existing, *new)
    assert conflicts(*new, *existing)


def test_one_range_fully_contains_the_other_conflicts():
    outer_start, outer_end = BASE, BASE + timedelta(hours=2)
    inner_start, inner_end = BASE + timedelta(minutes=30), BASE + timedelta(minutes=45)
    assert conflicts(outer_start, outer_end, inner_start, inner_end)


def test_back_to_back_pair_is_not_a_conflict_either_direction():
    existing, new = back_to_back_pair()
    assert not conflicts(*existing, *new)
    assert not conflicts(*new, *existing)


def test_smallest_possible_overlap_conflicts():
    existing_start, existing_end = BASE, BASE + timedelta(hours=1)
    new_start, new_end = existing_end - timedelta(minutes=1), existing_end + timedelta(minutes=30)
    assert conflicts(existing_start, existing_end, new_start, new_end)
