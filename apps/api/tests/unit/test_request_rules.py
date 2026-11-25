"""Unit tests for accommodation-request rules (SPEC-0005 FR-5, FR-6, SPEC-0006 FR-4)."""

from __future__ import annotations

import pytest

from sara_api.domain.requests import (
    ACTIVE_STATUSES,
    RequestStatus,
    RequestTransitionNotAllowed,
    RoomType,
    WithdrawalNotAllowed,
    ensure_review_transition,
    ensure_withdrawable,
)

LEGAL_TRANSITIONS = [
    (RequestStatus.SUBMITTED, RequestStatus.UNDER_REVIEW),
    (RequestStatus.SUBMITTED, RequestStatus.APPROVED),
    (RequestStatus.SUBMITTED, RequestStatus.REJECTED),
    (RequestStatus.UNDER_REVIEW, RequestStatus.APPROVED),
    (RequestStatus.UNDER_REVIEW, RequestStatus.REJECTED),
]


def test_room_types_match_the_contract() -> None:
    assert [room.value for room in RoomType] == ["single", "double", "triple", "quad"]


def test_request_statuses_match_the_contract() -> None:
    assert [status.value for status in RequestStatus] == [
        "submitted",
        "under_review",
        "approved",
        "rejected",
        "withdrawn",
    ]


def test_only_submitted_and_under_review_requests_are_active() -> None:
    assert {RequestStatus.SUBMITTED, RequestStatus.UNDER_REVIEW} == ACTIVE_STATUSES


@pytest.mark.parametrize("status", list(RequestStatus))
def test_only_a_submitted_request_can_be_withdrawn(status: RequestStatus) -> None:
    if status is RequestStatus.SUBMITTED:
        ensure_withdrawable(status)
    else:
        with pytest.raises(WithdrawalNotAllowed):
            ensure_withdrawable(status)


@pytest.mark.parametrize(("current", "target"), LEGAL_TRANSITIONS)
def test_legal_review_transitions_are_accepted(
    current: RequestStatus, target: RequestStatus
) -> None:
    ensure_review_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (RequestStatus.SUBMITTED, RequestStatus.SUBMITTED),
        (RequestStatus.UNDER_REVIEW, RequestStatus.UNDER_REVIEW),
        (RequestStatus.APPROVED, RequestStatus.UNDER_REVIEW),
        (RequestStatus.APPROVED, RequestStatus.REJECTED),
        (RequestStatus.REJECTED, RequestStatus.APPROVED),
        (RequestStatus.WITHDRAWN, RequestStatus.UNDER_REVIEW),
    ],
)
def test_illegal_review_transitions_are_rejected(
    current: RequestStatus, target: RequestStatus
) -> None:
    with pytest.raises(RequestTransitionNotAllowed):
        ensure_review_transition(current, target)
