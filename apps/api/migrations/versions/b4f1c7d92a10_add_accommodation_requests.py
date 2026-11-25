"""add accommodation requests

Revision ID: b4f1c7d92a10
Revises: a1c9f4e77b20
Create Date: 2026-11-25

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b4f1c7d92a10"
down_revision: str | None = "a1c9f4e77b20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "accommodation_request",
        sa.Column("applicant_id", sa.Uuid(), nullable=False),
        sa.Column("dormitory_name", sa.String(length=120), nullable=False),
        sa.Column("room_type", sa.String(length=16), nullable=False),
        sa.Column("desired_move_in", sa.Date(), nullable=False),
        sa.Column("duration_months", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["applicant_id"],
            ["user.id"],
            name=op.f("fk_accommodation_request_applicant_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_accommodation_request")),
    )
    op.create_index(
        op.f("ix_accommodation_request_applicant_id"),
        "accommodation_request",
        ["applicant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_accommodation_request_status"),
        "accommodation_request",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_accommodation_request_status"), table_name="accommodation_request"
    )
    op.drop_index(
        op.f("ix_accommodation_request_applicant_id"), table_name="accommodation_request"
    )
    op.drop_table("accommodation_request")
