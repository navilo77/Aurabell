"""Health endpoints (BE-08)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_factory, engine

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    """Liveness probe. Returns ``{"status": "ok"}``."""
    return {"status": "ok"}


@router.get("/health/ready")
async def ready():
    """Readiness probe. Checks critical dependencies."""
    checks = {}
    overall_ready = True

    # Database check
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {type(e).__name__}"
        overall_ready = False

    # Redis check (if configured)
    if settings.REDIS_URL:
        try:
            import redis.asyncio as redis
            client = redis.from_url(
                settings.REDIS_URL,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
            )
            await client.ping()
            await client.close()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {type(e).__name__}"
            # Redis is optional for some operations, don't fail readiness
            # overall_ready = False
    else:
        checks["redis"] = "not_configured"

    # Supabase/JWKS check (if configured)
    if settings.SUPABASE_URL:
        try:
            import httpx
            jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(jwks_url)
                resp.raise_for_status()
            checks["supabase_jwks"] = "ok"
        except Exception as e:
            checks["supabase_jwks"] = f"error: {type(e).__name__}"
            # JWKS failure means auth won't work
            overall_ready = False
    else:
        checks["supabase_jwks"] = "not_configured"

    return {
        "status": "ready" if overall_ready else "degraded",
        "checks": checks,
    }
