"""Exhaustive unit tests for the complaint status machine (SPEC-0007 FR-4, FR-5)."""

from __future__ import annotations

import pytest

from sara_api.domain.complaints import (
    ALLOWED_TRANSITIONS,
    ComplaintAlreadyAnswered,
    ComplaintStatus,
    ComplaintTransitionNotAllowed,
    ensure_answerable,
    ensure_review_transition,
)

LEGAL = {(ComplaintStatus.SUBMITTED, ComplaintStatus.IN_REVIEW)}


@pytest.mark.parametrize("current", list(ComplaintStatus))
@pytest.mark.parametrize("target", list(ComplaintStatus))
def test_transition_matrix_is_closed(current: ComplaintStatus, target: ComplaintStatus) -> None:
    if (current, target) in LEGAL:
        ensure_review_transition(current, target)
    else:
        with pytest.raises(ComplaintTransitionNotAllowed):
            ensure_review_transition(current, target)


def test_answered_is_terminal() -> None:
    assert ALLOWED_TRANSITIONS[ComplaintStatus.ANSWERED] == frozenset()


def test_only_an_unanswered_complaint_accepts_an_initial_response() -> None:
    ensure_answerable(ComplaintStatus.SUBMITTED)
    ensure_answerable(ComplaintStatus.IN_REVIEW)
    with pytest.raises(ComplaintAlreadyAnswered):
        ensure_answerable(ComplaintStatus.ANSWERED)
