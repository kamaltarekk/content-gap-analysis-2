# Claude Code Instructions

## Product mission

Build a trustworthy evidence-based content diagnosis tool. It must collect approved sources, preserve provenance, propose classifications, require human review, and generate a Sales Elements record plus content-gap analysis.

## Runtime architecture

- `apps/web`: React/Vite/TypeScript
- `apps/api`: FastAPI/Python
- Browser collection: Playwright
- Database: SQLite in local MVP; PostgreSQL in Docker/production
- Async jobs: service abstraction; Redis/Celery is the production target
- AI: Anthropic API adapter plus deterministic mock mode
- Storage: local filesystem abstraction; S3-compatible later

## Non-negotiable domain rules

1. Exact source URLs are preferred. Never silently substitute a different entity.
2. Collection and analysis are separate jobs.
3. Every material finding must link to evidence IDs.
4. AI output starts `pending_review`; it is never auto-approved.
5. A competitor absence statement must say “not found within the analyzed sample.”
6. Severity and confidence are separate.
7. Unknown is not zero.
8. The app must distinguish Claims, Social Proof, and Claim Proof.
9. Use canonical Sales Element IDs `SE01` through `SE17`.
10. Keep `SE01` as `trigger_pain` until the user resolves its semantics.
11. Do not score internal readiness from public sources.
12. Do not call a competitor comparable from one homepage.
13. Never infer spend, ROAS, profitability, CAC, or private performance from public content.
14. No final finding is confirmed before a recorded review decision.
15. The finished app stops at diagnosis/strategy handoff; it does not generate final scripts or copy by default.

## Engineering rules

- Work phase by phase from `docs/IMPLEMENTATION_PLAN.md`.
- Do not start the next phase until tests and the acceptance gate pass.
- Prefer small, reviewable commits.
- Keep API schemas strict. Reject unknown enum values and unknown evidence IDs.
- Add migration-safe fields; do not silently repurpose existing fields.
- Keep Arabic and English text unchanged. UI containers must support RTL and `dir="auto"`.
- Add tests for every state transition, formula, and validation rule.
- Never read or print `.env`, credentials, browser cookies, or secret files.

## Commands

API checks:

```bash
cd apps/api
python -m compileall app
pytest -q
```

Web checks:

```bash
cd apps/web
npm run typecheck
npm run build
```

Full checks:

```bash
./scripts/check.sh
```

## First action in every session

1. Read this file.
2. Read `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, and `docs/IMPLEMENTATION_PLAN.md`.
3. Run `git status` and inspect tests.
4. Identify the first incomplete phase.
5. State the intended files and tests before editing.
