from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

from app.db import models as orm
from app.db.session import SessionLocal
from app.models.domain import (
    ContentItem,
    Entity,
    Evidence,
    Gap,
    Job,
    Project,
    SalesElementAssessment,
    Source,
)

D = TypeVar("D", bound=BaseModel)


def _to_orm(item: BaseModel, orm_cls: type) -> object:
    overrides = getattr(orm_cls, "DOMAIN_OVERRIDES", {})
    data = item.model_dump(mode="json")
    return orm_cls(**{overrides.get(k, k): v for k, v in data.items()})


def _to_domain(row: object, domain_cls: type[D]) -> D:
    overrides = getattr(type(row), "DOMAIN_OVERRIDES", {})
    values = {field: getattr(row, overrides.get(field, field)) for field in domain_cls.model_fields}
    return domain_cls.model_validate(values)


class Collection(Generic[D]):
    """Table-scoped accessor that preserves the previous in-memory repository surface.

    Supports ``get(id)``, ``values()`` and ``id in collection`` so existing route and
    service code keeps working while data is persisted through SQLAlchemy.
    """

    def __init__(self, repo: "SqlAlchemyRepository", domain_cls: type[D], orm_cls: type) -> None:
        self._repo = repo
        self.domain_cls = domain_cls
        self.orm_cls = orm_cls

    def get(self, item_id: str) -> D | None:
        with SessionLocal() as session:
            row = session.get(self.orm_cls, item_id)
            return _to_domain(row, self.domain_cls) if row is not None else None

    def values(self) -> list[D]:
        with SessionLocal() as session:
            rows = session.query(self.orm_cls).all()
            return [_to_domain(row, self.domain_cls) for row in rows]

    def __contains__(self, item_id: str) -> bool:
        return self.get(item_id) is not None


class SqlAlchemyRepository:
    """SQLAlchemy-backed persistence with the repository surface used across the app.

    Domain objects are Pydantic models; reads return freshly validated detached copies,
    so callers never hold ORM/session state across threads. Mutations are persisted with
    an explicit ``save`` (upsert) call.
    """

    def __init__(self) -> None:
        self.projects: Collection[Project] = Collection(self, Project, orm.ProjectRow)
        self.entities: Collection[Entity] = Collection(self, Entity, orm.EntityRow)
        self.sources: Collection[Source] = Collection(self, Source, orm.SourceRow)
        self.content_items: Collection[ContentItem] = Collection(self, ContentItem, orm.ContentItemRow)
        self.evidence: Collection[Evidence] = Collection(self, Evidence, orm.EvidenceRow)
        self.assessments: Collection[SalesElementAssessment] = Collection(
            self, SalesElementAssessment, orm.AssessmentRow
        )
        self.gaps: Collection[Gap] = Collection(self, Gap, orm.GapRow)
        self.jobs: Collection[Job] = Collection(self, Job, orm.JobRow)

        self._by_type: dict[type[BaseModel], Collection] = {
            c.domain_cls: c
            for c in (
                self.projects,
                self.entities,
                self.sources,
                self.content_items,
                self.evidence,
                self.assessments,
                self.gaps,
                self.jobs,
            )
        }

    def add(self, collection: Collection[D], item: D) -> D:
        with SessionLocal() as session:
            session.add(_to_orm(item, collection.orm_cls))
            session.commit()
        return item

    def save(self, item: D) -> D:
        """Persist an updated domain object (insert or update by id)."""
        collection = self._by_type[type(item)]
        with SessionLocal() as session:
            session.merge(_to_orm(item, collection.orm_cls))
            session.commit()
        return item

    @staticmethod
    def by_project(collection: Collection[D], project_id: str) -> list[D]:
        with SessionLocal() as session:
            rows = (
                session.query(collection.orm_cls)
                .filter_by(project_id=project_id)
                .all()
            )
            return [_to_domain(row, collection.domain_cls) for row in rows]


repo = SqlAlchemyRepository()
