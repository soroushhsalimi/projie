"""Security primitives: password hashing, access tokens and opaque refresh tokens.

All time-sensitive operations accept an explicit ``now`` so tests never depend on the wall clock
(AGENTS.md §8.3).
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import PwdlibError

from sara_api.core.errors import InvalidToken


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime) -> datetime:
    """SQLite returns naive datetimes; treat stored values as UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class AccessClaims:
    subject: uuid.UUID
    role: str
    issued_at: datetime
    expires_at: datetime
    token_id: str


class PasswordHasher:
    """Argon2id via pwdlib; the algorithm is a property of the library's recommendation."""

    def __init__(self) -> None:
        self._hasher = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return self._hasher.verify(password, password_hash)
        except (PwdlibError, ValueError):
            return False


class AccessTokenIssuer:
    def __init__(
        self,
        *,
        secret_key: str,
        algorithm: str = "HS256",
        issuer: str = "sara",
        ttl_minutes: int = 15,
        leeway_seconds: int = 60,
    ) -> None:
        self._secret = secret_key
        self._algorithm = algorithm
        self._issuer = issuer
        self._ttl = timedelta(minutes=ttl_minutes)
        self._leeway = leeway_seconds

    @property
    def ttl_seconds(self) -> int:
        return int(self._ttl.total_seconds())

    def issue(self, user_id: uuid.UUID, role: str, *, now: datetime | None = None) -> str:
        issued = now or utcnow()
        payload = {
            "sub": str(user_id),
            "role": role,
            "typ": "access",
            "iss": self._issuer,
            "iat": int(issued.timestamp()),
            "exp": int((issued + self._ttl).timestamp()),
            "jti": uuid.uuid4().hex,
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode(self, token: str) -> AccessClaims:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                issuer=self._issuer,
                leeway=self._leeway,
                options={"require": ["exp", "iat", "sub", "iss"]},
            )
        except jwt.PyJWTError as exc:
            raise InvalidToken() from exc

        if payload.get("typ") != "access":
            raise InvalidToken()

        try:
            subject = uuid.UUID(str(payload["sub"]))
            issued_at = datetime.fromtimestamp(int(payload["iat"]), tz=timezone.utc)
            expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc)
            token_id = str(payload.get("jti", ""))
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidToken() from exc

        return AccessClaims(
            subject=subject,
            role=str(payload.get("role", "user")),
            issued_at=issued_at,
            expires_at=expires_at,
            token_id=token_id,
        )


def new_refresh_token() -> str:
    """256 bits of entropy, URL-safe so it can live in a cookie."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
