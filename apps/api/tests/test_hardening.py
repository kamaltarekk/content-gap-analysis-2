import threading

import pytest

from app.core.config import settings
from app.models.domain import ContentItem, Job, Project, ProjectStatus
from app.services.repository import repo
from app.services.storage import LocalStorage, get_storage
from app.services.tasks import InlineTaskBackend, get_task_backend, run_analysis


# --- storage factory ---------------------------------------------------------------


def test_storage_defaults_to_local() -> None:
    assert isinstance(get_storage(), LocalStorage)


def test_s3_backend_requires_bucket(monkeypatch) -> None:
    monkeypatch.setattr(settings, "storage_backend", "s3")
    monkeypatch.setattr(settings, "s3_bucket", None)
    with pytest.raises(RuntimeError):
        get_storage()


# --- task backend ------------------------------------------------------------------


def test_task_backend_defaults_to_inline() -> None:
    assert isinstance(get_task_backend(), InlineTaskBackend)


def test_inline_backend_runs_function() -> None:
    done = threading.Event()
    InlineTaskBackend().enqueue(lambda: done.set())
    assert done.wait(timeout=2.0)


def _project(status: ProjectStatus) -> Project:
    return repo.add(
        repo.projects,
        Project(
            name="Audit",
            brand_name="Acme",
            market="EG",
            product_or_service="filters",
            target_buying_decision="buy filter",
            purchase_type="considered",
            primary_segment="households",
            status=status,
        ),
    )


def test_run_analysis_job_completes(temp_db) -> None:
    project = _project(ProjectStatus.APPROVED_FOR_ANALYSIS)
    repo.add(
        repo.content_items,
        ContentItem(
            project_id=project.id,
            entity_id="e1",
            source_id="s1",
            url="http://acme.test",
            text="best quality safe",
        ),
    )
    job = repo.add(repo.jobs, Job(project_id=project.id, job_type="analysis"))

    run_analysis(project.id, job.id)

    assert repo.projects.get(project.id).status == ProjectStatus.ANALYZED
    assert repo.jobs.get(job.id).status == "completed"
    assert repo.by_project(repo.assessments, project.id)


# --- auth --------------------------------------------------------------------------


def test_open_by_default(client) -> None:
    assert client.get("/api/projects").status_code == 200


def test_bearer_token_enforced(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "api_auth_token", "s3cret")
    assert client.get("/api/projects").status_code == 401
    assert client.get("/api/projects", headers={"Authorization": "Bearer wrong"}).status_code == 401
    ok = client.get("/api/projects", headers={"Authorization": "Bearer s3cret"})
    assert ok.status_code == 200


# --- observability endpoints -------------------------------------------------------


def test_health_version_readiness_are_open(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "api_auth_token", "s3cret")  # ops endpoints stay open
    assert client.get("/health").json() == {"status": "ok"}
    version = client.get("/version").json()
    assert version["version"] == settings.app_version
    readiness = client.get("/readiness").json()
    assert readiness["status"] == "ready"
    assert readiness["database"] == "ok"
