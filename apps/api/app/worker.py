"""Celery worker entrypoint (production).

This module is imported only when JOB_BACKEND=celery, so Celery is a
production-only dependency. Run with:

    celery -A app.worker.celery_app worker --loglevel=info
"""
from __future__ import annotations

from celery import Celery

from app.core.config import settings
from app.services import tasks

_broker = settings.redis_url or "redis://localhost:6379/0"
celery_app = Celery("content_diagnosis", broker=_broker, backend=_broker)


@celery_app.task(name="tasks.run_collection")
def run_collection(project_id: str, job_id: str) -> None:
    tasks.run_collection(project_id, job_id)


@celery_app.task(name="tasks.run_analysis")
def run_analysis(project_id: str, job_id: str) -> None:
    tasks.run_analysis(project_id, job_id)
