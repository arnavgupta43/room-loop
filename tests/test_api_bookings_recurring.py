"""
API-level tests for POST /bookings/recurring - spec.md SS3.6 (R1+R2), proven end to end here,
not just at the domain layer.
"""


def _recurring_payload(
    room_id=3,
    start="2026-07-06T09:00:00",
    end="2026-07-06T09:30:00",
    user="priya",
    repeat_until="2026-07-27",
):
    return {
        "room_id": room_id,
        "start": start,
        "end": end,
        "user": user,
        "repeat_until": repeat_until,
    }


def test_happy_path_no_conflicts_creates_all_instances_under_one_series(client):
    response = client.post("/bookings/recurring", json=_recurring_payload())
    assert response.status_code == 201
    body = response.json()
    assert body["skipped"] == []
    assert len(body["created"]) == 4

    series_id = body["series_id"]
    assert series_id
    for booking in body["created"]:
        assert booking["series_id"] == series_id
        assert booking["status"] == "active"

    starts = [b["start"] for b in body["created"]]
    assert starts == [
        "2026-07-06T09:00:00",
        "2026-07-13T09:00:00",
        "2026-07-20T09:00:00",
        "2026-07-27T09:00:00",
    ]


def test_one_conflicting_instance_is_skipped_not_rejected(client):
    seed = client.post(
        "/bookings",
        json={"room_id": 3, "start": "2026-07-20T09:00:00", "end": "2026-07-20T09:30:00", "user": "sam"},
    ).json()

    response = client.post("/bookings/recurring", json=_recurring_payload())
    assert response.status_code == 201
    body = response.json()
    assert len(body["created"]) == 3
    assert len(body["skipped"]) == 1
    assert body["skipped"][0]["start"] == "2026-07-20T09:00:00"
    assert body["skipped"][0]["reason"] == "conflict"
    assert body["skipped"][0]["conflicting_booking_id"] == seed["id"]


def test_unknown_room_id_writes_nothing(client):
    response = client.post("/bookings/recurring", json=_recurring_payload(room_id=5))
    assert response.status_code == 404
    assert response.json()["error"] == "room_not_found"
    assert client.get("/bookings").json() == []


def test_invalid_duration_writes_nothing(client):
    response = client.post("/bookings/recurring", json=_recurring_payload(end="2026-07-06T09:20:00"))
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_duration"
    assert client.get("/bookings").json() == []


def test_every_instance_conflicted_is_rejected_and_writes_nothing(client):
    for day in ["2026-07-06", "2026-07-13", "2026-07-20", "2026-07-27"]:
        client.post(
            "/bookings",
            json={"room_id": 3, "start": f"{day}T09:00:00", "end": f"{day}T09:30:00", "user": "sam"},
        )

    response = client.post("/bookings/recurring", json=_recurring_payload())
    assert response.status_code == 409
    assert response.json()["error"] == "all_instances_conflicted"
    assert len(client.get("/bookings").json()) == 4


def test_repeat_until_exceeding_instance_cap_returns_400_and_writes_nothing(client):
    response = client.post("/bookings/recurring", json=_recurring_payload(repeat_until="2036-01-01"))
    assert response.status_code == 400
    assert response.json()["error"] == "range_too_large"
    assert client.get("/bookings").json() == []


def test_repeat_until_before_start_returns_400_and_writes_nothing(client):
    response = client.post("/bookings/recurring", json=_recurring_payload(repeat_until="2026-07-01"))
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_time_range"
    assert client.get("/bookings").json() == []


def test_malformed_repeat_until_returns_400_and_writes_nothing(client):
    response = client.post("/bookings/recurring", json=_recurring_payload(repeat_until="not-a-date"))
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_request"
    assert client.get("/bookings").json() == []


def test_recurring_conflict_skip_reason_names_every_distinct_clashing_booking(client):
    seed_week1 = client.post(
        "/bookings",
        json={"room_id": 3, "start": "2026-07-06T09:00:00", "end": "2026-07-06T09:30:00", "user": "sam"},
    ).json()
    seed_week2 = client.post(
        "/bookings",
        json={"room_id": 3, "start": "2026-07-13T09:00:00", "end": "2026-07-13T09:30:00", "user": "sam"},
    ).json()

    response = client.post("/bookings/recurring", json=_recurring_payload())
    body = response.json()
    assert len(body["created"]) == 2
    assert len(body["skipped"]) == 2
    assert body["skipped"][0]["conflicting_booking_id"] == seed_week1["id"]
    assert body["skipped"][1]["conflicting_booking_id"] == seed_week2["id"]
