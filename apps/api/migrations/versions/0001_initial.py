"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-04

Explicit baseline snapshot of the schema. It intentionally does NOT call
Base.metadata.create_all: a live-metadata baseline would recreate every current
column on a fresh upgrade, which then collides with any future op.add_column
revision. Freezing the tables here lets later revisions add columns incrementally.
A schema-parity test asserts these tables match the ORM exactly.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    "projects",
    "entities",
    "sources",
    "content_items",
    "evidence",
    "assessments",
    "gaps",
    "jobs",
)


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("brand_name", sa.String(), nullable=False),
        sa.Column("market", sa.String(), nullable=False),
        sa.Column("product_or_service", sa.String(), nullable=False),
        sa.Column("target_buying_decision", sa.String(), nullable=False),
        sa.Column("purchase_type", sa.String(), nullable=False),
        sa.Column("primary_segment", sa.String(), nullable=False),
        sa.Column("primary_bottleneck", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
    )

    op.create_table(
        "entities",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("comparable_status", sa.String(), nullable=False),
    )
    op.create_index("ix_entities_project_id", "entities", ["project_id"])

    op.create_table(
        "sources",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("max_items", sa.Integer(), nullable=False),
        sa.Column("discovered_count", sa.Integer(), nullable=False),
        sa.Column("attempted_count", sa.Integer(), nullable=False),
        sa.Column("accessible_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )
    op.create_index("ix_sources_project_id", "sources", ["project_id"])
    op.create_index("ix_sources_entity_id", "sources", ["entity_id"])

    op.create_table(
        "content_items",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("page_type", sa.String(), nullable=False),
        sa.Column("captured_at", sa.String(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
    )
    op.create_index("ix_content_items_project_id", "content_items", ["project_id"])
    op.create_index("ix_content_items_entity_id", "content_items", ["entity_id"])
    op.create_index("ix_content_items_source_id", "content_items", ["source_id"])

    op.create_table(
        "evidence",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("content_item_id", sa.String(), nullable=False),
        sa.Column("verbatim_text", sa.Text(), nullable=False),
        sa.Column("normalized_summary", sa.Text(), nullable=False),
        sa.Column("finding_status", sa.String(), nullable=False),
        sa.Column("confidence", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("review_status", sa.String(), nullable=False),
        sa.Column("reviewer", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.String(), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=False),
    )
    op.create_index("ix_evidence_project_id", "evidence", ["project_id"])
    op.create_index("ix_evidence_entity_id", "evidence", ["entity_id"])
    op.create_index("ix_evidence_source_id", "evidence", ["source_id"])
    op.create_index("ix_evidence_content_item_id", "evidence", ["content_item_id"])

    op.create_table(
        "assessments",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("canonical_element_id", sa.String(), nullable=False),
        sa.Column("canonical_key", sa.String(), nullable=False),
        sa.Column("presence_status", sa.String(), nullable=False),
        sa.Column("computed_score", sa.Float(), nullable=True),
        sa.Column("score_rule_version", sa.String(), nullable=True),
        sa.Column("confidence", sa.String(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("review_status", sa.String(), nullable=False),
    )
    op.create_index("ix_assessments_project_id", "assessments", ["project_id"])
    op.create_index("ix_assessments_entity_id", "assessments", ["entity_id"])

    op.create_table(
        "gaps",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("gap_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("confidence", sa.String(), nullable=False),
        sa.Column("root_cause", sa.String(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=True),
        sa.Column("alternative_explanations", sa.JSON(), nullable=True),
        sa.Column("review_status", sa.String(), nullable=False),
        sa.Column("reviewer", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.String(), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=False),
    )
    op.create_index("ix_gaps_project_id", "gaps", ["project_id"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("job_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
    )
    op.create_index("ix_jobs_project_id", "jobs", ["project_id"])


def downgrade() -> None:
    for table in reversed(_TABLES):
        op.drop_table(table)
