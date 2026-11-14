"""Authentication and authorization test suite for Aura Bell backend.

Tests cover:
- JWT token verification (valid, expired, invalid signature, wrong iss/aud)
- get_current_user dependency (loads user + roles from DB)
- require_role factory (allows/denies based on roles)
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jose import jwt

from app.core.exceptions import (
    AuthError,
    ExpiredTokenError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidTokenError,
    JWKSFetchError,
    PermissionDenied,
    UserNotFoundError,
    RateLimitExceeded,
)


# ─── TestVerifyToken ────────────────────────────────────────────────────────


class TestVerifyToken:
    """Tests for security.verify_token() function."""

    @pytest.mark.asyncio
    async def test_verify_token_valid(self) -> None:
        """Valid token with correct signature, iss, aud, exp → returns payload."""
        from app.core.security import verify_token

        mock_payload = {
            "sub": "test-user-id-123",
            "email": "test@example.com",
            "role": "authenticated",
            "aud": "authenticated",
            "iss": "http://localhost:54331/auth/v1",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        }

        with patch("app.core.security.get_jwks", new=AsyncMock(return_value={"keys": []})):
            with patch("jose.jwt.decode", return_value=mock_payload):
                payload = await verify_token("valid-token")

        assert payload["sub"] == "test-user-id-123"
        assert payload["email"] == "test@example.com"
        assert payload["aud"] == "authenticated"

    @pytest.mark.asyncio
    async def test_verify_token_expired(self) -> None:
        """Token with past exp claim → raises ExpiredTokenError."""
        from app.core.security import verify_token
        from jose import ExpiredSignatureError

        with patch("app.core.security.get_jwks", new=AsyncMock(return_value={"keys": []})):
            with patch("jose.jwt.decode", side_effect=ExpiredSignatureError()):
                with pytest.raises(ExpiredTokenError):
                    await verify_token("expired-token")

    @pytest.mark.asyncio
    async def test_verify_token_invalid_signature(self) -> None:
        """Token with wrong signature → raises InvalidTokenError."""
        from app.core.security import verify_token
        from jose import JWSError

        with patch("app.core.security.get_jwks", new=AsyncMock(return_value={"keys": []})):
            with patch("jose.jwt.decode", side_effect=JWSError("Invalid signature")):
                with pytest.raises(InvalidTokenError):
                    await verify_token("invalid-sig-token")

    @pytest.mark.asyncio
    async def test_verify_token_wrong_issuer(self) -> None:
        """Token with mismatched iss claim → raises InvalidIssuerError."""
        from app.core.security import verify_token
        from jose.exceptions import JWTClaimsError

        with patch("app.core.security.get_jwks", new=AsyncMock(return_value={"keys": []})):
            with patch("jose.jwt.decode", side_effect=JWTClaimsError("Invalid issuer")):
                with pytest.raises(InvalidIssuerError):
                    await verify_token("wrong-issuer-token")

    @pytest.mark.asyncio
    async def test_verify_token_wrong_audience(self) -> None:
        """Token with aud != 'authenticated' → raises InvalidAudienceError."""
        from app.core.security import verify_token
        from jose.exceptions import JWTClaimsError

        with patch("app.core.security.get_jwks", new=AsyncMock(return_value={"keys": []})):
            with patch("jose.jwt.decode", side_effect=JWTClaimsError("Invalid audience")):
                with pytest.raises(InvalidAudienceError):
                    await verify_token("wrong-aud-token")

    @pytest.mark.asyncio
    async def test_verify_token_jwks_unavailable(self) -> None:
        """JWKS endpoint unreachable → raises JWKSFetchError (503)."""
        from app.core.security import verify_token

        with patch("app.core.security.get_jwks", new=AsyncMock(side_effect=JWKSFetchError())):
            with pytest.raises(JWKSFetchError):
                await verify_token("any-token")

    @pytest.mark.asyncio
    async def test_verify_token_empty_token(self) -> None:
        """Empty token → raises InvalidTokenError."""
        from app.core.security import verify_token

        with pytest.raises(InvalidTokenError, match="Token is empty"):
            await verify_token("")

        with pytest.raises(InvalidTokenError, match="Token is empty"):
            await verify_token(None)  # type: ignore[arg-type]


# ─── TestGetCurrentUser ─────────────────────────────────────────────────────


class TestGetCurrentUser:
    """Tests for auth.get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_loads_roles(self) -> None:
        """Valid token → fetches profile + user_roles + roles → returns User with roles list."""
        from app.core.auth import get_current_user

        # Mock request with state
        request = MagicMock()
        request.state = MagicMock()
        request.state.user = None

        # Mock credentials
        credentials = MagicMock()
        credentials.credentials = "valid-token"

        # Mock database session
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(role_name="store_manager"),
            MagicMock(role_name="customer"),
        ]
        db.execute.return_value = mock_result

        # Mock verify_token
        with patch("app.core.auth.verify_token", new=AsyncMock(return_value={
            "sub": "user-123",
            "email": "test@example.com",
        })):
            user = await get_current_user(request, credentials, db)

        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert set(user.roles) == {"store_manager", "customer"}
        # Verify cached in request.state
        assert request.state.user is user

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self) -> None:
        """Token sub maps to no profile → raises UserNotFoundError (401)."""
        from app.core.auth import get_current_user
        from fastapi import HTTPException

        request = MagicMock()
        request.state = MagicMock()
        request.state.user = None

        credentials = MagicMock()
        credentials.credentials = "valid-token"

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []  # No rows = user not found
        db.execute.return_value = mock_result

        with patch("app.core.auth.verify_token", new=AsyncMock(return_value={
            "sub": "nonexistent-user",
            "email": "test@example.com",
        })):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(request, credentials, db)

        assert exc_info.value.status_code == 401
        assert "User not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_caches_in_request_state(self) -> None:
        """Second call within same request returns cached user from request.state.user."""
        from app.core.auth import get_current_user, User

        request = MagicMock()
        request.state = MagicMock()

        # Pre-populate cached user
        cached_user = User(id="user-123", email="test@example.com", roles=["customer"])
        request.state.user = cached_user

        credentials = MagicMock()
        credentials.credentials = "valid-token"
        db = AsyncMock()

        # Should return cached user without calling verify_token or db
        user = await get_current_user(request, credentials, db)

        assert user is cached_user
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_current_user_missing_auth_header(self) -> None:
        """Missing Authorization header → raises 401."""
        from app.core.auth import get_current_user
        from fastapi import HTTPException

        request = MagicMock()
        request.state = MagicMock()
        request.state.user = None

        credentials = None  # No auth header

        db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, credentials, db)

        assert exc_info.value.status_code == 401
        assert "Missing authorization header" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_missing_sub_claim(self) -> None:
        """Token missing 'sub' claim → raises 401."""
        from app.core.auth import get_current_user
        from fastapi import HTTPException

        request = MagicMock()
        request.state = MagicMock()
        request.state.user = None

        credentials = MagicMock()
        credentials.credentials = "valid-token"

        db = AsyncMock()

        with patch("app.core.auth.verify_token", new=AsyncMock(return_value={
            "email": "test@example.com",  # No 'sub'
        })):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(request, credentials, db)

        assert exc_info.value.status_code == 401
        assert "Token missing 'sub' claim" in exc_info.value.detail


