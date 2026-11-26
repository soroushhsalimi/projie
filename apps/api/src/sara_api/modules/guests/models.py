"""Persistence model for guest visits."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from sara_api.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from sara_api.domain.guests import GuestStatus


class GuestVisit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "guest_visit"

    host_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    guest_name: Mapped[str] = mapped_column(String(120), nullable=False)
    purpose: Mapped[str | None] = mapped_column(String(200), nullable=True)
    allowed_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    allowed_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, default=GuestStatus.EXPECTED.value, index=True
    )
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
