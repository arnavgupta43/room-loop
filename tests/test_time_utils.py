"""
Unit tests for app.time_utils - naive-timestamp parsing/formatting (G1) and per-office "now"
(G6). No test elsewhere calls the real now_in_office - tests/conftest.py's `frozen_now` fixture
monkeypatches it out everywhere cancellation logic is exercised, so its actual zoneinfo-backed
implementation needs direct coverage here.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.time_utils import format_naive_iso, now_in_office, parse_naive_iso


def test_parse_naive_iso_round_trips_a_valid_string():
    assert parse_naive_iso("2026-07-06T09:00:00") == datetime(2026, 7, 6, 9, 0, 0)


def test_parse_naive_iso_rejects_malformed_string():
    with pytest.raises(ValueError, match="invalid ISO datetime"):
        parse_naive_iso("not-a-timestamp")


def test_parse_naive_iso_rejects_offset_suffixed_string():
    with pytest.raises(ValueError, match="must be naive"):
        parse_naive_iso("2026-07-06T09:00:00+02:00")


def test_parse_naive_iso_rejects_fractional_seconds():
    with pytest.raises(ValueError, match="second precision"):
        parse_naive_iso("2026-07-06T09:00:00.500000")


def test_format_naive_iso_rejects_aware_datetime():
    aware = datetime(2026, 7, 6, 9, 0, 0, tzinfo=ZoneInfo("Europe/Berlin"))
    with pytest.raises(AssertionError):
        format_naive_iso(aware)


def test_now_in_office_returns_naive_datetime_for_each_known_office():
    for office in ("Berlin", "Denver"):
        result = now_in_office(office)
        assert isinstance(result, datetime)
        assert result.tzinfo is None


def test_now_in_office_matches_zoneinfo_wall_clock_within_a_few_seconds():
    for office, zone_name in (("Berlin", "Europe/Berlin"), ("Denver", "America/Denver")):
        expected = datetime.now(ZoneInfo(zone_name)).replace(tzinfo=None)
        actual = now_in_office(office)
        assert abs((actual - expected).total_seconds()) < 5


def test_now_in_office_unknown_office_raises_key_error():
    with pytest.raises(KeyError):
        now_in_office("Nowhere")
