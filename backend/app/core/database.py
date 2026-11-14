"""Async SQLAlchemy engine and session management.

Creates a 2.0 async engine against ``settings.DATABASE_URL`` and exposes:
- ``engine``: the underlying ``AsyncEngine``.
- ``async_session_factory``: a callable producing ``AsyncSession`` objects.
- ``get_db``: a FastAPI dependency yielding one session per request.

No table models, ``create_all``, or migrations live here — those belong to
later sub-milestones.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield a single ``AsyncSession`` for the duration of a request."""
    async with async_session_factory() as session:
        yield session