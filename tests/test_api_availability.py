"""
API-level tests for GET /availability - spec.md SS3.8, architecture.md SS3.
"""


def test_single_slot_query_sorted_by_capacity_then_conflict_count(client):
    response = client.get(
        "/availability", params={"start": "2026-07-06T09:00:00", "end": "2026-07-06T09:30:00"}
    )
    assert response.status_code == 200
    body = response.json()
    assert [r["room_id"] for r in body] == [4, 17, 3, 9]  # Basalt(4) < Dune(6) < Aurora(8) < Cinder(12)
    assert all(r["conflict_count"] == 0 for r in body)
    assert all(r["total_instances"] == 1 for r in body)


def test_capacity_filter_excludes_rooms_below_it(client):
    response = client.get(
        "/availability",
        params={"start": "2026-07-06T09:00:00", "end": "2026-07-06T09:30:00", "capacity": 8},
    )
    assert [r["room_id"] for r in response.json()] == [3, 9]  # only Aurora(8) and Cinder(12) qualify


def test_capacity_omitted_defaults_to_zero_including_every_room(client):
    response = client.get(
        "/availability", params={"start": "2026-07-06T09:00:00", "end": "2026-07-06T09:30:00"}
    )
    assert len(response.json()) == 4


def test_recurring_query_conflict_count_reflects_whole_series(client):
    client.post(
        "/bookings",
        json={"room_id": 3, "start": "2026-07-20T09:00:00", "end": "2026-07-20T09:30:00", "user": "sam"},
    )

    response = client.get(
        "/availability",
        params={
            "start": "2026-07-06T09:00:00",
            "end": "2026-07-06T09:30:00",
            "repeat_until": "2026-07-27",
        },
    )
    body = {r["room_id"]: r for r in response.json()}
    assert body[3]["conflict_count"] == 1
    assert body[3]["total_instances"] == 4
    assert body[4]["conflict_count"] == 0


def test_malformed_start_with_offset_returns_400(client):
    response = client.get(
        "/availability", params={"start": "2026-07-06T09:00:00Z", "end": "2026-07-06T09:30:00"}
    )
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_request"


def test_availability_search_has_no_side_effects(client):
    before = client.get("/bookings").json()
    client.get(
        "/availability",
        params={
            "start": "2026-07-06T09:00:00",
            "end": "2026-07-06T09:30:00",
            "repeat_until": "2026-07-27",
            "capacity": 4,
        },
    )
    after = client.get("/bookings").json()
    assert before == after == []