# ─── TestRequireRole ────────────────────────────────────────────────────────


class TestRequireRole:
    """Tests for auth.require_role factory."""

    @pytest.mark.asyncio
    async def test_require_role_allows_matching_role(self) -> None:
        """User has one of required roles → dependency passes."""
        from app.core.auth import require_role, User

        user = User(id="user-123", email="test@example.com", roles=["store_manager", "customer"])
        checker = require_role("store_manager", "admin")

        # Call the checker directly with mocked dependency
        result = await checker(user=user)
        assert result is user

    @pytest.mark.asyncio
    async def test_require_role_denies_missing_role(self) -> None:
        """User lacks all required roles → raises PermissionDenied (403)."""
        from app.core.auth import require_role, User
        from fastapi import HTTPException

        user = User(id="user-123", email="test@example.com", roles=["customer"])
        checker = require_role("store_manager", "admin")

        with pytest.raises(HTTPException) as exc_info:
            await checker(user=user)

        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_role_multiple_allowed(self) -> None:
        """require_role('admin', 'owner') allows user with either role."""
        from app.core.auth import require_role, User

        # User with admin role
        user_admin = User(id="user-1", email="admin@test.com", roles=["admin"])
        checker = require_role("admin", "owner")
        result = await checker(user=user_admin)
        assert result is user_admin

        # User with owner role
        user_owner = User(id="user-2", email="owner@test.com", roles=["owner"])
        result = await checker(user=user_owner)
        assert result is user_owner

    @pytest.mark.asyncio
    async def test_require_role_empty_raises(self) -> None:
        """require_role() with no args → raises ValueError at creation time."""
        from app.core.auth import require_role

        with pytest.raises(ValueError, match="at least one role"):
            require_role()


