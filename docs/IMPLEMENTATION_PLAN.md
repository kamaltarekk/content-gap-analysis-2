# Implementation Plan

Claude Code must execute one phase at a time.

## Phase 0 — Repository health

- [x] Install API dependencies
- [x] Install web dependencies
- [x] Run existing checks
- [x] Fix scaffold issues

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

Note: the Alembic baseline (`0001`) is an explicit table snapshot (not
`metadata.create_all`), so future revisions can add columns incrementally without
duplicate-column collisions. A schema-parity test asserts the migrated schema
matches the ORM column-for-column.

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

- [x] Add Anthropic structured-output adapter
- [x] Complete mock adapter
- [x] Validate SE01–SE17
- [x] Implement score eligibility
- [x] Build Sales Elements UI

Acceptance:

- unknown is not zero
- SE01 unresolved blocks numeric score
- evidence IDs resolve

## Phase 6 — Competitor comparability

- [x] Implement comparability thresholds
- [x] Build comparison matrix
- [x] Block totals for insufficient samples

Acceptance:

- one homepage cannot receive a total score

## Phase 7 — Gap engine

- [x] Implement candidate gap rules
- [x] Separate severity/confidence
- [x] Implement root-cause taxonomy
- [x] Build gap explorer

Acceptance:

- competitor behavior alone cannot confirm a gap
- non-content blockers remain separate

## Phase 8 — Exports and artifact

- [x] CSV/JSON exports
- [x] Interactive artifact
- [x] Evidence drawer and direct links
- [x] RTL/LTR QA

Acceptance:

- artifact loads without syntax errors
- all links and counters resolve

## Phase 9 — Production hardening

- [x] PostgreSQL
- [x] Celery/Redis
- [x] S3-compatible storage
- [x] authentication
- [x] deployment
- [x] observability
