"""Liveness and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter, Request
from sqlalchemy import text

from sara_api import __version__
from sara_api.core.errors import NotReady

router = APIRouter(tags=["health"])


@router.get("/health/live", summary="Liveness probe")
async def live() -> dict[str, str]:
    """Process is up. Deliberately does not touch the database."""
    return {"status": "ok", "version": __version__}


@router.get("/health/ready", summary="Readiness probe")
async def ready(request: Request) -> dict[str, str]:
    """Ready to serve traffic only when the database answers a trivial query."""
    engine = request.app.state.engine
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - probe boundary, any failure means not ready
        raise NotReady("Database is unreachable.") from exc
    return {"status": "ok", "database": "ok", "version": __version__}
