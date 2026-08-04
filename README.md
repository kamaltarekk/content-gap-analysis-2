# Evidence-Based Content Diagnosis Tool

A local-first MVP for brand/competitor content collection, Sales Elements diagnosis, evidence review, and content-gap analysis.

## What this repo contains

- React + Vite + TypeScript web app
- FastAPI API
- Playwright same-origin website collector
- Anthropic analysis adapter with `mock` fallback
- Evidence ledger, review queue, Sales Elements record, and gap register
- Docker Compose for PostgreSQL + Redis + API + web
- Claude Code project instructions, subagents, commands, and phased build plan

## Important runtime distinction

Claude Code is used to build and maintain this codebase. The deployed tool uses Playwright for browser collection and the Anthropic API for structured analysis.

## Quick start with Claude Code

```bash
cd content-diagnosis-claude-code-tool
claude
```

Then paste:

```text
Read CLAUDE.md and docs/IMPLEMENTATION_PLAN.md. Inspect the current repository. Start at the first incomplete phase. Do not skip tests or acceptance gates. Use the specialist subagents where appropriate.
```

## Local development

### 1. Environment

```bash
cp .env.example .env
```

For a no-cost local demo, leave:

```text
ANALYSIS_PROVIDER=mock
DATABASE_URL=sqlite:///./content_diagnosis.db
```

### 2. API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload --port 8000
```

### 3. Web

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:5173`.

## Current MVP scope

Implemented/scaffolded:

- Project creation and diagnostic context
- Brand/competitor entities
- Exact source URL registration
- Website collection jobs
- Evidence records
- 17 canonical Sales Elements
- Mock and Anthropic analysis adapters
- Candidate findings and human review states
- Content-gap register
- Dashboard APIs and starter UI

Not treated as complete until Claude Code finishes all acceptance gates:

- Authenticated social-platform collectors
- Meta Ad Library production adapter
- Robust PDF/video transcription
- Multi-user authentication and billing
- Production cloud deployment

## Core workflow

```text
Setup → Exact URLs → Collect → Normalize → Analyze → Review → Approve → Artifact
```
