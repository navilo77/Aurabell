"""Unified exception hierarchy for Aura Bell authentication and authorization.

All auth/permission failures raise these exceptions so middleware can map them
to consistent HTTP responses (401 Unauthorized, 403 Forbidden).
"""

from __future__ import annotations


class AuthError(Exception):
    """Base class for all authentication/authorization failures.

    Attributes:
        code: Machine-readable error code for client handling.
        message: Human-readable description.
        status_code: HTTP status code to return (default 401).
    """

    code: str = "AUTH_ERROR"
    message: str = "Authentication failed"
    status_code: int = 401

    def __init__(self, message: str | None = None, code: str | None = None) -> None:
        if message:
            self.message = message
        if code:
            self.code = code
        super().__init__(self.message)


class InvalidTokenError(AuthError):
    """Raised when JWT signature verification fails or token is malformed."""

    code = "INVALID_TOKEN"
    message = "Invalid or malformed token"


class ExpiredTokenError(AuthError):
    """Raised when JWT `exp` claim has passed."""

    code = "TOKEN_EXPIRED"
    message = "Token has expired"


class InvalidIssuerError(AuthError):
    """Raised when JWT `iss` claim does not match expected Supabase issuer."""

    code = "INVALID_ISSUER"
    message = "Token issuer mismatch"


class InvalidAudienceError(AuthError):
    """Raised when JWT `aud` claim is not 'authenticated'."""

    code = "INVALID_AUDIENCE"
    message = "Token audience mismatch"


class JWKSFetchError(AuthError):
    """Raised when JWKS endpoint is unreachable or returns invalid keys."""

    code = "JWKS_UNAVAILABLE"
    message = "Unable to fetch signing keys"
    status_code = 503


class UserNotFoundError(AuthError):
    """Raised when token `sub` maps to no profile in database."""

    code = "USER_NOT_FOUND"
    message = "User not found"
    status_code = 401


class PermissionDenied(AuthError):
    """Raised when authenticated user lacks required role(s).

    Attributes:
        required_roles: Role names that were required.
        user_roles: Role names the user actually has.
    """

    code = "PERMISSION_DENIED"
    message = "Insufficient permissions"
    status_code = 403

    def __init__(
        self,
        required_roles: list[str] | None = None,
        user_roles: list[str] | None = None,
        message: str | None = None,
    ) -> None:
        self.required_roles = required_roles or []
        self.user_roles = user_roles or []
        if message:
            self.message = message
        super().__init__(self.message)


class RateLimitExceeded(AuthError):
    """Raised when auth endpoint rate limit is exceeded."""

    code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests"
    status_code = 429