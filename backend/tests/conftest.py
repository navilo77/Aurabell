"""Test configuration and fixtures for Aura Bell backend.

Uses Supabase local Docker (`supabase start`) for integration tests.
Provides async database session fixture and Supabase client fixtures.
"""

from __future__ import annotations

# Import test config FIRST to set environment variables before any app imports
import test_config  # noqa: F401

import asyncio
from dotenv import load_dotenv
import os
import subprocess
import time
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

load_dotenv()
print(f"Loaded SUPABASE_ANON_KEY: {os.getenv('SUPABASE_ANON_KEY')}")

# Test-only NullPool engine so a fresh connection is used per test and none
# stay bound to a stale event loop across the function-scoped async loops.
def _db_url() -> str:
    from app.core.config import settings

    return settings.DATABASE_URL


_test_engine = create_async_engine(
    _db_url(),
    poolclass=NullPool,
    pool_pre_ping=True,
)
_test_session_factory = async_sessionmaker(
    bind=_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


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
    """Yield an AsyncSession wrapped in an outer transaction.

    The session joins the outer connection transaction with savepoints, so any
    ``session.commit()`` performed by service code only releases a savepoint and
    the outer transaction is rolled back afterwards. This keeps tests isolated
    even though the services commit internally.
    """
    async with _test_engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


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

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, key)


@pytest.fixture(scope="function")
def supabase_anon_client():
    """Supabase anon client (respects RLS)."""
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    return create_client(url, key)


@pytest.fixture
def platform_admin_user():
    """Platform admin user for testing central inventory access."""
    from app.core.auth import User
    return User(
        id="test-platform-admin",
        email="admin@test.com",
        roles=["super_admin"],
        store_ids=[],
    )


@pytest.fixture
def store_manager_user():
    """Store manager user for testing store-scoped access."""
    from app.core.auth import User
    return User(
        id="test-store-manager",
        email="manager@test.com",
        roles=["store_manager"],
        store_ids=["store-a", "store-b"],
    )


@pytest.fixture
def make_store_manager_user():
    """Factory fixture to create a store manager user for a specific store."""
    from app.core.auth import User
    
    def _make_store_manager_user(store_id: str) -> User:
        return User(
            id=f"test-store-manager-{store_id}",
            email=f"manager-{store_id}@test.com",
            roles=["store_manager"],
            store_ids=[store_id],
        )
    return _make_store_manager_user


