# RoomLoop — Architecture

Status: Approved — implementation proceeds from this contract
Scope: how `docs/spec.md`'s requirements get built — tech stack, project layout, the exact API
contract, and the invariants ("guardrails") the implementation must never violate. This is a
working document for our own process, not one of the brief's required deliverables — the brief
only requires code, README, test data, and DECISIONS.md in the final repo.

---

## 1. Tech stack

- **Python 3.11+, FastAPI + Pydantic v2** for the HTTP layer. Chosen over a CLI (docs/spec.md's
  scope decision) because the brief's own integration constraints (C1, C2) describe *other
  tools calling an HTTP API* — a CLI would be a worse fit for the scenario. FastAPI gives free
  request validation via Pydantic and a test client for HTTP-level tests, at no real cost over
  plain `http.server` for a service this size.
- **In-memory storage** — plain Python data structures behind a small repository module. No
  database, no ORM, no migrations. This is a single-process demo graded on business-logic
  correctness (recurrence, conflicts, cancellation, the DST fix), not persistence engineering;
  a DB adds setup time without adding evidence of the skills being tested. Explicitly a non-goal
  per docs/spec.md §7.
- **pytest**, with FastAPI's `TestClient` for endpoint-level tests and plain pytest for
  framework-free unit tests of the pure business logic.

## 2. Project layout

```
app/
  main.py          FastAPI app + route wiring only — no business logic lives here
  schemas.py       Pydantic request/response models (the contract in §3, enforced in code)
  domain.py        Pure business logic: duration validation, conflict detection, recurrence
                    generation, availability ranking. No FastAPI/Pydantic dependency — this is
                    what gets unit-tested first, before any HTTP wiring exists.
  store.py         In-memory repository: rooms, bookings, series. No logic beyond storage.
  rooms_seed.py    Fixed room data (from C2's sample) + each room's office, for internal use.
  time_utils.py    Naive-ISO parsing/formatting, per-office "now" helper.
tests/
  conftest.py
  test_domain_*.py   Unit tests against domain.py directly — no HTTP involved.
  test_api_*.py      Endpoint tests via TestClient — the contract in §3, end to end.
test_data/
  scenarios.py       The brief's requested "test data that demonstrates the highest-risk
                      behavior" (docs/spec.md §5) as reusable fixtures/scripts, not just assertions
                      buried in test files.
```

`domain.py` having zero framework dependency is deliberate: since we're doing TDD, the first
tests written (duration validation, conflict math, recurrence generation, the DST case) can be
written and run against pure functions before `main.py` or any route exists at all.

## 3. API contract

All timestamps in requests and responses are naive ISO strings, second precision, no offset:
`YYYY-MM-DDTHH:MM:SS`. Any string containing `Z`, `+HH:MM`, or `-HH:MM` timezone info is
rejected as a 400 (see Guardrail G1). `repeat_until` is a plain date: `YYYY-MM-DD`.

All error responses share one envelope:
```json
{ "error": "conflict", "message": "human-readable explanation" }
```

### `GET /rooms`
Returns the fixed room list, exactly matching C2's shape — nothing added, nothing removed.
```json
200 OK
[
  { "id": 3, "name": "Aurora", "capacity": 8 },
  { "id": 4, "name": "Basalt", "capacity": 4 },
  { "id": 9, "name": "Cinder", "capacity": 12 },
  { "id": 17, "name": "Dune", "capacity": 6 }
]
```

### `POST /bookings` — create a single booking
```json
Request
{ "room_id": 3, "start": "2026-07-06T09:00:00", "end": "2026-07-06T09:30:00", "user": "priya" }
```
- `201` → the created booking:
  `{ "id": 101, "room_id": 3, "start": "...", "end": "...", "user": "priya", "status": "active", "series_id": null }`
- `404` `room_not_found` — room_id isn't in the real room table (§4/C2, G2).
- `400` `invalid_time_range` — `end <= start`.
- `400` `invalid_duration` — `end - start` isn't one of §3.1's allowed durations.
- `409` `conflict` — overlaps an existing active booking in that room; response includes
  `"conflicting_booking_id"`.

