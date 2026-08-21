"""
Unit tests for domain.future_cutoff_for_room and the series-cancellation split logic -
spec.md SS3.4/SS3.7/G6, risk item SS5.4.
"""

from datetime import datetime, timedelta

from app import store
from app.domain import Booking, future_cutoff_for_room


def _seed_series(room_id, series_id, starts, user="priya"):
    new_bookings = [
        Booking(id=0, room_id=room_id, start=s, end=s + timedelta(minutes=30), user=user, series_id=series_id)
        for s in starts
    ]
    return store.add_bookings_batch(new_bookings)


def test_future_cutoff_for_room_uses_each_rooms_own_office_now(berlin_room, denver_room, frozen_now):
    berlin_now = datetime(2026, 7, 10, 9, 0, 0)
    denver_now = datetime(2026, 7, 10, 15, 0, 0)
    frozen_now("Berlin", berlin_now)
    frozen_now("Denver", denver_now)

    assert future_cutoff_for_room(berlin_room) == berlin_now
    assert future_cutoff_for_room(denver_room) == denver_now


def test_berlin_series_splits_future_and_past_on_its_own_now(berlin_room, frozen_now):
    now = datetime(2026, 7, 10, 9, 0, 0)
    frozen_now("Berlin", now)
    series_id = "berlin-series"
    past, future = _seed_series(
        berlin_room.id, series_id, [now - timedelta(weeks=1), now + timedelta(weeks=1)]
    )

    cancelled_count, left_untouched_count = store.cancel_series_future(
        series_id, future_cutoff_for_room(berlin_room)
    )

    assert cancelled_count == 1
    assert left_untouched_count == 1
    assert past.status == "active"
    assert future.status == "cancelled"


def test_denver_series_uses_denver_now_not_berlin_now(denver_room, frozen_now):
    # Deliberately different "now" per office - if the implementation used the wrong office's
    # clock for a Denver room, this booking would be misclassified as future and cancelled.
    frozen_now("Berlin", datetime(2026, 7, 10, 9, 0, 0))
    frozen_now("Denver", datetime(2026, 7, 10, 20, 0, 0))

    series_id = "denver-series"
    [booking] = _seed_series(denver_room.id, series_id, [datetime(2026, 7, 10, 15, 0, 0)])

    cancelled_count, left_untouched_count = store.cancel_series_future(
        series_id, future_cutoff_for_room(denver_room)
    )

    assert cancelled_count == 0
    assert left_untouched_count == 1
    assert booking.status == "active"


def test_instance_starting_exactly_at_cutoff_is_cancelled(berlin_room, frozen_now):
    now = datetime(2026, 7, 10, 9, 0, 0)
    frozen_now("Berlin", now)
    series_id = "boundary-series"
    [booking] = _seed_series(berlin_room.id, series_id, [now])

    cancelled_count, left_untouched_count = store.cancel_series_future(
        series_id, future_cutoff_for_room(berlin_room)
    )

    assert cancelled_count == 1
    assert left_untouched_count == 0
    assert booking.status == "cancelled"


def test_series_with_zero_future_instances_cancels_nothing(berlin_room, frozen_now):
    now = datetime(2026, 7, 10, 9, 0, 0)
    frozen_now("Berlin", now)
    series_id = "all-past-series"
    _seed_series(berlin_room.id, series_id, [now - timedelta(weeks=2), now - timedelta(weeks=1)])

    cancelled_count, left_untouched_count = store.cancel_series_future(
        series_id, future_cutoff_for_room(berlin_room)
    )

    assert cancelled_count == 0
    assert left_untouched_count == 2


def test_cancelling_a_series_twice_is_idempotent(berlin_room, frozen_now):
    now = datetime(2026, 7, 10, 9, 0, 0)
    frozen_now("Berlin", now)
    series_id = "idempotent-series"
    _seed_series(berlin_room.id, series_id, [now + timedelta(weeks=1)])

    cutoff = future_cutoff_for_room(berlin_room)
    first = store.cancel_series_future(series_id, cutoff)
    second = store.cancel_series_future(series_id, cutoff)

    assert first == (1, 0)
    assert second == (0, 1)
