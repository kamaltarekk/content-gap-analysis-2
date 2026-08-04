from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# ORM rows mirror the Pydantic domain models in app.models.domain field-for-field.
# Enum-valued fields are stored as their string values (StrEnum), so columns stay
# migration-safe and the Pydantic layer re-validates them on read. `DOMAIN_OVERRIDES`
# maps a domain field name to its ORM attribute where the two must differ.


class ProjectRow(Base):
    __tablename__ = "projects"
    DOMAIN_OVERRIDES: dict[str, str] = {}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    brand_name: Mapped[str] = mapped_column(String, nullable=False)
    market: Mapped[str] = mapped_column(String, nullable=False)
    product_or_service: Mapped[str] = mapped_column(String, nullable=False)
    target_buying_decision: Mapped[str] = mapped_column(String, nullable=False)
    purchase_type: Mapped[str] = mapped_column(String, nullable=False)
    primary_segment: Mapped[str] = mapped_column(String, nullable=False)
    primary_bottleneck: Mapped[str] = mapped_column(String, nullable=False, default="unknown")
    status: Mapped[str] = mapped_column(String, nullable=False, default="DRAFT")
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)


class EntityRow(Base):
    __tablename__ = "entities"
    DOMAIN_OVERRIDES: dict[str, str] = {}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    comparable_status: Mapped[str] = mapped_column(
        String, nullable=False, default="provisionally_comparable"
    )


class SourceRow(Base):
    __tablename__ = "sources"
    DOMAIN_OVERRIDES: dict[str, str] = {}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="registered")
    max_items: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    discovered_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accessible_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class ContentItemRow(Base):
    __tablename__ = "content_items"
    # `metadata` is reserved on the declarative Base, so store it under a distinct attr.
    DOMAIN_OVERRIDES: dict[str, str] = {"metadata": "content_metadata"}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    source_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False, default="")
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    page_type: Mapped[str] = mapped_column(String, nullable=False, default="unknown")
    captured_at: Mapped[str] = mapped_column(String, nullable=False)
    content_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)


class EvidenceRow(Base):
    __tablename__ = "evidence"
    DOMAIN_OVERRIDES: dict[str, str] = {}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    source_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    content_item_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    verbatim_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_summary: Mapped[str] = mapped_column(Text, nullable=False)
    finding_status: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False, default="unclassified")
    review_status: Mapped[str] = mapped_column(String, nullable=False, default="pending_review")
    reviewer: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewed_at: Mapped[str | None] = mapped_column(String, nullable=True)
    review_note: Mapped[str] = mapped_column(Text, nullable=False, default="")


class AssessmentRow(Base):
    __tablename__ = "assessments"
    DOMAIN_OVERRIDES: dict[str, str] = {}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    canonical_element_id: Mapped[str] = mapped_column(String, nullable=False)
    canonical_key: Mapped[str] = mapped_column(String, nullable=False)
    presence_status: Mapped[str] = mapped_column(String, nullable=False, default="unknown")
    computed_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_rule_version: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[str] = mapped_column(String, nullable=False, default="low")
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    review_status: Mapped[str] = mapped_column(String, nullable=False, default="pending_review")


class GapRow(Base):
    __tablename__ = "gaps"
    DOMAIN_OVERRIDES: dict[str, str] = {}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    gap_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="candidate")
    severity: Mapped[str] = mapped_column(String, nullable=False, default="medium")
    confidence: Mapped[str] = mapped_column(String, nullable=False, default="low")
    root_cause: Mapped[str] = mapped_column(String, nullable=False, default="unknown")
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    alternative_explanations: Mapped[list[str]] = mapped_column(JSON, default=list)
    review_status: Mapped[str] = mapped_column(String, nullable=False, default="pending_review")


class JobRow(Base):
    __tablename__ = "jobs"
    DOMAIN_OVERRIDES: dict[str, str] = {}

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    job_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="queued")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
