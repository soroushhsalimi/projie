"""Shared helpers for API-level tests."""

from __future__ import annotations

import hashlib

DEFAULT_PHONE = "09121234567"
DEFAULT_ADDRESS = "تهران، خیابان آزادی، پلاک ۱۲"


def national_id_for(email: str) -> str:
    """Return a deterministic 10-digit national ID derived from the email.

    Each test database is isolated, but a single test may register several accounts; deriving the
    ID from the email keeps them unique without hard-coding a list.
    """
    digest = hashlib.sha256(email.casefold().encode()).hexdigest()
    return f"{int(digest[:12], 16) % 10**10:010d}"


def registration_body(email: str, full_name: str, password: str) -> dict[str, str]:
    return {
        "full_name": full_name,
        "email": email,
        "password": password,
        "national_id": national_id_for(email),
        "phone": DEFAULT_PHONE,
        "address": DEFAULT_ADDRESS,
    }
