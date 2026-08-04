"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-04

Baseline migration. The ORM models in app.db.models are the single source of truth
for the schema, so this revision creates and drops all mapped tables from the shared
metadata. Later migrations should use explicit op.* operations for incremental changes.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from app.db.base import Base

# Import models so their tables are registered on Base.metadata.
import app.db.models  # noqa: F401

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
