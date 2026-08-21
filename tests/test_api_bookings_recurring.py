"""
API-level tests for POST /bookings/recurring - spec.md SS3.6 (R1+R2 resolution), risk item
SS5.3. This is where the R1-vs-R2 resolution gets proven end to end, not just at the domain
layer.

Cases to cover:
    - happy path, no conflicts: all instances created, skipped list empty, shared series_id on
      every created booking
    - one or two instances pre-conflicted (seed an existing booking that clashes with one
      occurrence): those specific instances appear in `skipped` with reason "conflict" and the
      right conflicting_booking_id; every other instance is still created (R2)
    - invalid room_id: whole request 404s, and a follow-up GET /bookings for that series_id
      confirms literally nothing was written (R1/G7) - not even the instances that would have
      been conflict-free
    - invalid duration: whole request 400s, nothing written, same verification as above
    - every single instance pre-conflicted: whole request 409s all_instances_conflicted,
      nothing written
    - repeat_until implying more than the instance cap: 400 range_too_large, nothing written
    - repeat_until before start: 400 (treat as invalid_time_range or a dedicated code - decide
      and document when implemented)
"""
