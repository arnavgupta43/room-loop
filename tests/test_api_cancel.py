"""
API-level tests for DELETE /bookings/series/{series_id} - architecture.md SS3, spec.md SS3.4.
Standalone-booking cancellation (DELETE /bookings/{id}) is covered in test_api_bookings.py.
"""

from datetime import datetime


def _create_recurring(
    client,
    room_id=3,
    start="2026-07-06T09:00:00",
    end="2026-07-06T09:30:00",
    user="priya",
    repeat_until="2026-07-27",
):
    return client.post(
        "/bookings/recurring",
        json={
            "room_id": room_id,
            "start": start,
            "end": end,
            "user": user,
            "repeat_until": repeat_until,
        },
    ).json()


def test_cancel_one_instance_of_a_series_does_not_affect_siblings(client):
    series = _create_recurring(client)
    target = series["created"][0]

    response = client.delete(f"/bookings/{target['id']}")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

    for sibling in series["created"][1:]:
        current = client.get(f"/bookings/{sibling['id']}").json()
        assert current["status"] == "active"


def test_cancel_series_splits_future_and_past_by_frozen_now(client, frozen_now):
    frozen_now("Berlin", datetime(2026, 7, 15, 0, 0, 0))
    series = _create_recurring(client)  # instances land on 07-06, 07-13, 07-20, 07-27

    response = client.delete(f"/bookings/series/{series['series_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["series_id"] == series["series_id"]
    assert body["cancelled_count"] == 2
    assert body["left_untouched_count"] == 2

    statuses = {
        b["start"]: client.get(f"/bookings/{b['id']}").json()["status"] for b in series["created"]
    }
    assert statuses["2026-07-06T09:00:00"] == "active"
    assert statuses["2026-07-13T09:00:00"] == "active"
    assert statuses["2026-07-20T09:00:00"] == "cancelled"
    assert statuses["2026-07-27T09:00:00"] == "cancelled"


def test_cancel_unknown_series_returns_404(client):
    response = client.delete("/bookings/series/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"] == "series_not_found"


def test_freed_slot_after_series_cancellation_is_immediately_bookable(client, frozen_now):
    frozen_now("Berlin", datetime(2026, 7, 1, 0, 0, 0))  # before every instance
    series = _create_recurring(client)
    client.delete(f"/bookings/series/{series['series_id']}")

    response = client.post(
        "/bookings",
        json={"room_id": 3, "start": "2026-07-06T09:00:00", "end": "2026-07-06T09:30:00", "user": "sam"},
    )
    assert response.status_code == 201
