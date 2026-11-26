"""Public complaint schemas, separate from the ORM models (AGENTS.md §4.1)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from sara_api.domain.complaints import ComplaintCategory, ComplaintStatus


def _iso_utc(value: datetime) -> str:
    aware = value.replace(tzinfo=UTC) if value.tzinfo is None else value
    return aware.astimezone(UTC).isoformat().replace("+00:00", "Z")


class ComplaintResponseRead(BaseModel):
    id: UUID
    body: str
    responder_name: str
    created_at: datetime

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime) -> str:
        return _iso_utc(value)


class ComplaintSummaryRead(BaseModel):
    id: UUID
    subject: str
    category: ComplaintCategory
    status: ComplaintStatus
    resident_name: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _serialize_timestamps(self, value: datetime) -> str:
        return _iso_utc(value)


class ComplaintDetailRead(ComplaintSummaryRead):
    description: str
    response: ComplaintResponseRead | None


class PageMeta(BaseModel):
    page: int
    per_page: int
    total: int


class ComplaintPageRead(BaseModel):
    items: list[ComplaintSummaryRead]
    meta: PageMeta


class ComplaintStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal[ComplaintStatus.IN_REVIEW]


class ComplaintResponseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: str = Field(min_length=2, max_length=2000)

    @field_validator("body")
    @classmethod
    def _clean_body(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("The initial response must be at least 2 characters long.")
        return cleaned
