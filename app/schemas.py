"""
Pydantic request/response models - the API contract from architecture.md SS3, enforced in code.

Timestamp fields are validated as NAIVE datetimes only - any input containing tzinfo/offset/'Z'
is rejected (G1), via time_utils.parse_naive_iso in a shared before-validator.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.time_utils import parse_naive_iso


class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    capacity: int


class BookingCreate(BaseModel):
    room_id: int
    start: datetime
    end: datetime
    user: str

    @field_validator("start", "end", mode="before")
    @classmethod
    def _reject_aware_datetimes(cls, value):
        if isinstance(value, str):
            return parse_naive_iso(value)
        return value


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    start: datetime
    end: datetime
    user: str
    status: str
    series_id: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    message: str
