"""
Pure business logic - no FastAPI, no Pydantic, no I/O. Everything here operates on plain
Python values (datetimes, dataclasses) so it can be unit-tested directly, before any HTTP layer
exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

ALLOWED_DURATIONS: frozenset[timedelta] = frozenset(
    {
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
    }
)


class RoomNotFound(Exception):
    pass


class InvalidTimeRange(Exception):
    pass


class InvalidDuration(Exception):
    pass


class RangeTooLarge(Exception):
    pass


class BookingConflict(Exception):
    def __init__(self, conflicting_booking_id: int):
        self.conflicting_booking_id = conflicting_booking_id
        super().__init__(f"conflicts with booking {conflicting_booking_id}")


class AllInstancesConflicted(Exception):
    pass


class BookingNotFound(Exception):
    pass


class SeriesNotFound(Exception):
    pass


@dataclass
class Room:
    id: int
    name: str
    capacity: int
    office: str


@dataclass
class Booking:
    id: int
    room_id: int
    start: datetime
    end: datetime
    user: str
    status: str = "active"
    series_id: Optional[str] = None
    cancelled_at: Optional[datetime] = None


def validate_duration(start: datetime, end: datetime) -> None:
    if end <= start:
        raise InvalidTimeRange("end must be after start")
    if (end - start) not in ALLOWED_DURATIONS:
        raise InvalidDuration("duration is not in the allowed set")


def conflicts(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end
