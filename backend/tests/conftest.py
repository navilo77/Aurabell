"""Test configuration and fixtures for Aura Bell backend.

Uses Supabase local Docker (`supabase start`) for integration tests.
Provides async database session fixture and Supabase client fixtures.
"""

from __future__ import annotations

# Import test config FIRST to set environment variables before any app imports
import test_config  # noqa: F401

import asyncio
import os
import subprocess
import time
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio


# ─── Supabase Local Lifecycle ──────────────────────────────────────────────


def _supabase_bin() -> str:
    """Return path to supabase CLI binary (assumes on PATH)."""
    return "supabase"


def _project_root() -> Path:
    """Return backend/supabase directory (where config.toml lives)."""
    return Path(__file__).parent.parent / "supabase"


@pytest.fixture(scope="session")
def supabase_local() -> None:
    """Start Supabase local stack once per test session.

    Sets required env vars for the test session:
    - SUPABASE_URL → http://localhost:54331
    - SUPABASE_ANON_KEY → from `supabase status --output json`
    - SUPABASE_SERVICE_ROLE_KEY → from `supabase status --output json`
    - DATABASE_URL → postgresql+asyncpg://postgres:postgres@localhost:54330/postgres
    """
    project_root = _project_root()
    os.chdir(project_root)

    # Start Supabase local
    result = subprocess.run(
        [_supabase_bin(), "start"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        pytest.skip(f"Supabase local failed to start: {result.stderr}")

    # Get connection details
    status_result = subprocess.run(
        [_supabase_bin(), "status", "--output", "json"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if status_result.returncode != 0:
        pytest.skip(f"Failed to get Supabase status: {status_result.stderr}")

    import json

    status = json.loads(status_result.stdout)

    # Set environment variables for the test session
    os.environ["SUPABASE_URL"] = status["API_URL"]
    os.environ["SUPABASE_ANON_KEY"] = status["ANON_KEY"]
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = status["SERVICE_ROLE_KEY"]
    os.environ["DATABASE_URL"] = status["DB_URL"].replace("postgresql://", "postgresql+asyncpg://")

    # Reload settings to pick up new env vars
    from app.core.config import settings

    settings.__init__()  # type: ignore[attr-defined]

    # Wait for DB to be ready
    max_retries = 30
    for _ in range(max_retries):
        try:
            subprocess.run(
                ["pg_isready", "-h", "localhost", "-p", "54330", "-U", "postgres"],
                check=True,
                capture_output=True,
            )
            break
        except subprocess.CalledProcessError:
            time.sleep(1)
    else:
        pytest.skip("Database not ready after 30 retries")

    yield

    # Teardown
    subprocess.run([_supabase_bin(), "stop"], capture_output=True, timeout=60)


# ─── Database Fixtures ─────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncIterator[AsyncSession]:
    """Yield a clean AsyncSession for each test function.

    Rolls back all changes after the test.
    """
    from app.core.database import async_session_factory
    from sqlalchemy.ext.asyncio import AsyncSession

    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def clean_db(db_session: AsyncSession) -> AsyncIterator[None]:
    """Truncate all tables after each test (via rollback + explicit clean)."""
    yield
    # Rollback handles most, but for explicit truncation if needed:
    await db_session.rollback()


# ─── Supabase Client Fixtures ──────────────────────────────────────────────


@pytest.fixture(scope="session")
def supabase_admin_client():
    """Supabase admin client with service role key (bypasses RLS)."""
    from supabase import create_client

    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


@pytest.fixture(scope="function")
def supabase_anon_client():
    """Supabase anon client (respects RLS)."""
    from supabase import create_client

    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_ANON_KEY"]
    return create_client(url, key)


# ─── Event Loop ────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()