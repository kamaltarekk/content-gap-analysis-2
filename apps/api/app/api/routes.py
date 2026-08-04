from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.models.domain import (
    Entity,
    Evidence,
    Job,
    Project,
    ProjectStatus,
    ReviewStatus,
    Source,
    now_iso,
)
from app.schemas.requests import (
    EntityCreate,
    ProjectCreate,
    ProjectSetupUpdate,
    ReviewDecision,
    SourceCreate,
    TransitionRequest,
)
from app.services.analyzer import get_analysis_provider
from app.services.collector import UnsafeUrlError, collect_website, validate_public_url
from app.services.evidence import extract_candidate_evidence
from app.services.repository import repo
from app.services.setup import is_setup_conditional, missing_setup_fields, setup_status
from app.services.state_machine import can_transition

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/projects", response_model=Project, status_code=201)
def create_project(payload: ProjectCreate) -> Project:
    project = Project(**payload.model_dump())
    return repo.add(repo.projects, project)


@router.get("/projects", response_model=list[Project])
def list_projects() -> list[Project]:
    return list(repo.projects.values())


@router.get("/projects/{project_id}", response_model=Project)
def get_project(project_id: str) -> Project:
    project = repo.projects.get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.patch("/projects/{project_id}", response_model=Project)
def update_project_setup(project_id: str, payload: ProjectSetupUpdate) -> Project:
    project = repo.projects.get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if project.status != ProjectStatus.DRAFT:
        raise HTTPException(409, "Setup can only be edited while the project is DRAFT")
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return project
    updated = project.model_copy(update={**updates, "updated_at": now_iso()})
    return repo.save(updated)


@router.get("/projects/{project_id}/setup")
def get_setup(project_id: str) -> dict:
    project = repo.projects.get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return setup_status(project)


@router.post("/projects/{project_id}/submit-setup")
def submit_setup(project_id: str) -> dict:
    project = repo.projects.get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    missing = missing_setup_fields(project)
    if missing:
        raise HTTPException(400, {"message": "Required setup fields are missing", "missing": missing})
    if not can_transition(project.status, ProjectStatus.READY_FOR_COLLECTION):
        raise HTTPException(409, f"Cannot submit setup from {project.status}")
    updated = project.model_copy(
        update={"status": ProjectStatus.READY_FOR_COLLECTION, "updated_at": now_iso()}
    )
    repo.save(updated)
    # Unknown bottleneck is allowed; the project proceeds but stays flagged conditional.
    return {"project": updated, "conditional": is_setup_conditional(updated)}


@router.post("/projects/{project_id}/transition", response_model=Project)
def transition_project(project_id: str, payload: TransitionRequest) -> Project:
    project = repo.projects.get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if not can_transition(project.status, payload.target):
        raise HTTPException(409, f"Invalid transition from {project.status} to {payload.target}")
    updated = project.model_copy(update={"status": payload.target, "updated_at": now_iso()})
    return repo.save(updated)


@router.post("/projects/{project_id}/entities", response_model=Entity, status_code=201)
def create_entity(project_id: str, payload: EntityCreate) -> Entity:
    if project_id not in repo.projects:
        raise HTTPException(404, "Project not found")
    entity = Entity(project_id=project_id, **payload.model_dump())
    return repo.add(repo.entities, entity)


@router.get("/projects/{project_id}/entities", response_model=list[Entity])
def list_entities(project_id: str) -> list[Entity]:
    return repo.by_project(repo.entities, project_id)


@router.post("/projects/{project_id}/sources", response_model=Source, status_code=201)
def create_source(project_id: str, payload: SourceCreate) -> Source:
    if project_id not in repo.projects:
        raise HTTPException(404, "Project not found")
    entity = repo.entities.get(payload.entity_id)
    if not entity or entity.project_id != project_id:
        raise HTTPException(400, "Entity does not belong to project")
    try:
        validate_public_url(str(payload.url))
    except UnsafeUrlError as exc:
        raise HTTPException(400, str(exc)) from exc
    source = Source(project_id=project_id, **payload.model_dump())
    return repo.add(repo.sources, source)


@router.get("/projects/{project_id}/sources", response_model=list[Source])
def list_sources(project_id: str) -> list[Source]:
    return repo.by_project(repo.sources, project_id)


