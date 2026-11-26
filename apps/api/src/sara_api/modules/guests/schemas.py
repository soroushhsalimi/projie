"""Public guest-visit schemas, separate from the ORM models (AGENTS.md §4.1)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator

from sara_api.domain.guests import GuestStatus


def _iso_utc(value: datetime) -> str:
    aware = value.replace(tzinfo=UTC) if value.tzinfo is None else value
    return aware.astimezone(UTC).isoformat().replace("+00:00", "Z")


class GuestVisitRead(BaseModel):
    id: UUID
    guest_name: str
    host_name: str
    purpose: str | None
    status: GuestStatus
    allowed_from: datetime
    allowed_until: datetime
    checked_in_at: datetime | None
    checked_out_at: datetime | None
    overdue: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer(
        "allowed_from",
        "allowed_until",
        "checked_in_at",
        "checked_out_at",
        "created_at",
        "updated_at",
    )
    def _serialize_timestamps(self, value: datetime | None) -> str | None:
        return None if value is None else _iso_utc(value)


class PageMeta(BaseModel):
    page: int
    per_page: int
    total: int


class GuestVisitPageRead(BaseModel):
    items: list[GuestVisitRead]
    meta: PageMeta


class GuestVisitCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    guest_name: str = Field(min_length=2, max_length=120)
    host_email: EmailStr
    purpose: str | None = Field(default=None, max_length=200)
    allowed_from: datetime
    allowed_until: datetime

    @field_validator("guest_name")
    @classmethod
    def _clean_guest_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("The guest name must be at least 2 characters long.")
        return cleaned

    @field_validator("purpose")
    @classmethod
    def _clean_purpose(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("allowed_from", "allowed_until")
    @classmethod
    def _require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timestamps must include a timezone offset.")
        return value.astimezone(UTC)
