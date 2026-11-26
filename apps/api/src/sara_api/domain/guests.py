"""Pure guest-visit rules: statuses, the allowed window and the entry/exit machine.

No I/O, no framework imports (AGENTS.md §5.2). A violation is expressed here as a plain
``ValueError`` subtype; the service maps it onto an ``AppError``. Every function receives the
current time explicitly so the rules stay deterministic.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum


class GuestStatus(StrEnum):
    EXPECTED = "expected"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"


#: V1 policy: a single visit may be allowed for at most one day (SPEC-0008 Q2).
MAX_VISIT_WINDOW = timedelta(hours=24)


class GuestWindowInvalid(ValueError):
    """Raised when the allowed window ends before it starts."""


class GuestWindowTooLong(ValueError):
    """Raised when the allowed window exceeds :data:`MAX_VISIT_WINDOW`."""


class GuestCheckInBlocked(ValueError):
    """Raised when a guest may not enter: wrong status, too early or too late."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Guest check-in is not allowed: {reason}.")


class GuestCheckOutBlocked(ValueError):
    """Raised when a guest who is not inside is asked to leave."""


def ensure_valid_window(allowed_from: datetime, allowed_until: datetime) -> None:
    """Require ``allowed_from < allowed_until`` and a window of at most one day."""
    if allowed_until <= allowed_from:
        raise GuestWindowInvalid("The allowed window must end after it starts.")
    if allowed_until - allowed_from > MAX_VISIT_WINDOW:
        raise GuestWindowTooLong("A guest visit may be allowed for at most 24 hours.")


def ensure_check_in_allowed(
    current: GuestStatus,
    *,
    allowed_from: datetime,
    allowed_until: datetime,
    now: datetime,
) -> None:
    """A guest enters only once, and only inside the allowed window (SPEC-0008 FR-4)."""
    if current is not GuestStatus.EXPECTED:
        raise GuestCheckInBlocked("the visit is not awaiting entry")
    if now < allowed_from:
        raise GuestCheckInBlocked("the allowed window has not started yet")
    if now > allowed_until:
        raise GuestCheckInBlocked("the allowed window has passed")


def ensure_check_out_allowed(current: GuestStatus) -> None:
    """Only a guest who is inside may leave (SPEC-0008 FR-5)."""
    if current is not GuestStatus.CHECKED_IN:
        raise GuestCheckOutBlocked("This guest is not checked in.")


def is_overdue(
    *,
    status: GuestStatus,
    allowed_until: datetime,
    checked_out_at: datetime | None,
    now: datetime,
) -> bool:
    """A visit is overdue when the guest's reference time is past the window (FR-6).

    A visit that has not started yet is never overdue, however long the desk waits.
    """
    if status is GuestStatus.EXPECTED:
        return False
    reference = checked_out_at if checked_out_at is not None else now
    return reference > allowed_until
