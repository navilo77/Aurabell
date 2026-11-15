"""FastAPI application entrypoint for the Aura Bell backend.

Exposes health-check and all API routes under /api/v1.
Includes CORS, TrustedHost, HSTS, and secure cookie middleware.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.stores.router import router as stores_router
from app.modules.users.router import router as users_router

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Aura Bell multi-store e-commerce backend API.",
)

# ─── Security Middleware ────────────────────────────────────────────────────

# TrustedHost - validates Host header against allowed hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost", "testserver"],
)

# CORS - configure for frontend origin(s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# Session middleware for secure cookies (HSTS, secure, httponly, samesite)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SUPABASE_SERVICE_ROLE_KEY or "dev-secret-change-in-production",
    session_cookie="aura_session",
    max_age=86400,  # 24 hours
    same_site="lax",
    https_only=False,  # Set True in production behind HTTPS
)

# HSTS header - enforce HTTPS
@app.middleware("http")
async def add_hsts_header(request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return response


# ─── API Routes ─────────────────────────────────────────────────────────────

app.include_router(auth_router, prefix="/api/v1")
app.include_router(stores_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    """Liveness probe. Returns ``{"status": "ok"}``."""
    return {"status": "ok"}