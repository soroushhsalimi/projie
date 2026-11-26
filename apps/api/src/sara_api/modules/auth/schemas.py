"""Auth request/response schemas and their validation rules."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from sara_api.domain.accounts import (
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    PasswordPolicyViolation,
    normalize_mobile,
    normalize_national_id,
    validate_password,
)
from sara_api.modules.users.schemas import UserRead


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    full_name: str = Field(min_length=3, max_length=120)
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    national_id: str = Field(max_length=20)
    phone: str = Field(max_length=20)
    address: str = Field(min_length=5, max_length=500)

    @field_validator("full_name")
    @classmethod
    def _clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 3:
            raise ValueError("Full name must be at least 3 characters long.")
        return cleaned

    @field_validator("national_id")
    @classmethod
    def _clean_national_id(cls, value: str) -> str:
        return normalize_national_id(value)

    @field_validator("phone")
    @classmethod
    def _clean_phone(cls, value: str) -> str:
        return normalize_mobile(value)

    @field_validator("address")
    @classmethod
    def _clean_address(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 5:
            raise ValueError("Address must be at least 5 characters long.")
        return cleaned

    @model_validator(mode="after")
    def _enforce_password_policy(self) -> RegisterRequest:
        try:
            validate_password(self.password, str(self.email))
        except PasswordPolicyViolation as exc:
            raise ValueError(str(exc)) from exc
        return self


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserRead
