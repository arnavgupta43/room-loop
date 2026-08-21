"""
Fixed room data. Rooms are not created via the API (spec.md SS7) - this is the one source of
truth store.py seeds itself from at startup. IDs are deliberately non-contiguous (3, 4, 9, 17),
matching the real dashboard data (C2) - never backfill or renumber these.
"""

from app.domain import Room

SEED_ROOMS: list[Room] = [
    Room(id=3, name="Aurora", capacity=8, office="Berlin"),
    Room(id=4, name="Basalt", capacity=4, office="Berlin"),
    Room(id=9, name="Cinder", capacity=12, office="Denver"),
    Room(id=17, name="Dune", capacity=6, office="Denver"),
]
