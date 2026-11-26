"""Pure account rules: roles, statuses, email normalization and password policy.

No I/O, no framework imports (AGENTS.md §5.2).
"""

from __future__ import annotations

import re
from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


class UserStatus(StrEnum):
    ACTIVE = "active"
    PENDING_VERIFICATION = "pending_verification"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class PasswordPolicyViolation(ValueError):
    """Raised when a candidate password violates the policy."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128

# Deliberately small and local; a production deployment replaces this with a breached-password
# corpus (see F-0404). It catches the passwords that actually appear in student projects.
COMMON_PASSWORDS = frozenset(
    {
        "1234567890",
        "password",
        "password1",
        "password123",
        "qwertyuiop",
        "1111111111",
        "12345678910",
        "iloveyou",
        "admin12345",
        "letmein123",
        "welcome123",
        "changeme123",
        "dormitory",
        "khanevade",
    }
)


def normalize_email(email: str) -> str:
    """Trim and case-fold an email so uniqueness is case-insensitive."""
    return email.strip().casefold()


#: Persian and Arabic-Indic digits, mapped to ASCII so a resident may type either.
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

_MOBILE = re.compile(r"^09\d{9}$")


def normalize_national_id(value: str) -> str:
    """Return the bare 10-digit national ID or raise ``ValueError`` (SPEC-0002 FR-10)."""
    digits = value.translate(_DIGITS).strip().replace(" ", "").replace("-", "")
    if len(digits) != 10 or not digits.isdigit():
        raise ValueError("National ID must be exactly 10 digits.")
    return digits


def normalize_mobile(value: str) -> str:
    """Canonicalize an Iranian mobile number to ``09xxxxxxxxx`` (SPEC-0002 FR-11)."""
    digits = value.translate(_DIGITS).strip().replace(" ", "").replace("-", "")
    if digits.startswith("+98"):
        digits = f"0{digits[3:]}"
    elif digits.startswith("0098"):
        digits = f"0{digits[4:]}"
    if not _MOBILE.fullmatch(digits):
        raise ValueError("Mobile number must be a valid Iranian number (09xxxxxxxxx).")
    return digits


def validate_password(password: str, email: str) -> None:
    """Enforce the V1 password policy.

    Composition rules are intentionally absent (ADR-0005): length plus a blocklist is more
    effective and produces better passphrases.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordPolicyViolation(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise PasswordPolicyViolation(
            f"Password must be at most {MAX_PASSWORD_LENGTH} characters long."
        )
    if password.strip() == "":
        raise PasswordPolicyViolation("Password must not be blank.")
    if password.casefold() in COMMON_PASSWORDS:
        raise PasswordPolicyViolation("This password is too common. Choose a longer passphrase.")
    if len(set(password)) == 1:
        raise PasswordPolicyViolation("Password must not repeat a single character.")

    local_part = normalize_email(email).split("@", 1)[0]
    if len(local_part) >= 3 and local_part in password.casefold():
        raise PasswordPolicyViolation("Password must not contain your email address.")
