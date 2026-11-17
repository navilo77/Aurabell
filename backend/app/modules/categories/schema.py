"""Categories module schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    """Schema for creating a new category."""

    store_id: str = Field(..., description="Store UUID this category belongs to")
    parent_id: str | None = Field(None, description="Parent category UUID; null for root")
    name: str = Field(..., min_length=1, max_length=150)
    slug: str | None = Field(None, min_length=1, max_length=150)
    description: str | None = None
    image_url: str | None = None
    sort_order: int = Field(default=0)


class CategoryUpdate(BaseModel):
    """Schema for updating a category. All fields optional."""

    parent_id: str | None = None
    name: str | None = Field(None, min_length=1, max_length=150)
    slug: str | None = Field(None, min_length=1, max_length=150)
    description: str | None = None
    image_url: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class CategoryRead(BaseModel):
    """Schema for returning category data."""

    id: str
    store_id: str
    parent_id: str | None
    name: str
    slug: str
    description: str | None
    image_url: str | None
    sort_order: int
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None


class CategoryTree(BaseModel):
    """Nested category tree node."""

    id: str
    store_id: str
    parent_id: str | None
    name: str
    slug: str
    description: str | None
    image_url: str | None
    sort_order: int
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None
    children: list[CategoryTree] = []