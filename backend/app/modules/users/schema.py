"""Users module request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints


class ProfileRead(BaseModel):
    """User profile response."""

    id: str
    email: str
    full_name: str | None
    phone: str | None
    avatar_url: str | None
    status: str
    roles: list[str]
    store_ids: list[str]
    created_at: datetime
    updated_at: datetime


class ProfileUpdate(BaseModel):
    """Profile update request."""

    full_name: Annotated[str | None, StringConstraints(max_length=150)] = None
    phone: Annotated[str | None, StringConstraints(max_length=20)] = None
    avatar_url: str | None = None


class AddressBase(BaseModel):
    """Shared address fields."""

    recipient_name: Annotated[str, StringConstraints(min_length=1, max_length=150)]
    phone: Annotated[str, StringConstraints(min_length=1, max_length=20)]
    division: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    district: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    upazila: Annotated[str | None, StringConstraints(max_length=100)] = None
    area: Annotated[str | None, StringConstraints(max_length=150)] = None
    address_line: str
    postal_code: Annotated[str | None, StringConstraints(max_length=20)] = None
    is_default: bool = False


class AddressCreate(AddressBase):
    """Create address request."""


class AddressUpdate(BaseModel):
    """Update address request (all fields optional)."""

    recipient_name: Annotated[str | None, StringConstraints(min_length=1, max_length=150)] = None
    phone: Annotated[str | None, StringConstraints(min_length=1, max_length=20)] = None
    division: Annotated[str | None, StringConstraints(min_length=1, max_length=100)] = None
    district: Annotated[str | None, StringConstraints(min_length=1, max_length=100)] = None
    upazila: Annotated[str | None, StringConstraints(max_length=100)] = None
    area: Annotated[str | None, StringConstraints(max_length=150)] = None
    address_line: str | None = None
    postal_code: Annotated[str | None, StringConstraints(max_length=20)] = None
    is_default: bool | None = None


class AddressRead(AddressBase):
    """Address response."""

    id: str
    user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}