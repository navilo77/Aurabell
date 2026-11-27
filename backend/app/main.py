"""FastAPI application entrypoint for the Aura Bell backend.

Exposes health-check and all API routes under /api/v1.
Includes CORS, TrustedHost, HSTS, and secure cookie middleware.
"""

from __future__ import annotations

import asyncio
import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.database import async_session_factory
from app.core.idempotency import IdempotencyMiddleware
from app.core.logging import setup_logging
from app.core.rate_limit import RateLimitMiddleware
from app.core.reliability import RequestIdMiddleware, SecurityHeadersMiddleware
from app.api.v1.router import api_v1_router
from app.modules.health.router import router as health_router
from app.modules.pricing.service import PricingError

_cleanup_task: asyncio.Task | None = None
_rate_limit_middleware: RateLimitMiddleware | None = None
_CLEANUP_INTERVAL_SECONDS = 60


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    global _cleanup_task, _rate_limit_middleware

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Application starting up", extra={"env": settings.APP_ENV})

    async def cleanup_loop() -> None:
        while True:
            try:
                async with async_session_factory() as session:
                    from app.modules.inventory.service import InventoryService
                    svc = InventoryService(session)
                    count = await svc.cleanup_expired_reservations()
                    if count > 0:
                        logger.info("Inventory cleanup completed", extra={"expired_count": count})
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.exception("Inventory cleanup failed", extra={"error": str(e)})
            await asyncio.sleep(_CLEANUP_INTERVAL_SECONDS)

    _cleanup_task = asyncio.create_task(cleanup_loop())
    # Initialize rate limit middleware for proper cleanup
    _rate_limit_middleware = RateLimitMiddleware(app_instance)
    try:
        yield
    finally:
        logger.info("Application shutting down")
        if _cleanup_task:
            _cleanup_task.cancel()
            try:
                await _cleanup_task
            except asyncio.CancelledError:
                pass
        if _rate_limit_middleware:
            await _rate_limit_middleware.close()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Aura Bell multi-store e-commerce backend API.",
    lifespan=lifespan,
)


@app.exception_handler(PricingError)
async def handle_pricing_error(request: Request, exc: PricingError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler - no stack traces in production responses."""
    logger = logging.getLogger(__name__)
    request_id = getattr(request.state, "request_id", "unknown")

    # Log full exception server-side
    logger.error(
        "Unhandled exception",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
        exc_info=True,
    )

    # Production-safe response
    if settings.APP_ENV == "production":
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "code": "INTERNAL_ERROR"},
        )

    # Development: include error details for debugging
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "code": "INTERNAL_ERROR",
            "error": str(exc),
            "type": type(exc).__name__,
        },
    )


# ─── Security Middleware ────────────────────────────────────────────────────

# TrustedHost - validates Host header against allowed hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.trusted_hosts_list,
)

# CORS - configure for frontend origin(s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# Session middleware for secure cookies (HSTS, secure, httponly, samesite)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    session_cookie="aura_session",
    max_age=86400,  # 24 hours
    same_site=settings.SESSION_COOKIE_SAMESITE,
    https_only=settings.SESSION_COOKIE_SECURE,  # Set True in production behind HTTPS
)

# Rate limiting middleware (BE-08) - token bucket with Redis
app.add_middleware(RateLimitMiddleware)

# Idempotency middleware - protects mutating endpoints from duplicate execution
app.add_middleware(IdempotencyMiddleware)

# BE-08: Request ID + security headers
app.add_middleware(RequestIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# HSTS header - enforce HTTPS
@app.middleware("http")
async def add_hsts_header(request, call_next):
    response = await call_next(request)
    if settings.APP_ENV == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return response


# ─── API Routes ─────────────────────────────────────────────────────────────

app.include_router(api_v1_router, prefix="/api/v1")

# Health endpoints at root level for backward compatibility
# (also available under /api/v1/health via api_v1_router)
app.include_router(health_router)