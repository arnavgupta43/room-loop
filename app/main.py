"""
FastAPI app instance and route wiring ONLY.

No business logic belongs in this file - every route handler is a thin adapter that parses
input via schemas.py, calls into domain.py and store.py, and shapes the response via schemas.py.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import domain, store
from app.schemas import BookingCreate, BookingOut, RecurringBookingCreate, RecurringBookingResult, RoomOut
from app.time_utils import format_naive_iso

app = FastAPI(title="RoomLoop")


@app.exception_handler(domain.RoomNotFound)
async def _room_not_found(request: Request, exc: domain.RoomNotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": "room_not_found", "message": str(exc)})


@app.exception_handler(domain.InvalidTimeRange)
async def _invalid_time_range(request: Request, exc: domain.InvalidTimeRange) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": "invalid_time_range", "message": str(exc)})


@app.exception_handler(domain.InvalidDuration)
async def _invalid_duration(request: Request, exc: domain.InvalidDuration) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": "invalid_duration", "message": str(exc)})


@app.exception_handler(domain.BookingConflict)
async def _booking_conflict(request: Request, exc: domain.BookingConflict) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "error": "conflict",
            "message": str(exc),
            "conflicting_booking_id": exc.conflicting_booking_id,
        },
    )


@app.exception_handler(domain.BookingNotFound)
async def _booking_not_found(request: Request, exc: domain.BookingNotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": "booking_not_found", "message": str(exc)})


@app.exception_handler(domain.RangeTooLarge)
async def _range_too_large(request: Request, exc: domain.RangeTooLarge) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": "range_too_large", "message": str(exc)})


@app.exception_handler(domain.AllInstancesConflicted)
async def _all_instances_conflicted(request: Request, exc: domain.AllInstancesConflicted) -> JSONResponse:
    return JSONResponse(
        status_code=409, content={"error": "all_instances_conflicted", "message": str(exc)}
    )


@app.get("/rooms", response_model=list[RoomOut])
def get_rooms() -> list[domain.Room]:
    return store.list_rooms()


@app.post("/bookings", response_model=BookingOut, status_code=201)
def create_booking(payload: BookingCreate) -> domain.Booking:
    room = store.get_room(payload.room_id)
    if room is None:
        raise domain.RoomNotFound(f"room {payload.room_id} not found")

    domain.validate_duration(payload.start, payload.end)

    for existing in store.list_bookings(room_id=payload.room_id, status="active"):
        if domain.conflicts(existing.start, existing.end, payload.start, payload.end):
            raise domain.BookingConflict(existing.id)

    booking = domain.Booking(
        id=0,
        room_id=payload.room_id,
        start=payload.start,
        end=payload.end,
        user=payload.user,
    )
    return store.add_booking(booking)


@app.post("/bookings/recurring", response_model=RecurringBookingResult, status_code=201)
def create_recurring_booking(payload: RecurringBookingCreate) -> dict:
    room = store.get_room(payload.room_id)
    if room is None:
        raise domain.RoomNotFound(f"room {payload.room_id} not found")

    existing = store.list_bookings(room_id=payload.room_id, status="active")
    series_id, created, skipped = domain.create_recurring_booking(
        room_id=payload.room_id,
        start=payload.start,
        end=payload.end,
        user=payload.user,
        repeat_until=payload.repeat_until,
        existing_bookings=existing,
    )
    persisted = store.add_bookings_batch(created)
    return {"series_id": series_id, "created": persisted, "skipped": skipped}


@app.get("/bookings", response_model=list[BookingOut])
def list_bookings(
    room_id: Optional[int] = None,
    user: Optional[str] = None,
    series_id: Optional[str] = None,
    status: Optional[str] = None,
) -> list[domain.Booking]:
    return store.list_bookings(room_id=room_id, user=user, series_id=series_id, status=status)


@app.get("/bookings/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int) -> domain.Booking:
    booking = store.get_booking(booking_id)
    if booking is None:
        raise domain.BookingNotFound(f"booking {booking_id} not found")
    return booking


@app.delete("/bookings/{booking_id}")
def cancel_booking(booking_id: int) -> dict:
    booking = store.get_booking(booking_id)
    if booking is None:
        raise domain.BookingNotFound(f"booking {booking_id} not found")
    cancelled = store.cancel_booking(booking_id, datetime.now().replace(microsecond=0))
    assert cancelled is not None
    return {
        "id": cancelled.id,
        "status": cancelled.status,
        "cancelled_at": format_naive_iso(cancelled.cancelled_at),
    }
