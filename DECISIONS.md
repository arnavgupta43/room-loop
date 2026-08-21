# DECISIONS

## (a) Judgment calls the brief didn't specify

- **R5 ("iterate rooms 1..N") vs C2's real sample data (non-contiguous IDs 3, 4, 9, 17)** —
  treated C2 as authoritative since it's real integration data and R5 is a simplifying
  assumption; room lookups and availability search iterate the actual known room set.
- **R1 (all-or-nothing) vs R2 (skip conflicting instances)** — resolved as two different levels:
  R2 governs per-instance time conflicts (skip and continue); R1 governs everything else (bad
  room, invalid duration/range, or literally every instance conflicting — abort, save nothing).
- **REST API, in-memory storage, and a fixed duration-picker set (15m/30m/45m/1h…4h)** — all
  places the brief was silent. REST fits the brief's own hint that other tools call an HTTP API;
  the rest are graded on business logic, not infra or free-form input handling.

## (b) Questions I'd ask the PM before shipping

- Is there a skip-threshold above which a recurring series should be rejected outright instead
  of partially created (R2 says "one or two" as an example, not a rule)?
- Should series cancellation be undoable within a window, and is a cancelled slot instantly
  re-bookable or held? The Office Manager's story suggests cancellation matters a lot, but not
  whether the fix itself needs to be reversible.

## (c) Where AI helped, and what it got wrong

- Built end-to-end with Claude Code: spec → architecture → tests → implementation, in that order.
- Two bugs it introduced, caught by manually probing behavior against the written contract rather
  than trusting the tests alone: `GET /availability`'s first query-param approach (FastAPI's
  `Depends()`-as-model) silently bypassed the shared naive-datetime validator, letting an
  offset/`Z` timestamp crash the route instead of returning `400`; and naive-datetime rejection
  was returning FastAPI's default `422` instead of the `400` envelope architecture.md promises.
  Both fixed once found.

## (d) Left out on purpose, and what's next

- No auth, no editing/rescheduling, no persistence or concurrency safety, no capacity enforcement
  at booking-creation time (only used by availability search) — all explicitly out of scope.
- Next: real persistence if this graduates past a demo, a soft-delete/undo window for series
  cancellation, and resolving the R2 skip-threshold question with the PM.
