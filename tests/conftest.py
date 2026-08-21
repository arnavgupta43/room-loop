"""
Shared pytest fixtures.
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


@pytest.fixture
def frozen_now(monkeypatch):
    fixed_times: dict[str, object] = {}

    def _fake_now_in_office(office):
        return fixed_times[office]

    monkeypatch.setattr("app.time_utils.now_in_office", _fake_now_in_office)

    def _freeze(office: str, when) -> None:
        fixed_times[office] = when

    return _freeze
