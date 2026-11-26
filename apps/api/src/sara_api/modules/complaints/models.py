"""Persistence models for complaints and their single initial response."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from sara_api.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from sara_api.domain.complaints import ComplaintCategory, ComplaintStatus


class Complaint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "complaint"

    resident_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ComplaintCategory.OTHER.value
    )
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, default=ComplaintStatus.SUBMITTED.value, index=True
    )


class ComplaintResponse(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The one initial response a manager records; uniqueness is enforced per complaint."""

    __tablename__ = "complaint_response"

    complaint_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("complaint.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    responder_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
