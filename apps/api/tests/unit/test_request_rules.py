"""Unit tests for accommodation-request rules (SPEC-0005 FR-5, FR-6)."""

from __future__ import annotations

import pytest

from sara_api.domain.requests import (
    RequestStatus,
    RoomType,
    WithdrawalNotAllowed,
    ensure_withdrawable,
)


def test_room_types_match_the_contract() -> None:
    assert [room.value for room in RoomType] == ["single", "double", "triple", "quad"]


def test_request_statuses_match_the_contract() -> None:
    assert [status.value for status in RequestStatus] == ["submitted", "withdrawn"]


@pytest.mark.parametrize("status", list(RequestStatus))
def test_only_a_submitted_request_can_be_withdrawn(status: RequestStatus) -> None:
    if status is RequestStatus.SUBMITTED:
        ensure_withdrawable(status)
    else:
        with pytest.raises(WithdrawalNotAllowed):
            ensure_withdrawable(status)
