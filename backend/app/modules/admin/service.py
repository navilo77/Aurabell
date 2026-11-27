"""Admin service (BE-05)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError
from app.core.pagination import compute_pagination_meta


class AdminError(AuthError):
    """Admin domain error."""

    pass


class AdminService:
    """Admin operations: user management, dashboard, reports."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─── User Management ─────────────────────────────────────────────────────

    async def list_users(
        self,
        page: int = 1,
        per_page: int = 20,
        role_filter: str | None = None,
        store_id: str | None = None,
        status_filter: str | None = None,
        search: str | None = None,
    ) -> tuple[list[dict], int]:
        """List users with pagination and filtering."""
        where_clauses = ["1=1"]
        params: dict[str, Any] = {}

        if status_filter:
            where_clauses.append("p.status = :status_filter")
            params["status_filter"] = status_filter
        if search:
            where_clauses.append("(p.full_name ILIKE :search OR p.email ILIKE :search)")
            params["search"] = f"%{search}%"

        # Role/store filtering via subquery
        if role_filter or store_id:
            role_conditions = []
            if role_filter:
                role_conditions.append("r.name = :role_filter")
                params["role_filter"] = role_filter
            if store_id:
                role_conditions.append("ur.store_id = :store_id")
                params["store_id"] = store_id
            if role_conditions:
                where_clauses.append(
                    "p.id IN (SELECT ur.user_id FROM user_roles ur JOIN roles r ON r.id = ur.role_id WHERE "
                    + " AND ".join(role_conditions)
                    + ")"
                )

        where_sql = " AND ".join(where_clauses)

        count_result = await self.db.execute(
            text(f"SELECT COUNT(*) FROM profiles p WHERE {where_sql}"), params
        )
        total = count_result.scalar() or 0

        offset = (page - 1) * per_page
        result = await self.db.execute(
            text(
                f"""
                SELECT p.id, p.email, p.full_name, p.phone, p.status, p.created_at, p.updated_at
                FROM profiles p
                WHERE {where_sql}
                ORDER BY p.created_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {**params, "limit": per_page, "offset": offset},
        )
        rows = result.mappings().all()

        users = []
        for row in rows:
            uid = str(row["id"])
            roles = await self._get_user_roles(uid)
            users.append({
                "id": uid,
                "email": row["email"],
                "full_name": row["full_name"],
                "phone": row["phone"],
                "status": row["status"],
                "roles": roles,
                "created_at": str(row["created_at"]) if row["created_at"] else None,
                "updated_at": str(row["updated_at"]) if row["updated_at"] else None,
            })

        return users, total

    async def _get_user_roles(self, user_id: str) -> list[dict]:
        """Get roles for a user."""
        result = await self.db.execute(
            text(
                """
                SELECT ur.id, r.id as role_id, r.name as role_name,
                       ur.store_id, s.name as store_name, ur.assigned_by, ur.created_at
                FROM user_roles ur
                JOIN roles r ON r.id = ur.role_id
                LEFT JOIN stores s ON s.id = ur.store_id
                WHERE ur.user_id = :user_id
                """
            ),
            {"user_id": user_id},
        )
        return [
            {
                "role_id": str(row["role_id"]),
                "role_name": row["role_name"],
                "store_id": str(row["store_id"]) if row["store_id"] else None,
                "store_name": row["store_name"],
                "assigned_by": str(row["assigned_by"]) if row["assigned_by"] else None,
                "created_at": str(row["created_at"]) if row["created_at"] else None,
            }
            for row in result.mappings().all()
        ]

    async def get_user(self, user_id: str) -> dict:
        """Get a single user by ID."""
        result = await self.db.execute(
            text(
                "SELECT id, email, full_name, phone, status, created_at, updated_at "
                "FROM profiles WHERE id = :user_id"
            ),
            {"user_id": user_id},
        )
        row = result.mappings().first()
        if not row:
            raise AdminError(message="User not found", code="USER_NOT_FOUND", status_code=404)

        roles = await self._get_user_roles(str(row["id"]))
        return {
            "id": str(row["id"]),
            "email": row["email"],
            "full_name": row["full_name"],
            "phone": row["phone"],
            "status": row["status"],
            "roles": roles,
            "created_at": str(row["created_at"]) if row["created_at"] else None,
            "updated_at": str(row["updated_at"]) if row["updated_at"] else None,
        }

    async def assign_role(self, user_id: str, role_id: str, store_id: str | None, assigned_by: str) -> None:
        """Assign a role to a user."""
        # Verify user exists
        user_check = await self.db.execute(
            text("SELECT id FROM profiles WHERE id = :user_id"),
            {"user_id": user_id},
        )
        if not user_check.scalar_one_or_none():
            raise AdminError(message="User not found", code="USER_NOT_FOUND", status_code=404)

        # Verify role exists
        role_check = await self.db.execute(
            text("SELECT id FROM roles WHERE id = :role_id"),
            {"role_id": role_id},
        )
        if not role_check.scalar_one_or_none():
            raise AdminError(message="Role not found", code="ROLE_NOT_FOUND", status_code=404)

        # Verify store exists if store_id provided
        if store_id:
            store_check = await self.db.execute(
                text("SELECT id FROM stores WHERE id = :store_id"),
                {"store_id": store_id},
            )
            if not store_check.scalar_one_or_none():
                raise AdminError(message="Store not found", code="STORE_NOT_FOUND", status_code=404)

        # Check for duplicate assignment
        dup_check = await self.db.execute(
            text(
                "SELECT id FROM user_roles WHERE user_id = :user_id AND role_id = :role_id "
                "AND (store_id = :store_id OR (store_id IS NULL AND :store_id IS NULL))"
            ),
            {"user_id": user_id, "role_id": role_id, "store_id": store_id},
        )
        if dup_check.scalar_one_or_none():
            raise AdminError(message="Role already assigned", code="DUPLICATE_ROLE", status_code=409)

        await self.db.execute(
            text(
                "INSERT INTO user_roles (user_id, role_id, store_id, assigned_by, created_at) "
                "VALUES (:user_id, :role_id, :store_id, :assigned_by, NOW())"
            ),
            {"user_id": user_id, "role_id": role_id, "store_id": store_id, "assigned_by": assigned_by},
        )
        await self.db.commit()

    async def remove_role(self, user_id: str, role_id: str, store_id: str | None) -> None:
        """Remove a role from a user."""
        result = await self.db.execute(
            text(
                "DELETE FROM user_roles WHERE user_id = :user_id AND role_id = :role_id "
                "AND (store_id = :store_id OR (store_id IS NULL AND :store_id IS NULL)) "
                "RETURNING id"
            ),
            {"user_id": user_id, "role_id": role_id, "store_id": store_id},
        )
        if not result.scalar_one_or_none():
            raise AdminError(message="Role assignment not found", code="NOT_FOUND", status_code=404)
        await self.db.commit()

    async def update_account_status(self, user_id: str, status: str) -> None:
        """Activate or deactivate a user account."""
        if status not in ("active", "inactive", "suspended"):
            raise AdminError(message="Invalid status", code="INVALID_STATUS", status_code=400)

        result = await self.db.execute(
            text("UPDATE profiles SET status = :status, updated_at = NOW() WHERE id = :user_id RETURNING id"),
            {"user_id": user_id, "status": status},
        )
        if not result.scalar_one_or_none():
            raise AdminError(message="User not found", code="USER_NOT_FOUND", status_code=404)
        await self.db.commit()

    async def list_roles(self) -> list[dict]:
        """List all roles."""
        result = await self.db.execute(
            text("SELECT id, name, description FROM roles ORDER BY name")
        )
        return [
            {"id": str(row["id"]), "name": row["name"], "description": row["description"]}
            for row in result.mappings().all()
        ]

    # ─── Dashboard & Reports ─────────────────────────────────────────────────

    async def get_dashboard_stats(self, store_id: str | None = None) -> dict:
        """Get dashboard statistics, optionally scoped to a store."""
        stats: dict[str, Any] = {}

        # Total users
        user_count = await self.db.execute(text("SELECT COUNT(*) FROM profiles"))
        stats["total_users"] = user_count.scalar() or 0

        # Total stores
        store_count = await self.db.execute(text("SELECT COUNT(*) FROM stores"))
        stats["total_stores"] = store_count.scalar() or 0

        # Active stores
        active_store_count = await self.db.execute(
            text("SELECT COUNT(*) FROM stores WHERE status = 'active'")
        )
        stats["active_stores"] = active_store_count.scalar() or 0

        # Total products
        if store_id:
            prod_count = await self.db.execute(
                text("SELECT COUNT(*) FROM products WHERE store_id = :store_id"),
                {"store_id": store_id},
            )
            active_prod_count = await self.db.execute(
                text("SELECT COUNT(*) FROM products WHERE store_id = :store_id AND status = 'active'"),
                {"store_id": store_id},
            )
        else:
            prod_count = await self.db.execute(text("SELECT COUNT(*) FROM products"))
            active_prod_count = await self.db.execute(
                text("SELECT COUNT(*) FROM products WHERE status = 'active'")
            )
        stats["total_products"] = prod_count.scalar() or 0
        stats["active_products"] = active_prod_count.scalar() or 0

        # Orders
        if store_id:
            order_count = await self.db.execute(
                text(
                    "SELECT COUNT(*) FROM orders o "
                    "JOIN store_orders so ON so.order_id = o.id "
                    "WHERE so.store_id = :store_id"
                ),
                {"store_id": store_id},
            )
            pending_count = await self.db.execute(
                text(
                    "SELECT COUNT(*) FROM orders o "
                    "JOIN store_orders so ON so.order_id = o.id "
                    "WHERE so.store_id = :store_id AND o.order_status = 'pending'"
                ),
                {"store_id": store_id},
            )
            revenue_result = await self.db.execute(
                text(
                    "SELECT COALESCE(SUM(o.grand_total), 0) FROM orders o "
                    "JOIN store_orders so ON so.order_id = o.id "
                    "WHERE so.store_id = :store_id"
                ),
                {"store_id": store_id},
            )
        else:
            order_count = await self.db.execute(text("SELECT COUNT(*) FROM orders"))
            pending_count = await self.db.execute(
                text("SELECT COUNT(*) FROM orders WHERE order_status = 'pending'")
            )
            revenue_result = await self.db.execute(
                text("SELECT COALESCE(SUM(grand_total), 0) FROM orders")
            )
        stats["total_orders"] = order_count.scalar() or 0
        stats["pending_orders"] = pending_count.scalar() or 0
        stats["total_revenue"] = revenue_result.scalar() or 0

        return stats

    async def get_sales_report(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        store_id: str | None = None,
    ) -> dict:
        """Get sales report with status distribution."""
        where_clauses = ["1=1"]
        params: dict[str, Any] = {}

        if store_id:
            where_clauses.append(
                "o.id IN (SELECT order_id FROM store_orders WHERE store_id = :store_id)"
            )
            params["store_id"] = store_id
        if date_from:
            where_clauses.append("o.created_at >= :date_from")
            params["date_from"] = date_from
        if date_to:
            where_clauses.append("o.created_at <= :date_to")
            params["date_to"] = date_to

        where_sql = " AND ".join(where_clauses)

        # Totals
        totals_result = await self.db.execute(
            text(
                f"SELECT COUNT(*) as total_orders, "
                f"COALESCE(SUM(grand_total), 0) as total_revenue, "
                f"COALESCE(SUM(discount_total), 0) as total_discount, "
                f"COALESCE(SUM(delivery_total), 0) as total_delivery "
                f"FROM orders o WHERE {where_sql}"
            ),
            params,
        )
        totals = totals_result.mappings().first()

        # Status distribution
        status_result = await self.db.execute(
            text(
                f"SELECT order_status, COUNT(*) as count FROM orders o "
                f"WHERE {where_sql} GROUP BY order_status"
            ),
            params,
        )
        status_dist = [
            {"status": row["order_status"], "count": row["count"]}
            for row in status_result.mappings().all()
        ]

        return {
            "total_orders": totals["total_orders"] if totals else 0,
            "total_revenue": str(totals["total_revenue"]) if totals else "0",
            "total_discount": str(totals["total_discount"]) if totals else "0",
            "total_delivery": str(totals["total_delivery"]) if totals else "0",
            "currency_code": "BDT",
            "status_distribution": status_dist,
            "date_from": date_from,
            "date_to": date_to,
            "store_id": store_id,
        }

    async def get_inventory_summary(self, store_id: str | None = None) -> dict:
        """Get inventory summary."""
        if store_id:
            result = await self.db.execute(
                text(
                    "SELECT COUNT(*) as total_variants, "
                    "COALESCE(SUM(quantity_on_hand), 0) as total_on_hand, "
                    "COALESCE(SUM(quantity_reserved), 0) as total_reserved "
                    "FROM inventory_balances ib "
                    "JOIN product_variants pv ON pv.id = ib.variant_id "
                    "JOIN products p ON p.id = pv.product_id "
                    "WHERE p.store_id = :store_id"
                ),
                {"store_id": store_id},
            )
            low_stock = await self.db.execute(
                text(
                    "SELECT COUNT(*) FROM inventory_balances ib "
                    "JOIN product_variants pv ON pv.id = ib.variant_id "
                    "JOIN products p ON p.id = pv.product_id "
                    "WHERE p.store_id = :store_id AND ib.quantity_on_hand <= 5"
                ),
                {"store_id": store_id},
            )
        else:
            result = await self.db.execute(
                text(
                    "SELECT COUNT(*) as total_variants, "
                    "COALESCE(SUM(quantity_on_hand), 0) as total_on_hand, "
                    "COALESCE(SUM(quantity_reserved), 0) as total_reserved "
                    "FROM inventory_balances"
                )
            )
            low_stock = await self.db.execute(
                text("SELECT COUNT(*) FROM inventory_balances WHERE quantity_on_hand <= 5")
            )

        row = result.mappings().first()
        return {
            "total_variants": row["total_variants"] if row else 0,
            "total_on_hand": int(row["total_on_hand"]) if row else 0,
            "total_reserved": int(row["total_reserved"]) if row else 0,
            "low_stock_count": low_stock.scalar() or 0,
            "store_id": store_id,
        }
