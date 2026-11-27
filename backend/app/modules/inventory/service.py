"""Inventory service - stock balances, reservations, movements, batches, serials."""

from __future__ import annotations

from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import User
from app.core.exceptions import AuthError
from app.modules.inventory.schema import (
    InventoryAdjustmentCreate,
    InventoryBalanceRead,
    InventoryReservationConsume,
    InventoryReservationCreate,
    InventoryReservationRead,
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

_INVENTORY_ERROR_BASE = "INVENTORY"


class InventoryError(AuthError):
    """Inventory-domain error carrying the HTTP status used by the router."""

    def __init__(self, message: str, code: str, status_code: int) -> None:
        super().__init__(message=message, code=code)
        self.status_code = status_code


def _row_to_balance_read(row) -> InventoryBalanceRead:
    return InventoryBalanceRead(
        id=str(row["id"]),
        warehouse_id=str(row["warehouse_id"]),
        variant_id=str(row["variant_id"]),
        quantity_on_hand=int(row["quantity_on_hand"]),
        quantity_reserved=int(row["quantity_reserved"]),
        updated_at=str(row["updated_at"]) if row["updated_at"] else None,
    )


def _row_to_reservation_read(row) -> InventoryReservationRead:
    return InventoryReservationRead(
        id=str(row["id"]),
        variant_id=str(row["variant_id"]),
        warehouse_id=str(row["warehouse_id"]),
        order_id=str(row["order_id"]) if row["order_id"] else None,
        quantity=int(row["quantity"]),
        status=row["status"],
        expires_at=str(row["expires_at"]) if row["expires_at"] else None,
        created_at=str(row["created_at"]) if row["created_at"] else None,
    )


def _row_to_movement_read(row) -> InventoryStockMovementRead:
    return InventoryStockMovementRead(
        id=str(row["id"]),
        warehouse_id=str(row["warehouse_id"]),
        variant_id=str(row["variant_id"]),
        movement_type=row["movement_type"],
        quantity_delta=int(row["quantity_delta"]),
        reference_type=row["reference_type"],
        reference_id=str(row["reference_id"]) if row["reference_id"] else None,
        note=row["note"],
        created_by=str(row["created_by"]) if row["created_by"] else None,
        created_at=str(row["created_at"]) if row["created_at"] else None,
    )


def _row_to_batch_read(row) -> ProductBatchRead:
    return ProductBatchRead(
        id=str(row["id"]),
        variant_id=str(row["variant_id"]),
        batch_number=row["batch_number"],
        manufacture_date=str(row["manufacture_date"]) if row["manufacture_date"] else None,
        expiry_date=str(row["expiry_date"]),
        quantity_received=int(row["quantity_received"]),
        created_at=str(row["created_at"]) if row["created_at"] else None,
    )


def _row_to_serial_read(row) -> ProductSerialRead:
    return ProductSerialRead(
        id=str(row["id"]),
        variant_id=str(row["variant_id"]),
        serial_number=row["serial_number"],
        status=row["status"],
        created_at=str(row["created_at"]) if row["created_at"] else None,
    )


class InventoryService:
    """Inventory management: balances, reservations, movements, batches, serials."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _check_platform_admin(self, user: User) -> None:
        """Verify user has platform admin access (super_admin or owner)."""
        if "super_admin" not in user.roles and "owner" not in user.roles:
            raise AuthError(
                message="Platform admin access required for inventory operations",
                code="PERMISSION_DENIED",
                status_code=403,
            )

    # ------------------------------------------------------------------
    # Stock Balances
    # ------------------------------------------------------------------
    async def get_balance(self, warehouse_id: str, variant_id: str, user: User) -> InventoryBalanceRead:
        """Return current stock balance for a variant in a warehouse.

        Platform admin access required (central warehouse).
        """
        self._check_platform_admin(user)
        result = await self.db.execute(
            text(
                "SELECT id, warehouse_id, variant_id, quantity_on_hand, "
                "quantity_reserved, updated_at FROM inventory_balances "
                "WHERE warehouse_id = :warehouse_id AND variant_id = :variant_id"
            ),
            {"warehouse_id": warehouse_id, "variant_id": variant_id},
        )
        row = result.mappings().one_or_none()
        if row is None:
            return InventoryBalanceRead(
                id="",
                warehouse_id=warehouse_id,
                variant_id=variant_id,
                quantity_on_hand=0,
                quantity_reserved=0,
                updated_at=None,
            )
        return _row_to_balance_read(row)

    async def adjust_inventory(
        self,
        warehouse_id: str,
        variant_id: str,
        data: InventoryAdjustmentCreate,
        created_by: str | None = None,
        user: User | None = None,
    ) -> InventoryBalanceRead:
        """Adjust stock quantity (inbound positive, outbound negative).

        Atomically updates quantity_on_hand and inserts a stock_movements ledger row.
        Enforces quantity_on_hand >= 0 and quantity_reserved <= quantity_on_hand.

        Platform admin access required (central warehouse).
        """
        if user is not None:
            self._check_platform_admin(user)
        # Lock the balance row for concurrency safety
        existing = await self.db.execute(
            text(
                "SELECT id, quantity_on_hand, quantity_reserved FROM inventory_balances "
                "WHERE warehouse_id = :wid AND variant_id = :vid FOR UPDATE"
            ),
            {"wid": warehouse_id, "vid": variant_id},
        )
        balance_row = existing.mappings().one_or_none()

        if balance_row is None:
            # No balance row exists yet; can only adjust if delta is >= 0 (inbound)
            if data.quantity_delta < 0:
                raise InventoryError(
                    "No stock exists to deduct; cannot go negative",
                    "NEGATIVE_STOCK",
                    422,
                )
            await self.db.execute(
                text(
                    "INSERT INTO inventory_balances "
                    "(warehouse_id, variant_id, quantity_on_hand, quantity_reserved) "
                    "VALUES (:wid, :vid, :delta, 0) "
                    "RETURNING id, warehouse_id, variant_id, quantity_on_hand, "
                    "quantity_reserved, updated_at"
                ),
                {"wid": warehouse_id, "vid": variant_id, "delta": data.quantity_delta},
            )
            movement_type = "inbound"
        else:
            new_on_hand = int(balance_row["quantity_on_hand"]) + data.quantity_delta
            if new_on_hand < 0:
                raise InventoryError(
                    f"Insufficient stock: on_hand={balance_row['quantity_on_hand']}, "
                    f"delta={data.quantity_delta}",
                    "INSUFFICIENT_STOCK",
                    422,
                )
            if new_on_hand < int(balance_row["quantity_reserved"]):
                raise InventoryError(
                    "Cannot reduce stock below reserved quantity",
                    "RESERVED_STOCK_EXCEEDS",
                    422,
                )
            await self.db.execute(
                text(
                    "UPDATE inventory_balances "
                    "SET quantity_on_hand = :on_hand, updated_at = NOW() "
                    "WHERE warehouse_id = :wid AND variant_id = :vid "
                    "RETURNING id, warehouse_id, variant_id, quantity_on_hand, "
                    "quantity_reserved, updated_at"
                ),
                {
                    "on_hand": new_on_hand,
                    "wid": warehouse_id,
                    "vid": variant_id,
                },
            )
            movement_type = "inbound" if data.quantity_delta > 0 else "outbound"

        # Insert stock movement ledger row
        await self.db.execute(
            text(
                "INSERT INTO stock_movements "
                "(warehouse_id, variant_id, movement_type, quantity_delta, "
                "reference_type, reference_id, note, created_by) "
                "VALUES (:wid, :vid, :mtype, :delta, NULL, NULL, :note, :created_by)"
            ),
            {
                "wid": warehouse_id,
                "vid": variant_id,
                "mtype": movement_type,
                "delta": data.quantity_delta,
                "note": data.reason,
                "created_by": created_by,
            },
        )

        await self.db.commit()

        return await self._get_balance_internal(warehouse_id, variant_id)

    async def _get_balance_internal(self, warehouse_id: str, variant_id: str) -> InventoryBalanceRead:
        """Internal version without auth check for internal callers."""
        result = await self.db.execute(
            text(
                "SELECT id, warehouse_id, variant_id, quantity_on_hand, "
                "quantity_reserved, updated_at FROM inventory_balances "
                "WHERE warehouse_id = :warehouse_id AND variant_id = :variant_id"
            ),
            {"warehouse_id": warehouse_id, "variant_id": variant_id},
        )
        row = result.mappings().one_or_none()
        if row is None:
            return InventoryBalanceRead(
                id="",
                warehouse_id=warehouse_id,
                variant_id=variant_id,
                quantity_on_hand=0,
                quantity_reserved=0,
                updated_at=None,
            )
        return _row_to_balance_read(row)

    # ------------------------------------------------------------------
    # Reservations
    # ------------------------------------------------------------------
    async def create_reservation(
        self,
        data: InventoryReservationCreate,
        created_by: str | None = None,
        user: User | None = None,
    ) -> InventoryReservationRead:
        """Create a stock reservation with TTL.

        Locks the inventory_balance row with SELECT FOR UPDATE to prevent
        concurrent overselling.

        Platform admin access required (central warehouse).
        """
        if user is not None:
            self._check_platform_admin(user)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        # Lock balance row
        result = await self.db.execute(
            text(
                "SELECT quantity_on_hand, quantity_reserved FROM inventory_balances "
                "WHERE warehouse_id = :wid AND variant_id = :vid FOR UPDATE"
            ),
            {"wid": data.warehouse_id, "vid": data.variant_id},
        )
        balance = result.mappings().one_or_none()
        if balance is None:
            raise InventoryError(
                "No inventory balance exists for this variant in this warehouse",
                "BALANCE_NOT_FOUND",
                404,
            )

        available = int(balance["quantity_on_hand"]) - int(balance["quantity_reserved"])
        if data.quantity > available:
            raise InventoryError(
                f"Insufficient available stock: {available}, requested {data.quantity}",
                "INSUFFICIENT_STOCK",
                422,
            )

        # Insert reservation
        res_result = await self.db.execute(
            text(
                "INSERT INTO inventory_reservations "
                "(variant_id, warehouse_id, order_id, quantity, status, expires_at) "
                "VALUES (:vid, :wid, :oid, :qty, 'active', :expires) "
                "RETURNING id, variant_id, warehouse_id, order_id, quantity, status, "
                "expires_at, created_at"
            ),
            {
                "vid": data.variant_id,
                "wid": data.warehouse_id,
                "oid": data.order_id,
                "qty": data.quantity,
                "expires": expires_at,
            },
        )
        res_row = res_result.mappings().one()

        # Increase reserved quantity
        await self.db.execute(
            text(
                "UPDATE inventory_balances "
                "SET quantity_reserved = quantity_reserved + :qty, updated_at = NOW() "
                "WHERE warehouse_id = :wid AND variant_id = :vid"
            ),
            {"qty": data.quantity, "wid": data.warehouse_id, "vid": data.variant_id},
        )

        # Movement ledger
        await self.db.execute(
            text(
                "INSERT INTO stock_movements "
                "(warehouse_id, variant_id, movement_type, quantity_delta, "
                "reference_type, reference_id, note, created_by) "
                "VALUES (:wid, :vid, 'reserved', :qty, 'inventory_reservations', :rid, "
                ":note, :created_by)"
            ),
            {
                "wid": data.warehouse_id,
                "vid": data.variant_id,
                "qty": data.quantity,
                "rid": str(res_row["id"]),
                "note": "Stock reservation created",
                "created_by": created_by,
            },
        )

        await self.db.commit()
        return _row_to_reservation_read(res_row)

    async def get_reservation(self, reservation_id: str, user: User | None = None) -> InventoryReservationRead:
        """Fetch a reservation by ID.

        Platform admin access required (central warehouse).
        """
        if user is not None:
            self._check_platform_admin(user)
        result = await self.db.execute(
            text(
                "SELECT id, variant_id, warehouse_id, order_id, quantity, status, "
                "expires_at, created_at FROM inventory_reservations "
                "WHERE id = :rid"
            ),
            {"rid": reservation_id},
        )
        row = result.mappings().one_or_none()
        if row is None:
            raise InventoryError("Reservation not found", "NOT_FOUND", 404)
        return _row_to_reservation_read(row)

    async def list_reservations(
        self,
        warehouse_id: str | None = None,
        variant_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        user: User | None = None,
    ) -> list[InventoryReservationRead]:
        """List reservations with optional filters.

        Platform admin access required (central warehouse).
        """
        if user is not None:
            self._check_platform_admin(user)
        conditions = []
        params: dict[str, object] = {"limit": limit}
        if warehouse_id:
            conditions.append("warehouse_id = :wid")
            params["wid"] = warehouse_id
        if variant_id:
            conditions.append("variant_id = :vid")
            params["vid"] = variant_id
        if status:
            conditions.append("status = :status")
            params["status"] = status
        where_clause = " AND ".join(conditions) if conditions else "true"
        result = await self.db.execute(
            text(
                f"SELECT id, variant_id, warehouse_id, order_id, quantity, status, "
                f"expires_at, created_at FROM inventory_reservations "
                f"WHERE {where_clause} ORDER BY created_at DESC LIMIT :limit"
            ),
            params,
        )
        return [_row_to_reservation_read(row) for row in result.mappings().all()]

    async def consume_reservation(
        self,
        reservation_id: str,
        created_by: str | None = None,
        user: User | None = None,
    ) -> InventoryReservationRead:
        """Mark a reservation as consumed (stock deducted from on-hand).

        Platform admin access required (central warehouse).
        """
        if user is not None:
            self._check_platform_admin(user)
        res = await self.get_reservation(reservation_id, user)
        if res.status != "active":
            raise InventoryError(
                f"Cannot consume reservation in status '{res.status}'",
                "INVALID_STATUS",
                422,
            )

        # Lock balance row
        result = await self.db.execute(
            text(
                "SELECT quantity_on_hand, quantity_reserved FROM inventory_balances "
                "WHERE warehouse_id = :wid AND variant_id = :vid FOR UPDATE"
            ),
            {"wid": res.warehouse_id, "vid": res.variant_id},
        )
        balance = result.mappings().one()
        if int(balance["quantity_on_hand"]) < res.quantity:
            raise InventoryError("Insufficient on-hand stock", "INSUFFICIENT_STOCK", 422)

        await self.db.execute(
            text(
                "UPDATE inventory_reservations SET status = 'consumed' "
                "WHERE id = :rid RETURNING id"
            ),
            {"rid": reservation_id},
        )
        await self.db.execute(
            text(
                "UPDATE inventory_balances "
                "SET quantity_on_hand = quantity_on_hand - :qty, "
                "quantity_reserved = quantity_reserved - :qty, updated_at = NOW() "
                "WHERE warehouse_id = :wid AND variant_id = :vid"
            ),
            {"qty": res.quantity, "wid": res.warehouse_id, "vid": res.variant_id},
        )
        await self.db.execute(
            text(
                "INSERT INTO stock_movements "
                "(warehouse_id, variant_id, movement_type, quantity_delta, "
                "reference_type, reference_id, note, created_by) "
                "VALUES (:wid, :vid, 'consumed', -CAST(:qty AS BIGINT), 'inventory_reservations', :rid, "
                ":note, :created_by)"
            ),
            {
                "wid": res.warehouse_id,
                "vid": res.variant_id,
                "qty": res.quantity,
                "rid": reservation_id,
                "note": "Stock consumed (order fulfilled)",
                "created_by": created_by,
            },
        )
        await self.db.commit()
        return await self.get_reservation(reservation_id, user)

    async def release_reservation(
        self,
        reservation_id: str,
        created_by: str | None = None,
        user: User | None = None,
    ) -> InventoryReservationRead:
        """Release an active reservation back to available stock.

        Platform admin access required (central warehouse).
        """
        if user is not None:
            self._check_platform_admin(user)
        res = await self.get_reservation(reservation_id, user)
        if res.status != "active":
            raise InventoryError(
                f"Cannot release reservation in status '{res.status}'",
                "INVALID_STATUS",
                422,
            )

        await self.db.execute(
            text(
                "UPDATE inventory_reservations SET status = 'released' "
                "WHERE id = :rid RETURNING id"
            ),
            {"rid": reservation_id},
        )
        await self.db.execute(
            text(
                "UPDATE inventory_balances "
                "SET quantity_reserved = quantity_reserved - :qty, updated_at = NOW() "
                "WHERE warehouse_id = :wid AND variant_id = :vid"
            ),
            {"qty": res.quantity, "wid": res.warehouse_id, "vid": res.variant_id},
        )
        await self.db.execute(
            text(
                "INSERT INTO stock_movements "
                "(warehouse_id, variant_id, movement_type, quantity_delta, "
                "reference_type, reference_id, note, created_by) "
                "VALUES (:wid, :vid, 'released', :qty, 'inventory_reservations', :rid, "
                ":note, :created_by)"
            ),
            {
                "wid": res.warehouse_id,
                "vid": res.variant_id,
                "qty": res.quantity,
                "rid": reservation_id,
                "note": "Reservation released back to stock",
                "created_by": created_by,
            },
        )
        await self.db.commit()
        return await self.get_reservation(reservation_id, user)

    async def cleanup_expired_reservations(self, user: User | None = None) -> int:
        """Expire active reservations past their TTL and release reserved stock.

        Returns the number of reservations expired.
        Called by the background worker every 1 minute.

        Platform admin access required (central warehouse).
        """
        if user is not None:
            self._check_platform_admin(user)
        now = datetime.now(timezone.utc)
        expired = await self.db.execute(
            text(
                "SELECT id, warehouse_id, variant_id, quantity FROM inventory_reservations "
                "WHERE status = 'active' AND expires_at <= :now FOR UPDATE"
            ),
            {"now": now},
        )
        rows = expired.mappings().all()
        count = 0
        for row in rows:
            await self.db.execute(
                text(
                    "UPDATE inventory_reservations SET status = 'expired' WHERE id = :rid"
                ),
                {"rid": row["id"]},
            )
            await self.db.execute(
                text(
                    "UPDATE inventory_balances "
                    "SET quantity_reserved = quantity_reserved - :qty, updated_at = NOW() "
                    "WHERE warehouse_id = :wid AND variant_id = :vid"
                ),
                {
                    "qty": row["quantity"],
                    "wid": row["warehouse_id"],
                    "vid": row["variant_id"],
                },
            )
            await self.db.execute(
                text(
                    "INSERT INTO stock_movements "
                    "(warehouse_id, variant_id, movement_type, quantity_delta, "
                    "reference_type, reference_id, note, created_by) "
                    "VALUES (:wid, :vid, 'released', :qty, 'inventory_reservations', :rid, "
                    ":note, NULL)"
                ),
                {
                    "wid": row["warehouse_id"],
                    "vid": row["variant_id"],
                    "qty": row["quantity"],
                    "rid": row["id"],
                    "note": "Reservation expired (TTL)",
                },
            )
            count += 1
        await self.db.commit()
        return count

    # ------------------------------------------------------------------
    # Stock Movements (read-only ledger)
    # ------------------------------------------------------------------
    async def list_movements(
        self,
        warehouse_id: str | None = None,
        variant_id: str | None = None,
        limit: int = 100,
        user: User | None = None,
    ) -> list[InventoryStockMovementRead]:
        """List stock movement ledger entries.

        Platform admin access required (central warehouse).
        """
        if user is not None:
            self._check_platform_admin(user)
        conditions = []
        params: dict[str, object] = {"limit": limit}
        if warehouse_id:
            conditions.append("warehouse_id = :wid")
            params["wid"] = warehouse_id
        if variant_id:
            conditions.append("variant_id = :vid")
            params["vid"] = variant_id
        where_clause = " AND ".join(conditions) if conditions else "true"
        result = await self.db.execute(
            text(
                f"SELECT id, warehouse_id, variant_id, movement_type, quantity_delta, "
                f"reference_type, reference_id, note, created_by, created_at "
                f"FROM stock_movements WHERE {where_clause} "
                f"ORDER BY created_at DESC LIMIT :limit"
            ),
            params,
        )
        return [_row_to_movement_read(row) for row in result.mappings().all()]

    # ------------------------------------------------------------------
    # Product Batches
    # ------------------------------------------------------------------
    async def create_batch(self, data: ProductBatchCreate, user: User | None = None) -> ProductBatchRead:
        """Create a product batch (skincare expiry tracking).

        Platform admin access required (central warehouse).
        """
        if user is not None:
            self._check_platform_admin(user)
        mfd = date.fromisoformat(data.manufacture_date) if data.manufacture_date else None
        exp = date.fromisoformat(data.expiry_date)
        result = await self.db.execute(
            text(
                "INSERT INTO product_batches "
                "(variant_id, batch_number, manufacture_date, expiry_date, quantity_received) "
                "VALUES (:vid, :bn, :mfd, :exp, :qty) "
                "RETURNING id, variant_id, batch_number, manufacture_date, expiry_date, "
                "quantity_received, created_at"
            ),
            {
                "vid": data.variant_id,
                "bn": data.batch_number,
                "mfd": mfd,
                "exp": exp,
                "qty": data.quantity_received,
            },
        )
        row = result.mappings().one()
        await self.db.commit()
        return _row_to_batch_read(row)

    async def get_batch(self, batch_id: str, user: User | None = None) -> ProductBatchRead:
        """Fetch a batch by ID.

        Platform admin access required (central warehouse).
        """
        if user is not None:
            self._check_platform_admin(user)
        result = await self.db.execute(
            text(
                "SELECT id, variant_id, batch_number, manufacture_date, expiry_date, "
                "quantity_received, created_at FROM product_batches WHERE id = :bid"
            ),
            {"bid": batch_id},
        )
        row = result.mappings().one_or_none()
        if row is None:
            raise InventoryError("Batch not found", "NOT_FOUND", 404)
        return _row_to_batch_read(row)

    async def list_batches(
        self,
        variant_id: str | None = None,
        limit: int = 100,
        user: User | None = None,
    ) -> list[ProductBatchRead]:
        """List batches with optional filters.

        Platform admin access required (central warehouse).
        """
        if user is not None:
            self._check_platform_admin(user)
        conditions = []
        params: dict[str, object] = {"limit": limit}
        if variant_id:
            conditions.append("variant_id = :vid")
            params["vid"] = variant_id
        where_clause = " AND ".join(conditions) if conditions else "true"
        result = await self.db.execute(
            text(
                f"SELECT id, variant_id, batch_number, manufacture_date, expiry_date, "
                f"quantity_received, created_at FROM product_batches "
                f"WHERE {where_clause} ORDER BY expiry_date ASC LIMIT :limit"
            ),
            params,
        )
        return [_row_to_batch_read(row) for row in result.mappings().all()]

    async def update_batch(
        self,
        batch_id: str,
        data: ProductBatchUpdate,
        user: User | None = None,
    ) -> ProductBatchRead:
        """Update a product batch.

        Platform admin access required (central warehouse).
        """
        if user is not None:
            self._check_platform_admin(user)
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return await self.get_batch(batch_id, user)
        for key in ("manufacture_date", "expiry_date"):
            if changes.get(key):
                changes[key] = date.fromisoformat(changes[key])
        set_clause = ", ".join(f"{key} = :{key}" for key in changes)
        result = await self.db.execute(
            text(
                f"UPDATE product_batches SET {set_clause} WHERE id = :bid "
                "RETURNING id, variant_id, batch_number, manufacture_date, expiry_date, "
                "quantity_received, created_at"
            ),
            {"bid": batch_id, **changes},
        )
        row = result.mappings().one_or_none()
        if row is None:
            raise InventoryError("Batch not found", "NOT_FOUND", 404)
        await self.db.commit()
        return _row_to_batch_read(row)

    # ------------------------------------------------------------------
    # Product Serials
    # ------------------------------------------------------------------
    async def create_serial(self, data: ProductSerialCreate, user: User | None = None) -> ProductSerialRead:
        """Create a product serial number.

        Platform admin access required (central warehouse).
        """
        if user is not None:
            self._check_platform_admin(user)
        result = await self.db.execute(
            text(
                "INSERT INTO product_serials "
                "(variant_id, serial_number, status) "
                "VALUES (:vid, :sn, :status) "
                "RETURNING id, variant_id, serial_number, status, created_at"
            ),
            {
                "vid": data.variant_id,
                "sn": data.serial_number,
                "status": data.status or "available",
            },
        )
        row = result.mappings().one()
        await self.db.commit()
        return _row_to_serial_read(row)

    async def get_serial(self, serial_id: str, user: User | None = None) -> ProductSerialRead:
        """Fetch a serial by ID.

        Platform admin access required (central warehouse).
        """
        if user is not None:
            self._check_platform_admin(user)
        result = await self.db.execute(
            text(
                "SELECT id, variant_id, serial_number, status, created_at "
                "FROM product_serials WHERE id = :sid"
            ),
            {"sid": serial_id},
        )
        row = result.mappings().one_or_none()
        if row is None:
            raise InventoryError("Serial not found", "NOT_FOUND", 404)
        return _row_to_serial_read(row)

    async def list_serials(
        self,
        variant_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        user: User | None = None,
    ) -> list[ProductSerialRead]:
        """List serials with optional filters.

        Platform admin access required (central warehouse).
        """
        if user is not None:
            self._check_platform_admin(user)
        conditions = []
        params: dict[str, object] = {"limit": limit}
        if variant_id:
            conditions.append("variant_id = :vid")
            params["vid"] = variant_id
        if status:
            conditions.append("status = :status")
            params["status"] = status
        where_clause = " AND ".join(conditions) if conditions else "true"
        result = await self.db.execute(
            text(
                f"SELECT id, variant_id, serial_number, status, created_at "
                f"FROM product_serials WHERE {where_clause} ORDER BY created_at DESC LIMIT :limit"
            ),
            params,
        )
        return [_row_to_serial_read(row) for row in result.mappings().all()]

    async def update_serial(
        self,
        serial_id: str,
        data: ProductSerialUpdate,
        user: User | None = None,
    ) -> ProductSerialRead:
        """Update a product serial.

        Platform admin access required (central warehouse).
        """
        if user is not None:
            self._check_platform_admin(user)
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return await self.get_serial(serial_id, user)
        set_clause = ", ".join(f"{key} = :{key}" for key in changes)
        result = await self.db.execute(
            text(
                f"UPDATE product_serials SET {set_clause} WHERE id = :sid "
                "RETURNING id, variant_id, serial_number, status, created_at"
            ),
            {"sid": serial_id, **changes},
        )
        row = result.mappings().one_or_none()
        if row is None:
            raise InventoryError("Serial not found", "NOT_FOUND", 404)
        await self.db.commit()
        return _row_to_serial_read(row)
