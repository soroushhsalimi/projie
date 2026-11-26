"""add guest visits

Revision ID: b6d1f0a4c932
Revises: f2b9d41c7a68
Create Date: 2026-11-26

Additive only (SPEC-0008 §7). One table per visit: the allowed window plus the actual entry and exit
timestamps; the status column is the authoritative state.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b6d1f0a4c932"
down_revision: str | None = "f2b9d41c7a68"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "guest_visit",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("host_id", sa.Uuid(), nullable=False),
        sa.Column("guest_name", sa.String(length=120), nullable=False),
        sa.Column("purpose", sa.String(length=200), nullable=True),
        sa.Column("allowed_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("allowed_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["host_id"],
            ["user.id"],
            name=op.f("fk_guest_visit_host_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_guest_visit")),
    )
    op.create_index(op.f("ix_guest_visit_host_id"), "guest_visit", ["host_id"])
    op.create_index(op.f("ix_guest_visit_status"), "guest_visit", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_guest_visit_status"), table_name="guest_visit")
    op.drop_index(op.f("ix_guest_visit_host_id"), table_name="guest_visit")
    op.drop_table("guest_visit")
