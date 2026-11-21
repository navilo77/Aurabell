"""Auth router - authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
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
async def login(credentials: UserLogin, response: Response) -> Token:
    """Authenticate user and return access + refresh tokens."""
    try:
        token = await get_auth_service().login(credentials)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e
    response.set_cookie("aura_access_token", token.access_token, httponly=True, secure=True, samesite="strict", path="/", max_age=token.expires_in)
    response.set_cookie("aura_refresh_token", token.refresh_token, httponly=True, secure=True, samesite="strict", path="/", max_age=60 * 60 * 24 * 7)
    return token


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
async def register(data: UserRegister, response: Response) -> Token:
    """Register a new user account. May require email confirmation."""
    try:
        token = await get_auth_service().register(data)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e
    if token.access_token:
        response.set_cookie("aura_access_token", token.access_token, httponly=True, secure=True, samesite="strict", path="/", max_age=token.expires_in)
        response.set_cookie("aura_refresh_token", token.refresh_token, httponly=True, secure=True, samesite="strict", path="/", max_age=60 * 60 * 24 * 7)
    return token


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
async def verify_otp(data: OTPVerify, response: Response) -> Token:
    """Verify OTP code received via email and return tokens."""
    try:
        token = await get_auth_service().verify_otp(data)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e
    response.set_cookie("aura_access_token", token.access_token, httponly=True, secure=True, samesite="strict", path="/", max_age=token.expires_in)
    response.set_cookie("aura_refresh_token", token.refresh_token, httponly=True, secure=True, samesite="strict", path="/", max_age=60 * 60 * 24 * 7)
    return token


@router.post(
    "/refresh",
    response_model=Token,
    responses={
        401: {"model": AuthErrorResponse, "description": "Invalid or expired refresh token"},
    },
    summary="Refresh access token",
)
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    response: Response,
) -> Token:
    """Get new access token using refresh token.

    Preferred source: HttpOnly ``aura_refresh_token`` cookie.
    Request body is a temporary migration fallback.
    """
    # Preferred source: HttpOnly cookie; body as migration fallback
    refresh_token = request.cookies.get("aura_refresh_token")
    if not isinstance(refresh_token, str):
        refresh_token = data.refresh_token
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"detail": "Missing refresh token", "code": "MISSING_REFRESH_TOKEN"},
        )
    try:
        token = await get_auth_service().refresh_token(
            RefreshTokenRequest(refresh_token=refresh_token)
        )
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e
    response.set_cookie("aura_access_token", token.access_token, httponly=True, secure=True, samesite="strict", path="/", max_age=token.expires_in)
    response.set_cookie("aura_refresh_token", token.refresh_token, httponly=True, secure=True, samesite="strict", path="/", max_age=60 * 60 * 24 * 7)
    return token


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Sign out current user",
)
async def logout(
    response: Response,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    user=Depends(get_current_user),
) -> Response:
    """Sign out the current user (revokes session server-side)."""
    if credentials:
        await get_auth_service().logout(credentials.credentials)
    response.delete_cookie("aura_access_token", path="/")
    response.delete_cookie("aura_refresh_token", path="/")
    return Response(status_code=status.HTTP_204_NO_CONTENT)