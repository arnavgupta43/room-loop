"""
Pydantic request/response models - the API contract from architecture.md SS3, enforced in code.

Timestamp fields are validated as NAIVE datetimes only - any input containing tzinfo/offset/'Z'
is rejected (G1), via time_utils.parse_naive_iso in a shared before-validator.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.time_utils import parse_naive_iso


class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    capacity: int


class _NaiveTimestampMixin(BaseModel):
    @field_validator("start", "end", mode="before", check_fields=False)
    @classmethod
    def _reject_aware_datetimes(cls, value):
        if not isinstance(value, str):
            raise ValueError(f"timestamp must be an ISO string, not {type(value).__name__}")
        return parse_naive_iso(value)


class BookingCreate(_NaiveTimestampMixin):
    room_id: int
    start: datetime
    end: datetime
    user: str


class RecurringBookingCreate(_NaiveTimestampMixin):
    room_id: int
    start: datetime
    end: datetime
    user: str
    repeat_until: date


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    start: datetime
    end: datetime
    user: str
    status: str
    series_id: Optional[str] = None


class SkippedInstance(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    start: datetime
    end: datetime
    reason: str
    conflicting_booking_id: int


class RecurringBookingResult(BaseModel):
    series_id: str
    created: list[BookingOut]
    skipped: list[SkippedInstance]


class SeriesCancelResult(BaseModel):
    series_id: str
    cancelled_count: int
    left_untouched_count: int


class AvailabilityQuery(_NaiveTimestampMixin):
    start: datetime
    end: datetime
    repeat_until: Optional[date] = None
    capacity: int = 0


class AvailableRoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    room_id: int
    name: str
    capacity: int
    conflict_count: int
    total_instances: int


class ErrorResponse(BaseModel):
    error: str
    message: str
