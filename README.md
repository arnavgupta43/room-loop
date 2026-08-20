# RoomLoop Booking Service

Take-home assignment: Junior Software Development Engineer, Round 2. A booking-core rebuild for
an internal meeting-room service — create single and recurring bookings, cancel them, with a
handful of real integration constraints from other teams to respect.

## Start here if you're reviewing this

This wasn't coded directly from the brief. Before any implementation, the brief was worked
through in three stages, in this order — reading them in order is the fastest way to see the
reasoning, not just the result:

1. **[`docs/spec.md`](docs/spec.md)** — the brief's requirements restated precisely, plus every
   place the brief was ambiguous or self-contradictory, made explicit with a resolution and a
   reason. (There are three real contradictions in the brief itself — worth reading §3.6 and §4
   in particular.)
2. **[`docs/hld.md`](docs/hld.md)** — the same decisions in plain language, no jargon, aimed at
   a non-technical reader (what this does, why it's built this way, how it behaves).
3. **[`architecture.md`](architecture.md)** — how `spec.md` turns into code: tech stack choice,
   the exact API contract (every endpoint, request/response shape, status code), and a checklist
   of hard invariants ("guardrails") the implementation is not allowed to violate, each one
   traceable back to a specific decision in `spec.md`.

Only after those three were settled did implementation start — test-first, against the contract
`architecture.md` already pinned down, not written ad hoc alongside the code.

## Project status

Planning docs (spec, HLD, architecture) are done. Implementation is in progress — this section
and the "Running it" section below will be filled in as code lands.

## Repo layout (current)

```
docs/
  spec.md            requirements + resolved ambiguities (technical)
  hld.md             what/why/how (plain language)
architecture.md       tech stack, API contract, guardrails
README.md             this file
```

`app/`, `tests/`, and `test_data/` will appear here as implementation proceeds, per the layout
already defined in `architecture.md` §2.

## Running it

Not yet — implementation hasn't started. This section will cover setup and run instructions
once there's a service to run.

## Deliverables checklist (per the brief)

- [ ] Code — in progress
- [x] README with run instructions — run instructions pending code
- [ ] Test data demonstrating highest-risk behavior (see `docs/spec.md` §5 for what that is)
- [ ] `DECISIONS.md`
