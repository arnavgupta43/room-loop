"""
API-level tests for POST /bookings, GET /bookings, GET /bookings/{id}, DELETE /bookings/{id} -
architecture.md SS3.
"""

from test_data.scenarios import overlapping_pair


def _booking_payload(room_id=3, start="2026-07-06T09:00:00", end="2026-07-06T09:30:00", user="priya"):
    return {"room_id": room_id, "start": start, "end": end, "user": user}


def test_create_booking_happy_path(client):
    response = client.post("/bookings", json=_booking_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["room_id"] == 3
    assert body["start"] == "2026-07-06T09:00:00"
    assert body["end"] == "2026-07-06T09:30:00"
    assert body["user"] == "priya"
    assert body["status"] == "active"
    assert body["series_id"] is None
    assert isinstance(body["id"], int)


def test_create_booking_unknown_room_id_returns_404(client):
    response = client.post("/bookings", json=_booking_payload(room_id=5))
    assert response.status_code == 404
    assert response.json()["error"] == "room_not_found"


def test_create_booking_end_before_start_returns_400(client):
    response = client.post(
        "/bookings", json=_booking_payload(start="2026-07-06T09:30:00", end="2026-07-06T09:00:00")
    )
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_time_range"


def test_create_booking_rejects_offset_or_z_suffixed_timestamps(client):
    response = client.post(
        "/bookings",
        json=_booking_payload(start="2026-07-06T09:00:00Z", end="2026-07-06T09:30:00Z"),
    )
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_request"


def test_create_booking_rejects_numeric_epoch_timestamps(client):
    response = client.post(
        "/bookings", json=_booking_payload(start=1732000000, end=1732001800)
    )
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_request"


def test_create_booking_rejects_fractional_seconds(client):
    response = client.post(
        "/bookings",
        json=_booking_payload(start="2026-07-06T09:00:00.123456", end="2026-07-06T09:30:00.123456"),
    )
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_request"


def test_create_booking_disallowed_duration_returns_400(client):
    response = client.post("/bookings", json=_booking_payload(end="2026-07-06T09:20:00"))
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_duration"


def test_create_booking_conflict_returns_409_with_conflicting_id(client):
    (existing_start, existing_end), (new_start, new_end) = overlapping_pair()
    first = client.post(
        "/bookings",
        json=_booking_payload(start=existing_start.isoformat(), end=existing_end.isoformat()),
    ).json()
    response = client.post(
        "/bookings",
        json=_booking_payload(start=new_start.isoformat(), end=new_end.isoformat(), user="sam"),
    )
    assert response.status_code == 409
    body = response.json()
    assert body["error"] == "conflict"
    assert body["conflicting_booking_id"] == first["id"]


def test_create_booking_same_time_different_room_succeeds(client):
    client.post("/bookings", json=_booking_payload(room_id=3))
    response = client.post("/bookings", json=_booking_payload(room_id=4, user="sam"))
    assert response.status_code == 201


def test_cancelled_booking_does_not_block_a_new_one_in_its_slot(client):
    created = client.post("/bookings", json=_booking_payload()).json()
    client.delete(f"/bookings/{created['id']}")
    response = client.post("/bookings", json=_booking_payload(user="sam"))
    assert response.status_code == 201


def test_response_timestamps_are_naive_iso_strings(client):
    body = client.post("/bookings", json=_booking_payload()).json()
    assert body["start"] == "2026-07-06T09:00:00"
    assert body["end"] == "2026-07-06T09:30:00"


def test_cancel_booking_returns_cancelled_status(client):
    created = client.post("/bookings", json=_booking_payload()).json()
    response = client.delete(f"/bookings/{created['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["status"] == "cancelled"
    assert body["cancelled_at"] is not None


def test_cancel_is_idempotent(client):
    created = client.post("/bookings", json=_booking_payload()).json()
    first = client.delete(f"/bookings/{created['id']}")
    second = client.delete(f"/bookings/{created['id']}")
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["cancelled_at"] == first.json()["cancelled_at"]


def test_cancel_unknown_booking_returns_404(client):
    response = client.delete("/bookings/999")
    assert response.status_code == 404
    assert response.json()["error"] == "booking_not_found"


def test_get_booking_by_id_returns_404_for_unknown_id(client):
    response = client.get("/bookings/999")
    assert response.status_code == 404
    assert response.json()["error"] == "booking_not_found"


def test_get_booking_by_id_happy_path(client):
    created = client.post("/bookings", json=_booking_payload()).json()
    response = client.get(f"/bookings/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_list_bookings_filters_by_room_id(client):
    client.post("/bookings", json=_booking_payload(room_id=3))
    client.post("/bookings", json=_booking_payload(room_id=4, user="sam"))
    response = client.get("/bookings", params={"room_id": 3})
    body = response.json()
    assert len(body) == 1
    assert body[0]["room_id"] == 3


def test_list_bookings_filters_by_user(client):
    client.post("/bookings", json=_booking_payload(room_id=3, user="priya"))
    client.post("/bookings", json=_booking_payload(room_id=4, user="sam"))
    response = client.get("/bookings", params={"user": "sam"})
    body = response.json()
    assert len(body) == 1
    assert body[0]["user"] == "sam"


def test_list_bookings_filters_by_status(client):
    created = client.post("/bookings", json=_booking_payload()).json()
    client.delete(f"/bookings/{created['id']}")
    response = client.get("/bookings", params={"status": "cancelled"})
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == created["id"]
