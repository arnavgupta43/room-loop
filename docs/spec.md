# RoomLoop Booking Service — Spec

Status: Approved
Source: `RoomLoop-Take-Home-Brief.pdf` (Junior SDE, Round 2)

This document defines **what** the service must do and the business rules it must enforce.
It intentionally excludes implementation details (language frameworks, storage engine, file
layout) — those live in `../architecture.md`. Non-technical framing lives in `hld.md`.

---

## 1. Scope

Build the booking core for RoomLoop: create single bookings, create recurring (weekly)
bookings, cancel bookings, and a room-availability search helper (§3.8). Two other internal
systems already integrate against this service and constrain what we can change (see §4).

**Out of scope for v1** (see §7 for full list): auth/authz, multi-tenant orgs, non-weekly
recurrence (daily/monthly), editing/rescheduling an existing booking, capacity-based booking
(booking a room for more people than it holds), email/calendar notifications.

---

## 2. Entities

- **Room** — `id`, `name`, `capacity`, plus an internal-only `office` (Berlin or Denver).
  `office` is never returned by the public room-listing endpoint (see §4, C2) — it exists
  purely so the system can evaluate "now" correctly per room during series cancellation
  (§3.4, §3.7). Rooms are seeded/fixed data, not created via this service (no `POST /rooms`
  in scope). Real room IDs are **not** contiguous (see §4, C2).
- **Booking** — a single occupied slot: `room`, `start`, `end`, `user`. May stand alone or be
  one instance of a recurring series.
- **Recurring series** — a template (`room`, `start` time, `end` time, weekday, `repeat_until`
  date) that expands into individual Bookings at creation time. The expansion is a one-time
  event — instances are materialized up front, not computed lazily.

---

## 3. Functional Requirements

### 3.1 Allowed booking durations
A deliberate simplification beyond the brief, modeled on the familiar calendar-app duration
picker (e.g. Google Meet/Calendar): a booking's length (`end - start`) must be one of a fixed
set of values rather than any arbitrary span. This applies uniformly to single bookings and to
every instance of a recurring booking.

**Allowed durations:** 15m, 30m, 45m, 1h, then 0.5h increments up to a 4h cap — i.e.
`{15m, 30m, 45m, 1h, 1.5h, 2h, 2.5h, 3h, 3.5h, 4h}`. Nothing shorter than 15 minutes, nothing
longer than 4 hours.

**Start time is unconstrained** — it does not need to land on a grid (e.g. a 9:07 AM start is
valid as long as the resulting duration is in the allowed set). Only the duration is
restricted.

A duration outside this set is rejected as a validation error — the same failure class as
`end <= start` below, which for a recurring booking voids the entire request per R1 (§3.6).

### 3.2 Create a single booking
Input: room, start time, end time, user.
- Rejected if the room doesn't exist.
- Rejected if `end <= start`, or if the duration isn't in the allowed set (§3.1).
- Rejected if it conflicts (§3.5) with an existing active booking in the same room.

### 3.3 Create a recurring booking
Input: room, start time, end time, user, weekly repeat rule, repeat-until date.
- The weekday of repetition is the weekday of the given `start` (e.g. start on a Monday →
  repeats every Monday). No separate weekday field.
