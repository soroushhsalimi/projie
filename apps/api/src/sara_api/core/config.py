"""Application configuration.

Every environment-dependent value is read here and nowhere else (AGENTS.md §9.2).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DEV_SECRET = "sara-dev-only-secret-change-me-0123456789abcdef"


class Settings(BaseSettings):
    """12-factor settings, prefixed with ``SARA_`` in the environment."""

    model_config = SettingsConfigDict(
        env_prefix="SARA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "SARA API"
    version: str = "0.1.0"
    environment: Literal["local", "test", "staging", "production"] = "local"

    database_url: str = "sqlite+aiosqlite:///./sara.db"
    auto_create_schema: bool = True

    secret_key: str = DEFAULT_DEV_SECRET
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "sara"
    access_token_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_days: int = Field(default=30, ge=1, le=90)
    refresh_cookie_name: str = "sara_refresh"
    cookie_secure: bool = False

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @model_validator(mode="after")
    def _guard_production(self) -> Settings:
        if self.environment == "production":
            if self.secret_key == DEFAULT_DEV_SECRET or len(self.secret_key) < 32:
                raise ValueError("SARA_SECRET_KEY must be set to a strong unique value in production")
            if not self.cookie_secure:
                raise ValueError("SARA_COOKIE_SECURE must be true in production")
            if self.auto_create_schema:
                raise ValueError("SARA_AUTO_CREATE_SCHEMA must be false in production; run migrations")
        return self

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def refresh_cookie_path(self) -> str:
        return "/api/v1/auth"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton (tests construct their own Settings)."""
    return Settings()
