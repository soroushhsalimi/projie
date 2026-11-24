"""Application factory and process entry point."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from sara_api import __version__
from sara_api.core.config import Settings, get_settings
from sara_api.core.problem import register_exception_handlers
from sara_api.db.base import Base
from sara_api.db.session import build_engine, build_session_factory
from sara_api.modules.auth.router import router as auth_router
from sara_api.modules.health.router import router as health_router

# Importing the models registers their tables on Base.metadata.
from sara_api.modules.tickets import models as _ticket_models  # noqa: F401
from sara_api.modules.tickets.router import router as tickets_router
from sara_api.modules.users import models as _models  # noqa: F401

logger = logging.getLogger("sara.app")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if settings.auto_create_schema:
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
        logger.info(
            "app.startup",
            extra={"environment": settings.environment, "dialect": engine.dialect.name},
        )
        try:
            yield
        finally:
            await engine.dispose()

    app = FastAPI(
        title="SARA API",
        version=__version__,
        description="Self-governed dormitory management — identity and accommodation workflows.",
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = session_factory

    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
        max_age=600,
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

    app.include_router(health_router)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(tickets_router, prefix="/api/v1")

    @app.get("/", include_in_schema=False)
    async def index() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "version": __version__,
            "openapi": "/api/openapi.json",
            "docs": "/api/docs",
        }

    return app


app = create_app()
