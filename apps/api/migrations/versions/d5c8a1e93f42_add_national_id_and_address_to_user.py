"""add national id and address to user

Revision ID: d5c8a1e93f42
Revises: b4f1c7d92a10
Create Date: 2026-11-25

The columns stay nullable so accounts created before this revision keep working; registration
(SPEC-0002 v1.1.0) always writes both. The unique index makes the national ID an identity key.

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d5c8a1e93f42"
down_revision: str | None = "b4f1c7d92a10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("user", sa.Column("national_id", sa.String(length=10), nullable=True))
    op.add_column("user", sa.Column("address", sa.Text(), nullable=True))
    op.create_index(
        op.f("ix_user_national_id"), "user", ["national_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_national_id"), table_name="user")
    op.drop_column("user", "address")
    op.drop_column("user", "national_id")
