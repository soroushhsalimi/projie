"""Async engine and session factory.

The engine is created once per application instance and stored on ``app.state`` so tests can build
isolated apps without module-level globals (AGENTS.md §9.2).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from sara_api.core.config import Settings


def build_engine(settings: Settings) -> AsyncEngine:
    if settings.is_sqlite:
        return create_async_engine(
            settings.database_url,
            echo=False,
            future=True,
            connect_args={"check_same_thread": False},
        )
    return create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
        pool_pre_ping=True,
    )


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
