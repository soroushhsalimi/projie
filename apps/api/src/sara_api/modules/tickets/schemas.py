"""Public ticket schemas, separate from the ORM models (AGENTS.md §4.1)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from sara_api.domain.accounts import Role
from sara_api.domain.tickets import TicketCategory, TicketStatus


def _iso_utc(value: datetime) -> str:
    aware = value.replace(tzinfo=UTC) if value.tzinfo is None else value
    return aware.astimezone(UTC).isoformat().replace("+00:00", "Z")


class TicketMessageRead(BaseModel):
    id: UUID
    author_name: str
    author_role: Role
    body: str
    created_at: datetime

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime) -> str:
        return _iso_utc(value)


class TicketSummaryRead(BaseModel):
    id: UUID
    subject: str
    category: TicketCategory
    status: TicketStatus
    reporter_name: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _serialize_timestamps(self, value: datetime) -> str:
        return _iso_utc(value)


class TicketDetailRead(TicketSummaryRead):
    description: str
    messages: list[TicketMessageRead]


class PageMeta(BaseModel):
    page: int
    per_page: int
    total: int


class TicketPageRead(BaseModel):
    items: list[TicketSummaryRead]
    meta: PageMeta


class TicketReplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: str = Field(min_length=2, max_length=2000)

    @field_validator("body")
    @classmethod
    def _clean_body(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Reply must be at least 2 characters long.")
        return cleaned


class TicketStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal[TicketStatus.UNDER_REVIEW, TicketStatus.RESOLVED]
