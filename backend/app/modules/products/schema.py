"""Products module schemas — Product, Variant, and Image CRUD models."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ─── Product Images ────────────────────────────────────────────────────────────


class ImageCreate(BaseModel):
    """Schema for adding an image to a product."""

    image_url: str = Field(..., description="Supabase Storage public URL")
    alt_text: str | None = Field(None, max_length=255)
    sort_order: int = Field(default=0)
    is_primary: bool = Field(default=False)


class ImageRead(BaseModel):
    """Schema for returning a product image."""

    id: str
    product_id: str
    image_url: str
    alt_text: str | None
    sort_order: int
    is_primary: bool


# ─── Product Variants ─────────────────────────────────────────────────────────


class VariantCreate(BaseModel):
    """Schema for creating a variant under a product."""

    sku: str | None = Field(None, max_length=100, description="Auto-generated if omitted")
    variant_name: str | None = Field(None, max_length=150)
    attributes: dict = Field(default={}, description="e.g. {color: red, size: M}")
    barcode: str | None = Field(None, max_length=100)


class VariantRead(BaseModel):
    """Schema for returning a product variant."""

    id: str
    product_id: str
    sku: str
    variant_name: str | None
    attributes: dict
    barcode: str | None
    is_active: bool
    created_at: str | None = None


# ─── Products ─────────────────────────────────────────────────────────────────


class ProductCreate(BaseModel):
    """Schema for creating a new product."""

    store_id: str = Field(..., description="Store UUID this product belongs to")
    category_id: str | None = Field(None, description="Category UUID; null if uncategorized")
    name: str = Field(..., min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    brand: str | None = Field(None, max_length=150)
    product_type: str | None = Field(None, max_length=50)
    status: str = Field(default="draft", pattern="^(draft|active|archived)$")
    is_featured: bool = Field(default=False)
    variants: list[VariantCreate] = Field(default=[], description="Initial variants")
    images: list[ImageCreate] = Field(default=[], description="Initial images")


class ProductUpdate(BaseModel):
    """Schema for updating a product. All fields optional."""

    category_id: str | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    brand: str | None = Field(None, max_length=150)
    product_type: str | None = Field(None, max_length=50)
    status: str | None = Field(None, pattern="^(draft|active|archived)$")
    is_featured: bool | None = None


class ProductRead(BaseModel):
    """Schema for returning a product with nested variants and images."""

    id: str
    store_id: str
    category_id: str | None
    name: str
    slug: str
    description: str | None
    brand: str | None
    product_type: str | None
    status: str
    is_featured: bool
    created_at: str | None = None
    updated_at: str | None = None
    variants: list[VariantRead] = []
    images: list[ImageRead] = []