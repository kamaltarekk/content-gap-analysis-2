from __future__ import annotations

import asyncio
import threading
from abc import ABC, abstractmethod
from typing import Callable

from app.core.config import settings
from app.models.domain import ProjectStatus
from app.services.analyzer import get_analysis_provider
from app.services.collector import collect_website
from app.services.repository import repo


def run_collection(project_id: str, job_id: str) -> None:
    """Collect all website sources for a project. Loads state by id so the same
    function works inline (dev thread) or as a Celery task (production)."""
    project = repo.projects.get(project_id)
    job = repo.jobs.get(job_id)
    if project is None or job is None:
        return
    try:
        project.status = ProjectStatus.COLLECTING
        repo.save(project)
        job.status = "running"
        repo.save(job)
        sources = [s for s in repo.by_project(repo.sources, project_id) if s.source_type == "website"]
        for index, source in enumerate(sources, 1):
            asyncio.run(collect_website(source))
            repo.save(source)
            job.progress = int(index / max(1, len(sources)) * 100)
            repo.save(job)
        project.status = ProjectStatus.COLLECTED
        repo.save(project)
        job.status = "completed"
        job.message = "Collection completed"
        repo.save(job)
    except Exception as exc:  # pragma: no cover - defensive; failure path is simple
        project.status = ProjectStatus.FAILED
        repo.save(project)
        job.status = "failed"
        job.message = str(exc)
        repo.save(job)


def run_analysis(project_id: str, job_id: str) -> None:
    project = repo.projects.get(project_id)
    job = repo.jobs.get(job_id)
    if project is None or job is None:
        return
    try:
        project.status = ProjectStatus.ANALYZING
        repo.save(project)
        job.status = "running"
        repo.save(job)
        get_analysis_provider().analyze(project_id)
        project.status = ProjectStatus.ANALYZED
        repo.save(project)
        job.status = "completed"
        job.progress = 100
        repo.save(job)
    except Exception as exc:
        project.status = ProjectStatus.FAILED
        repo.save(project)
        job.status = "failed"
        job.message = str(exc)
        repo.save(job)


class TaskBackend(ABC):
    @abstractmethod
    def enqueue(self, fn: Callable[..., None], *args: object) -> None:
        raise NotImplementedError


class InlineTaskBackend(TaskBackend):
    """In-process execution on a daemon thread (dev/local; the FastAPI process owns it)."""

    def enqueue(self, fn: Callable[..., None], *args: object) -> None:
        threading.Thread(target=fn, args=args, daemon=True).start()


class CeleryTaskBackend(TaskBackend):
    """Dispatches to the Celery worker (production). Celery is imported lazily."""

    def __init__(self) -> None:
        from app.worker import celery_app

        self._app = celery_app

    def enqueue(self, fn: Callable[..., None], *args: object) -> None:
        self._app.send_task(f"tasks.{fn.__name__}", args=list(args))


def get_task_backend() -> TaskBackend:
    if settings.job_backend == "celery":
        return CeleryTaskBackend()
    return InlineTaskBackend()
