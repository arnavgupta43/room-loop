"""
API-level tests for GET /availability - spec.md SS3.8, architecture.md SS3.

Cases to cover:
    - single-slot query returns rooms sorted (capacity asc, conflict_count asc), matching the
      domain-level ranking tests but proven through the actual query-param parsing
    - capacity filter excludes rooms below it (query param present) vs. includes all rooms
      (query param omitted, defaults to 0)
    - recurring query (repeat_until supplied) - conflict_count reflects the whole series per
      room, not just the first instance, verified through the HTTP layer end to end
    - malformed start/end (bad format, contains an offset/Z) returns 400, same validation as
      booking creation reuses (schemas.py's shared naive-datetime validator)
    - this endpoint never creates or modifies any booking - a GET call has zero side effects,
      verified by checking booking count before/after
"""
