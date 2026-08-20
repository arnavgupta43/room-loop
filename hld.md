# RoomLoop — What, Why, How

Status: DRAFT — for review
Audience: anyone, not just engineers. No code or technical jargon below — for the technical
version of these decisions, see `spec.md`; for the technical build plan, see `architecture.md`.

---

## What is RoomLoop?

RoomLoop is the internal service that lets employees book meeting rooms. This project rebuilds
its "booking core" — the part that actually creates, repeats, and cancels bookings — properly,
replacing an early prototype. Two other internal tools already depend on this service (a
facilities dashboard that displays the room list, and a nightly reporting job that reads booking
times), so the rebuild has to keep working for them without changes on their end.

## Why does this need care, not just a quick rewrite?

Three real problems, all reported by actual users of the current prototype, shaped this design:

1. **"Dead" recurring bookings.** The Office Manager's biggest complaint: someone books a room
   every Monday for six months, the project ends, and nobody remembers to free the room — it
   just sits "busy" forever on the calendar. RoomLoop needs to make cancelling an entire
   recurring series a single, easy action.
2. **Bookings showing up an hour wrong.** Denver bookings have, in the past, silently landed an
   hour off from what was booked, for no reason anyone could pin down. This is a known symptom
   of daylight saving time bugs (see "The Denver problem" below) — the new system is built to
   not have this class of bug at all, rather than to patch around it.
3. **Two systems already depend on how this data looks today.** A dashboard renders whatever the
   room list looks like, and a nightly report parses booking times in a specific format. Both
   are owned by other teams and won't change this quarter — so the rebuild has to fit their
   existing expectations, not the other way around.

## How does it work?

### Creating a one-off booking
You provide a room, a start time, an end time, and who it's for. The system checks two things:
the room actually exists, and no one else already has that room during that time. If both check
out, the booking is made.

### Booking lengths follow a simple picker, not free-form times
Rather than letting someone type any arbitrary length ("47 minutes"), booking length is chosen
from a familiar short list, the same idea as the duration dropdown in Google Meet or Google
Calendar: 15, 30, or 45 minutes, then 1 hour, then half-hour steps up to a 4-hour cap. The start
time itself can be anything (a meeting can start at 9:07) — only the *length* is restricted.
This keeps the room's schedule predictable and avoids a long tail of odd-length bookings to
reason about.

### Creating a recurring (weekly) booking
Instead of booking one slot, you describe a pattern: this room, this time, every week, on this
same weekday, until a given end date. RoomLoop immediately works out every individual occurrence
that pattern implies (e.g. 26 separate Monday-9am bookings for a 6-month series) and creates them
all up front, rather than figuring them out later one at a time.

**What happens if some of those occurrences clash with something already booked?** The instinct
might be "reject the whole series" — but that would mean one unlucky clash six months from now
blocks a series that's otherwise completely fine. Instead: any occurrence that clashes is simply
skipped, and everything else in the series is still created. The person booking finds out exactly
which occurrences (if any) were skipped and why. The only time the *entire* series is rejected
outright is if the request itself is invalid in some other way (bad room, bad time range) — or if
literally every single occurrence would clash, which means there'd be nothing left to book
anyway.

### Cancelling a booking
Two ways to cancel, matching the two things you might have booked:
- Cancel **one specific booking** — whether it's a standalone booking or a single week of a
  recurring series.
- Cancel **a whole series at once** — this is the direct fix for the Office Manager's complaint.
  One action ends the entire remaining series. Occurrences that already happened in the past are
  left alone (you can't retroactively un-book last month), only future ones are cancelled.

A cancelled booking isn't erased — it's marked cancelled and kept on record, so there's still a
history of what happened, and the room's time slot becomes bookable again for someone else.

### Finding an available room
This wasn't explicitly asked for, but the brief hints strongly that it's needed (it gives
guidance specifically about "checking availability across rooms," which otherwise wouldn't apply
to anything in the basic booking flow). It's a simple helper: give it a time window (and,
optionally, how many people need to fit), and it returns a ranked list of rooms that could work
— smallest room that's big enough first, and among equally-sized options, whichever one has
fewer clashes. For a recurring pattern, it checks the *entire* series against each candidate
room, so the suggestion reflects "this room would need to skip 2 occurrences," not just whether
the very first Monday is free. This is purely a suggestion tool — it doesn't book anything on its
own; you still create the booking with your chosen room, same as before.

### The Denver problem, explained
"Wall-clock time" means the number on the clock — if you book 9:00 AM every Monday, every single
occurrence should say 9:00 AM, full stop. That sounds obvious, but it's a genuinely easy thing to
get wrong once daylight saving time is involved, and RoomLoop has offices in two places (Berlin
and Denver) that each shift their clocks on *different* calendar dates. A system that quietly
converts times through a single global time standard behind the scenes can shift by exactly one
hour whenever a clock-change happens to fall in the middle of a series — which lines up exactly
with what was reported about Denver bookings. The fix here is architectural, not a patch: this
system is built to never convert times through a shared standard in the first place, so the
1-hour drift can't happen no matter how the two offices' DST calendars line up.

## Key decisions worth knowing about

- **Room list isn't a clean 1-to-N sequence.** The real room IDs (pulled from the dashboard's
  actual data) are scattered — 3, 4, 9, 17 — not 1, 2, 3, 4. One part of the brief's guidance
  assumed a clean sequential list; the real sample data doesn't match that assumption, so the
  real data wins. This matters because a naive "just loop from 1 to N" implementation would
  silently skip real rooms or check rooms that don't exist.
- **A booking's exact office location is tracked, but never shown.** Internally, the system
  needs to know whether a room is in Berlin or Denver — specifically to correctly judge "is this
  occurrence in the future or the past" when cancelling a series. It is never included in
  anything the dashboard or any other consumer sees, to avoid changing a data shape that other
  tools already depend on.

## What's deliberately not included in this version

- Logging in / verifying who's making a booking (the "user" is just a name, not a checked
  identity).
- Editing an existing booking — to change one, cancel it and create a new one.
- Any repeat pattern other than weekly (no daily, no monthly).
- Enforcing that a room is big enough for the group — capacity is only used by the availability
  search as a helpful filter, not as a hard rule when actually creating a booking.
- Creating or editing the room list itself — rooms are fixed, existing data.
- Any kind of notification (no emails, no calendar invites).

## Questions to settle before this ships

1. R2 (the "skip clashing occurrences" rule) uses "one or two" as an example — should there be a
   cutoff where too many clashes means rejecting the whole series instead of creating a
   mostly-empty one?
2. Should cancelling an entire series be undoable for some grace period, given how much the
   Office Manager cares about dead series being cleaned up?
3. Once a booking is cancelled, is its slot instantly free for someone else, or should there be
   a short hold/cooldown first?
4. Should people be able to look up existing bookings (not just create/cancel them) in this
   version, or is that a later phase?
5. Is each room's office location (Berlin vs. Denver) something that already exists somewhere
   we should pull from, or is it fine that this project defines it for the exercise?
6. For the "find an available room" helper, if someone asks for a room for 6 people, should
   rooms that seat fewer than 6 be hidden entirely, or shown anyway ranked lower?
