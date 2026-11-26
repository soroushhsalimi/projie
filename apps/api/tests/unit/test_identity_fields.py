"""Unit tests for the registration identity fields (SPEC-0002 FR-10, FR-11)."""

from __future__ import annotations

import pytest

from sara_api.domain.accounts import normalize_mobile, normalize_national_id


@pytest.mark.parametrize(
    "raw",
    ["0012345679", " 0012345679 ", "001-234-5679", "۰۰۱۲۳۴۵۶۷۹", "٠٠١٢٣٤٥٦٧٩"],
)
def test_national_id_is_reduced_to_ten_digits(raw: str) -> None:
    assert normalize_national_id(raw) == "0012345679"


@pytest.mark.parametrize("raw", ["123456789", "00123456789", "abcdefghij", ""])
def test_invalid_national_ids_are_rejected(raw: str) -> None:
    with pytest.raises(ValueError):
        normalize_national_id(raw)


@pytest.mark.parametrize(
    "raw",
    [
        "09121234567",
        "0912 123 4567",
        "0912-123-4567",
        "+989121234567",
        "00989121234567",
        "۰۹۱۲۱۲۳۴۵۶۷",
    ],
)
def test_mobile_numbers_are_canonicalized(raw: str) -> None:
    assert normalize_mobile(raw) == "09121234567"


@pytest.mark.parametrize("raw", ["02112345678", "0912123456", "+447700900123", ""])
def test_invalid_mobile_numbers_are_rejected(raw: str) -> None:
    with pytest.raises(ValueError):
        normalize_mobile(raw)
