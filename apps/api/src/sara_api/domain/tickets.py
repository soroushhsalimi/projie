"""Pure maintenance-ticket rules: statuses and the status machine.

No I/O, no framework imports (AGENTS.md §5.2). The service maps a violation of this machine onto an
``AppError``; the domain itself only knows that the transition is not allowed.
"""

from __future__ import annotations

from enum import StrEnum


class TicketStatus(StrEnum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"


class TicketCategory(StrEnum):
    GENERAL = "general"
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    FURNITURE = "furniture"
    HEATING = "heating"
    CLEANING = "cleaning"


class TicketTransitionNotAllowed(ValueError):
    """Raised when a ticket is asked to move to a status it cannot reach."""

    def __init__(self, current: TicketStatus, target: TicketStatus) -> None:
        self.current = current
        self.target = target
        super().__init__(f"A ticket in status '{current}' cannot move to '{target}'.")


#: ``resolved`` is terminal; reopening is a separate decision (SPEC-0004 Q1).
ALLOWED_TRANSITIONS: dict[TicketStatus, frozenset[TicketStatus]] = {
    TicketStatus.OPEN: frozenset({TicketStatus.UNDER_REVIEW, TicketStatus.RESOLVED}),
    TicketStatus.UNDER_REVIEW: frozenset({TicketStatus.RESOLVED}),
    TicketStatus.RESOLVED: frozenset(),
}


def ensure_transition(current: TicketStatus, target: TicketStatus) -> None:
    """Raise :class:`TicketTransitionNotAllowed` unless ``current → target`` is legal."""
    if target in ALLOWED_TRANSITIONS[current]:
        return
    raise TicketTransitionNotAllowed(current, target)
