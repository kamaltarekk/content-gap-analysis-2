from __future__ import annotations

from collections import defaultdict
from threading import Lock
from typing import TypeVar

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

T = TypeVar("T")


class InMemoryRepository:
    """MVP repository. Replace with SQLAlchemy in Phase 1."""

    def __init__(self) -> None:
        self._lock = Lock()
        self.projects: dict[str, Project] = {}
        self.entities: dict[str, Entity] = {}
        self.sources: dict[str, Source] = {}
        self.content_items: dict[str, ContentItem] = {}
        self.evidence: dict[str, Evidence] = {}
        self.assessments: dict[str, SalesElementAssessment] = {}
        self.gaps: dict[str, Gap] = {}
        self.jobs: dict[str, Job] = {}

    def add(self, collection: dict[str, T], item: T) -> T:
        with self._lock:
            collection[getattr(item, "id")] = item
        return item

    @staticmethod
    def by_project(collection: dict[str, T], project_id: str) -> list[T]:
        return [x for x in collection.values() if getattr(x, "project_id", None) == project_id]


repo = InMemoryRepository()
