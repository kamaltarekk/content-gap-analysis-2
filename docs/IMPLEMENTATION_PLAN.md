# Implementation Plan

Claude Code must execute one phase at a time.

## Phase 0 — Repository health

- [ ] Install API dependencies
- [ ] Install web dependencies
- [ ] Run existing checks
- [ ] Fix scaffold issues

Acceptance:

- API imports
- API tests pass
- Web typecheck and build pass

## Phase 1 — Persistence and migrations

- [x] Replace in-memory repository with SQLAlchemy persistence
- [x] Add Alembic
- [x] Add project/entity/source/job models
- [x] Add test database fixtures

Acceptance:

- CRUD survives process restart
- migrations upgrade/downgrade

## Phase 2 — Guided setup and state machine

- [x] Implement setup API
- [x] Implement project state transitions
- [x] Build setup wizard
- [x] Validate required fields

Acceptance:

- invalid transition returns 409
- unknown bottleneck remains allowed but conditional

## Phase 3 — Website collection

- [x] Implement SSRF-safe URL validation
- [x] Implement same-origin Playwright crawler
- [x] Add caps, delay, screenshots, and logs
- [x] Store snapshots and normalized content

Acceptance:

- exact URL preserved
- blocked/failed status preserved
- cap enforced

## Phase 4 — Evidence and review queue

- [x] Extract candidate evidence
- [x] Build review APIs
- [x] Build review queue UI
- [x] Add approve/edit/reject/hypothesis actions

Acceptance:

- no candidate is auto-approved
- every approved item has reviewer and timestamp

## Phase 5 — Sales Elements analysis

- [ ] Add Anthropic structured-output adapter
- [ ] Complete mock adapter
- [ ] Validate SE01–SE17
- [ ] Implement score eligibility
- [ ] Build Sales Elements UI

Acceptance:

- unknown is not zero
- SE01 unresolved blocks numeric score
- evidence IDs resolve

## Phase 6 — Competitor comparability

- [ ] Implement comparability thresholds
- [ ] Build comparison matrix
- [ ] Block totals for insufficient samples

Acceptance:

- one homepage cannot receive a total score

## Phase 7 — Gap engine

- [ ] Implement candidate gap rules
- [ ] Separate severity/confidence
- [ ] Implement root-cause taxonomy
- [ ] Build gap explorer

Acceptance:

- competitor behavior alone cannot confirm a gap
- non-content blockers remain separate

## Phase 8 — Exports and artifact

- [ ] CSV/JSON exports
- [ ] Interactive artifact
- [ ] Evidence drawer and direct links
- [ ] RTL/LTR QA

Acceptance:

- artifact loads without syntax errors
- all links and counters resolve

## Phase 9 — Production hardening

- [ ] PostgreSQL
- [ ] Celery/Redis
- [ ] S3-compatible storage
- [ ] authentication
- [ ] deployment
- [ ] observability
