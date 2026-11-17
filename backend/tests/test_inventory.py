"""Tests for Inventory module - M3.0 Inventory & Warehouse Ledger.

M3.1 Warehouse Stock Balances
M3.2 Atomic Stock Reservation Engine
M3.3 Automatic Reservation Cleanup Worker
M3.4 Immutable Stock Movement Ledger
M3.5 Specialized Tracking (Batch & Serial)

Requires local Supabase on port 54322 (backend/.env DATABASE_URL).
Savepoint-based session isolation is provided by the db_session fixture.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.modules.inventory.schema import (
    InventoryAdjustmentCreate,
    InventoryReservationCreate,
    ProductBatchCreate,
    ProductSerialCreate,
)
from app.modules.inventory.service import InventoryError, InventoryService


def _suffix() -> str:
    return uuid4().hex[:8]


@pytest_asyncio.fixture(scope="function")
async def inventory_service(db_session) -> InventoryService:
    return InventoryService(db_session)


@pytest_asyncio.fixture(scope="function")
async def seed_ids(db_session):
    """Create a real store -> warehouse -> product -> variant chain.

    Returns valid UUID strings required by the inventory FK columns.
    """
    suffix = _suffix()

    store_id = (
        await db_session.execute(
            text(
                "INSERT INTO stores (name, slug, status) "
                "VALUES (:n, :s, 'active') RETURNING id"
            ),
            {"n": f"Inv Test Store {suffix}", "s": f"inv-test-store-{suffix}"},
        )
    ).scalar_one()

    warehouse_id = (
        await db_session.execute(
            text(
                "INSERT INTO warehouses (store_id, name) "
                "VALUES (:sid, :n) RETURNING id"
            ),
            {"sid": store_id, "n": f"Inv Test Warehouse {suffix}"},
        )
    ).scalar_one()

    product_id = (
        await db_session.execute(
            text(
                "INSERT INTO products (store_id, name, slug, status) "
                "VALUES (:sid, :n, :s, 'active') RETURNING id"
            ),
            {
                "sid": store_id,
                "n": f"Inv Test Product {suffix}",
                "s": f"inv-test-product-{suffix}",
            },
        )
    ).scalar_one()

    variant_id = (
        await db_session.execute(
            text(
                "INSERT INTO product_variants (product_id, sku) "
                "VALUES (:pid, :sku) RETURNING id"
            ),
            {"pid": product_id, "sku": f"INV-SKU-{suffix}"},
        )
    ).scalar_one()

    await db_session.commit()

    return {
        "store_id": str(store_id),
        "warehouse_id": str(warehouse_id),
        "product_id": str(product_id),
        "variant_id": str(variant_id),
    }


class TestInventoryBalances:
    """M3.1 Warehouse Stock Balances."""

    @pytest.mark.asyncio
    async def test_get_balance_new_warehouse(self, inventory_service, seed_ids):
        """A warehouse/variant pair with no balance row returns zeros."""
        bal = await inventory_service.get_balance(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
        )
        assert bal.quantity_on_hand == 0
        assert bal.quantity_reserved == 0

    @pytest.mark.asyncio
    async def test_adjust_inventory_inbound(self, inventory_service, seed_ids):
        """Inbound adjustment creates a balance row with the given quantity."""
        bal = await inventory_service.adjust_inventory(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
            data=InventoryAdjustmentCreate(quantity_delta=50, reason="restock"),
        )
        assert bal.quantity_on_hand == 50
        assert bal.quantity_reserved == 0

    @pytest.mark.asyncio
    async def test_adjust_inventory_outbound(self, inventory_service, seed_ids):
        """Outbound adjustment reduces on-hand stock."""
        await inventory_service.adjust_inventory(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
            data=InventoryAdjustmentCreate(quantity_delta=100, reason="initial"),
        )
        bal = await inventory_service.adjust_inventory(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
            data=InventoryAdjustmentCreate(quantity_delta=-30, reason="sale"),
        )
        assert bal.quantity_on_hand == 70
        assert bal.quantity_reserved == 0

    @pytest.mark.asyncio
    async def test_adjust_inventory_insufficient_stock(self, inventory_service, seed_ids):
        """Stock can never go negative."""
        with pytest.raises(InventoryError) as exc:
            await inventory_service.adjust_inventory(
                warehouse_id=seed_ids["warehouse_id"],
                variant_id=seed_ids["variant_id"],
                data=InventoryAdjustmentCreate(quantity_delta=-50, reason="oversell"),
            )
        assert exc.value.code == "NEGATIVE_STOCK"

    @pytest.mark.asyncio
    async def test_adjust_inventory_reserved_exceeded(self, inventory_service, seed_ids):
        """Cannot reduce on-hand below the currently reserved quantity."""
        await inventory_service.adjust_inventory(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
            data=InventoryAdjustmentCreate(quantity_delta=50, reason="initial"),
        )
        await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=seed_ids["variant_id"],
                warehouse_id=seed_ids["warehouse_id"],
                quantity=20,
            )
        )
        with pytest.raises(InventoryError) as exc:
            await inventory_service.adjust_inventory(
                warehouse_id=seed_ids["warehouse_id"],
                variant_id=seed_ids["variant_id"],
                data=InventoryAdjustmentCreate(quantity_delta=-40, reason="more sales"),
            )
        assert exc.value.code == "RESERVED_STOCK_EXCEEDS"


class TestInventoryReservations:
    """M3.2 / M3.3 Atomic reservations and TTL cleanup."""

    @pytest.mark.asyncio
    async def test_create_reservation(self, inventory_service, seed_ids):
        """Creating a reservation increases the reserved quantity."""
        await inventory_service.adjust_inventory(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
            data=InventoryAdjustmentCreate(quantity_delta=100, reason="initial"),
        )
        res = await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=seed_ids["variant_id"],
                warehouse_id=seed_ids["warehouse_id"],
                quantity=30,
            )
        )
        assert res.quantity == 30
        assert res.status == "active"

        bal = await inventory_service.get_balance(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
        )
        assert bal.quantity_on_hand == 100
        assert bal.quantity_reserved == 30

    @pytest.mark.asyncio
    async def test_consume_reservation(self, inventory_service, seed_ids):
        """Consuming a reservation deducts on-hand and clears reserved."""
        await inventory_service.adjust_inventory(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
            data=InventoryAdjustmentCreate(quantity_delta=100, reason="initial"),
        )
        res = await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=seed_ids["variant_id"],
                warehouse_id=seed_ids["warehouse_id"],
                quantity=30,
            )
        )
        consumed = await inventory_service.consume_reservation(res.id)
        assert consumed.status == "consumed"

        bal = await inventory_service.get_balance(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
        )
        assert bal.quantity_on_hand == 70
        assert bal.quantity_reserved == 0

    @pytest.mark.asyncio
    async def test_release_reservation(self, inventory_service, seed_ids):
        """Releasing a reservation returns stock to available."""
        await inventory_service.adjust_inventory(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
            data=InventoryAdjustmentCreate(quantity_delta=100, reason="initial"),
        )
        res = await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=seed_ids["variant_id"],
                warehouse_id=seed_ids["warehouse_id"],
                quantity=20,
            )
        )
        released = await inventory_service.release_reservation(res.id)
        assert released.status == "released"

        bal = await inventory_service.get_balance(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
        )
        assert bal.quantity_on_hand == 100
        assert bal.quantity_reserved == 0

    @pytest.mark.asyncio
    async def test_list_reservations(self, inventory_service, seed_ids):
        """Reservations can be listed and filtered."""
        await inventory_service.adjust_inventory(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
            data=InventoryAdjustmentCreate(quantity_delta=200, reason="initial"),
        )
        await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=seed_ids["variant_id"],
                warehouse_id=seed_ids["warehouse_id"],
                quantity=25,
            )
        )
        await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=seed_ids["variant_id"],
                warehouse_id=seed_ids["warehouse_id"],
                quantity=15,
            )
        )
        listed = await inventory_service.list_reservations(
            warehouse_id=seed_ids["warehouse_id"], limit=50
        )
        assert len(listed) == 2

    @pytest.mark.asyncio
    async def test_cleanup_expired_reservations(
        self, inventory_service, seed_ids, db_session
    ):
        """Cleanup worker expires active reservations past their TTL."""
        await inventory_service.adjust_inventory(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
            data=InventoryAdjustmentCreate(quantity_delta=100, reason="initial"),
        )
        res = await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=seed_ids["variant_id"],
                warehouse_id=seed_ids["warehouse_id"],
                quantity=40,
            )
        )
        # Force this reservation into the past so the cleanup job picks it up.
        await db_session.execute(
            text(
                "UPDATE inventory_reservations SET expires_at = :past WHERE id = :rid"
            ),
            {
                "past": datetime.now(timezone.utc) - timedelta(minutes=5),
                "rid": res.id,
            },
        )
        await db_session.commit()

        count = await inventory_service.cleanup_expired_reservations()
        assert count == 1

        expired = await inventory_service.get_reservation(res.id)
        assert expired.status == "expired"

        bal = await inventory_service.get_balance(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
        )
        assert bal.quantity_reserved == 0
        assert bal.quantity_on_hand == 100


class TestInventoryMovements:
    """M3.4 Immutable Stock Movement Ledger."""

    @pytest.mark.asyncio
    async def test_adjust_creates_movement(self, inventory_service, seed_ids):
        """An inbound adjustment writes an 'inbound' ledger row."""
        await inventory_service.adjust_inventory(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
            data=InventoryAdjustmentCreate(quantity_delta=42, reason="restock"),
        )
        movements = await inventory_service.list_movements(
            warehouse_id=seed_ids["warehouse_id"], limit=10
        )
        assert len(movements) == 1
        assert movements[0].movement_type == "inbound"
        assert movements[0].quantity_delta == 42

    @pytest.mark.asyncio
    async def test_reservation_creates_movement(self, inventory_service, seed_ids):
        """A reservation writes a 'reserved' ledger row."""
        await inventory_service.adjust_inventory(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
            data=InventoryAdjustmentCreate(quantity_delta=100, reason="initial"),
        )
        await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=seed_ids["variant_id"],
                warehouse_id=seed_ids["warehouse_id"],
                quantity=25,
            )
        )
        movements = await inventory_service.list_movements(
            warehouse_id=seed_ids["warehouse_id"], limit=10
        )
        types = {m.movement_type for m in movements}
        assert "reserved" in types

    @pytest.mark.asyncio
    async def test_consume_creates_movement(self, inventory_service, seed_ids):
        """Consuming a reservation writes a 'consumed' ledger row."""
        await inventory_service.adjust_inventory(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
            data=InventoryAdjustmentCreate(quantity_delta=100, reason="initial"),
        )
        res = await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=seed_ids["variant_id"],
                warehouse_id=seed_ids["warehouse_id"],
                quantity=20,
            )
        )
        await inventory_service.consume_reservation(res.id)
        movements = await inventory_service.list_movements(
            warehouse_id=seed_ids["warehouse_id"], limit=10
        )
        types = {m.movement_type for m in movements}
        assert "consumed" in types


class TestProductBatchesAndSerials:
    """M3.5 Specialized tracking (batch & serial)."""

    @pytest.mark.asyncio
    async def test_create_batch(self, inventory_service, seed_ids):
        """Batches store expiry metadata for skincare products."""
        suffix = _suffix()
        batch = await inventory_service.create_batch(
            ProductBatchCreate(
                variant_id=seed_ids["variant_id"],
                batch_number=f"BATCH-{suffix}",
                manufacture_date="2025-01-15",
                expiry_date="2026-01-15",
                quantity_received=50,
            )
        )
        assert batch.batch_number == f"BATCH-{suffix}"
        assert batch.quantity_received == 50

    @pytest.mark.asyncio
    async def test_create_serial(self, inventory_service, seed_ids):
        """Serials store IMEI numbers for gadget products."""
        suffix = _suffix()
        serial = await inventory_service.create_serial(
            ProductSerialCreate(
                variant_id=seed_ids["variant_id"],
                serial_number=f"IMEI-{suffix}",
                status="available",
            )
        )
        assert serial.serial_number == f"IMEI-{suffix}"
        assert serial.status == "available"


class TestInventoryValidation:
    """Error handling and guard rails."""

    @pytest.mark.asyncio
    async def test_negative_adjustment_with_no_stock(self, inventory_service, seed_ids):
        """Negative adjustment on an empty warehouse is rejected."""
        with pytest.raises(InventoryError) as exc:
            await inventory_service.adjust_inventory(
                warehouse_id=seed_ids["warehouse_id"],
                variant_id=seed_ids["variant_id"],
                data=InventoryAdjustmentCreate(quantity_delta=-10, reason="oversell"),
            )
        assert exc.value.code == "NEGATIVE_STOCK"

    @pytest.mark.asyncio
    async def test_reserve_more_than_available(self, inventory_service, seed_ids):
        """Cannot reserve more than available on-hand."""
        await inventory_service.adjust_inventory(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
            data=InventoryAdjustmentCreate(quantity_delta=10, reason="initial"),
        )
        with pytest.raises(InventoryError) as exc:
            await inventory_service.create_reservation(
                InventoryReservationCreate(
                    variant_id=seed_ids["variant_id"],
                    warehouse_id=seed_ids["warehouse_id"],
                    quantity=20,
                )
            )
        assert exc.value.code == "INSUFFICIENT_STOCK"

    @pytest.mark.asyncio
    async def test_consume_inactive_reservation(
        self, inventory_service, seed_ids, db_session
    ):
        """Only active reservations may be consumed."""
        await inventory_service.adjust_inventory(
            warehouse_id=seed_ids["warehouse_id"],
            variant_id=seed_ids["variant_id"],
            data=InventoryAdjustmentCreate(quantity_delta=10, reason="initial"),
        )
        res = await inventory_service.create_reservation(
            InventoryReservationCreate(
                variant_id=seed_ids["variant_id"],
                warehouse_id=seed_ids["warehouse_id"],
                quantity=5,
            )
        )
        await db_session.execute(
            text("UPDATE inventory_reservations SET status = 'consumed' WHERE id = :rid"),
            {"rid": res.id},
        )
        await db_session.commit()

        with pytest.raises(InventoryError) as exc:
            await inventory_service.consume_reservation(res.id)
        assert exc.value.code == "INVALID_STATUS"
