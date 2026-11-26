"""Guest-visit use cases.

The service owns the unit of work (it never commits) and contains no FastAPI imports. Role
enforcement happens in the transport layer; this layer owns existence, the allowed window, the
entry/exit rules and the overdue derivation. The current time is read through the module-level
``utcnow`` so tests can patch that single boundary.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from sara_api.core.errors import (
    GuestCheckInBlockedConflict,
    GuestCheckOutBlockedConflict,
    NotFound,
    ValidationFailed,
)
from sara_api.core.security import utcnow
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
from sara_api.modules.guests.models import GuestVisit
from sara_api.modules.guests.repository import GuestRepository

logger = logging.getLogger("sara.guests")


def _aware(value: datetime) -> datetime:
    """SQLite returns naive datetimes; the domain always compares timezone-aware values."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class GuestVisitItem:
    visit: GuestVisit
    host_name: str
    overdue: bool


@dataclass(frozen=True, slots=True)
class GuestVisitPage:
    items: list[GuestVisitItem]
    total: int
    page: int
    per_page: int


class GuestService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = GuestRepository(session)

    async def list_visits(
        self,
        *,
        status: GuestStatus | None,
        page: int,
        per_page: int,
    ) -> GuestVisitPage:
        status_value = status.value if status is not None else None
        total = await self._repo.count(status=status_value)
        rows = await self._repo.list_with_host(
            status=status_value,
            limit=per_page,
            offset=(page - 1) * per_page,
        )
        now = _aware(utcnow())
        return GuestVisitPage(
            items=[self._item(visit, name, now) for visit, name in rows],
            total=total,
            page=page,
            per_page=per_page,
        )

    async def get_visit(self, visit_id: UUID) -> GuestVisitItem:
        visit, host_name = await self._require(visit_id)
        return self._item(visit, host_name, _aware(utcnow()))

    async def register_visit(
        self,
        *,
        guest_name: str,
        host_email: str,
        purpose: str | None,
        allowed_from: datetime,
        allowed_until: datetime,
    ) -> GuestVisitItem:
        try:
            ensure_valid_window(allowed_from, allowed_until)
        except (GuestWindowInvalid, GuestWindowTooLong) as exc:
            raise ValidationFailed(str(exc)) from exc

        host = await self._repo.find_resident_by_email(host_email)
        if host is None or host.role != "user":
            raise ValidationFailed("The host must be an existing resident account.")

        visit = await self._repo.add(
            GuestVisit(
                host_id=host.id,
                guest_name=guest_name,
                purpose=purpose,
                allowed_from=allowed_from,
                allowed_until=allowed_until,
                status=GuestStatus.EXPECTED.value,
            )
        )
        logger.info(
            "guest.visit.registered",
            extra={"guest_visit_id": str(visit.id), "status": visit.status},
        )
        return self._item(visit, host.full_name, _aware(utcnow()))

    async def check_in(self, visit_id: UUID) -> GuestVisitItem:
        visit, host_name = await self._require(visit_id)
        now = _aware(utcnow())
        try:
            ensure_check_in_allowed(
                GuestStatus(visit.status),
                allowed_from=_aware(visit.allowed_from),
                allowed_until=_aware(visit.allowed_until),
                now=now,
            )
        except GuestCheckInBlocked as exc:
            raise GuestCheckInBlockedConflict(str(exc)) from exc

        visit.status = GuestStatus.CHECKED_IN.value
        visit.checked_in_at = now
        await self._repo.save(visit)
        item = self._item(visit, host_name, now)
        logger.info(
            "guest.checked_in",
            extra={
                "guest_visit_id": str(visit.id),
                "status": visit.status,
                "overdue": item.overdue,
            },
        )
        return item

    async def check_out(self, visit_id: UUID) -> GuestVisitItem:
        visit, host_name = await self._require(visit_id)
        now = _aware(utcnow())
        try:
            ensure_check_out_allowed(GuestStatus(visit.status))
        except GuestCheckOutBlocked as exc:
            raise GuestCheckOutBlockedConflict(str(exc)) from exc

        visit.status = GuestStatus.CHECKED_OUT.value
        visit.checked_out_at = now
        await self._repo.save(visit)
        item = self._item(visit, host_name, now)
        logger.info(
            "guest.checked_out",
            extra={
                "guest_visit_id": str(visit.id),
                "status": visit.status,
                "overdue": item.overdue,
            },
        )
        return item

    async def _require(self, visit_id: UUID) -> tuple[GuestVisit, str]:
        row = await self._repo.get_with_host(visit_id)
        if row is None:
            raise NotFound("Guest visit not found.")
        return row

    def _item(self, visit: GuestVisit, host_name: str, now: datetime) -> GuestVisitItem:
        checked_out_at = (
            _aware(visit.checked_out_at) if visit.checked_out_at is not None else None
        )
        overdue = is_overdue(
            status=GuestStatus(visit.status),
            allowed_until=_aware(visit.allowed_until),
            checked_out_at=checked_out_at,
            now=now,
        )
        return GuestVisitItem(visit=visit, host_name=host_name, overdue=overdue)
