"""
API-level tests for DELETE /bookings/{id} and DELETE /bookings/series/{series_id} -
architecture.md SS3, spec.md SS3.4.

Cases to cover:
    - cancel a standalone booking: 200, status becomes "cancelled", cancelled_at populated
    - cancel one instance of a series: only that instance is affected, siblings stay active
    - cancelling an already-cancelled booking: 200 again (idempotent, not an error), same
      cancelled_at as the first call (not bumped to a new timestamp)
    - cancel unknown booking id: 404 booking_not_found
    - cancel a whole series with a frozen "now": future instances cancelled, past instances
      untouched, response counts match exactly
    - cancel unknown series_id: 404 series_not_found
    - after series cancellation, the freed room/time slot is immediately bookable again by a
      new request (ties to spec.md SS6 open question 3 - current assumption is "yes,
      immediately")
"""
