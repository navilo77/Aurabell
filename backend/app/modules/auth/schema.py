"""Auth module request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserLogin(BaseModel):
    """User login request."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserRegister(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=150)
    phone: str | None = Field(None, max_length=20)


class OTPRequest(BaseModel):
    """OTP request (email or phone)."""

    email: EmailStr
    channel: str = Field(default="email", pattern="^(email|sms)$")


class OTPVerify(BaseModel):
    """OTP verification request."""

    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    channel: str = Field(default="email", pattern="^(email|sms)$")


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str


class AuthErrorResponse(BaseModel):
    """Standard auth error response."""

    detail: str
    code: str