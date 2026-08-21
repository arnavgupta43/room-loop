"""
Unit tests for domain.generate_weekly_instances - spec.md SS3.3/SS3.7, risk item SS5.1.
This is the single highest-priority test file in the project: it directly targets the Denver
DST bug described by the Office Manager.
"""

from datetime import date, datetime, time, timedelta

import pytest

from app.domain import (
    MAX_RECURRING_INSTANCES,
    InvalidTimeRange,
    RangeTooLarge,
    generate_weekly_instances,
)
from test_data.scenarios import (
    BERLIN_DST_2026_FALL_BACK,
    BERLIN_DST_2026_SPRING_FORWARD,
    DENVER_DST_2026_FALL_BACK,
    DENVER_DST_2026_SPRING_FORWARD,
    weekly_series_spanning,
)


def _series_spanning(transition_date, weeks_before=2, weeks_after=2):
    """A weekly series starting `weeks_before` the given date and running `weeks_after` past it,
    so the generated instances straddle the transition instead of merely approaching it."""
    start_date = transition_date - timedelta(weeks=weeks_before)
    weeks = weeks_before + weeks_after + 1
    built = weekly_series_spanning(start_date, weeks, time(9, 0), room_id=3, user="priya")
    return built["start"], built["end"], built["repeat_until"]


def _assert_wall_clock_time_preserved(instances, start, end):
    assert len(instances) > 1
    for instance_start, instance_end in instances:
        assert instance_start.time() == start.time()
        assert instance_end.time() == end.time()
        assert (instance_end - instance_start) == (end - start)


def test_denver_dst_spring_forward_2026_preserves_wall_clock_time():
    start, end, repeat_until = _series_spanning(DENVER_DST_2026_SPRING_FORWARD)
    instances = generate_weekly_instances(start, end, repeat_until)
    assert instances[0][0].date() < DENVER_DST_2026_SPRING_FORWARD < instances[-1][0].date()
    _assert_wall_clock_time_preserved(instances, start, end)


def test_denver_dst_fall_back_2026_preserves_wall_clock_time():
    start, end, repeat_until = _series_spanning(DENVER_DST_2026_FALL_BACK)
    instances = generate_weekly_instances(start, end, repeat_until)
    assert instances[0][0].date() < DENVER_DST_2026_FALL_BACK < instances[-1][0].date()
    _assert_wall_clock_time_preserved(instances, start, end)


def test_berlin_dst_spring_forward_2026_preserves_wall_clock_time():
    start, end, repeat_until = _series_spanning(BERLIN_DST_2026_SPRING_FORWARD)
    instances = generate_weekly_instances(start, end, repeat_until)
    assert instances[0][0].date() < BERLIN_DST_2026_SPRING_FORWARD < instances[-1][0].date()
    _assert_wall_clock_time_preserved(instances, start, end)


def test_berlin_dst_fall_back_2026_preserves_wall_clock_time():
    start, end, repeat_until = _series_spanning(BERLIN_DST_2026_FALL_BACK)
    instances = generate_weekly_instances(start, end, repeat_until)
    assert instances[0][0].date() < BERLIN_DST_2026_FALL_BACK < instances[-1][0].date()
    _assert_wall_clock_time_preserved(instances, start, end)


def test_no_dst_crossing_control_case_still_preserves_wall_clock_time():
    start = datetime(2026, 7, 6, 9, 0, 0)
    end = start + timedelta(minutes=30)
    instances = generate_weekly_instances(start, end, date(2026, 7, 27))
    _assert_wall_clock_time_preserved(instances, start, end)


def test_instance_count_matches_matching_weekdays_inclusive_of_repeat_until():
    start = datetime(2026, 7, 6, 9, 0, 0)
    end = start + timedelta(minutes=30)
    instances = generate_weekly_instances(start, end, date(2026, 7, 27))
    assert [instance_start.date() for instance_start, _ in instances] == [
        date(2026, 7, 6),
        date(2026, 7, 13),
        date(2026, 7, 20),
        date(2026, 7, 27),
    ]


def test_repeat_until_on_non_matching_weekday_stops_at_last_real_occurrence():
    start = datetime(2026, 7, 6, 9, 0, 0)
    end = start + timedelta(minutes=30)
    instances = generate_weekly_instances(start, end, date(2026, 7, 29))
    assert instances[-1][0].date() == date(2026, 7, 27)


def test_repeat_until_before_start_date_rejected():
    start = datetime(2026, 7, 6, 9, 0, 0)
    end = start + timedelta(minutes=30)
    with pytest.raises(InvalidTimeRange):
        generate_weekly_instances(start, end, date(2026, 7, 1))


def test_repeat_until_exceeding_instance_cap_raises_range_too_large():
    start = datetime(2020, 1, 6, 9, 0, 0)
    end = start + timedelta(minutes=30)
    repeat_until = start.date() + timedelta(weeks=MAX_RECURRING_INSTANCES + 10)
    with pytest.raises(RangeTooLarge):
        generate_weekly_instances(start, end, repeat_until)