- Duration is validated once against §3.1 (it's identical for every instance).
- All instances from `start` through `repeat_until` (inclusive) are generated **up front** at
  creation time — not lazily expanded later.
- Each instance is checked for conflicts independently (§3.5, §3.6).
- Instances that survive are saved as Bookings, tagged with a shared series identifier.

### 3.4 Cancel a booking
Two cancellation shapes:
- **Cancel one booking** — cancels that single Booking (whether standalone or one instance of
  a series). Does not affect sibling instances.
- **Cancel a whole series** — cancels every instance of that series whose `start` is in the
  future relative to *now, in that room's own local time*. Instances already in the past are
  left untouched, per the brief and the Office Manager's complaint about dead series lingering
  forever.

A cancelled booking is retained (not hard-deleted) with a cancelled status/timestamp, so past
occupancy history isn't destroyed by a cancellation.

### 3.5 Conflict rule (R4)
Two bookings conflict iff they are in the **same room** and their time ranges overlap:
`existing.start < new.end AND new.start < existing.end`.
Back-to-back bookings (one ends exactly when the other starts) do **not** conflict — this is a
strict overlap test, not `<=`.
Only bookings with active status are considered; cancelled bookings never conflict.

### 3.6 Partial-conflict handling for recurring bookings (R1 + R2, resolved)
The brief states two rules that read as contradictory:
- R1: recurring creation is all-or-nothing.
- R2: if one or two instances conflict, skip just those and create the rest.

**Resolution:** these operate at different levels.
- R2 governs *per-instance time conflicts*: a conflicting instance is skipped; it is not a
  reason to fail the whole request. There is no cap on how many instances may be skipped this
  way (R2's "one or two" is illustrative, not a threshold) — see open question in §6.
- R1 governs *everything else*: any non-conflict failure (room doesn't exist, invalid time
  range, malformed input) fails the **entire** request and nothing is saved — including
  instances that would otherwise have succeeded. Partial saves due to a mid-request error are
  never acceptable.
- **Edge case, decided:** if *every* instance conflicts (zero would be created), the whole
  request is rejected and nothing is saved — a zero-instance series is not a meaningful
  booking. This is a judgment call; see open question in §6.
- The response to a recurring-booking request must distinguish created instances from skipped
  ones, and say why each skipped instance was skipped (which existing booking it clashed
  with).

### 3.7 Wall-clock recurrence across DST (R3, C1)
Recurring bookings repeat at the same **wall-clock** time every week (e.g. every Monday 9:00
AM), for employees in two offices with different DST calendars (Berlin, Denver).

Per the Office Manager: past Denver bookings have shown up an hour off, unexplained. Combined
with C1 (timestamps are stored/returned as naive local ISO strings, no UTC offset), the likely
root cause of that historical bug is a conversion through UTC (or a fixed offset) at some point
in the pipeline — which silently breaks across a DST transition, since Denver's offset from UTC
is not constant year-round.

**Decision:** never convert booking timestamps to UTC or through any fixed-offset
representation, anywhere in the system. Timestamps are naive local values end-to-end: stored,
compared, and returned that way. Weekly recurrence is generated by adding 7 days to the naive
local date while holding the time-of-day fixed — which is DST-proof by construction, since a
naive value carries no timezone/DST state to get wrong.

Each room's office (Berlin/Denver) is still tracked internally, but only to determine "now" for
series cancellation (§3.4) — a Denver room's "future" is judged against Denver's current
wall-clock time, not the server's or Berlin's. It plays no part in recurrence math or conflict
detection.

### 3.8 Room availability search
A deliberate addition beyond the brief's "What to Build" list, but one the brief itself hints
at: R5's "iterate rooms 1..N for availability checks" only makes sense if something scans
*all* rooms — nothing in create-booking does, since the caller always supplies a specific
`room` (§3.2, §3.3). This is that something: a **read-only helper endpoint** that suggests
candidate rooms for a time window. It does not change booking creation — `room` stays a
required input there, unchanged.

**Input:** `start`, `end` (or, for a recurring series, `start`, `end`, `repeat_until`, same
shape as §3.3), and an optional minimum `capacity`.

**Behavior:**
1. Filter to rooms whose capacity ≥ the requested `capacity` (all rooms if omitted).
2. For each candidate room, compute how many of the requested instances would conflict
   (§3.5) with that room's existing active bookings:
   - Single-slot request: exactly one instance, so this is 0 or 1.
   - Recurring request: expand the full series (§3.3) against that room and count how many of
     the instances would conflict — mirrors the skip-logic in §3.6, so this number is exactly
     "how many instances would be skipped if this room were chosen."
3. Sort survivors by **capacity ascending** (smallest sufficient room first, so large rooms
   aren't handed to small meetings), then by **conflict count ascending** as a tie-break
   (prefer the room that would need to skip the fewest instances).
4. Return the ranked list — including rooms with some conflicts, not only fully-free ones — so
   the caller can see the tradeoff (e.g. a smaller, mostly-free room vs. a larger, fully-free
   one) rather than only ever seeing binary availability.

This reuses the exact same conflict rule (§3.5) and series-expansion logic (§3.3) as booking
creation — it is a dry run, not a separate notion of "availability."

---

## 4. Integration Constraints (must not break)

- **C1 — timestamp format:** stored and returned booking timestamps must be naive local ISO
  strings with no UTC offset (e.g. `2026-07-02T09:00:00`), because the nightly reporting job
  (owned by another team, won't change this quarter) parses them that way.
- **C2 — room listing shape:** `GET /rooms`-equivalent output must match the existing shape
  consumed by the facilities dashboard: a list of `{id, name, capacity}` objects. The real
  sample data has **non-contiguous IDs** (`3, 4, 9, 17`).
  - **This contradicts R5**, which says availability checks may iterate room IDs 1..N assuming
    sequential numbering. The sample data in C2 is real integration data from the current
    prototype; R5's simplifying assumption is not. **Decision: treat C2 as authoritative.**
    Room lookups and the availability search (§3.8) iterate the actual set of known room IDs,
    never an assumed contiguous range. Flagged as an open question for the PM (§6).

---

## 5. Test-risk priorities

Per the brief's request for "test data that demonstrates the behavior most at risk of being
wrong," the highest-risk areas to cover are, in order:
1. Weekly recurrence spanning a DST transition in Denver and in Berlin — wall-clock time must
   not shift.
2. Conflict boundary: back-to-back bookings (shared instant) must not conflict; smallest
   possible overlap must conflict.
3. Recurring creation where some instances conflict (partial skip) vs. where a non-conflict
   error occurs (full rejection) vs. where every instance conflicts (full rejection).
4. Series cancellation splitting cleanly on past vs. future relative to per-office "now."
5. Room ID lookups against the real non-contiguous ID set, not an assumed 1..N range.
6. Duration boundary values (§3.1): just-under 15m, exactly each allowed value, just-over 4h,
   and an in-between value like 20m that isn't in the allowed set.
7. Availability search ranking (§3.8): capacity filtering excludes too-small rooms; among
   qualifying rooms, a smaller-but-fully-free room ranks above a larger room with any conflicts
   only if capacity ties — capacity is always the primary key, conflict count only breaks ties.
   For a recurring search, conflict count must reflect the *whole* expanded series per
   candidate room, not just the first instance.

---

## 6. Open questions for the PM

1. R2 says "skip one or two" conflicting instances — is there a threshold above which we
   should instead reject the whole series (e.g. "more than half the instances conflict")? We're
   currently treating any number of conflicts as skippable, with total rejection only at 100%
   conflict.
2. Should cancelling a whole series be reversible (undo) within some window, given the Office
   Manager's story about a bad recurring booking sitting for months? Currently no.
3. Is a cancelled booking's room/time slot immediately free for a new booking, or is there a
   cooldown/audit hold? Currently: immediately free.
4. Should `GET` endpoints (list bookings, etc.) be in scope for this take-home, or is create +
   cancel sufficient? Currently including minimal read endpoints since cancellation and conflict
   testing need a way to inspect state.
5. Is per-room office (Berlin/Denver) actually fixed data we should know, or should it be an
   explicit input somewhere? Currently assumed as fixed internal metadata per room, invented for
   this exercise since the brief doesn't supply it.
6. For the availability search (§3.8), should `capacity` be a hard filter (rooms below it never
   appear at all, current behavior) or a soft one (shown but ranked last)? Hard filter currently
   assumed since showing a room too small for the meeting isn't a useful suggestion.

---

## 7. Explicitly out of scope

- Authentication/authorization — `user` is a free-text identifier, not a verified account.
- Editing or rescheduling an existing booking (cancel + recreate is the only path).
- Non-weekly recurrence patterns (daily, monthly, custom RRULE).
- Room capacity enforcement (booking a room with too few seats for the party).
- Creating/editing rooms via the API — the room list is fixed seed data.
- Notifications (email/calendar invites).
- Concurrency/multi-process safety — this is a single-process demo service.
