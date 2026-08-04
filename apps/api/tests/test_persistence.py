from app.db import session
from app.models.domain import (
    Entity,
    EntityType,
    Project,
    ProjectStatus,
    Source,
    SourceStatus,
    SourceType,
)
from app.services.repository import repo


def _make_project() -> Project:
    return Project(
        name="Acme Audit",
        brand_name="Acme",
        market="EG",
        product_or_service="Water filters",
        target_buying_decision="Buy a home water filter",
        purchase_type="considered",
        primary_segment="households",
    )


def test_crud_survives_process_restart(temp_db) -> None:
    project = repo.add(repo.projects, _make_project())
    entity = repo.add(
        repo.entities,
        Entity(project_id=project.id, name="Acme", entity_type=EntityType.BRAND),
    )
    repo.add(
        repo.sources,
        Source(
            project_id=project.id,
            entity_id=entity.id,
            source_type=SourceType.WEBSITE,
            url="https://example.com",
        ),
    )

    # Simulate a process restart: dispose the engine and rebind to the same file DB.
    session.configure(temp_db)

    reloaded = repo.projects.get(project.id)
    assert reloaded is not None
    assert reloaded.brand_name == "Acme"
    assert reloaded.status == ProjectStatus.DRAFT

    entities = repo.by_project(repo.entities, project.id)
    sources = repo.by_project(repo.sources, project.id)
    assert [e.id for e in entities] == [entity.id]
    assert len(sources) == 1
    assert sources[0].source_type == SourceType.WEBSITE
    assert sources[0].status == SourceStatus.REGISTERED


def test_save_updates_persist_across_restart(temp_db) -> None:
    project = repo.add(repo.projects, _make_project())

    updated = repo.projects.get(project.id)
    assert updated is not None
    updated.status = ProjectStatus.READY_FOR_COLLECTION
    repo.save(updated)

    session.configure(temp_db)

    after = repo.projects.get(project.id)
    assert after is not None
    assert after.status == ProjectStatus.READY_FOR_COLLECTION


def test_membership_and_listing(temp_db) -> None:
    assert repo.projects.get("missing") is None
    assert "missing" not in repo.projects

    project = repo.add(repo.projects, _make_project())
    assert project.id in repo.projects
    assert [p.id for p in repo.projects.values()] == [project.id]