### `POST /bookings/recurring` — create a recurring booking
```json
Request
{ "room_id": 3, "start": "2026-07-06T09:00:00", "end": "2026-07-06T09:30:00",
  "user": "priya", "repeat_until": "2026-12-28" }
```
- `201` → 
  ```json
  { "series_id": "b3f1...", "created": [ {booking}, {booking}, ... ],
    "skipped": [ { "start": "...", "end": "...", "reason": "conflict",
                   "conflicting_booking_id": 88 } ] }
  ```
- `404` `room_not_found`, `400` `invalid_time_range`, `400` `invalid_duration` — same as
  single-booking, and per R1/G7, fail before anything is written.
- `400` `range_too_large` — implied instance count exceeds the safety cap (G9).
- `409` `all_instances_conflicted` — every generated instance clashed; nothing saved (§3.6).

### `DELETE /bookings/{id}` — cancel one booking (or one instance of a series)
Idempotent: cancelling an already-cancelled booking is not an error, it just returns current
state. Simpler than a strict "already cancelled" error, and matches DELETE's usual semantics.
- `200` → `{ "id": 101, "status": "cancelled", "cancelled_at": "..." }`
- `404` `booking_not_found`

### `DELETE /bookings/series/{series_id}` — cancel a whole series
Cancels every instance with `start` in the future relative to that room's own office "now"
(§3.4, §3.7, G6); past instances are left untouched.
- `200` → `{ "series_id": "...", "cancelled_count": 19, "left_untouched_count": 7 }`
- `404` `series_not_found`

### `GET /bookings` — list/filter (read-only, for inspection; docs/spec.md §6 open question 4)
Query params, all optional: `room_id`, `user`, `series_id`, `status`.
- `200` → `[ {booking}, {booking}, ... ]`

### `GET /bookings/{id}`
- `200` → `{booking}`
- `404` `booking_not_found`

### `GET /availability` — room availability search (§3.8)
Query params: `start`, `end`, `repeat_until` (optional — if present, this is scored as a
recurring request per the same expansion as `POST /bookings/recurring`), `capacity` (optional,
default 0).
```json
200 OK
[
  { "room_id": 4, "name": "Basalt", "capacity": 4, "conflict_count": 0, "total_instances": 26 },
  { "room_id": 3, "name": "Aurora", "capacity": 8, "conflict_count": 2, "total_instances": 26 }
]
```
Sorted by `capacity` ascending, then `conflict_count` ascending (§3.8). Rooms below the
requested `capacity` are excluded entirely (docs/spec.md §6 open question 6 — hard filter).

---

## 4. Guardrails

Hard invariants the implementation must never violate, each tied to a decision already made in
`docs/spec.md`. These are the checklist for reviewing our own code, and a source of test cases.

- **G1 — No timezone-aware datetimes, anywhere.** Every datetime in this codebase is naive.
  No `zoneinfo`, no UTC conversion, no fixed-offset arithmetic, in storage, comparison, or the
  API boundary. (spec §3.7 — this is *the* DST fix.)
- **G2 — No assumed room ID range.** Room lookups always go through the actual known room set,
  never `range(1, N+1)` or similar. (spec §4/C2)
- **G3 — Recurrence is calendar arithmetic, not duration arithmetic.** Each next occurrence is
  the previous naive start/end plus exactly 7 calendar days, computed directly on the naive
  datetime — never via a 168-hour delta computed through any absolute/UTC representation.
  (spec §3.7)
- **G4 — Duration is validated once per request, not once per instance.** All instances in a
  recurring booking share one duration; validate it once against §3.1's allowed set.
- **G5 — Conflict checks are same-room and active-only.** Never compare bookings across
  different rooms; never let a cancelled booking participate in a conflict check. (spec §3.5)
- **G6 — "Now" for series cancellation is the room's own office wall-clock time.** Never the
  server's local time, never UTC. (spec §3.4, §3.7)
- **G7 — Recurring creation writes are all-or-nothing at the batch level.** Compute and validate
  everything first; only write once the full set of surviving instances is known. Any
  non-conflict failure aborts before any write happens — no partial series ever gets persisted.
  (spec §3.6, R1)
- **G8 — `GET /rooms` response shape is frozen.** Exactly `{id, name, capacity}` per room, in
  that field set — this is a live contract with the facilities dashboard (C2) we cannot verify
  against directly, so we don't take risks with it.
- **G9 — Recurring instance count is capped.** A sanity limit (260 instances, ~5 years weekly)
  prevents a pathological `repeat_until` from generating an unbounded series; requests over the
  cap are rejected outright, not silently truncated.
