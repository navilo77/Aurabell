"""Auth service - Supabase GoTrue integration.

Handles user authentication flows using Supabase Auth:
- Email/password login
- User registration
- OTP (magic link) request/verify
- Token refresh
"""

from __future__ import annotations

from supabase import create_client

from app.core.config import settings
from app.core.exceptions import AuthError, InvalidTokenError, RateLimitExceeded
from app.modules.auth.schema import (
    OTPRequest,
    OTPVerify,
    RefreshTokenRequest,
    Token,
    UserLogin,
    UserRegister,
)


class AuthService:
    """Supabase Auth service wrapper."""

    def __init__(self) -> None:
        self._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        self._admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    # ─── Email/Password Auth ────────────────────────────────────────────────

    async def login(self, credentials: UserLogin) -> Token:
        """Authenticate user with email and password."""
        try:
            resp = self._client.auth.sign_in_with_password({
                "email": credentials.email,
                "password": credentials.password,
            })
        except Exception as e:
            raise AuthError(message=f"Login failed: {e}", code="LOGIN_FAILED") from e

        if not resp.session:
            raise InvalidTokenError(message="Invalid credentials")

        return Token(
            access_token=resp.session.access_token,
            refresh_token=resp.session.refresh_token,
            expires_in=resp.session.expires_in,
        )

    async def register(self, data: UserRegister) -> Token:
        """Register new user with email and password."""
        try:
            resp = self._client.auth.sign_up({
                "email": data.email,
                "password": data.password,
                "options": {
                    "data": {
                        "full_name": data.full_name,
                        "phone": data.phone,
                    }
                },
            })
        except Exception as e:
            raise AuthError(message=f"Registration failed: {e}", code="REGISTRATION_FAILED") from e

        if not resp.session:
            # Email confirmation required - no session yet
            return Token(
                access_token="",
                refresh_token="",
                expires_in=0,
            )

        return Token(
            access_token=resp.session.access_token,
            refresh_token=resp.session.refresh_token,
            expires_in=resp.session.expires_in,
        )

    # ─── OTP (Magic Link) Auth ──────────────────────────────────────────────

    async def request_otp(self, data: OTPRequest) -> None:
        """Send OTP/magic link to user's email."""
        try:
            self._client.auth.sign_in_with_otp({
                "email": data.email,
                "options": {"should_create_user": True},
            })
        except Exception as e:
            raise AuthError(message=f"OTP request failed: {e}", code="OTP_REQUEST_FAILED") from e

    async def verify_otp(self, data: OTPVerify) -> Token:
        """Verify OTP code and return tokens."""
        try:
            resp = self._client.auth.verify_otp({
                "email": data.email,
                "token": data.code,
                "type": "email",
            })
        except Exception as e:
            raise AuthError(message=f"OTP verification failed: {e}", code="OTP_VERIFICATION_FAILED") from e

        if not resp.session:
            raise InvalidTokenError(message="Invalid or expired OTP code")

        return Token(
            access_token=resp.session.access_token,
            refresh_token=resp.session.refresh_token,
            expires_in=resp.session.expires_in,
        )

    # ─── Token Management ───────────────────────────────────────────────────

    async def refresh_token(self, data: RefreshTokenRequest) -> Token:
        """Refresh access token using refresh token."""
        try:
            resp = self._client.auth.refresh_session(data.refresh_token)
        except Exception as e:
            raise AuthError(message=f"Token refresh failed: {e}", code="TOKEN_REFRESH_FAILED") from e

        if not resp.session:
            raise InvalidTokenError(message="Invalid or expired refresh token")

        return Token(
            access_token=resp.session.access_token,
            refresh_token=resp.session.refresh_token,
            expires_in=resp.session.expires_in,
        )

    async def logout(self, access_token: str) -> None:
        """Sign out user (revokes session server-side)."""
        try:
            self._client.auth.sign_out()
        except Exception:
            # Best effort - token may already be expired
            pass

    # ─── Admin Operations (service role) ────────────────────────────────────

    async def admin_get_user(self, user_id: str):
        """Get user by ID (admin only)."""
        return self._admin_client.auth.admin.get_user_by_id(user_id)

    async def admin_delete_user(self, user_id: str) -> None:
        """Delete user (admin only)."""
        self._admin_client.auth.admin.delete_user(user_id)

    async def admin_update_user(self, user_id: str, data: dict):
        """Update user metadata (admin only)."""
        return self._admin_client.auth.admin.update_user_by_id(user_id, data)


# ─── Singleton Instance ─────────────────────────────────────────────────────

_auth_service: AuthService | None = None


def get_auth_service() -> AuthService:
    """Get or create AuthService singleton."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service