"""Authentication use cases.

The service owns the unit of work: it never commits (the request dependency does), never imports
FastAPI, and never returns ORM objects to the transport layer.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from sara_api.core.config import Settings
from sara_api.core.errors import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidSession,
    InvalidToken,
    ValidationFailed,
)
from sara_api.core.security import (
    AccessTokenIssuer,
    PasswordHasher,
    ensure_utc,
    hash_refresh_token,
    new_refresh_token,
    utcnow,
)
from sara_api.domain.accounts import (
    PasswordPolicyViolation,
    Role,
    UserStatus,
    normalize_email,
    validate_password,
)
from sara_api.modules.users.models import RefreshToken, User
from sara_api.modules.users.repository import RefreshTokenRepository, UserRepository

logger = logging.getLogger("sara.auth")

# Verified against when the account does not exist, so a missing email costs the same as a wrong
# password. Generated once per process.
_DUMMY_HASH = PasswordHasher().hash("sara-timing-equalizer-not-a-real-password")


@dataclass(frozen=True, slots=True)
class AuthResult:
    user: User
    access_token: str
    expires_in: int
    refresh_token: str


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._users = UserRepository(session)
        self._tokens = RefreshTokenRepository(session)
        self._hasher = PasswordHasher()
        self._issuer = AccessTokenIssuer(
            secret_key=settings.secret_key,
            algorithm=settings.jwt_algorithm,
            issuer=settings.jwt_issuer,
            ttl_minutes=settings.access_token_minutes,
        )

    async def register(
        self,
        *,
        full_name: str,
        email: str,
        password: str,
        phone: str | None,
        user_agent: str | None = None,
        ip: str | None = None,
    ) -> AuthResult:
        normalized = normalize_email(email)
        try:
            validate_password(password, normalized)
        except PasswordPolicyViolation as exc:
            raise ValidationFailed(str(exc)) from exc

        if await self._users.get_by_email(normalized) is not None:
            raise EmailAlreadyRegistered("An account with this email already exists.")

        user = User(
            email=normalized,
            password_hash=self._hasher.hash(password),
            full_name=full_name.strip(),
            phone=phone,
            role=Role.USER.value,
            status=UserStatus.ACTIVE.value,
        )
        await self._users.add(user)
        logger.info("auth.registration.succeeded", extra={"user_id": str(user.id)})
        return await self._issue_session(user, family_id=uuid.uuid4(), user_agent=user_agent, ip=ip)

    async def login(
        self,
        *,
        email: str,
        password: str,
        user_agent: str | None = None,
        ip: str | None = None,
    ) -> AuthResult:
        normalized = normalize_email(email)
        user = await self._users.get_by_email(normalized)

        if user is None:
            self._hasher.verify(password, _DUMMY_HASH)
            logger.warning("auth.login.failed", extra={"reason": "unknown_account"})
            raise InvalidCredentials()

        if not self._hasher.verify(password, user.password_hash):
            logger.warning("auth.login.failed", extra={"reason": "bad_password", "user_id": str(user.id)})
            raise InvalidCredentials()

        if user.status != UserStatus.ACTIVE.value:
            logger.warning("auth.login.failed", extra={"reason": "inactive", "user_id": str(user.id)})
            raise InvalidCredentials()

        user.last_login_at = utcnow()
        logger.info("auth.login.succeeded", extra={"user_id": str(user.id)})
        return await self._issue_session(user, family_id=uuid.uuid4(), user_agent=user_agent, ip=ip)

    async def refresh(
        self,
        raw_token: str | None,
        *,
        user_agent: str | None = None,
        ip: str | None = None,
    ) -> AuthResult:
        if not raw_token:
            raise InvalidSession()

        record = await self._tokens.get_by_hash(hash_refresh_token(raw_token))
        now = utcnow()

        if record is None:
            raise InvalidSession()

        if record.revoked_at is not None:
            # Reuse of a rotated token: assume theft and revoke the whole family. The revocation is
            # committed immediately because the request will end in a 401 and the session dependency
            # rolls back on any raised error. Losing this write would leave the thief's token alive.
            await self._tokens.revoke_family(record.family_id, revoked_at=now)
            await self._session.commit()
            logger.warning(
                "auth.refresh.reuse_detected",
                extra={"user_id": str(record.user_id), "family_id": str(record.family_id)},
            )
            raise InvalidSession("Session has been revoked. Please sign in again.")

        if ensure_utc(record.expires_at) <= now:
            raise InvalidSession("Session has expired. Please sign in again.")

        user = await self._users.get_by_id(record.user_id)
        if user is None or user.status != UserStatus.ACTIVE.value:
            await self._tokens.revoke_family(record.family_id, revoked_at=now)
            await self._session.commit()
            raise InvalidSession()

        new_raw = new_refresh_token()
        new_record = RefreshToken(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash=hash_refresh_token(new_raw),
            family_id=record.family_id,
            issued_at=now,
            expires_at=now + timedelta(days=self._settings.refresh_token_days),
            user_agent=user_agent,
            ip=ip,
        )
        await self._tokens.revoke(record, revoked_at=now, replaced_by=new_record.id)
        await self._tokens.add(new_record)

        access_token = self._issuer.issue(user.id, user.role, now=now)
        logger.info("auth.refresh.rotated", extra={"user_id": str(user.id)})
        return AuthResult(
            user=user,
            access_token=access_token,
            expires_in=self._issuer.ttl_seconds,
            refresh_token=new_raw,
        )

    async def logout(self, raw_token: str | None) -> None:
        if not raw_token:
            return
        record = await self._tokens.get_by_hash(hash_refresh_token(raw_token))
        if record is None or record.revoked_at is not None:
            return
        await self._tokens.revoke_family(record.family_id, revoked_at=utcnow())
        logger.info("auth.logout.succeeded", extra={"user_id": str(record.user_id)})

    async def authenticate(self, access_token: str) -> User:
        claims = self._issuer.decode(access_token)
        user = await self._users.get_by_id(claims.subject)
        if user is None or user.status != UserStatus.ACTIVE.value:
            raise InvalidToken()
        return user

    async def _issue_session(
        self,
        user: User,
        *,
        family_id: UUID,
        user_agent: str | None,
        ip: str | None,
    ) -> AuthResult:
        now = utcnow()
        raw_refresh = new_refresh_token()
        record = RefreshToken(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            family_id=family_id,
            issued_at=now,
            expires_at=now + timedelta(days=self._settings.refresh_token_days),
            user_agent=user_agent[:300] if user_agent else None,
            ip=ip[:64] if ip else None,
        )
        await self._tokens.add(record)
        access_token = self._issuer.issue(user.id, user.role, now=now)
        return AuthResult(
            user=user,
            access_token=access_token,
            expires_in=self._issuer.ttl_seconds,
            refresh_token=raw_refresh,
        )
