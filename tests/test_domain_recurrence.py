"""
Unit tests for domain.generate_weekly_instances - spec.md SS3.3/SS3.7, risk item SS5.1.
This is the single highest-priority test file in the project: it directly targets the Denver
DST bug described by the Office Manager.

Cases to cover:
    - a weekly series spanning the Denver DST transitions in 2026 (spring forward Mar 8,
      fall back Nov 1): every generated instance must have the exact same time-of-day as the
      first one. Construct the series to start before the transition and run past it.
    - same test shape for Berlin's DST transitions in 2026 (spring forward Mar 29, fall back
      Oct 25) - the dates deliberately do NOT line up with Denver's, which is the point (two
      offices, two independent DST calendars, spec.md SS3.7).
    - a series that does NOT cross any DST boundary, as a control case - should obviously also
      preserve time-of-day, just isn't interesting on its own.
    - instance count matches the expected number of Mondays (or whichever weekday) between
      start and repeat_until inclusive.
    - repeat_until falling on a non-matching weekday is still handled correctly (last instance
      is the last occurrence <= repeat_until, not repeat_until itself).
    - a repeat_until far enough out to exceed the instance-count safety cap (G9) raises
      RangeTooLarge rather than generating a huge list.
"""
