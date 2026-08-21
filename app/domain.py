"""
Pure business logic - no FastAPI, no Pydantic, no I/O. Everything here operates on plain
Python values (datetimes, dataclasses) so it can be unit-tested directly, before any HTTP layer
exists.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
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

# G9 - sanity limit on recurring-series length (~5 years weekly), so a pathological
# repeat_until can't generate an unbounded instance list.
MAX_RECURRING_INSTANCES = 260


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


@dataclass
class SkippedInstance:
    start: datetime
    end: datetime
    reason: str
    conflicting_booking_id: int


def validate_duration(start: datetime, end: datetime) -> None:
    if end <= start:
        raise InvalidTimeRange("end must be after start")
    if (end - start) not in ALLOWED_DURATIONS:
        raise InvalidDuration("duration is not in the allowed set")


def conflicts(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def generate_weekly_instances(
    start: datetime, end: datetime, repeat_until: date
) -> list[tuple[datetime, datetime]]:
    """Each next instance is the previous naive start/end plus exactly 7 calendar days (G3) -
    plain timedelta arithmetic on naive values, no timezone involvement, which is what makes it
    DST-proof by construction."""
    if repeat_until < start.date():
        raise InvalidTimeRange("repeat_until is before the series start date")

    duration = end - start
    instances: list[tuple[datetime, datetime]] = []
    instance_start = start
    while instance_start.date() <= repeat_until:
        if len(instances) >= MAX_RECURRING_INSTANCES:
            raise RangeTooLarge(
                f"recurring booking would generate more than {MAX_RECURRING_INSTANCES} instances"
            )
        instances.append((instance_start, instance_start + duration))
        instance_start = instance_start + timedelta(weeks=1)
    return instances


def create_recurring_booking(
    room_id: int,
    start: datetime,
    end: datetime,
    user: str,
    repeat_until: date,
    existing_bookings: list[Booking],
) -> tuple[str, list[Booking], list[SkippedInstance]]:
    """Orchestrates recurring creation (SS3.6/R1+R2): validate duration once (G4), generate
    instances up front, check each against existing_bookings independently, and partition into
    created/skipped. Callers are responsible for the room lookup and for persisting `created`
    (this function does no I/O) - so any exception raised here happens before any write, per G7.
    """
    validate_duration(start, end)
    instances = generate_weekly_instances(start, end, repeat_until)

    series_id = str(uuid.uuid4())
    created: list[Booking] = []
    skipped: list[SkippedInstance] = []

    for instance_start, instance_end in instances:
        conflicting = next(
            (b for b in existing_bookings if conflicts(b.start, b.end, instance_start, instance_end)),
            None,
        )
        if conflicting is not None:
            skipped.append(
                SkippedInstance(
                    start=instance_start,
                    end=instance_end,
                    reason="conflict",
                    conflicting_booking_id=conflicting.id,
                )
            )
        else:
            created.append(
                Booking(
                    id=0,
                    room_id=room_id,
                    start=instance_start,
                    end=instance_end,
                    user=user,
                    series_id=series_id,
                )
            )

    if not created:
        raise AllInstancesConflicted("every instance of the recurring booking conflicted")

    return series_id, created, skipped
