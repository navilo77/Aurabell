"""Tests for Inventory module - M3.0 Inventory & Warehouse Ledger.

M3.1 Warehouse Stock Balances
M3.2 Atomic Stock Reservation Engine  
M3.3 Automatic Reservation Cleanup Worker
M3.4 Immutable Stock Movement Ledger
M3.5 Specialized Tracking (Batch & Serial)

Assumes Supabase DB on port 54322 (local Supabase local).
Savepoint-based session isolation via conftest.py (db_session fixture).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from pydantic import ValidationError

from app.modules.inventory.schema import (
    InventoryAdjustmentCreate,
    InventoryBalanceRead,
    InventoryReservationCreate,
    InventoryReservationRead,
    InventoryReservationConsume,
    InventoryReservationRelease,
    InventoryReservationUpdate,
    InventoryStockMovementRead,
    ProductBatchCreate,
    ProductBatchRead,
    ProductBatchUpdate,
    ProductSerialCreate,
    ProductSerialRead,
    ProductSerialUpdate,
)
from app.modules.inventory.service import InventoryError, InventoryService
from sqlalchemy import text


def _suffix() -> str:
    """Short random suffix so slugs stay unique across repeated runs."""
    return uuid4().hex[:8]


@pytest_asyncio.fixture(scope="function")
async def inventory_service(db_session) -> InventoryService:
    return InventoryService(db_session)


class TestInventoryBalances:
    """M3.1 Warehouse Stock Balances tests."""

    @pytest.mark.asyncio
    async def test_get_balance_new_warehouse(self, db_session, inventory_service):
        """Get balance for a warehouse/variant combo that has no row yet."""
        bal = await inventory_service.get_balance(
            warehouse_id=f"test-warehouse-{_suffix()}",
            variant_id=f"test-variant-{_suffix()}",
        )
        assert bal.quantity_on_hand == 0
        assert bal.quantity_reserved == 0

    @pytest.mark.asyncio
    async def test_adjust_inventory_inbound(self, db_session, inventory_service):
        """Inbound adjustment (+delta) creates new balance row."""
        bal = await inventory_service.adjust_inventory(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
            data=InventoryAdjustmentCreate(quantity_delta=50, reason="restock"),
        )
        assert bal.quantity_on_hand == 50
        assert bal.quantity_reserved == 0

    @pytest.mark.asyncio
    async def test_adjust_inventory_outbound(self, db_session, inventory_service):
        """Outbound adjustment (-delta) reduces on-hand if enough stock."""
        # First create a balance
        await inventory_service.adjust_inventory(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
            data=InventoryAdjustmentCreate(quantity_delta=100, reason="initial"),
        )
        # Now remove 30
        bal = await inventory_service.adjust_inventory(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
            data=InventoryAdjustmentCreate(quantity_delta=-30, reason="sale"),
        )
        assert bal.quantity_on_hand == 70
        assert bal.quantity_reserved == 0

    @pytest.mark.asyncio
    async def test_adjust_inventory_insufficient_stock(self, db_session, inventory_service):
        """Cannot go negative."""
        try:
            await inventory_service.adjust_inventory(
                warehouse_id=f"warehouse-{_suffix()}",
                variant_id=f"variant-{_suffix()}",
                data=InventoryAdjustmentCreate(quantity_delta=-50, reason="oversell"),
            )
            assert False, "Expected InventoryError"
        except InventoryError as e:
            assert e.code == "INSUFFICIENT_STOCK"

    @pytest.mark.asyncio
    async def test_adjust_inventory_reserved_exceeded(self, db_session, inventory_service):
        """Cannot reduce stock below reserved quantity."""
        # Create balance + reservation
        await inventory_service.adjust_inventory(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
            data=InventoryAdjustmentCreate(quantity_delta=50, reason="initial"),
        )
        res = await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=f"variant-{_suffix()}",
                warehouse_id=f"warehouse-{_suffix()}",
                quantity=20,
            )
        )
        # Now try to reduce stock below reserved
        try:
            await inventory_service.adjust_inventory(
                warehouse_id=f"warehouse-{_suffix()}",
                variant_id=f"variant-{_suffix()}",
                data=InventoryAdjustmentCreate(quantity_delta=-40, reason="more sales"),
            )
            assert False, "Expected InventoryError"
        except InventoryError as e:
            assert e.code == "RESERVED_STOCK_EXCEEDS"


class TestInventoryReservations:
    """M3.2 / M3.3 Atomic Stock Reservation + Automatic Cleanup Worker tests."""

    @pytest.mark.asyncio
    async def test_create_reservation(self, db_session, inventory_service):
        """Create a reservation with TTL (15 min)."""
        bal = await inventory_service.adjust_inventory(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
            data=InventoryAdjustmentCreate(quantity_delta=100, reason="initial"),
        )
        res = await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=f"variant-{_suffix()}",
                warehouse_id=f"warehouse-{_suffix()}",
                quantity=30,
            )
        )
        assert res.quantity == 30
        assert res.status == "active"
        # Check balance reserved increased
        new_bal = await inventory_service.get_balance(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
        )
        assert new_bal.quantity_reserved == 30

    @pytest.mark.asyncio
    async def test_consume_reservation(self, db_session, inventory_service):
        """Consume a reservation deducts from on-hand."""
        await inventory_service.adjust_inventory(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
            data=InventoryAdjustmentCreate(quantity_delta=100, reason="initial"),
        )
        res = await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=f"variant-{_suffix()}",
                warehouse_id=f"warehouse-{_suffix()}",
                quantity=30,
            )
        )
        consumed = await inventory_service.consume_reservation(reservation_id=res.id)
        assert consumed.status == "consumed"
        new_bal = await inventory_service.get_balance(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
        )
        assert new_bal.quantity_on_hand == 70  # 100 - 30 consumed
        assert new_bal.quantity_reserved == 0  # reserved cleared

    @pytest.mark.asyncio
    async def test_release_reservation(self, db_session, inventory_service):
        """Release a reservation returns stock to available."""
        await inventory_service.adjust_inventory(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
            data=InventoryAdjustmentCreate(quantity_delta=100, reason="initial"),
        )
        res = await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=f"variant-{_suffix()}",
                warehouse_id=f"warehouse-{_suffix()}",
                quantity=20,
            )
        )
        released = await inventory_service.release_reservation(reservation_id=res.id)
        assert released.status == "released"
        new_bal = await inventory_service.get_balance(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
        )
        assert new_bal.quantity_on_hand == 100  # all stock back
        assert new_bal.quantity_reserved == 0

    @pytest.mark.asyncio
    async def test_list_reservations(self, db_session, inventory_service):
        """List reservations with filters."""
        await inventory_service.adjust_inventory(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
            data=InventoryAdjustmentCreate(quantity_delta=200, reason="initial"),
        )
        await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=f"variant-{_suffix()}",
                warehouse_id=f"warehouse-{_suffix()}",
                quantity=25,
            )
        )
        await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=f"variant-{_suffix()}",
                warehouse_id=f"warehouse-{_suffix()}",
                quantity=15,
            )
        )
        listed = await inventory_service.list_reservations(
            warehouse_id=f"warehouse-{_suffix()}", limit=50
        )
        assert len(listed) >= 2

    @pytest.mark.asyncio
    async def test_cleanup_expired_reservations(self, db_session, inventory_service):
        """Cleanup worker expires active reservations past TTL."""
        await inventory_service.adjust_inventory(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
            data=InventoryAdjustmentCreate(quantity_delta=100, reason="initial"),
        )
        # Create a reservation - it expires in 15 min.  We manually set it to past now.
        res = await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=f"variant-{_suffix()}",
                warehouse_id=f"warehouse-{_suffix()}",
                quantity=40,
            )
        )
        # Manually move expires_at to past now so cleanup fires
        await inventory_service.db.execute(
            text(
                "UPDATE inventory_reservations SET expires_at = :now WHERE id = :rid"
            ),
            {"now": datetime.now(timezone.utc) - timedelta(minutes=5), "rid": res.id},
        )
        await inventory_service.db.commit()
        count = await inventory_service.cleanup_expired_reservations()
        assert count >= 1  # should have expired at least one
        # Verify it's now released
        new_bal = await inventory_service.get_balance(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
        )
        assert new_bal.quantity_reserved == 0  # released back


class TestInventoryMovements:
    """M3.4 Immutable Stock Movement Ledger tests."""

    @pytest.mark.asyncio
    async def test_adjust_creates_movement(self, db_session, inventory_service):
        """Adjustment creates a stock_movements ledger row."""
        await inventory_service.adjust_inventory(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
            data=InventoryAdjustmentCreate(quantity_delta=42, reason="restock"),
        )
        movements = await inventory_service.list_movements(
            warehouse_id=f"warehouse-{_suffix()}", limit=10
        )
        assert len(movements) >= 1
        assert movements[0].movement_type == "inbound"
        assert movements[0].quantity_delta == 42

    @pytest.mark.asyncio
    async def test_reservation_creates_movement(self, db_session, inventory_service):
        """Reservation creates a stock_movements ledger row."""
        await inventory_service.adjust_inventory(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
            data=InventoryAdjustmentCreate(quantity_delta=100, reason="initial"),
        )
        res = await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=f"variant-{_suffix()}",
                warehouse_id=f"warehouse-{_suffix()}",
                quantity=25,
            )
        )
        movements = await inventory_service.list_movements(
            warehouse_id=f"warehouse-{_suffix()}", limit=10
        )
        assert len(movements) >= 1
        # There should be an 'inbound' from initial adjust + 'reserved' from reservation
        types = {m.movement_type for m in movements}
        assert "reserved" in types

    @pytest.mark.asyncio
    async def test_consume_creates_movement(self, db_session, inventory_service):
        """Consume creates a stock_movements ledger row."""
        await inventory_service.adjust_inventory(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
            data=InventoryAdjustmentCreate(quantity_delta=100, reason="initial"),
        )
        res = await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=f"variant-{_suffix()}",
                warehouse_id=f"warehouse-{_suffix()}",
                quantity=20,
            )
        )
        consumed = await inventory_service.consume_reservation(reservation_id=res.id)
        movements = await inventory_service.list_movements(
            warehouse_id=f"warehouse-{_suffix()}", limit=10
        )
        assert len(movements) >= 2  # adjust + reservation + consume = 3, but at least 2
        types = {m.movement_type for m in movements}
        assert "consumed" in types


class TestProductBatches:
    """M3.5 Specialized Tracking (Batch & Serial)."""

    @pytest.mark.asyncio
    async def test_create_batch(self, db_session, inventory_service):
        """Create a product batch with expiry date."""
        await inventory_service.adjust_inventory(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
            data=InventoryAdjustmentCreate(quantity_delta=50, reason="initial"),
        )
        batch = await inventory_service.create_batch(
            ProductBatchCreate(
                variant_id=f"variant-{_suffix()}",
                batch_number="BATCH-001",
                manufacture_date="2025-01-15",
                expiry_date="2026-01-15",
                quantity_received=50,
            )
        )
        assert batch.batch_number == "BATCH-001"
        assert batch.expiry_date == "2026-01-15"

    @pytest.mark.asyncio
    async def test_create_serial(self, db_session, inventory_service):
        """Create a product serial (IMEI tracking)."""
        await inventory_service.adjust_inventory(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
            data=InventoryAdjustmentCreate(quantity_delta=10, reason="initial"),
        )
        serial = await inventory_service.create_serial(
            ProductSerialCreate(
                variant_id=f"variant-{_suffix()}",
                serial_number="IMEI-123456789012341",
                status="available",
            )
        )
        assert serial.serial_number == "IMEI-123456789012341"
        assert serial.status == "available"


class TestInventoryValidation:
    """Error handling and validation tests."""

    @pytest.mark.asyncio
    async def test_negative_adjustment_with_no_stock(self, db_session, inventory_service):
        """Cannot adjust negative on empty warehouse."""
        try:
            await inventory_service.adjust_inventory(
                warehouse_id=f"warehouse-{_suffix()}",
                variant_id=f"variant-{_suffix()}",
                data=InventoryAdjustmentCreate(quantity_delta=-10, reason="oversell"),
            )
            assert False, "Expected InventoryError"
        except InventoryError as e:
            assert e.code == "INSUFFICIENT_STOCK"

    @pytest.mark.asyncio
    async def test_reserve_more_than_available(self, db_session, inventory_service):
        """Cannot reserve more than available on-hand."""
        await inventory_service.adjust_inventory(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
            data=InventoryAdjustmentCreate(quantity_delta=10, reason="initial"),
        )
        try:
            await inventory_service.create_reservation(
                InventoryReservationCreate(
                    variant_id=f"variant-{_suffix()}",
                    warehouse_id=f"warehouse-{_suffix()}",
                    quantity=20,  # more than 10 available
                )
            )
            assert False, "Expected InventoryError"
        except InventoryError as e:
            assert e.code == "INSUFFICIENT_STOCK"

    @pytest.mark.asyncio
    async def test_consume_inactive_reservation(self, db_session, inventory_service):
        """Cannot consume a reservation that's already consumed/released."""
        await inventory_service.adjust_inventory(
            warehouse_id=f"warehouse-{_suffix()}",
            variant_id=f"variant-{_suffix()}",
            data=InventoryAdjustmentCreate(quantity_delta=10, reason="initial"),
        )
        res = await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=f"variant-{_suffix()}",
                warehouse_id=f"warehouse-{_suffix()}",
                quantity=5,
            )
        )
        # Manually set status to 'consumed' to test the check
        await inventory_service.db.execute(
            text("UPDATE inventory_reservations SET status = 'consumed' WHERE id = :rid"),
            {"rid": res.id},
        )
        await inventory_service.db.commit()
        try:
            await inventory_service.consume_reservation(reservation_id=res.id)
            assert False, "Expected InventoryError"
        except InventoryError as e:
            assert e.code == "INVALID_STATUS"


def _make_adj(delta: int, reason: str | None = None) -> InventoryAdjustmentCreate:
    return InventoryAdjustmentCreate(quantity_delta=delta, reason=reason)