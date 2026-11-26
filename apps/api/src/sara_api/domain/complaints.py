"""Pure complaint rules: statuses, categories and the review/answer machine.

No I/O, no framework imports (AGENTS.md §5.2). A violation is expressed here as a plain
``ValueError`` subtype; the service maps it onto an ``AppError``.
"""

from __future__ import annotations

from enum import StrEnum


class ComplaintStatus(StrEnum):
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    ANSWERED = "answered"


class ComplaintCategory(StrEnum):
    NOISE = "noise"
    CLEANLINESS = "cleanliness"
    SAFETY = "safety"
    STAFF = "staff"
    FACILITIES = "facilities"
    OTHER = "other"


class ComplaintTransitionNotAllowed(ValueError):
    """Raised when a complaint is asked to move to a status it cannot reach."""

    def __init__(self, current: ComplaintStatus, target: ComplaintStatus) -> None:
        self.current = current
        self.target = target
        super().__init__(f"A complaint in status '{current}' cannot move to '{target}'.")


class ComplaintAlreadyAnswered(ValueError):
    """Raised when a second initial response is recorded for the same complaint."""


#: ``answered`` is terminal; reopening is a separate decision (SPEC-0007 Q1).
ALLOWED_TRANSITIONS: dict[ComplaintStatus, frozenset[ComplaintStatus]] = {
    ComplaintStatus.SUBMITTED: frozenset({ComplaintStatus.IN_REVIEW}),
    ComplaintStatus.IN_REVIEW: frozenset(),
    ComplaintStatus.ANSWERED: frozenset(),
}


def ensure_review_transition(current: ComplaintStatus, target: ComplaintStatus) -> None:
    """Raise :class:`ComplaintTransitionNotAllowed` unless ``current → target`` is legal."""
    if target in ALLOWED_TRANSITIONS[current]:
        return
    raise ComplaintTransitionNotAllowed(current, target)


def ensure_answerable(current: ComplaintStatus) -> None:
    """Only an unanswered complaint accepts its one initial response (SPEC-0007 FR-5)."""
    if current is ComplaintStatus.ANSWERED:
        raise ComplaintAlreadyAnswered("This complaint already has an initial response.")
