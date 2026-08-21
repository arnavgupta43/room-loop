"""
Unit tests for domain.validate_duration - spec.md SS3.1, risk item SS5.6.
"""

from datetime import datetime, timedelta

import pytest

from app.domain import InvalidDuration, InvalidTimeRange, validate_duration

BASE = datetime(2026, 7, 6, 9, 0, 0)

ALLOWED = [
    timedelta(minutes=15),
    timedelta(minutes=30),
    timedelta(minutes=45),
    timedelta(hours=1),
    timedelta(hours=1, minutes=30),
    timedelta(hours=2),
    timedelta(hours=2, minutes=30),
    timedelta(hours=3),
    timedelta(hours=3, minutes=30),
    timedelta(hours=4),
]


@pytest.mark.parametrize("duration", ALLOWED)
def test_each_allowed_duration_accepted(duration):
    validate_duration(BASE, BASE + duration)


def test_just_under_floor_rejected():
    with pytest.raises(InvalidDuration):
        validate_duration(BASE, BASE + timedelta(minutes=14, seconds=59))


def test_just_over_ceiling_rejected():
    with pytest.raises(InvalidDuration):
        validate_duration(BASE, BASE + timedelta(hours=4, seconds=1))


@pytest.mark.parametrize("duration", [timedelta(minutes=20), timedelta(minutes=50)])
def test_in_between_value_rejected(duration):
    with pytest.raises(InvalidDuration):
        validate_duration(BASE, BASE + duration)


def test_end_equal_to_start_rejected_as_invalid_time_range():
    with pytest.raises(InvalidTimeRange):
        validate_duration(BASE, BASE)


def test_end_before_start_rejected_as_invalid_time_range():
    with pytest.raises(InvalidTimeRange):
        validate_duration(BASE, BASE - timedelta(minutes=5))


def test_odd_start_time_with_valid_duration_accepted():
    odd_start = BASE.replace(minute=7)
    validate_duration(odd_start, odd_start + timedelta(minutes=30))
