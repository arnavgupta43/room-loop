"""
Unit tests for domain.future_cutoff_for_room and the series-cancellation split logic -
spec.md SS3.4/SS3.7/G6, risk item SS5.4.

Cases to cover:
    - given a frozen "now" for a Berlin room, instances with start >= now are marked
      cancelled; instances with start < now are left untouched
    - same shape for a Denver room, with a DIFFERENT frozen "now" chosen so the test would fail
      if the implementation used server time or the wrong office's time instead of the room's
      own office
    - an instance whose start is exactly equal to "now" - decide and assert one behavior
      (boundary case, currently undecided in spec.md; pick "cancel it" - it hasn't started yet
      at the instant of cancellation - and document the choice here once implemented)
    - cancelling a series with zero future instances left (all in the past): cancelled_count=0,
      left_untouched_count = total, no error
    - cancelling an already-fully-cancelled series is idempotent, same result on repeat calls
"""
