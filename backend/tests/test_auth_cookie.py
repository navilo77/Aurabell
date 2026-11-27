"""Cookie-based authentication unit tests for Aura Bell backend.

Tests cover:
- get_current_user reads HttpOnly cookie (primary)
- Missing token → 401
- ProfileRead schema includes roles + store_ids
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.auth import get_current_user, get_optional_user
from app.modules.users.schema import ProfileRead


class TestGetCurrentUserCookie:
    """Tests for cookie-primary get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_from_cookie(self) -> None:
        """Valid aura_access_token cookie → loads user + roles from DB."""
        from app.core.auth import User

        request = MagicMock()
        request.state = MagicMock()
        request.state.user = None
        request.cookies.get = MagicMock(return_value="valid-cookie-token")

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(role_name="store_manager", store_id="store-1"),
            MagicMock(role_name="customer", store_id=None),
        ]
        db.execute.return_value = mock_result

        with patch("app.core.auth.verify_token", new=AsyncMock(return_value={
            "sub": "user-123",
            "email": "test@example.com",
        })):
            user = await get_current_user(request, db)

        assert user.id == "user-123"
        assert user.email == "test@example.com"
        assert set(user.roles) == {"store_manager", "customer"}
        assert user.store_ids == ["store-1"]
        # Verify cookie was consulted
        request.cookies.get.assert_called_with("aura_access_token")

    @pytest.mark.asyncio
    async def test_get_current_user_missing_both(self) -> None:
        """No cookie and no Bearer header → raises 401."""
        from fastapi import HTTPException

        request = MagicMock()
        request.state = MagicMock()
        request.state.user = None
        request.cookies.get = MagicMock(return_value=None)

        db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, db)

        assert exc_info.value.status_code == 401
        assert "Missing authorization header" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_cookie_takes_priority(self) -> None:
        """Valid cookie token → loads user from cookie only."""
        request = MagicMock()
        request.state = MagicMock()
        request.state.user = None
        request.cookies.get = MagicMock(return_value="cookie-token")

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(role_name="customer", store_id=None),
        ]
        db.execute.return_value = mock_result

        with patch("app.core.auth.verify_token", new=AsyncMock(return_value={
            "sub": "user-cookie",
            "email": "cookie@example.com",
        })) as mock_verify:
            user = await get_current_user(request, db)

        assert user.id == "user-cookie"
        # verify_token should have been called with cookie token
        mock_verify.assert_called_once_with("cookie-token")

    @pytest.mark.asyncio
    async def test_get_optional_user_from_cookie(self) -> None:
        """get_optional_user with valid cookie → returns User."""
        from app.core.auth import User

        request = MagicMock()
        request.state = MagicMock()
        request.state.user = None
        request.cookies.get = MagicMock(return_value="valid-cookie-token")

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(role_name="customer", store_id=None),
        ]
        db.execute.return_value = mock_result

        with patch("app.core.auth.verify_token", new=AsyncMock(return_value={
            "sub": "user-opt",
            "email": "opt@example.com",
        })):
            user = await get_optional_user(request, db)

        assert user is not None
        assert user.id == "user-opt"

    @pytest.mark.asyncio
    async def test_get_current_user_bearer_only_returns_401(self) -> None:
        """Valid Bearer token without cookie → raises 401 (Bearer fallback removed)."""
        from app.core.auth import verify_token

        request = MagicMock()
        request.state = MagicMock()
        request.state.user = None
        request.cookies.get = MagicMock(return_value=None)

        db = AsyncMock()

        mock_verify = AsyncMock()
        with patch("app.core.auth.verify_token", new=mock_verify):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(request, db)

        assert exc_info.value.status_code == 401
        assert "Missing authorization header" in exc_info.value.detail

        # verify_token should never be called for requests without a cookie
        mock_verify.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_optional_user_missing_both(self) -> None:
        """get_optional_user with no cookie → returns None."""
        request = MagicMock()
        request.state = MagicMock()
        request.state.user = None
        request.cookies.get = MagicMock(return_value=None)

        db = AsyncMock()

        user = await get_optional_user(request, db)
        assert user is None


