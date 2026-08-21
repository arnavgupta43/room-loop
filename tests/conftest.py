"""
Shared pytest fixtures.

Implemented so far: fresh_store, client, berlin_room, denver_room.
Not yet implemented: frozen_now (needed once series cancellation / time_utils.now_in_office
exist).
"""

import pytest
from fastapi.testclient import TestClient

from app import store
from app.main import app


@pytest.fixture
def fresh_store():
    store.reset()
    yield
    store.reset()


@pytest.fixture
def client(fresh_store):
    return TestClient(app)


@pytest.fixture
def berlin_room(fresh_store):
    return next(room for room in store.list_rooms() if room.office == "Berlin")


@pytest.fixture
def denver_room(fresh_store):
    return next(room for room in store.list_rooms() if room.office == "Denver")
