"""Public user schemas.

Separate from ORM models on purpose (AGENTS.md §4.1): a model change must not silently change the
public contract, and the password hash can never be serialized by accident.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer

from sara_api.domain.accounts import Role, UserStatus


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    phone: str | None = None
    role: Role
    status: UserStatus
    created_at: datetime

    @field_serializer("created_at")
    def _serialize_created_at(self, value: datetime) -> str:
        """SQLite returns naive datetimes; the API always emits an explicit UTC marker."""
        aware = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
        return aware.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    role: Role


class ProfileUpdate(BaseModel):
    """Reserved for F-0106; defined here only to freeze the public profile shape."""

    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=3, max_length=120)
    phone: str | None = Field(default=None, max_length=20)
