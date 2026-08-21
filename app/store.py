"""
In-memory repository - plain Python data structures, no persistence, no logic beyond storage
and lookup. Business rules (conflicts, duration, recurrence) live in domain.py, not here.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.domain import Booking, Room
from app.rooms_seed import SEED_ROOMS

rooms: dict[int, Room] = {}
bookings: dict[int, Booking] = {}
next_booking_id: int = 1


def _seed_rooms() -> None:
    rooms.clear()
    for room in SEED_ROOMS:
        rooms[room.id] = room


def reset() -> None:
    global next_booking_id
    _seed_rooms()
    bookings.clear()
    next_booking_id = 1


_seed_rooms()


def get_room(room_id: int) -> Optional[Room]:
    return rooms.get(room_id)


def list_rooms() -> list[Room]:
    return sorted(rooms.values(), key=lambda room: room.id)


def add_booking(booking: Booking) -> Booking:
    global next_booking_id
    booking.id = next_booking_id
    next_booking_id += 1
    bookings[booking.id] = booking
    return booking


def get_booking(booking_id: int) -> Optional[Booking]:
    return bookings.get(booking_id)


def list_bookings(
    room_id: Optional[int] = None,
    user: Optional[str] = None,
    series_id: Optional[str] = None,
    status: Optional[str] = None,
) -> list[Booking]:
    result = list(bookings.values())
    if room_id is not None:
        result = [b for b in result if b.room_id == room_id]
    if user is not None:
        result = [b for b in result if b.user == user]
    if series_id is not None:
        result = [b for b in result if b.series_id == series_id]
    if status is not None:
        result = [b for b in result if b.status == status]
    return sorted(result, key=lambda b: b.id)


def cancel_booking(booking_id: int, cancelled_at: datetime) -> Optional[Booking]:
    booking = bookings.get(booking_id)
    if booking is None:
        return None
    if booking.status != "cancelled":
        booking.status = "cancelled"
        booking.cancelled_at = cancelled_at
    return booking
