"""Redis-based OTP storage for COD verification.

Provides durable, shared OTP storage with TTL, attempt limiting,
and atomic operations suitable for multi-worker deployments.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Any

import redis.asyncio as redis

from app.core.config import settings


_OTP_PREFIX = "cod_otp:"
_OTP_TTL_SECONDS = 5 * 60  # 5 minutes
_MAX_ATTEMPTS = 3


class CODOTPStore:
    """Redis-backed COD OTP store with TTL and attempt limiting."""

    def __init__(self, redis_client: redis.Redis | None = None):
        self._redis = redis_client
        self._own_redis = redis_client is None

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis is not None:
            return self._redis

        if not settings.REDIS_URL:
            raise RuntimeError("REDIS_URL not configured")

        self._redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
        )
        await self._redis.ping()
        return self._redis

    def _key(self, order_id: str) -> str:
        return f"{_OTP_PREFIX}{order_id}"

    async def store_otp(self, order_id: str, otp: str) -> None:
        """Store OTP with expiry and attempt tracking."""
        client = await self._get_redis()
        data = {
            "otp": otp,
            "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=_OTP_TTL_SECONDS)).isoformat(),
            "attempts": 0,
        }
        await client.setex(
            self._key(order_id),
            _OTP_TTL_SECONDS,
            json.dumps(data),
        )

    async def verify_otp(self, order_id: str, otp_code: str) -> tuple[bool, str]:
        """Verify COD OTP atomically. Returns (success, message)."""
        client = await self._get_redis()
        key = self._key(order_id)

        # Use Lua script for atomic check-and-update
        lua_script = """
        local key = KEYS[1]
        local otp_code = ARGV[1]
        local max_attempts = tonumber(ARGV[2])

        local data = redis.call('GET', key)
        if not data then
            return {0, "OTP not found or expired"}
        end

        local otp_data = cjson.decode(data)
        local expires_at = otp_data.expires_at
        local now = ARGV[3]

        if now > expires_at then
            redis.call('DEL', key)
            return {0, "OTP has expired"}
        end

        if otp_data.attempts >= max_attempts then
            redis.call('DEL', key)
            return {0, "Maximum OTP attempts exceeded"}
        end

        otp_data.attempts = otp_data.attempts + 1

        if otp_data.otp ~= otp_code then
            local remaining = max_attempts - otp_data.attempts
            redis.call('SET', key, cjson.encode(otp_data), 'EX', ARGV[4])
            return {0, "Invalid OTP. " .. remaining .. " attempts remaining"}
        end

        -- Success - remove OTP
        redis.call('DEL', key)
        return {1, "OTP verified successfully"}
        """

        now_iso = datetime.now(timezone.utc).isoformat()
        ttl_remaining = _OTP_TTL_SECONDS

        result = await client.eval(
            lua_script,
            1,
            key,
            otp_code,
            str(_MAX_ATTEMPTS),
            now_iso,
            str(ttl_remaining),
        )

        success = int(result[0])
        message = result[1]
        return success == 1, message

    async def close(self) -> None:
        """Close Redis connection if we created it."""
        if self._own_redis and self._redis:
            await self._redis.close()
            self._redis = None


# Global instance for dependency injection
_cod_otp_store: CODOTPStore | None = None


async def get_cod_otp_store() -> CODOTPStore:
    """Get or create CODOTPStore singleton."""
    global _cod_otp_store
    if _cod_otp_store is None:
        _cod_otp_store = CODOTPStore()
    return _cod_otp_store