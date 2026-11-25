"""Pure accommodation-request rules: statuses, room types and the state machine.

No I/O, no framework imports (AGENTS.md §5.2). The service maps a violation onto an ``AppError``;
the domain only knows that the transition is not allowed.
"""

from __future__ import annotations

from enum import StrEnum


class RequestStatus(StrEnum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class RoomType(StrEnum):
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    QUAD = "quad"


#: A request still occupying the resident's single active slot (SPEC-0005 FR-3).
ACTIVE_STATUSES: frozenset[RequestStatus] = frozenset(
    {RequestStatus.SUBMITTED, RequestStatus.UNDER_REVIEW}
)

_ALLOWED_TRANSITIONS: dict[RequestStatus, frozenset[RequestStatus]] = {
    RequestStatus.SUBMITTED: frozenset(
        {RequestStatus.UNDER_REVIEW, RequestStatus.APPROVED, RequestStatus.REJECTED}
    ),
    RequestStatus.UNDER_REVIEW: frozenset(
        {RequestStatus.APPROVED, RequestStatus.REJECTED}
    ),
    RequestStatus.APPROVED: frozenset(),
    RequestStatus.REJECTED: frozenset(),
    RequestStatus.WITHDRAWN: frozenset(),
}


class WithdrawalNotAllowed(ValueError):
    """Raised when a request in a terminal status is asked to be withdrawn."""

    def __init__(self, current: RequestStatus) -> None:
        self.current = current
        super().__init__(f"A request in status '{current}' cannot be withdrawn.")


class RequestTransitionNotAllowed(ValueError):
    """Raised when a manager asks for a status change the state machine forbids."""

    def __init__(self, current: RequestStatus, target: RequestStatus) -> None:
        self.current = current
        self.target = target
        super().__init__(f"A request in status '{current}' cannot move to '{target}'.")


def ensure_withdrawable(status: RequestStatus) -> None:
    """Allow withdrawal only while the request is still ``submitted`` (SPEC-0005 FR-5)."""
    if status is RequestStatus.SUBMITTED:
        return
    raise WithdrawalNotAllowed(status)


def ensure_review_transition(current: RequestStatus, target: RequestStatus) -> None:
    """Allow only the manager transitions of SPEC-0006 (FR-4)."""
    if target in _ALLOWED_TRANSITIONS[current]:
        return
    raise RequestTransitionNotAllowed(current, target)
