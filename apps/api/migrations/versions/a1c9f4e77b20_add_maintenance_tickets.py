"""add maintenance tickets

Revision ID: a1c9f4e77b20
Revises: 397e3882bfd3
Create Date: 2026-11-24

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1c9f4e77b20"
down_revision: str | None = "397e3882bfd3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ticket",
        sa.Column("reporter_id", sa.Uuid(), nullable=False),
        sa.Column("subject", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["reporter_id"],
            ["user.id"],
            name=op.f("fk_ticket_reporter_id_user"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ticket")),
    )
    op.create_index(op.f("ix_ticket_reporter_id"), "ticket", ["reporter_id"], unique=False)
    op.create_index(op.f("ix_ticket_status"), "ticket", ["status"], unique=False)

    op.create_table(
        "ticket_message",
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["user.id"],
            name=op.f("fk_ticket_message_author_id_user"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["ticket.id"],
            name=op.f("fk_ticket_message_ticket_id_ticket"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ticket_message")),
    )
    op.create_index(
        op.f("ix_ticket_message_ticket_id"), "ticket_message", ["ticket_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ticket_message_ticket_id"), table_name="ticket_message")
    op.drop_table("ticket_message")
    op.drop_index(op.f("ix_ticket_status"), table_name="ticket")
    op.drop_index(op.f("ix_ticket_reporter_id"), table_name="ticket")
    op.drop_table("ticket")
