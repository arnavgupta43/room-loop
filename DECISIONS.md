# DECISIONS

## (a) Judgment calls the brief didn't specify

- **R5 ("iterate rooms 1..N") vs C2's real sample data (non-contiguous IDs 3, 4, 9, 17)** — these
  directly contradict each other. Treated C2 as authoritative since it's real integration data
  from the current prototype and R5 is a simplifying assumption; room lookups and availability
  search iterate the actual known room set, never an assumed range.
- **R1 (all-or-nothing) vs R2 (skip conflicting instances)** — resolved as operating at different
  levels: R2 governs per-instance *time conflicts* (skip and continue); R1 governs everything else
  (bad room, invalid duration/range — abort the whole request, nothing saved). If literally every
  instance conflicts, the whole request is rejected too, since a zero-instance series isn't a
  meaningful booking.
- **REST API over a CLI** — the brief's own constraints (C1, C2) describe *other tools* calling an
  HTTP API, which a CLI is a poor fit for.
- **Booking durations restricted to a fixed set** (15m/30m/45m/1h…4h in 30m steps) — beyond what
  the brief asked for, but modeled on a familiar calendar-app duration picker; otherwise "start
  time" and "end time" alone leave duration completely unconstrained.
- **In-memory storage, no persistence** — this is graded on business logic (recurrence, conflicts,
  cancellation, the DST fix), not persistence engineering, and a DB adds setup cost without adding
  evidence of the skills being tested.

## (b) Questions I'd ask the PM before shipping

- R2 says "skip one or two" — is there a threshold above which we should reject the whole series
  instead (e.g. more than half the instances conflicting)? Currently any number is skippable.
- Should cancelling a whole series be undoable within some window? The Office Manager's story
  (a stale series sitting for months) suggests cancellation matters a lot, but reversibility of
  the fix itself is unaddressed.
- Is a cancelled slot immediately re-bookable, or should there be a cooldown/audit hold? Currently
  assumed immediate.

## (c) Where AI helped, and what it got wrong

- This was built end-to-end with Claude Code (spec → architecture → tests → implementation, in
  that order), including the DST regression tests that pin down the Denver bug.
- First pass at `GET /availability`'s query-param parsing used FastAPI's `Depends()`-as-query-model
  pattern. That silently bypassed the shared naive-datetime validator (FastAPI coerces query
  params by their raw type before the model's validator runs), so an offset/`Z`-suffixed timestamp
  slipped through and crashed with a raw `TypeError` instead of a clean `400`. Caught by manually
  probing the endpoint before writing tests; fixed by constructing the Pydantic model explicitly
  inside the route instead.
- Also missed on the first pass: naive-datetime rejection (offset/`Z` in a timestamp) was returning
  FastAPI's default `422` instead of the `400` the architecture doc's error envelope promises.
  Caught by re-checking actual behavior against the written contract, not by a failing test — the
  tests hadn't covered that case yet either.

## (d) Left out on purpose, and what's next

- No auth/authz — `user` is a free-text identifier, per the brief's scope.
- No editing/rescheduling — cancel + recreate is the only path, per spec.
- No persistence, no concurrency safety — single-process in-memory demo.
- Booking creation doesn't enforce room capacity against party size (only availability search uses
  capacity, as a ranking/filter input) — explicitly out of scope per the brief.
- Next, in priority order: real persistence (so state survives a restart) if this graduates past a
  demo; a soft-delete/undo window for series cancellation; and revisiting the R2 skip-threshold
  question with the PM before any team relies on it for a large recurring series.
