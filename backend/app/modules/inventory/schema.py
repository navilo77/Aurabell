"""Inventory module schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class InventoryBalanceRead(BaseModel):
    """Schema for returning inventory balance data."""

    id: str
    warehouse_id: str
    variant_id: str
    quantity_on_hand: int
    quantity_reserved: int
    updated_at: str | None = None


class InventoryAdjustmentCreate(BaseModel):
    """Schema for creating an inventory adjustment (inbound/outbound)."""

    quantity_delta: int = Field(..., description="Positive for inbound, negative for outbound")
    reason: str | None = Field(None, max_length=500)


class InventoryReservationCreate(BaseModel):
    """Schema for creating a new inventory reservation."""

    variant_id: str = Field(..., description="Product variant UUID")
    warehouse_id: str = Field(..., description="Warehouse UUID")
    order_id: str | None = Field(None, description="Order UUID if applicable")
    quantity: int = Field(..., gt=0, description="Quantity to reserve")


class InventoryReservationRead(BaseModel):
    """Schema for returning inventory reservation data."""

    id: str
    variant_id: str
    warehouse_id: str
    order_id: str | None
    quantity: int
    status: str
    expires_at: str
    created_at: str | None = None


class InventoryReservationRelease(BaseModel):
    """Schema for releasing a reservation."""

    reservation_id: str = Field(..., description="Reservation UUID")


class InventoryReservationConsume(BaseModel):
    """Schema for consuming a reservation."""

    reservation_id: str = Field(..., description="Reservation UUID")


class InventoryReservationUpdate(BaseModel):
    """Schema for updating a reservation status."""

    status: str = Field(..., description="New status: active, consumed, released, expired")


class InventoryStockMovementRead(BaseModel):
    """Schema for returning stock movement data."""

    id: str
    warehouse_id: str
    variant_id: str
    movement_type: str
    quantity_delta: int
    reference_type: str | None
    reference_id: str | None
    note: str | None
    created_by: str | None
    created_at: str | None = None


class ProductBatchCreate(BaseModel):
    """Schema for creating a product batch."""

    variant_id: str = Field(..., description="Product variant UUID")
    batch_number: str = Field(..., max_length=100)
    manufacture_date: str | None = Field(None, description="ISO format date")
    expiry_date: str = Field(..., description="ISO format date")
    quantity_received: int = Field(..., ge=0)


class ProductBatchRead(BaseModel):
    """Schema for returning product batch data."""

    id: str
    variant_id: str
    batch_number: str
    manufacture_date: str | None
    expiry_date: str
    quantity_received: int
    created_at: str | None = None


class ProductBatchUpdate(BaseModel):
    """Schema for updating a product batch."""

    manufacture_date: str | None = None
    expiry_date: str | None = None
    quantity_received: int | None = None


class ProductSerialCreate(BaseModel):
    """Schema for creating a product serial."""

    variant_id: str = Field(..., description="Product variant UUID")
    serial_number: str = Field(..., max_length=150)
    status: str = Field(default="available", description="available, reserved, sold, returned, damaged")


class ProductSerialRead(BaseModel):
    """Schema for returning product serial data."""

    id: str
    variant_id: str
    serial_number: str
    status: str
    created_at: str | None = None


class ProductSerialUpdate(BaseModel):
    """Schema for updating a product serial."""

    status: str | None = None