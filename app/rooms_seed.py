"""
Fixed room data (not created via the API, spec.md SS7). IDs are deliberately non-contiguous,
matching real dashboard data (C2) - never renumber.
"""

from app.domain import Room

SEED_ROOMS: list[Room] = [
    Room(id=3, name="Aurora", capacity=8, office="Berlin"),
    Room(id=4, name="Basalt", capacity=4, office="Berlin"),
    Room(id=9, name="Cinder", capacity=12, office="Denver"),
    Room(id=17, name="Dune", capacity=6, office="Denver"),
]
