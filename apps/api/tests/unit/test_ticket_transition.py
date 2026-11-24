"""Exhaustive unit tests for the ticket status machine (SPEC-0004 FR-4, AC-3)."""

from __future__ import annotations

import pytest

from sara_api.domain.tickets import (
    ALLOWED_TRANSITIONS,
    TicketStatus,
    TicketTransitionNotAllowed,
    ensure_transition,
)

LEGAL = {
    (TicketStatus.OPEN, TicketStatus.UNDER_REVIEW),
    (TicketStatus.OPEN, TicketStatus.RESOLVED),
    (TicketStatus.UNDER_REVIEW, TicketStatus.RESOLVED),
}


@pytest.mark.parametrize("current", list(TicketStatus))
@pytest.mark.parametrize("target", list(TicketStatus))
def test_transition_matrix_is_closed(current: TicketStatus, target: TicketStatus) -> None:
    if (current, target) in LEGAL:
        ensure_transition(current, target)
    else:
        with pytest.raises(TicketTransitionNotAllowed):
            ensure_transition(current, target)


def test_resolved_is_terminal() -> None:
    assert ALLOWED_TRANSITIONS[TicketStatus.RESOLVED] == frozenset()
