"""Stores module schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StoreCreate(BaseModel):
    """Schema for creating a new store."""

    name: str = Field(..., min_length=1, max_length=150)
    slug: str | None = Field(None, min_length=1, max_length=150)
    description: str | None = None
    logo_url: str | None = None
    primary_color: str | None = Field(None, max_length=20)
    status: str = Field(default="active", pattern="^(active|inactive)$")


class StoreRead(BaseModel):
    """Schema for returning store data."""

    id: str
    name: str
    slug: str
    description: str | None = None
    logo_url: str | None = None
    primary_color: str | None = None
    status: str
    created_at: str | None = None
    updated_at: str | None = None
    policies: list[PolicyRead] = []


class StoreUpdate(BaseModel):
    """Schema for updating a store."""

    name: str | None = Field(None, min_length=1, max_length=150)
    slug: str | None = Field(None, min_length=1, max_length=150)
    description: str | None = None
    logo_url: str | None = None
    primary_color: str | None = Field(None, max_length=20)
    status: str | None = Field(None, pattern="^(active|inactive)$")


class StoreBannerUpdate(BaseModel):
    """Schema for updating store banner."""

    banner_url: str = Field(..., pattern=r"^https?://.+")


class ReturnPolicyCreate(BaseModel):
    """Schema for creating return policy."""

    policy_content: dict = Field(default={})
    is_active: bool = Field(default=True)


class WarrantyPolicyCreate(BaseModel):
    """Schema for creating warranty policy."""

    policy_content: dict = Field(default={})
    is_active: bool = Field(default=True)


class TermsConditionsCreate(BaseModel):
    """Schema for creating terms and conditions."""

    policy_content: dict = Field(default={})
    is_active: bool = Field(default=True)


class PolicyRead(BaseModel):
    """Schema for returning store policy data."""

    id: str
    store_id: str
    policy_type: str
    policy_content: dict
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None