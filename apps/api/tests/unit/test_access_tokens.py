"""Unit tests for JWT access tokens (SPEC-0003 FR-2, FR-7)."""

from __future__ import annotations

import uuid
from datetime import timedelta

import jwt
import pytest

from sara_api.core.errors import InvalidToken
from sara_api.core.security import AccessTokenIssuer, utcnow

SECRET = "unit-test-secret-0123456789abcdef0123456789"


def issuer() -> AccessTokenIssuer:
    return AccessTokenIssuer(secret_key=SECRET, ttl_minutes=15, leeway_seconds=0)


def test_round_trip_preserves_claims() -> None:
    subject = uuid.uuid4()
    token = issuer().issue(subject, "manager")
    claims = issuer().decode(token)
    assert claims.subject == subject
    assert claims.role == "manager"
    assert claims.expires_at > claims.issued_at
    assert claims.token_id


def test_rejects_wrong_typ() -> None:
    now = utcnow()
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "role": "user",
            "typ": "refresh",
            "iss": "sara",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        SECRET,
        algorithm="HS256",
    )
    with pytest.raises(InvalidToken):
        issuer().decode(token)


def test_rejects_expired_token() -> None:
    token = issuer().issue(uuid.uuid4(), "user", now=utcnow() - timedelta(minutes=30))
    with pytest.raises(InvalidToken):
        issuer().decode(token)


def test_rejects_token_signed_with_another_secret() -> None:
    other = AccessTokenIssuer(secret_key="another-secret-0123456789abcdef0123456789")
    token = other.issue(uuid.uuid4(), "user")
    with pytest.raises(InvalidToken):
        issuer().decode(token)


def test_rejects_tampered_token() -> None:
    token = issuer().issue(uuid.uuid4(), "user")
    with pytest.raises(InvalidToken):
        issuer().decode(token[:-3] + "abc")
