"""JWT verification using Supabase GoTrue JWKS.

Fetches and caches JWKS from Supabase, validates JWT signature, iss, aud, exp.
All validation failures raise specific AuthError subclasses.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
from jose import jwt
from jose.exceptions import JOSEError

from app.core.config import settings
from app.core.exceptions import (
    AuthError,
    ExpiredTokenError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidTokenError,
    JWKSFetchError,
)

# ─── JWKS Cache ─────────────────────────────────────────────────────────────

_jwks_cache: dict[str, Any] | None = None
_jwks_fetched_at: float = 0.0
_JWKS_TTL_SECONDS = 3600  # 1 hour


def _get_supabase_base_url() -> str:
    """Return the configured Supabase base URL without trailing slash.

    Raises:
        JWKSFetchError: If SUPABASE_URL is not configured.
    """
    if not settings.SUPABASE_URL:
        raise JWKSFetchError(message="SUPABASE_URL is not configured")
    return settings.SUPABASE_URL.rstrip("/")


def _get_jwks_url() -> str:
    """Construct JWKS endpoint URL from Supabase URL."""
    base = _get_supabase_base_url()
    return f"{base}/auth/v1/.well-known/jwks.json"


def _get_expected_issuer() -> str:
    """Construct expected issuer from Supabase URL."""
    base = _get_supabase_base_url()
    return f"{base}/auth/v1"


async def _fetch_jwks() -> dict[str, Any]:
    """Fetch JWKS from Supabase GoTrue endpoint."""
    url = _get_jwks_url()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


async def get_jwks() -> dict[str, Any]:
    """Get JWKS, using cache if valid (1 hour TTL)."""
    global _jwks_cache, _jwks_fetched_at

    now = time.time()
    if _jwks_cache is not None and (now - _jwks_fetched_at) < _JWKS_TTL_SECONDS:
        return _jwks_cache

    try:
        _jwks_cache = await _fetch_jwks()
        _jwks_fetched_at = now
        return _jwks_cache
    except httpx.HTTPError as e:
        raise JWKSFetchError(message=f"Failed to fetch JWKS: {e}") from e
    except ValueError as e:
        raise JWKSFetchError(message=f"Invalid JWKS response: {e}") from e


# ─── Token Verification ─────────────────────────────────────────────────────


async def verify_token(token: str) -> dict[str, Any]:
    """Verify JWT token from Supabase GoTrue.

    Validates:
    - Signature using JWKS (ES256)
    - `iss` claim matches Supabase project issuer
    - `aud` claim equals "authenticated"
    - `exp` claim not in the past

    Args:
        token: Raw JWT string (without "Bearer " prefix)

    Returns:
        Decoded token payload (dict with sub, email, role, etc.)

    Raises:
        InvalidTokenError: Malformed token or signature verification failed
        ExpiredTokenError: Token `exp` claim has passed
        InvalidIssuerError: Token `iss` doesn't match expected Supabase issuer
        InvalidAudienceError: Token `aud` is not "authenticated"
        JWKSFetchError: JWKS endpoint unreachable (503)
    """
    if not token or not isinstance(token, str):
        raise InvalidTokenError(message="Token is empty")

    # Get JWKS for signature verification
    jwks = await get_jwks()

    expected_issuer = _get_expected_issuer()

    try:
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["ES256"],
            audience="authenticated",
            issuer=expected_issuer,
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iss": True,
                "verify_exp": True,
            },
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        raise ExpiredTokenError(message="Token has expired") from e
    except jwt.JWTClaimsError as e:
        # Check which claim failed
        error_msg = str(e).lower()
        if "audience" in error_msg or "aud" in error_msg:
            raise InvalidAudienceError(message="Token audience mismatch") from e
        if "issuer" in error_msg or "iss" in error_msg:
            raise InvalidIssuerError(message="Token issuer mismatch") from e
        # Other claims errors (exp already caught above)
        raise InvalidTokenError(message=f"Invalid token claims: {e}") from e
    except JOSEError as e:
        raise InvalidTokenError(message=f"Token verification failed: {e}") from e


# ─── Sync wrapper for non-async contexts (e.g., middleware) ─────────────────

# Note: verify_token is async due to JWKS fetch. For sync contexts, use
# verify_token_sync which requires pre-fetched JWKS (not recommended for production).
def verify_token_sync(token: str, jwks: dict[str, Any]) -> dict[str, Any]:
    """Synchronous token verification using pre-fetched JWKS.

    Use only in contexts where async is not available and JWKS is already cached.
    """
    expected_issuer = _get_expected_issuer()

    try:
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["ES256"],
            audience="authenticated",
            issuer=expected_issuer,
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iss": True,
                "verify_exp": True,
            },
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        raise ExpiredTokenError(message="Token has expired") from e
    except jwt.JWTClaimsError as e:
        error_msg = str(e).lower()
        if "audience" in error_msg or "aud" in error_msg:
            raise InvalidAudienceError(message="Token audience mismatch") from e
        if "issuer" in error_msg or "iss" in error_msg:
            raise InvalidIssuerError(message="Token issuer mismatch") from e
        raise InvalidTokenError(message=f"Invalid token claims: {e}") from e
    except JOSEError as e:
        raise InvalidTokenError(message=f"Token verification failed: {e}") from e