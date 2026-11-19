"""Request-scoped dependencies: settings, database session, service and principal."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from sara_api.core.config import Settings
from sara_api.core.errors import InvalidToken, OriginNotAllowed
from sara_api.modules.auth.service import AuthService
from sara_api.modules.users.models import User

_bearer = HTTPBearer(auto_error=False)


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    """One request = one transaction; commit on success, rollback on any exception."""
    session_factory = request.app.state.sessionmaker
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


def get_auth_service(
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> AuthService:
    return AuthService(session, settings)


@dataclass(frozen=True, slots=True)
class ClientMeta:
    user_agent: str | None
    ip: str | None


def get_client_meta(request: Request) -> ClientMeta:
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",", 1)[0].strip() if forwarded else (request.client.host if request.client else None)
    return ClientMeta(user_agent=request.headers.get("user-agent"), ip=ip)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    service: AuthService = Depends(get_auth_service),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise InvalidToken()
    return await service.authenticate(credentials.credentials)


async def require_trusted_origin(
    request: Request,
    settings: Settings = Depends(get_app_settings),
) -> None:
    """Cookie-authenticated endpoints reject an untrusted browser Origin (ADR-0005)."""
    origin = request.headers.get("origin")
    if origin is not None and origin not in settings.cors_origins:
        raise OriginNotAllowed()