class TestProfileReadSchema:
    """Tests for ProfileRead schema including roles + store_ids."""

    def test_profile_read_has_roles_and_store_ids(self) -> None:
        """ProfileRead includes roles: list[str] and store_ids: list[str] fields."""
        profile = ProfileRead(
            id="user-123",
            email="test@example.com",
            full_name="Test User",
            phone=None,
            avatar_url=None,
            status="active",
            roles=["customer", "store_manager"],
            store_ids=["store-1"],
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        assert profile.id == "user-123"
        assert profile.roles == ["customer", "store_manager"]
        assert profile.store_ids == ["store-1"]

    def test_profile_read_defaults_empty_lists(self) -> None:
        """roles and store_ids default to empty lists when not provided."""
        profile = ProfileRead(
            id="user-123",
            email="test@example.com",
            full_name=None,
            phone=None,
            avatar_url=None,
            status="active",
            roles=[],
            store_ids=[],
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        assert profile.roles == []
        assert profile.store_ids == []


class TestLogoutCookieClearing:
    """Tests for /auth/logout cookie deletion behavior."""

    @pytest.mark.asyncio
    async def test_logout_clears_both_cookies(self) -> None:
        """Logout deletes both aura_access_token and aura_refresh_token cookies."""
        from app.modules.auth.router import logout
        from fastapi import Response

        request = MagicMock()
        request.cookies.get = MagicMock(return_value="valid-access-token")

        response = Response()
        response.status_code = 200

        auth_service = MagicMock()
        auth_service.logout = AsyncMock()

        with patch("app.modules.auth.router.get_auth_service", return_value=auth_service):
            result = await logout(request, response)

        assert result.status_code == 204
        # Verify both cookies were deleted
        delete_calls = response.headers.getlist("set-cookie")
        cookie_names = []
        for header in delete_calls:
            if header.startswith("aura_access_token=") or header.startswith("aura_refresh_token="):
                name = header.split("=")[0]
                cookie_names.append(name)
        assert "aura_access_token" in cookie_names
        assert "aura_refresh_token" in cookie_names
        # Verify deletion attributes (Max-Age=0 or expired)
        for header in delete_calls:
            if header.startswith("aura_access_token="):
                assert "Max-Age=0" in header or "expires=" in header
                assert "Path=/" in header

    @pytest.mark.asyncio
    async def test_logout_safe_without_session(self) -> None:
        """Logout returns 204 even when no access token cookie is present."""
        from app.modules.auth.router import logout
        from fastapi import Response

        request = MagicMock()
        request.cookies.get = MagicMock(return_value=None)

        response = Response()

        auth_service = MagicMock()
        auth_service.logout = AsyncMock()

        with patch("app.modules.auth.router.get_auth_service", return_value=auth_service):
            result = await logout(request, response)

        assert result.status_code == 204
        # Cookies should still be cleared (best-effort)
        delete_calls = response.headers.getlist("set-cookie")
        cookie_names = []
        for header in delete_calls:
            if header.startswith("aura_access_token=") or header.startswith("aura_refresh_token="):
                name = header.split("=")[0]
                cookie_names.append(name)
        assert "aura_access_token" in cookie_names
        assert "aura_refresh_token" in cookie_names


# ─── Login Cookie Attributes (P-02 regression guard) ─────────────────────────


class TestLoginCookieAttributes:
    """Tests that login sets cookies with correct attributes (P-02)."""

    @pytest.mark.asyncio
    async def test_login_sets_cookie_attributes(self) -> None:
        """Set-Cookie must include HttpOnly, SameSite=Lax, Path=/; Secure only when configured."""
        from app.modules.auth.router import login
        from app.modules.auth.schema import Token, UserLogin
        from app.core.config import settings
        from fastapi import Response

        token = Token(access_token="access-x", refresh_token="refresh-x", expires_in=3600)
        auth_service = MagicMock()
        auth_service.login = AsyncMock(return_value=token)

        response = Response()
        with patch("app.modules.auth.router.get_auth_service", return_value=auth_service):
            await login(
                UserLogin(email="user@example.com", password="TestPass123!"),
                response,
            )

        headers = response.headers.getlist("set-cookie")
        access = next(h for h in headers if h.startswith("aura_access_token="))
        refresh = next(h for h in headers if h.startswith("aura_refresh_token="))
        for header in (access, refresh):
            assert "HttpOnly" in header
            assert "samesite=lax" in header.lower()
            assert "Path=/" in header
        # Secure flag must reflect SESSION_COOKIE_SECURE (False in dev)
        if settings.SESSION_COOKIE_SECURE:
            assert "Secure" in access
        else:
            assert "Secure" not in access


# ─── Registration + Profile Creation ────────────────────────────────────────


class TestRegisterProfileCreation:
    """Tests for registration with automatic public.profiles creation."""

    @pytest.mark.asyncio
    async def test_register_creates_auth_user_and_profile(self) -> None:
        """register() creates Supabase Auth user + public.profiles row (Case A: session exists)."""
        from app.modules.auth.service import AuthService
        from app.modules.auth.schema import UserRegister

        mock_client = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_session = MagicMock()
        mock_session.access_token = "access-token"
        mock_session.refresh_token = "refresh-token"
        mock_session.expires_in = 3600
        mock_resp = MagicMock()
        mock_resp.user = mock_user
        mock_resp.session = mock_session
        mock_client.auth.sign_up = MagicMock(return_value=mock_resp)

        mock_db = AsyncMock()

        with patch("app.modules.auth.service.create_client", return_value=mock_client):
            service = AuthService()
            token = await service.register(
                UserRegister(email="test@example.com", password="TestPass123!", full_name="Test User"),
                mock_db,
            )

        assert token.access_token == "access-token"
        assert token.refresh_token == "refresh-token"
        assert token.expires_in == 3600
        # Verify profile insert was called against public.profiles
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()
        call_args = mock_db.execute.call_args
        sql_text = str(call_args[0][0])
        assert "public.profiles" in sql_text
        assert "VALUES" in sql_text
        params = call_args[0][1]
        assert params["id"] == "user-123"
        assert params["email"] == "test@example.com"
        assert params["full_name"] == "Test User"
        assert params["phone"] is None

    @pytest.mark.asyncio
    async def test_register_confirmation_required_creates_profile_no_session(self) -> None:
        """Registration without session still creates profile, returns empty token (Case B)."""
        from app.modules.auth.service import AuthService
        from app.modules.auth.schema import UserRegister

        mock_client = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "user-456"
        mock_resp = MagicMock()
        mock_resp.user = mock_user
        mock_resp.session = None
        mock_client.auth.sign_up = MagicMock(return_value=mock_resp)

        mock_db = AsyncMock()

        with patch("app.modules.auth.service.create_client", return_value=mock_client):
            service = AuthService()
            token = await service.register(
                UserRegister(email="confirm@example.com", password="TestPass123!"),
                mock_db,
            )

        assert token.access_token == ""
        assert token.refresh_token == ""
        assert token.expires_in == 0
        # Profile should still be created even without session
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()
        params = mock_db.execute.call_args[0][1]
        assert params["id"] == "user-456"
        assert params["email"] == "confirm@example.com"

    @pytest.mark.asyncio
    async def test_register_profile_insert_failure_raises(self) -> None:
        """Profile insertion failure → AuthError, no silent success."""
        from app.modules.auth.service import AuthService
        from app.modules.auth.schema import UserRegister
        from app.core.exceptions import AuthError

        mock_client = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "user-789"
        mock_session = MagicMock()
        mock_session.access_token = "access-token"
        mock_session.refresh_token = "refresh-token"
        mock_session.expires_in = 3600
        mock_resp = MagicMock()
        mock_resp.user = mock_user
        mock_resp.session = mock_session
        mock_client.auth.sign_up = MagicMock(return_value=mock_resp)

        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("DB connection lost")

        with patch("app.modules.auth.service.create_client", return_value=mock_client):
            service = AuthService()
            with pytest.raises(AuthError) as exc_info:
                await service.register(
                    UserRegister(email="fail@example.com", password="TestPass123!"),
                    mock_db,
                )

        assert exc_info.value.code == "PROFILE_CREATION_FAILED"
        assert exc_info.value.status_code == 500
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_profile_duplicate_raises_409(self) -> None:
        """Duplicate profile constraint → AuthError 409."""
        from app.modules.auth.service import AuthService
        from app.modules.auth.schema import UserRegister
        from app.core.exceptions import AuthError
        from sqlalchemy.exc import IntegrityError

        mock_client = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "user-dup"
        mock_session = MagicMock()
        mock_session.access_token = "access-token"
        mock_session.refresh_token = "refresh-token"
        mock_session.expires_in = 3600
        mock_resp = MagicMock()
        mock_resp.user = mock_user
        mock_resp.session = mock_session
        mock_client.auth.sign_up = MagicMock(return_value=mock_resp)

        mock_db = AsyncMock()
        mock_db.execute.side_effect = IntegrityError("duplicate key", None, None)

        with patch("app.modules.auth.service.create_client", return_value=mock_client):
            service = AuthService()
            with pytest.raises(AuthError) as exc_info:
                await service.register(
                    UserRegister(email="dup@example.com", password="TestPass123!"),
                    mock_db,
                )

        assert exc_info.value.code == "PROFILE_ALREADY_EXISTS"
        assert exc_info.value.status_code == 409
        mock_db.rollback.assert_called_once()
