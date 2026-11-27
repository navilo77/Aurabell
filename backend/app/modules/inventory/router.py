"""Inventory router - Admin CRUD and Public endpoints for inventory management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_role
from app.core.database import get_db
from app.modules.inventory.schema import (
    InventoryAdjustmentCreate,
    InventoryBalanceRead,
    InventoryReservationConsume,
    InventoryReservationCreate,
    InventoryReservationRead,
    InventoryReservationRelease,
    InventoryStockMovementRead,
    ProductBatchCreate,
    ProductBatchRead,
    ProductBatchUpdate,
    ProductSerialCreate,
    ProductSerialRead,
    ProductSerialUpdate,
)
from app.modules.inventory.service import InventoryError, InventoryService

admin_router = APIRouter(prefix="/admin/inventory", tags=["Admin - Inventory"])
public_router = APIRouter(prefix="/inventory", tags=["Public - Inventory"])


def get_inventory_service(db: AsyncSession = Depends(get_db)):
    return InventoryService(db)


def _raise_http(exc: InventoryError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"detail": exc.message, "code": exc.code},
    )


# ─── Stock Balances ───────────────────────────────────────────────────────────

@admin_router.get(
    "/balances/{warehouse_id}/{variant_id}",
    response_model=InventoryBalanceRead,
    summary="Get stock balance",
)
async def get_balance(
    warehouse_id: str = Path(..., description="Warehouse UUID"),
    variant_id: str = Path(..., description="Product variant UUID"),
    service: InventoryService = Depends(get_inventory_service),
    user=Depends(require_role("store_manager", "inventory_manager", "super_admin")),
):
    """Get current stock balance for a variant in a warehouse."""
    try:
        return await service.get_balance(warehouse_id, variant_id)
    except InventoryError as e:
        raise _raise_http(e)


@admin_router.post(
    "/balances/{warehouse_id}/{variant_id}/adjust",
    response_model=InventoryBalanceRead,
    status_code=status.HTTP_200_OK,
    summary="Adjust inventory (inbound/outbound)",
)
async def adjust_inventory(
    data: InventoryAdjustmentCreate,
    warehouse_id: str = Path(..., description="Warehouse UUID"),
    variant_id: str = Path(..., description="Product variant UUID"),
    service: InventoryService = Depends(get_inventory_service),
    user=Depends(require_role("inventory_manager", "super_admin")),
):
    """Adjust stock quantity. Positive delta = inbound, negative = outbound."""
    try:
        return await service.adjust_inventory(
            warehouse_id, variant_id, data, created_by=getattr(user, "id", None)
        )
    except InventoryError as e:
        raise _raise_http(e)


# ─── Reservations ─────────────────────────────────────────────────────────────

@admin_router.post(
    "/reservations",
    response_model=InventoryReservationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create stock reservation",
)
async def create_reservation(
    data: InventoryReservationCreate,
    service: InventoryService = Depends(get_inventory_service),
    user=Depends(require_role("inventory_manager", "super_admin")),
):
    """Create a 15-minute TTL stock reservation for checkout."""
    try:
        return await service.create_reservation(
            data, created_by=getattr(user, "id", None)
        )
    except InventoryError as e:
        raise _raise_http(e)


@admin_router.get(
    "/reservations",
    response_model=list[InventoryReservationRead],
    summary="List reservations",
)
async def list_reservations(
    warehouse_id: str | None = Query(None, description="Filter by warehouse UUID"),
    variant_id: str | None = Query(None, description="Filter by variant UUID"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    service: InventoryService = Depends(get_inventory_service),
    user=Depends(require_role("inventory_manager", "store_manager", "super_admin")),
):
    """List inventory reservations with optional filters."""
    return await service.list_reservations(warehouse_id, variant_id, status, limit)


@admin_router.get(
    "/reservations/{reservation_id}",
    response_model=InventoryReservationRead,
    summary="Get reservation by ID",
)
async def get_reservation(
    reservation_id: str = Path(..., description="Reservation UUID"),
    service: InventoryService = Depends(get_inventory_service),
    user=Depends(require_role("inventory_manager", "store_manager", "super_admin")),
):
    """Get a reservation by ID."""
    try:
        return await service.get_reservation(reservation_id)
    except InventoryError as e:
        raise _raise_http(e)


@admin_router.post(
    "/reservations/{reservation_id}/consume",
    response_model=InventoryReservationRead,
    summary="Consume reservation",
)
async def consume_reservation(
    reservation_id: str = Path(..., description="Reservation UUID"),
    service: InventoryService = Depends(get_inventory_service),
    user=Depends(require_role("inventory_manager", "super_admin")),
):
    """Mark a reservation as consumed (stock deducted from on-hand)."""
    try:
        return await service.consume_reservation(
            reservation_id, created_by=getattr(user, "id", None)
        )
    except InventoryError as e:
        raise _raise_http(e)


@admin_router.post(
    "/reservations/{reservation_id}/release",
    response_model=InventoryReservationRead,
    summary="Release reservation",
)
async def release_reservation(
    reservation_id: str = Path(..., description="Reservation UUID"),
    service: InventoryService = Depends(get_inventory_service),
    user=Depends(require_role("inventory_manager", "super_admin")),
):
    """Release an active reservation back to available stock."""
    try:
        return await service.release_reservation(
            reservation_id, created_by=getattr(user, "id", None)
        )
    except InventoryError as e:
        raise _raise_http(e)


# ─── Stock Movements (Ledger) ─────────────────────────────────────────────────

@admin_router.get(
    "/movements",
    response_model=list[InventoryStockMovementRead],
    summary="List stock movements (immutable ledger)",
)
async def list_movements(
    warehouse_id: str | None = Query(None, description="Filter by warehouse UUID"),
    variant_id: str | None = Query(None, description="Filter by variant UUID"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    service: InventoryService = Depends(get_inventory_service),
    user=Depends(require_role("inventory_manager", "store_manager", "super_admin")),
):
    """List stock movement ledger entries (read-only, immutable)."""
    return await service.list_movements(warehouse_id, variant_id, limit)


# ─── Product Batches ─────────────────────────────────────────────────────────

@admin_router.post(
    "/batches",
    response_model=ProductBatchRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create product batch",
)
async def create_batch(
    data: ProductBatchCreate,
    service: InventoryService = Depends(get_inventory_service),
    user=Depends(require_role("inventory_manager", "super_admin")),
):
    """Create a product batch (skincare expiry tracking)."""
    try:
        return await service.create_batch(data)
    except InventoryError as e:
        raise _raise_http(e)


@admin_router.get(
    "/batches",
    response_model=list[ProductBatchRead],
    summary="List product batches",
)
async def list_batches(
    variant_id: str | None = Query(None, description="Filter by variant UUID"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    service: InventoryService = Depends(get_inventory_service),
    user=Depends(require_role("inventory_manager", "store_manager", "super_admin")),
):
    """List product batches."""
    return await service.list_batches(variant_id, limit)


@admin_router.get(
    "/batches/{batch_id}",
    response_model=ProductBatchRead,
    summary="Get product batch by ID",
)
async def get_batch(
    batch_id: str = Path(..., description="Batch UUID"),
    service: InventoryService = Depends(get_inventory_service),
    user=Depends(require_role("inventory_manager", "store_manager", "super_admin")),
):
    """Get a product batch by ID."""
    try:
        return await service.get_batch(batch_id)
    except InventoryError as e:
        raise _raise_http(e)


@admin_router.patch(
    "/batches/{batch_id}",
    response_model=ProductBatchRead,
    summary="Update product batch",
)
async def update_batch(
    data: ProductBatchUpdate,
    batch_id: str = Path(..., description="Batch UUID"),
    service: InventoryService = Depends(get_inventory_service),
    user=Depends(require_role("inventory_manager", "super_admin")),
):
    """Update a product batch."""
    try:
        return await service.update_batch(batch_id, data)
    except InventoryError as e:
        raise _raise_http(e)


# ─── Product Serials ─────────────────────────────────────────────────────────

@admin_router.post(
    "/serials",
    response_model=ProductSerialRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create product serial",
)
async def create_serial(
    data: ProductSerialCreate,
    service: InventoryService = Depends(get_inventory_service),
    user=Depends(require_role("inventory_manager", "super_admin")),
):
    """Create a product serial (IMEI/serial number tracking)."""
    try:
        return await service.create_serial(data)
    except InventoryError as e:
        raise _raise_http(e)


@admin_router.get(
    "/serials",
    response_model=list[ProductSerialRead],
    summary="List product serials",
)
async def list_serials(
    variant_id: str | None = Query(None, description="Filter by variant UUID"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    service: InventoryService = Depends(get_inventory_service),
    user=Depends(require_role("inventory_manager", "store_manager", "super_admin")),
):
    """List product serials."""
    return await service.list_serials(variant_id, status, limit)


@admin_router.get(
    "/serials/{serial_id}",
    response_model=ProductSerialRead,
    summary="Get product serial by ID",
)
async def get_serial(
    serial_id: str = Path(..., description="Serial UUID"),
    service: InventoryService = Depends(get_inventory_service),
    user=Depends(require_role("inventory_manager", "store_manager", "super_admin")),
):
    """Get a product serial by ID."""
    try:
        return await service.get_serial(serial_id)
    except InventoryError as e:
        raise _raise_http(e)


@admin_router.patch(
    "/serials/{serial_id}",
    response_model=ProductSerialRead,
    summary="Update product serial",
)
async def update_serial(
    data: ProductSerialUpdate,
    serial_id: str = Path(..., description="Serial UUID"),
    service: InventoryService = Depends(get_inventory_service),
    user=Depends(require_role("inventory_manager", "super_admin")),
):
    """Update a product serial (status change)."""
    try:
        return await service.update_serial(serial_id, data)
    except InventoryError as e:
        raise _raise_http(e)


# ─── Public (read-only) ──────────────────────────────────────────────────────

@public_router.get(
    "/stock/{warehouse_id}/{variant_id}",
    response_model=InventoryBalanceRead,
    summary="Get public stock balance",
)
async def get_public_stock(
    warehouse_id: str = Path(..., description="Warehouse UUID"),
    variant_id: str = Path(..., description="Product variant UUID"),
    service: InventoryService = Depends(get_inventory_service),
):
    """Get public stock balance (on-hand minus reserved)."""
    return await service.get_balance(warehouse_id, variant_id)