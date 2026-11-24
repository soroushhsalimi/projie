"""Persistence models for maintenance tickets and their message thread."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from sara_api.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from sara_api.domain.tickets import TicketCategory, TicketStatus


class Ticket(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ticket"

    reporter_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(32), nullable=False, default=TicketCategory.GENERAL.value
    )
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, default=TicketStatus.OPEN.value, index=True
    )


class TicketMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ticket_message"

    ticket_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ticket.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
