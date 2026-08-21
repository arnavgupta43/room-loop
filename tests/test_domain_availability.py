"""
Unit tests for domain.rank_available_rooms - spec.md SS3.8, risk item SS5.7.
"""

from datetime import date, datetime, timedelta

from app.domain import Booking, Room, rank_available_rooms

ROOM_SMALL = Room(id=1, name="Small", capacity=4, office="Berlin")
ROOM_MEDIUM = Room(id=2, name="Medium", capacity=8, office="Berlin")
ROOM_LARGE = Room(id=3, name="Large", capacity=12, office="Berlin")

START = datetime(2026, 7, 6, 9, 0, 0)
END = START + timedelta(minutes=30)


def test_room_below_requested_capacity_is_excluded_entirely():
    results = rank_available_rooms(
        [ROOM_SMALL, ROOM_MEDIUM], START, END, capacity=8, existing_bookings_by_room={}
    )
    room_ids = [r.room_id for r in results]
    assert ROOM_SMALL.id not in room_ids
    assert ROOM_MEDIUM.id in room_ids


def test_capacity_is_the_primary_sort_key():
    results = rank_available_rooms(
        [ROOM_LARGE, ROOM_SMALL, ROOM_MEDIUM], START, END, capacity=0, existing_bookings_by_room={}
    )
    assert [r.room_id for r in results] == [ROOM_SMALL.id, ROOM_MEDIUM.id, ROOM_LARGE.id]


def test_conflict_count_only_breaks_ties_within_same_capacity():
    tie_a = Room(id=10, name="TieA", capacity=6, office="Berlin")
    tie_b = Room(id=11, name="TieB", capacity=6, office="Berlin")
    bigger_but_free = Room(id=12, name="Bigger", capacity=8, office="Berlin")

    conflicting_booking = Booking(id=1, room_id=tie_a.id, start=START, end=END, user="sam")
    bookings_by_room = {tie_a.id: [conflicting_booking]}

    results = rank_available_rooms(
        [tie_a, tie_b, bigger_but_free], START, END, capacity=0, existing_bookings_by_room=bookings_by_room
    )

    # same capacity: the conflict-free room ranks first, the conflicting one second
    assert [r.room_id for r in results[:2]] == [tie_b.id, tie_a.id]
    # bigger_but_free has 0 conflicts but a larger capacity, so it still ranks last
    assert results[-1].room_id == bigger_but_free.id


def test_single_slot_conflict_count_is_zero_or_one():
    booking = Booking(id=1, room_id=ROOM_SMALL.id, start=START, end=END, user="sam")
    results = rank_available_rooms(
        [ROOM_SMALL], START, END, capacity=0, existing_bookings_by_room={ROOM_SMALL.id: [booking]}
    )
    assert results[0].conflict_count == 1
    assert results[0].total_instances == 1


def test_recurring_query_conflict_count_reflects_the_whole_expanded_series():
    repeat_until = date(2026, 7, 27)  # weekly: 07-06, 07-13, 07-20, 07-27
    week3_start = START + timedelta(weeks=2)
    week3_end = END + timedelta(weeks=2)
    conflicting = Booking(id=1, room_id=ROOM_SMALL.id, start=week3_start, end=week3_end, user="sam")

    results = rank_available_rooms(
        [ROOM_SMALL],
        START,
        END,
        capacity=0,
        existing_bookings_by_room={ROOM_SMALL.id: [conflicting]},
        repeat_until=repeat_until,
    )

    assert results[0].total_instances == 4
    assert results[0].conflict_count == 1


def test_no_capacity_filter_defaults_to_zero_including_every_room():
    results = rank_available_rooms(
        [ROOM_SMALL, ROOM_MEDIUM, ROOM_LARGE], START, END, capacity=0, existing_bookings_by_room={}
    )
    assert len(results) == 3