# ─── Exception Hierarchy Tests ─────────────────────────────────────────────


class TestExceptions:
    """Verify exception classes have correct codes and status codes."""

    def test_auth_error_defaults(self) -> None:
        err = AuthError()
        assert err.code == "AUTH_ERROR"
        assert err.status_code == 401

    def test_auth_error_custom_message(self) -> None:
        err = AuthError(message="Custom msg")
        assert err.message == "Custom msg"

    def test_auth_error_custom_code(self) -> None:
        err = AuthError(code="CUSTOM_CODE")
        assert err.code == "CUSTOM_CODE"

    def test_invalid_token_error(self) -> None:
        err = InvalidTokenError()
        assert err.code == "INVALID_TOKEN"
        assert err.status_code == 401

    def test_expired_token_error(self) -> None:
        err = ExpiredTokenError()
        assert err.code == "TOKEN_EXPIRED"
        assert err.status_code == 401

    def test_invalid_issuer_error(self) -> None:
        err = InvalidIssuerError()
        assert err.code == "INVALID_ISSUER"
        assert err.status_code == 401

    def test_invalid_audience_error(self) -> None:
        err = InvalidAudienceError()
        assert err.code == "INVALID_AUDIENCE"
        assert err.status_code == 401

    def test_jwks_fetch_error(self) -> None:
        err = JWKSFetchError()
        assert err.code == "JWKS_UNAVAILABLE"
        assert err.status_code == 503

    def test_user_not_found_error(self) -> None:
        err = UserNotFoundError()
        assert err.code == "USER_NOT_FOUND"
        assert err.status_code == 401

    def test_permission_denied_defaults(self) -> None:
        err = PermissionDenied()
        assert err.code == "PERMISSION_DENIED"
        assert err.status_code == 403
        assert err.required_roles == []
        assert err.user_roles == []

    def test_permission_denied_with_roles(self) -> None:
        err = PermissionDenied(
            required_roles=["admin", "owner"],
            user_roles=["customer"],
        )
        assert err.required_roles == ["admin", "owner"]
        assert err.user_roles == ["customer"]

    def test_rate_limit_exceeded(self) -> None:
        err = RateLimitExceeded()
        assert err.code == "RATE_LIMIT_EXCEEDED"
        assert err.status_code == 429


# ─── Integration Test Placeholders ─────────────────────────────────────────


class TestAuthIntegration:
    """End-to-end auth flow tests (require running Supabase local)."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_login_flow(self, supabase_anon_client) -> None:
        """POST /auth/login → returns access + refresh token."""
        pytest.skip("Implementation pending: auth router not yet created")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_register_flow(self, supabase_anon_client) -> None:
        """POST /auth/register → creates user + profile → returns tokens."""
        pytest.skip("Implementation pending: auth router not yet created")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_otp_request_verify(self, supabase_anon_client) -> None:
        """POST /auth/otp/request → POST /auth/otp/verify → returns tokens."""
        pytest.skip("Implementation pending: auth router not yet created")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_protected_endpoint_requires_auth(self) -> None:
        """GET /users/me without token → 401."""
        pytest.skip("Implementation pending: users router not yet created")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rbac_store_manager_only(self) -> None:
        """Endpoint with require_role('store_manager') → 403 for customer."""
        pytest.skip("Implementation pending: users router not yet created")