"""Public accommodation-request schemas, separate from the ORM models (AGENTS.md §4.1)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from sara_api.domain.requests import RequestStatus, RoomType


def _iso_utc(value: datetime) -> str:
    aware = value.replace(tzinfo=UTC) if value.tzinfo is None else value
    return aware.astimezone(UTC).isoformat().replace("+00:00", "Z")


class RequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dormitory_name: str = Field(min_length=2, max_length=120)
    room_type: RoomType
    desired_move_in: date
    duration_months: int = Field(ge=1, le=24)
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("dormitory_name")
    @classmethod
    def _clean_dormitory(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Dormitory name must be at least 2 characters long.")
        return cleaned

    @field_validator("note")
    @classmethod
    def _clean_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class AccommodationRequestRead(BaseModel):
    id: UUID
    dormitory_name: str
    room_type: RoomType
    desired_move_in: date
    duration_months: int
    note: str | None
    status: RequestStatus
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _serialize_timestamps(self, value: datetime) -> str:
        return _iso_utc(value)


class PageMeta(BaseModel):
    page: int
    per_page: int
    total: int


class RequestPageRead(BaseModel):
    items: list[AccommodationRequestRead]
    meta: PageMeta
