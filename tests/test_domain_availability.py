"""
Unit tests for domain.rank_available_rooms - spec.md SS3.8, risk item SS5.7.

Cases to cover:
    - a room below the requested capacity is excluded entirely, never appears ranked-last
      (hard filter, spec.md SS6 open question 6)
    - capacity is the primary sort key: a larger-capacity room with 0 conflicts still sorts
      AFTER a smaller-capacity room with 0 conflicts, as long as both meet the minimum
    - conflict_count only breaks ties within the same capacity value - never overrides capacity
      ordering
    - single-slot query: conflict_count is always 0 or 1 for every candidate room
    - recurring query (start/end/repeat_until all given): conflict_count reflects the count of
      conflicting instances across the WHOLE expanded series for that room, not just the first
      occurrence - construct a case where a room is free for week 1 but clashes in week 3, and
      assert conflict_count counts that
    - no capacity filter supplied: defaults to 0, i.e. every room is a candidate
"""
