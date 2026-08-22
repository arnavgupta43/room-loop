"""
Unit tests for app.store's own not-found guards. The API layer (main.py) already checks
existence before calling store.cancel_booking / store.cancel_series_future, so these
defensive `return None` branches are unreachable through the HTTP surface - they're exercised
here by calling the store directly, matching how test_domain_cancellation.py already calls
store.cancel_series_future without going through main.py.
"""

from app import store


def test_cancel_booking_unknown_id_returns_none(fresh_store):
    assert store.cancel_booking(999, cancelled_at=None) is None


def test_cancel_series_future_unknown_series_id_returns_none(fresh_store):
    assert store.cancel_series_future("does-not-exist", cutoff=None) is None
