# Deployment & Production Hardening

The MVP runs with local defaults (SQLite, in-process jobs, local filesystem, no
auth). Each production concern is behind a configuration switch, so the same code
runs locally and in production.

## Configuration switches

| Concern | Local default | Production | Settings |
|---|---|---|---|
| Database | SQLite file | PostgreSQL | `DATABASE_URL=postgresql+psycopg://…` |
| Async jobs | inline thread | Celery + Redis | `JOB_BACKEND=celery`, `REDIS_URL=redis://…` |
| Storage | local filesystem | S3-compatible | `STORAGE_BACKEND=s3`, `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_REGION`, `S3_PREFIX` |
| Auth | open | bearer token | `API_AUTH_TOKEN=<token>` → `Authorization: Bearer <token>` |

Secrets (`ANTHROPIC_API_KEY`, `API_AUTH_TOKEN`, DB/S3 credentials) come only from
the environment and are never logged.

## Database migrations

The schema is defined by the ORM in `app/db/models.py`; Alembic uses it as the
source of truth. Apply migrations before starting the API:

```bash
cd apps/api
alembic upgrade head
```

The API also runs `create_all()` on startup as a local convenience; controlled
environments should rely on Alembic and can disable that if desired.

## Running with Docker Compose

`docker-compose.yml` provisions PostgreSQL, Redis, the API, a Celery `worker`,
and the web app:

```bash
cp .env.example .env   # fill in secrets
docker compose up --build
```

The API and worker share the same image; the worker runs
`celery -A app.worker.celery_app worker`.

## Observability

Unauthenticated operational endpoints for probes:

- `GET /health` — liveness
- `GET /readiness` — checks the database (`SELECT 1`)
- `GET /version` — app version and environment

Each HTTP request is logged with method, path, status, and duration (no headers
or bodies, so no secrets leak).
