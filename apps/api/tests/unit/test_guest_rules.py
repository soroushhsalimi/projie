"""Domain tests for guest visits (SPEC-0008 FR-3…FR-6)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from sara_api.domain.guests import (
    GuestCheckInBlocked,
    GuestCheckOutBlocked,
    GuestStatus,
    GuestWindowInvalid,
    GuestWindowTooLong,
    ensure_check_in_allowed,
    ensure_check_out_allowed,
    ensure_valid_window,
    is_overdue,
)

BASE = datetime(2026, 11, 26, 16, 0, tzinfo=UTC)
WINDOW_END = BASE + timedelta(hours=2)


def test_window_must_end_after_it_starts() -> None:
    with pytest.raises(GuestWindowInvalid):
        ensure_valid_window(BASE, BASE)


def test_window_may_not_exceed_one_day() -> None:
    with pytest.raises(GuestWindowTooLong):
        ensure_valid_window(BASE, BASE + timedelta(hours=25))


def test_a_window_of_exactly_one_day_is_accepted() -> None:
    ensure_valid_window(BASE, BASE + timedelta(hours=24))


@pytest.mark.parametrize("now", [BASE, WINDOW_END])
def test_check_in_is_allowed_on_the_window_boundaries(now: datetime) -> None:
    ensure_check_in_allowed(
        GuestStatus.EXPECTED, allowed_from=BASE, allowed_until=WINDOW_END, now=now
    )


def test_check_in_is_blocked_before_the_window() -> None:
    with pytest.raises(GuestCheckInBlocked):
        ensure_check_in_allowed(
            GuestStatus.EXPECTED,
            allowed_from=BASE,
            allowed_until=WINDOW_END,
            now=BASE - timedelta(minutes=1),
        )


def test_check_in_is_blocked_after_the_window() -> None:
    with pytest.raises(GuestCheckInBlocked):
        ensure_check_in_allowed(
            GuestStatus.EXPECTED,
            allowed_from=BASE,
            allowed_until=WINDOW_END,
            now=WINDOW_END + timedelta(minutes=1),
        )


@pytest.mark.parametrize("status", [GuestStatus.CHECKED_IN, GuestStatus.CHECKED_OUT])
def test_check_in_requires_an_expected_visit(status: GuestStatus) -> None:
    with pytest.raises(GuestCheckInBlocked):
        ensure_check_in_allowed(status, allowed_from=BASE, allowed_until=WINDOW_END, now=BASE)


def test_check_out_requires_a_guest_inside() -> None:
    with pytest.raises(GuestCheckOutBlocked):
        ensure_check_out_allowed(GuestStatus.EXPECTED)
    ensure_check_out_allowed(GuestStatus.CHECKED_IN)


def test_an_expected_visit_is_never_overdue() -> None:
    assert (
        is_overdue(
            status=GuestStatus.EXPECTED,
            allowed_until=WINDOW_END,
            checked_out_at=None,
            now=WINDOW_END + timedelta(hours=1),
        )
        is False
    )


def test_a_guest_still_inside_after_the_window_is_overdue() -> None:
    assert (
        is_overdue(
            status=GuestStatus.CHECKED_IN,
            allowed_until=WINDOW_END,
            checked_out_at=None,
            now=WINDOW_END + timedelta(minutes=1),
        )
        is True
    )


def test_a_late_exit_is_overdue_but_an_on_time_exit_is_not() -> None:
    assert (
        is_overdue(
            status=GuestStatus.CHECKED_OUT,
            allowed_until=WINDOW_END,
            checked_out_at=WINDOW_END + timedelta(minutes=5),
            now=BASE,
        )
        is True
    )
    assert (
        is_overdue(
            status=GuestStatus.CHECKED_OUT,
            allowed_until=WINDOW_END,
            checked_out_at=WINDOW_END,
            now=BASE,
        )
        is False
    )
