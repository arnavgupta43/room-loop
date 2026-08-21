"""
Reusable test data - the brief's requested "test data that demonstrates the behavior most at
risk of being wrong" (spec.md SS5), as importable constants/builder functions rather than values
buried inline in individual test files. Both tests/test_domain_*.py and tests/test_api_*.py
should import from here rather than re-deriving these dates by hand.

Constants to define here:

    DENVER_DST_2026_SPRING_FORWARD = date(2026, 3, 8)   clocks jump 2am -> 3am MST -> MDT
    DENVER_DST_2026_FALL_BACK      = date(2026, 11, 1)  clocks fall 2am -> 1am MDT -> MST
    BERLIN_DST_2026_SPRING_FORWARD = date(2026, 3, 29)  clocks jump 2am -> 3am CET -> CEST
    BERLIN_DST_2026_FALL_BACK      = date(2026, 10, 25) clocks fall 3am -> 2am CEST -> CET

    (deliberately non-aligned with the Denver dates - that mismatch is the whole reason a
    per-office, DST-proof recurrence rule matters, spec.md SS3.7)

Builder functions to define here:

    weekly_series_spanning(start_date, weeks, time_of_day, room_id, user)
        -> the (room_id, start, end, user, repeat_until) tuple/dict for a recurring-booking
           request that crosses a given date range, for feeding directly into either
           domain.generate_weekly_instances or a POST /bookings/recurring test call

    overlapping_pair() / back_to_back_pair()
        -> canonical (existing_booking, new_booking) time-range pairs for conflict tests,
           so the exact boundary values used in test_domain_conflicts.py and
           test_api_bookings.py stay in sync instead of being redefined twice

    duration_boundary_cases()
        -> list of (end - start, expected: valid/invalid) pairs covering every allowed
           duration plus the just-under/just-over/in-between cases from spec.md SS5.6
"""
