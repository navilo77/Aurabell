"""Cart module schemas (M4.1 Shared Cart).

Supports both authenticated (user_id) and guest (session_id) carts.
Follows Pydantic v2 conventions used across the codebase.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    """Schema for adding an item to a cart."""

    variant_id: str = Field(..., min_length=1, max_length=50, description="Product variant UUID")
    quantity: int = Field(default=1, gt=0, description="Quantity to add")


class CartItemUpdate(BaseModel):
    """Schema for updating a cart item quantity."""

    quantity: int = Field(..., gt=0, description="New quantity")


class CartItemRead(BaseModel):
    """Schema for returning a cart item."""

    id: str
    cart_id: str
    variant_id: str
    quantity: int
    product_name_snapshot: str | None = None
    sku_snapshot: str | None = None
    variant_snapshot: dict | None = None
    unit_price: Decimal | None = None
    line_total: Decimal | None = None
    store_id: str | None = None
    store_name: str | None = None
    in_stock: bool | None = None
    available_qty: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class CartRead(BaseModel):
    """Schema for returning a cart."""

    id: str
    user_id: str | None = None
    session_id: str | None = None
    status: str
    created_at: str | None = None
    updated_at: str | None = None


class CheckoutPreviewItem(BaseModel):
    """Per-variant preview for checkout calculation."""

    variant_id: str
    sku: str | None = None
    product_name: str | None = None
    quantity: int = 1
    unit_price: Decimal = Decimal("0.00")
    line_total: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    store_id: str = ""
    store_name: str | None = None
    in_stock: bool = False
    available_qty: int | None = None


class CheckoutPreview(BaseModel):
    """Checkout preview: per-store breakdown and totals."""

    items: list[CheckoutPreviewItem] = []
    subtotal: Decimal = Decimal("0.00")
    discount_total: Decimal = Decimal("0.00")
    delivery_total: Decimal = Decimal("0.00")
    grand_total: Decimal = Decimal("0.00")
    currency_code: str = "BDT"
