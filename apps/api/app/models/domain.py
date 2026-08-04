from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectStatus(StrEnum):
    DRAFT = "DRAFT"
    READY_FOR_COLLECTION = "READY_FOR_COLLECTION"
    COLLECTING = "COLLECTING"
    COLLECTED = "COLLECTED"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVED_FOR_ANALYSIS = "APPROVED_FOR_ANALYSIS"
    ANALYZING = "ANALYZING"
    ANALYZED = "ANALYZED"
    READY_FOR_FINAL_REVIEW = "READY_FOR_FINAL_REVIEW"
    APPROVED = "APPROVED"
    FAILED = "FAILED"


class Bottleneck(StrEnum):
    UNKNOWN = "unknown"
    ATTENTION = "attention"
    DESIRE = "desire"
    PERSUASION = "persuasion"
    FRICTION = "friction"


class EntityType(StrEnum):
    BRAND = "brand"
    COMPETITOR = "competitor"


class SourceType(StrEnum):
    WEBSITE = "website"
    SOCIAL = "social"
    AD_LIBRARY = "ad_library"
    REVIEW = "review"
    UPLOAD = "upload"


class SourceStatus(StrEnum):
    REGISTERED = "registered"
    COLLECTING = "collecting"
    COLLECTED = "collected"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    FAILED = "failed"


class ReviewStatus(StrEnum):
    PENDING = "pending_review"
    APPROVED = "approved"
    EDITED_APPROVED = "edited_and_approved"
    REJECTED = "rejected"
    HYPOTHESIS = "hypothesis"
    CONFLICT = "conflict"


class PresenceStatus(StrEnum):
    PRESENT = "present"
    PARTIAL = "partial"
    ABSENT_WITHIN_SAMPLE = "absent_within_sample"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    brand_name: str
    market: str
    product_or_service: str
    target_buying_decision: str
    purchase_type: str
    primary_segment: str
    primary_bottleneck: Bottleneck = Bottleneck.UNKNOWN
    status: ProjectStatus = ProjectStatus.DRAFT
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class Entity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    name: str
    entity_type: EntityType
    comparable_status: str = "provisionally_comparable"


class Source(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    entity_id: str
    source_type: SourceType
    url: HttpUrl
    status: SourceStatus = SourceStatus.REGISTERED
    max_items: int = 20
    discovered_count: int = 0
    attempted_count: int = 0
    accessible_count: int = 0
    failed_count: int = 0
    created_at: str = Field(default_factory=now_iso)


class ContentItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    entity_id: str
    source_id: str
    url: str
    title: str = ""
    text: str = ""
    page_type: str = "unknown"
    captured_at: str = Field(default_factory=now_iso)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    entity_id: str
    source_id: str
    content_item_id: str
    verbatim_text: str
    normalized_summary: str
    finding_status: str
    confidence: str
    review_status: ReviewStatus = ReviewStatus.PENDING


class SalesElementAssessment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    entity_id: str
    canonical_element_id: str
    canonical_key: str
    presence_status: PresenceStatus = PresenceStatus.UNKNOWN
    computed_score: float | None = None
    score_rule_version: str | None = None
    confidence: str = "low"
    evidence_ids: list[str] = Field(default_factory=list)
    recommendation: str = ""
    review_status: ReviewStatus = ReviewStatus.PENDING


class Gap(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    title: str
    gap_type: str
    status: str = "candidate"
    severity: str = "medium"
    confidence: str = "low"
    root_cause: str = "unknown"
    evidence_ids: list[str] = Field(default_factory=list)
    alternative_explanations: list[str] = Field(default_factory=list)
    review_status: ReviewStatus = ReviewStatus.PENDING


class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    job_type: str
    status: str = "queued"
    progress: int = 0
    message: str = ""
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)
