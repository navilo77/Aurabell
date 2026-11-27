"""Rate limiting middleware (BE-08): per-user token-bucket using Redis.

Implements configurable rate limits:
- Authenticated users: rate-limited by user identity
- Unauthenticated requests: rate-limited by IP
- Separate stricter limits for sensitive endpoints (auth, payment, community, admin)
- Graceful degradation when Redis is unavailable
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import redis.asyncio as redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings


@dataclass
class RateLimitConfig:
    """Rate limit configuration for an endpoint category."""

    requests_per_minute: int
    burst_allowance: int = 0


DEFAULT_LIMITS: dict[str, RateLimitConfig] = {
    "default": RateLimitConfig(requests_per_minute=settings.RATE_LIMIT_DEFAULT_PER_MINUTE, burst_allowance=10),
    "auth": RateLimitConfig(requests_per_minute=settings.RATE_LIMIT_AUTH_PER_MINUTE, burst_allowance=3),
    "payment": RateLimitConfig(requests_per_minute=settings.RATE_LIMIT_PAYMENT_PER_MINUTE, burst_allowance=2),
    "community": RateLimitConfig(requests_per_minute=settings.RATE_LIMIT_COMMUNITY_PER_MINUTE, burst_allowance=5),
    "admin": RateLimitConfig(requests_per_minute=settings.RATE_LIMIT_ADMIN_PER_MINUTE, burst_allowance=20),
}


ENDPOINT_CATEGORIES: dict[str, str] = {
    "/api/v1/auth/login": "auth",
    "/api/v1/auth/register": "auth",
    "/api/v1/auth/otp/request": "auth",
    "/api/v1/auth/otp/verify": "auth",
    "/api/v1/auth/refresh": "auth",
    "/api/v1/payments/initiate": "payment",
    "/api/v1/payments/verify": "payment",
    "/api/v1/payments/callback": "payment",
    "/api/v1/payments/ipn": "payment",
    "/api/v1/community/conversations": "community",
    "/api/v1/community/messages": "community",
    "/api/v1/admin": "admin",
}


def _get_category(path: str) -> str:
    """Determine rate limit category for a path."""
    for prefix, category in ENDPOINT_CATEGORIES.items():
        if path.startswith(prefix):
            return category
    return "default"


def _get_client_identifier(request: Request) -> tuple[str, str]:
    """Get rate limit key: (identifier_type, identifier_value).

    Returns ("user", user_id) for authenticated requests, ("ip", client_ip) for anonymous.
    """
    # Check for authenticated user (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user is not None:
        return "user", str(request.state.user.id)

    # Fall back to IP address
    client_host = request.client.host if request.client else "unknown"
    # Check for forwarded header (when behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_host = forwarded_for.split(",")[0].strip()
    return "ip", client_host


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token-bucket rate limiting with Redis backend.

    Graceful degradation: if Redis is unavailable, allows request through
    (fail-open) but logs the event. In production with strict security
    requirements, this could be changed to fail-closed.
    """

    def __init__(self, app, redis_client: redis.Redis | None = None):
        super().__init__(app)
        self._redis = redis_client
        self._own_redis = redis_client is None

    async def _get_redis(self) -> redis.Redis | None:
        """Get or create Redis connection."""
        if self._redis is not None:
            return self._redis

        if not settings.REDIS_URL:
            return None

        try:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            )
            # Test connection
            await self._redis.ping()
            return self._redis
        except Exception:
            # Redis unavailable - fail open
            self._redis = None
            return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Skip rate limiting for health checks
        if request.url.path in ("/health", "/health/ready", "/api/v1/health"):
            return await call_next(request)

        redis_client = await self._get_redis()
        if redis_client is None:
            # Redis unavailable - fail open (allow request)
            return await call_next(request)

        try:
            identifier_type, identifier = _get_client_identifier(request)
            category = _get_category(request.url.path)
            config = DEFAULT_LIMITS.get(category, DEFAULT_LIMITS["default"])

            key = f"ratelimit:{category}:{identifier_type}:{identifier}"
            now = time.time()
            window_start = int(now // 60) * 60  # Current minute window

            # Lua script for atomic token bucket
            lua_script = """
            local key = KEYS[1]
            local limit = tonumber(ARGV[1])
            local burst = tonumber(ARGV[2])
            local window = tonumber(ARGV[3])
            local now = tonumber(ARGV[4])

            local current = redis.call('GET', key)
            if current then
                local data = cjson.decode(current)
                if data.window == window then
                    data.count = data.count + 1
                else
                    data.count = 1
                    data.window = window
                end
                redis.call('SET', key, cjson.encode(data), 'EX', 120)
                return {data.count, limit + burst}
            else
                local data = {count = 1, window = window}
                redis.call('SET', key, cjson.encode(data), 'EX', 120)
                return {1, limit + burst}
            end
            """

            result = await redis_client.eval(
                lua_script,
                1,
                key,
                config.requests_per_minute,
                config.burst_allowance,
                window_start,
                now,
            )

            current_count = int(result[0])
            effective_limit = int(result[1])

            if current_count > effective_limit:
                # Rate limited
                retry_after = 60 - (now - window_start)
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded",
                        "code": "RATE_LIMIT_EXCEEDED",
                        "retry_after": int(retry_after) + 1,
                    },
                    headers={
                        "X-RateLimit-Limit": str(effective_limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(window_start + 60),
                        "Retry-After": str(int(retry_after) + 1),
                    },
                )

            # Add rate limit headers
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(effective_limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, effective_limit - current_count))
            response.headers["X-RateLimit-Reset"] = str(window_start + 60)
            return response

        except Exception:
            # Any Redis error - fail open
            return await call_next(request)

    async def close(self) -> None:
        """Close Redis connection if we created it."""
        if self._own_redis and self._redis:
            await self._redis.close()
            self._redis = None