"""Orders module schemas (M4.2-M4.4).

Order placement, split-orders, and COD verification schemas.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    """Schema for adding an item to an order during checkout."""

    variant_id: str = Field(..., min_length=1, max_length=50, description="Product variant UUID")
    quantity: int = Field(..., gt=0, description="Quantity to order")


class OrderCreate(BaseModel):
    """Schema for creating an order via checkout."""

    cart_id: str = Field(..., description="Cart UUID to convert to order")
    delivery_address_id: str | None = Field(None, description="Delivery address ID (optional)")
    payment_method: str = Field(..., description="Payment method: 'cod', 'bkash', 'sslcommerz'")
    coupon_code: str | None = Field(None, max_length=50, description="Optional coupon code")
    district: str | None = Field(None, max_length=100, description="District for delivery fee")


class OrderAddressCreate(BaseModel):
    """Schema for creating order address snapshot."""

    recipient_name: str = Field(..., min_length=1, max_length=150)
    phone: str = Field(..., min_length=1, max_length=20)
    division: str = Field(..., min_length=1, max_length=100)
    district: str = Field(..., min_length=1, max_length=100)
    upazila: str | None = Field(None, max_length=100)
    area: str | None = Field(None, max_length=150)
    address_line: str = Field(..., description="Full address line")
    postal_code: str | None = Field(None, max_length=20)
    address_type: str = Field(default="delivery", description="'delivery', 'billing', or 'both'")


class OrderRead(BaseModel):
    """Schema for returning an order with parent and store order details."""

    id: str
    order_number: str
    user_id: str | None = None
    subtotal: Decimal = Decimal("0.00")
    discount_total: Decimal = Decimal("0.00")
    delivery_total: Decimal = Decimal("0.00")
    grand_total: Decimal = Decimal("0.00")
    currency_code: str = "BDT"
    order_status: str
    created_at: str
    store_orders: list["OrderRead"] = []
    order_items: list["OrderItemRead"] = []


class OrderItemRead(BaseModel):
    """Schema for returning an order item snapshot."""

    id: str
    product_name_snapshot: str
    sku_snapshot: str
    variant_snapshot: dict | None = None
    unit_price: Decimal
    quantity: int
    discount_amount: Decimal = Decimal("0.00")
    line_total: Decimal


class CODVerifyRequest(BaseModel):
    """Schema for COD OTP verification request."""

    order_id: str = Field(..., description="Order UUID to verify")
    otp_code: str = Field(..., min_length=4, max_length=4, description="4-digit OTP code")


class CODVerifyResponse(BaseModel):
    """Schema for COD verification response."""

    order_id: str
    order_status: str
    confirmed_at: str
    message: str


class DistrictDeliveryFee(BaseModel):
    """Schema for district-based delivery fee calculation."""

    district: str
    fee: Decimal
    is_dhaka_metro: bool