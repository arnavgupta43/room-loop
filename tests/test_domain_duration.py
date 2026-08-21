"""
Unit tests for domain.validate_duration - spec.md SS3.1, risk item SS5.6.
"""

from datetime import datetime, timedelta

import pytest

from app.domain import InvalidDuration, InvalidTimeRange, validate_duration
from test_data.scenarios import duration_boundary_cases

BASE = datetime(2026, 7, 6, 9, 0, 0)


@pytest.mark.parametrize("duration, expected_valid", duration_boundary_cases())
def test_duration_boundary_cases(duration, expected_valid):
    if expected_valid:
        validate_duration(BASE, BASE + duration)
    else:
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