async def _collect_job(job: Job, project: Project) -> None:
    try:
        project.status = ProjectStatus.COLLECTING
        repo.save(project)
        job.status = "running"
        repo.save(job)
        sources = repo.by_project(repo.sources, project.id)
        website_sources = [s for s in sources if s.source_type == "website"]
        for index, source in enumerate(website_sources, 1):
            await collect_website(source)
            repo.save(source)
            job.progress = int(index / max(1, len(website_sources)) * 100)
            repo.save(job)
        project.status = ProjectStatus.COLLECTED
        repo.save(project)
        job.status = "completed"
        job.message = "Collection completed"
        repo.save(job)
    except Exception as exc:
        project.status = ProjectStatus.FAILED
        repo.save(project)
        job.status = "failed"
        job.message = str(exc)
        repo.save(job)


def _run_collect(job: Job, project: Project) -> None:
    asyncio.run(_collect_job(job, project))


@router.post("/projects/{project_id}/collect", response_model=Job, status_code=202)
def start_collection(project_id: str, background_tasks: BackgroundTasks) -> Job:
    project = repo.projects.get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if project.status == ProjectStatus.DRAFT:
        project.status = ProjectStatus.READY_FOR_COLLECTION
        repo.save(project)
    if project.status != ProjectStatus.READY_FOR_COLLECTION:
        raise HTTPException(409, f"Collection cannot start from {project.status}")
    if not repo.by_project(repo.sources, project_id):
        raise HTTPException(400, "Register at least one source")
    job = Job(project_id=project_id, job_type="collection")
    repo.add(repo.jobs, job)
    background_tasks.add_task(_run_collect, job, project)
    return job


@router.post("/projects/{project_id}/prepare-review", response_model=Project)
def prepare_review(project_id: str) -> Project:
    project = repo.projects.get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if not can_transition(project.status, ProjectStatus.READY_FOR_REVIEW):
        raise HTTPException(409, f"Cannot prepare review from {project.status}")
    # Populate the review queue with candidate evidence (all pending_review).
    extract_candidate_evidence(project_id)
    project.status = ProjectStatus.READY_FOR_REVIEW
    repo.save(project)
    return project


@router.get("/projects/{project_id}/review-queue", response_model=list[Evidence])
def review_queue(project_id: str, review_status: str | None = None) -> list[Evidence]:
    project = repo.projects.get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    items = repo.by_project(repo.evidence, project_id)
    if review_status:
        items = [item for item in items if item.review_status == review_status]
    return items


@router.post("/projects/{project_id}/analyze", response_model=Job, status_code=202)
def analyze(project_id: str, background_tasks: BackgroundTasks) -> Job:
    project = repo.projects.get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if project.status == ProjectStatus.READY_FOR_REVIEW:
        project.status = ProjectStatus.APPROVED_FOR_ANALYSIS
        repo.save(project)
    if project.status != ProjectStatus.APPROVED_FOR_ANALYSIS:
        raise HTTPException(409, f"Analysis cannot start from {project.status}")
    job = Job(project_id=project_id, job_type="analysis")
    repo.add(repo.jobs, job)

    def run() -> None:
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

    background_tasks.add_task(run)
    return job


@router.get("/jobs/{job_id}", response_model=Job)
def get_job(job_id: str) -> Job:
    job = repo.jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/projects/{project_id}/dashboard")
def dashboard(project_id: str) -> dict:
    project = repo.projects.get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return {
        "project": project,
        "entities": repo.by_project(repo.entities, project_id),
        "sources": repo.by_project(repo.sources, project_id),
        "content_items": repo.by_project(repo.content_items, project_id),
        "evidence": repo.by_project(repo.evidence, project_id),
        "sales_elements": repo.by_project(repo.assessments, project_id),
        "gaps": repo.by_project(repo.gaps, project_id),
        "jobs": repo.by_project(repo.jobs, project_id),
    }


@router.post("/evidence/{evidence_id}/review", response_model=Evidence)
def review_evidence(evidence_id: str, decision: ReviewDecision) -> Evidence:
    evidence = repo.evidence.get(evidence_id)
    if not evidence:
        raise HTTPException(404, "Evidence not found")

    final_status = decision.status
    updates: dict = {}
    if decision.edited_value:
        updates["normalized_summary"] = decision.edited_value
        # An edit that is accepted is recorded as edited_and_approved, never a silent
        # approval of the original candidate.
        if decision.status == ReviewStatus.APPROVED:
            final_status = ReviewStatus.EDITED_APPROVED

    # Every recorded decision captures who decided and when (domain rules 4 and 14).
    updates.update(
        review_status=final_status,
        reviewer=decision.reviewer,
        reviewed_at=now_iso(),
        review_note=decision.note,
    )
    updated = evidence.model_copy(update=updates)
    return repo.save(updated)
