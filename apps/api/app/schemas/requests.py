from pydantic import BaseModel, Field, HttpUrl

from app.models.domain import Bottleneck, EntityType, ProjectStatus, ReviewStatus, SourceType


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2)
    brand_name: str = Field(min_length=2)
    market: str = Field(min_length=1)
    product_or_service: str = Field(min_length=1)
    target_buying_decision: str = Field(min_length=1)
    purchase_type: str = Field(min_length=1)
    primary_segment: str = Field(min_length=1)
    primary_bottleneck: Bottleneck = Bottleneck.UNKNOWN


class ProjectSetupUpdate(BaseModel):
    """Partial update of guided-setup fields (editable while the project is DRAFT)."""

    model_config = {"extra": "forbid"}

    name: str | None = Field(default=None, min_length=2)
    brand_name: str | None = Field(default=None, min_length=2)
    market: str | None = Field(default=None, min_length=1)
    product_or_service: str | None = Field(default=None, min_length=1)
    target_buying_decision: str | None = Field(default=None, min_length=1)
    purchase_type: str | None = Field(default=None, min_length=1)
    primary_segment: str | None = Field(default=None, min_length=1)
    primary_bottleneck: Bottleneck | None = None


class TransitionRequest(BaseModel):
    target: ProjectStatus


class EntityCreate(BaseModel):
    name: str
    entity_type: EntityType


class SourceCreate(BaseModel):
    entity_id: str
    source_type: SourceType
    url: HttpUrl
    max_items: int = Field(default=20, ge=1, le=500)


class ReviewDecision(BaseModel):
    status: ReviewStatus
    edited_value: str | None = None
    reviewer: str = "user"
