"""Auth router - authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth import get_current_user
from app.core.exceptions import AuthError
from app.modules.auth.schema import (
    AuthErrorResponse,
    OTPRequest,
    OTPVerify,
    RefreshTokenRequest,
    Token,
    UserLogin,
    UserRegister,
)
from app.modules.auth.service import get_auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

bearer_scheme = HTTPBearer(auto_error=False)


@router.post(
    "/login",
    response_model=Token,
    responses={
        401: {"model": AuthErrorResponse, "description": "Invalid credentials"},
        429: {"model": AuthErrorResponse, "description": "Rate limited"},
    },
    summary="User login with email and password",
)
async def login(credentials: UserLogin) -> Token:
    """Authenticate user and return access + refresh tokens."""
    try:
        return await get_auth_service().login(credentials)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": AuthErrorResponse, "description": "Registration failed"},
        429: {"model": AuthErrorResponse, "description": "Rate limited"},
    },
    summary="Register new user",
)
async def register(data: UserRegister) -> Token:
    """Register a new user account. May require email confirmation."""
    try:
        return await get_auth_service().register(data)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.post(
    "/otp/request",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": AuthErrorResponse, "description": "OTP request failed"},
        429: {"model": AuthErrorResponse, "description": "Rate limited"},
    },
    summary="Request OTP/magic link via email",
)
async def request_otp(data: OTPRequest) -> Response:
    """Send OTP (magic link) to user's email for passwordless login."""
    try:
        await get_auth_service().request_otp(data)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.post(
    "/otp/verify",
    response_model=Token,
    responses={
        401: {"model": AuthErrorResponse, "description": "Invalid or expired OTP"},
        429: {"model": AuthErrorResponse, "description": "Rate limited"},
    },
    summary="Verify OTP code and get tokens",
)
async def verify_otp(data: OTPVerify) -> Token:
    """Verify OTP code received via email and return access + refresh tokens."""
    try:
        return await get_auth_service().verify_otp(data)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.post(
    "/refresh",
    response_model=Token,
    responses={
        401: {"model": AuthErrorResponse, "description": "Invalid or expired refresh token"},
    },
    summary="Refresh access token",
)
async def refresh_token(data: RefreshTokenRequest) -> Token:
    """Get new access token using refresh token."""
    try:
        return await get_auth_service().refresh_token(data)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sign out current user",
)
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    user=Depends(get_current_user),
) -> Response:
    """Sign out the current user (revokes session server-side)."""
    if credentials:
        await get_auth_service().logout(credentials.credentials)
    return Response(status_code=status.HTTP_204_NO_CONTENT)