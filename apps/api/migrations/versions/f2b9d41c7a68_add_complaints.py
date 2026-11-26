"""add complaints and their initial response

Revision ID: f2b9d41c7a68
Revises: d5c8a1e93f42
Create Date: 2026-11-26

Additive only (SPEC-0007 §7). The unique index on ``complaint_response.complaint_id`` is the
database half of the "one initial response" rule.

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f2b9d41c7a68"
down_revision: str | None = "d5c8a1e93f42"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "complaint",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("resident_id", sa.Uuid(), nullable=False),
        sa.Column("subject", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["resident_id"],
            ["user.id"],
            name=op.f("fk_complaint_resident_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_complaint")),
    )
    op.create_index(op.f("ix_complaint_resident_id"), "complaint", ["resident_id"])
    op.create_index(op.f("ix_complaint_status"), "complaint", ["status"])

    op.create_table(
        "complaint_response",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("complaint_id", sa.Uuid(), nullable=False),
        sa.Column("responder_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["complaint_id"],
            ["complaint.id"],
            name=op.f("fk_complaint_response_complaint_id_complaint"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["responder_id"],
            ["user.id"],
            name=op.f("fk_complaint_response_responder_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_complaint_response")),
    )
    op.create_index(
        op.f("ix_complaint_response_complaint_id"),
        "complaint_response",
        ["complaint_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_complaint_response_complaint_id"), table_name="complaint_response"
    )
    op.drop_table("complaint_response")
    op.drop_index(op.f("ix_complaint_status"), table_name="complaint")
    op.drop_index(op.f("ix_complaint_resident_id"), table_name="complaint")
    op.drop_table("complaint")
