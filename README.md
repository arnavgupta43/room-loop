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

Planning docs are done and approved. A first vertical slice is implemented and tested: room
listing, and single-booking create/read/list/cancel, including duration validation and conflict
detection (`domain.validate_duration`, `domain.conflicts`). 42 tests passing.

Not yet built: recurring (weekly) bookings, series cancellation, and the availability-search
endpoint — the pieces that need `time_utils.now_in_office` and DST handling. Every still-stubbed
file/function keeps its docstring describing what's planned, per `spec.md`/`architecture.md`.

## Repo layout (current)

```
app/
  main.py            FastAPI app + route wiring only
  schemas.py         Pydantic request/response models (the API contract)
  domain.py          pure business logic — no FastAPI/Pydantic dependency
  store.py           in-memory repository
  rooms_seed.py      fixed room data (from C2) + internal office field
  time_utils.py      naive-ISO parsing + the one per-office "now" helper
tests/
  conftest.py
  test_domain_*.py   unit tests against domain.py directly, no HTTP
  test_api_*.py      endpoint tests via FastAPI's TestClient
test_data/
  scenarios.py       shared fixtures for the brief's highest-risk behavior (spec.md §5)
docs/
  spec.md            requirements + resolved ambiguities (technical)
  hld.md             what/why/how (plain language)
architecture.md       tech stack, API contract, guardrails
requirements.txt
pytest.ini
```

Every file above already exists with a docstring explaining its contents (implemented parts say
so; unbuilt parts describe what's planned) — open any of them to see what's there.

## Running it

```bash
python -m venv .venv
.venv/Scripts/activate        # .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
pytest                        # 42 tests, all passing
uvicorn app.main:app --reload # run the service locally at http://127.0.0.1:8000
```

## Deliverables checklist (per the brief)

- [ ] Code — in progress (single bookings done; recurring/cancellation/availability pending)
- [x] README with run instructions
- [ ] Test data demonstrating highest-risk behavior (see `docs/spec.md` §5 for what that is)
- [ ] `DECISIONS.md`
