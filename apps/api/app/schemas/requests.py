from pydantic import BaseModel, Field, HttpUrl

from app.models.domain import EntityType, ReviewStatus, SourceType


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2)
    brand_name: str = Field(min_length=2)
    market: str
    product_or_service: str
    target_buying_decision: str
    purchase_type: str
    primary_segment: str
    primary_bottleneck: str = "unknown"


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
