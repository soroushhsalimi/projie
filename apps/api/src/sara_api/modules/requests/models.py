"""Persistence model for accommodation requests."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from sara_api.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from sara_api.domain.requests import RequestStatus


class AccommodationRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "accommodation_request"

    applicant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dormitory_name: Mapped[str] = mapped_column(String(120), nullable=False)
    room_type: Mapped[str] = mapped_column(String(16), nullable=False)
    desired_move_in: Mapped[date] = mapped_column(Date, nullable=False)
    duration_months: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, default=RequestStatus.SUBMITTED.value, index=True
    )
