"""Pure accommodation-request rules: statuses, room types and the withdrawal rule.

No I/O, no framework imports (AGENTS.md §5.2). The service maps a violation onto an ``AppError``;
the domain only knows that the withdrawal is not allowed.
"""

from __future__ import annotations

from enum import StrEnum


class RequestStatus(StrEnum):
    SUBMITTED = "submitted"
    WITHDRAWN = "withdrawn"


class RoomType(StrEnum):
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    QUAD = "quad"


class WithdrawalNotAllowed(ValueError):
    """Raised when a request in a terminal status is asked to be withdrawn."""

    def __init__(self, current: RequestStatus) -> None:
        self.current = current
        super().__init__(f"A request in status '{current}' cannot be withdrawn.")


def ensure_withdrawable(status: RequestStatus) -> None:
    """Allow withdrawal only while the request is still ``submitted`` (SPEC-0005 FR-5)."""
    if status is RequestStatus.SUBMITTED:
        return
    raise WithdrawalNotAllowed(status)
