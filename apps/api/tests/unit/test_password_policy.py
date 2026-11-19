"""Unit tests for the pure password policy (SPEC-0002 FR-3)."""

from __future__ import annotations

import pytest

from sara_api.domain.accounts import PasswordPolicyViolation, normalize_email, validate_password


def test_normalize_email_is_trimmed_and_casefolded() -> None:
    assert normalize_email("  Ali@Example.COM ") == "ali@example.com"


@pytest.mark.parametrize(
    "password",
    [
        "short",
        "123456789",
        "        ",
        "aaaaaaaaaaaa",
        "password123",
        "ali-rezaei-2026",
    ],
)
def test_rejects_invalid_passwords(password: str) -> None:
    with pytest.raises(PasswordPolicyViolation):
        validate_password(password, "ali@example.com")


@pytest.mark.parametrize(
    "password",
    [
        "CorrectHorseBatteryStaple",
        "یک-عبارت-عبور-طولانی-و-امن",
        "Vb9#kLm2QpXz",
        "my long dorm passphrase",
    ],
)
def test_accepts_strong_passphrases(password: str) -> None:
    validate_password(password, "ali@example.com")


def test_rejects_password_containing_email_local_part() -> None:
    with pytest.raises(PasswordPolicyViolation, match="email"):
        validate_password("ali-rezaei-is-here", "ali@example.com")


def test_rejects_over_max_length() -> None:
    with pytest.raises(PasswordPolicyViolation, match="128"):
        validate_password("aB3!" * 40, "ali@example.com")
