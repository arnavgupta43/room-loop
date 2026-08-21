"""
API-level tests for GET /rooms - architecture.md SS3, G8, risk item SS5.5.
"""


def test_get_rooms_matches_c2_sample_shape(client):
    response = client.get("/rooms")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 3, "name": "Aurora", "capacity": 8},
        {"id": 4, "name": "Basalt", "capacity": 4},
        {"id": 9, "name": "Cinder", "capacity": 12},
        {"id": 17, "name": "Dune", "capacity": 6},
    ]


def test_get_rooms_ids_are_sparse_and_ordered_by_id(client):
    ids = [room["id"] for room in client.get("/rooms").json()]
    assert ids == [3, 4, 9, 17]


def test_get_rooms_never_leaks_internal_office_field(client):
    for room in client.get("/rooms").json():
        assert set(room.keys()) == {"id", "name", "capacity"}
