"""Authentication dependencies for FastAPI routes.

Provides:
- get_current_user: Extracts and validates JWT, loads user + roles from DB
- require_role: Factory for role-based access control dependencies
"""

from __future__ import annotations

from collections.abc import Awaitable
from dataclasses import dataclass, field
from typing import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import (
    AuthError,
    PermissionDenied,
    UserNotFoundError,
)
from app.core.security import verify_token


# ─── Security Scheme ────────────────────────────────────────────────────────

bearer_scheme = HTTPBearer(auto_error=False)


# ─── User Model ─────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class User:
    """Authenticated user with roles and store scoping.

    Attributes:
        id: User UUID (from JWT `sub` claim)
        email: User email (from JWT `email` claim or profile)
        roles: List of role names (e.g., ["store_manager", "customer"])
        store_ids: List of store UUIDs this user is associated with via
            ``user_roles.store_id``. Empty for customers (no store scope),
            populated for store managers and super admins.
    """

    id: str
    email: str
    roles: list[str]
    store_ids: list[str] = field(default_factory=list)


# ─── get_current_user Dependency ────────────────────────────────────────────


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency that returns the authenticated user.

    Flow:
    1. Extract token from HttpOnly cookie (primary) or Bearer header (migration fallback)
    2. Verify JWT signature, iss, aud, exp via verify_token()
    3. Fetch profile + user_roles + roles from database
    4. Cache User in request.state.user for subsequent calls
    5. Return User(id, email, roles)

    Raises:
        HTTPException 401: Missing/invalid/expired token, user not found
        HTTPException 503: JWKS unavailable
    """
    # Return cached user if already loaded in this request
    if hasattr(request.state, "user") and request.state.user is not None:
        return request.state.user

    # Extract token: HttpOnly cookie primary, Bearer header as migration fallback
    token = request.cookies.get("aura_access_token")
    if not isinstance(token, str):
        token = None
    if token is None and credentials is not None:
        token = credentials.credentials

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = await verify_token(token)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"} if e.status_code == 401 else {},
        ) from e

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("email", "")

    # Fetch user roles from database
    from app.core.config import settings

    # Query profiles + user_roles + roles
    query = text("""
        SELECT p.id, p.email, r.name as role_name, ur.store_id
        FROM public.profiles p
        LEFT JOIN public.user_roles ur ON ur.user_id = p.id
        LEFT JOIN public.roles r ON r.id = ur.role_id
        WHERE p.id = :user_id
    """)

    result = await db.execute(query, {"user_id": user_id})
    rows = result.fetchall()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    roles = [row.role_name for row in rows if row.role_name is not None]
    # Collect store_ids from user_roles (for store_manager role scoping)
    store_ids = [str(row.store_id) for row in rows if row.store_id is not None]
    user = User(id=user_id, email=email or rows[0].email, roles=roles, store_ids=store_ids)

    # Cache in request state
    request.state.user = user
    return user


# ─── require_role Factory ───────────────────────────────────────────────────


def require_role(*required_roles: str) -> Callable[[], Awaitable[User]]:
    """Create a FastAPI dependency that requires specific role(s).

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role("admin", "owner"))):
            ...

    Args:
        *required_roles: One or more role names. User must have AT LEAST ONE.

    Returns:
        Dependency callable that returns User if authorized, raises 403 otherwise.

    Raises:
        HTTPException 403: User lacks all required roles
    """
    if not required_roles:
        raise ValueError("require_role requires at least one role")

    async def role_checker(user: User = Depends(get_current_user)) -> User:
        user_roles = set(user.roles)
        required = set(required_roles)

        if not user_roles & required:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=PermissionDenied(
                    required_roles=list(required_roles),
                    user_roles=user.roles,
                ).message,
            )
        return user

    return role_checker


# ─── Convenience: get_optional_user ─────────────────────────────────────────


async def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Like get_current_user but returns None instead of raising 401.

    Use for endpoints that support both authenticated and anonymous access.
    """
    token = request.cookies.get("aura_access_token")
    if token is None and credentials is None:
        return None

    if token is None:
        token = credentials.credentials

    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None