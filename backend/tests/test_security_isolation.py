"""Security isolation test suite for cross-store tenant isolation and IDOR prevention.

Tests cover:
- User model carries store_ids (STEP 1)
- Cart endpoints reject cross-user access (IDOR) (STEP 2)
- Order endpoints reject cross-user/vendor access (IDOR) (STEP 2)
- RLS policies scoped by store_id (STEP 3 - schema-level validation)
"""

from __future__ import annotations

from dataclasses import fields

import pytest

from app.core.auth import User


# ─── STEP 1: User model carries store_ids ───────────────────────────────────


class TestUserStoreIds:
    """The User dataclass must expose store_ids for cross-store authorization."""

    def test_user_dataclass_has_store_ids_field(self) -> None:
        field_names = {f.name for f in fields(User)}
        assert "store_ids" in field_names

    def test_user_default_store_ids_is_empty_list(self) -> None:
        user = User(id="u-1", email="a@b.c", roles=["customer"])
        assert user.store_ids == []

    def test_user_accepts_store_ids(self) -> None:
        user = User(
            id="u-2",
            email="mgr@b.c",
            roles=["store_manager"],
            store_ids=["store-a", "store-b"],
        )
        assert user.store_ids == ["store-a", "store-b"]


# ─── STEP 2: Cart IDOR prevention ───────────────────────────────────────────


class TestCartIdor:
    """Cart service must reject access by a user who does not own the cart."""

    @pytest.mark.asyncio
    async def test_assert_cart_access_rejects_other_user(self) -> None:
        """User B cannot read User A's cart → 404."""
        from unittest.mock import AsyncMock, MagicMock

        from app.core.exceptions import AuthError
        from app.modules.cart.service import CartService

        fake_db = AsyncMock()
        fake_result = MagicMock()
        fake_result.mappings.return_value.first.return_value = None
        fake_db.execute = AsyncMock(return_value=fake_result)

        service = CartService(fake_db)
        with pytest.raises(AuthError) as excinfo:
            await service._assert_cart_access(
                "cart-user-a", user_id="user-b", session_id=None
            )
        assert excinfo.value.status_code == 404
        assert excinfo.value.code == "CART_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_assert_cart_access_allows_owner_user(self) -> None:
        from unittest.mock import AsyncMock, MagicMock

        from app.modules.cart.service import CartService

        fake_db = AsyncMock()
        fake_result = MagicMock()
        fake_result.mappings.return_value.first.return_value = {
            "user_id": "user-a",
            "session_id": None,
        }
        fake_db.execute = AsyncMock(return_value=fake_result)

        service = CartService(fake_db)
        await service._assert_cart_access(
            "cart-user-a", user_id="user-a", session_id=None
        )

    @pytest.mark.asyncio
    async def test_assert_cart_access_allows_guest_session(self) -> None:
        from unittest.mock import AsyncMock, MagicMock

        from app.modules.cart.service import CartService

        fake_db = AsyncMock()
        fake_result = MagicMock()
        fake_result.mappings.return_value.first.return_value = {
            "user_id": None,
            "session_id": "guest-abc",
        }
        fake_db.execute = AsyncMock(return_value=fake_result)

        service = CartService(fake_db)
        await service._assert_cart_access(
            "guest-cart", user_id=None, session_id="guest-abc"
        )

    @pytest.mark.asyncio
    async def test_assert_cart_access_rejects_wrong_guest_session(self) -> None:
        from unittest.mock import AsyncMock, MagicMock

        from app.core.exceptions import AuthError
        from app.modules.cart.service import CartService

        fake_db = AsyncMock()
        fake_result = MagicMock()
        fake_result.mappings.return_value.first.return_value = {
            "user_id": None,
            "session_id": "guest-abc",
        }
        fake_db.execute = AsyncMock(return_value=fake_result)

        service = CartService(fake_db)
        with pytest.raises(AuthError):
            await service._assert_cart_access(
                "guest-cart", user_id=None, session_id="guest-xyz"
            )


# ─── STEP 2: Order IDOR prevention ──────────────────────────────────────────


class TestOrderIdor:
    """Order service must reject cross-user and cross-vendor access."""

    @pytest.mark.asyncio
    async def test_assert_order_access_rejects_other_customer(self) -> None:
        """User B cannot read User A's order → 404."""
        from unittest.mock import AsyncMock, MagicMock

        from app.core.exceptions import AuthError
        from app.modules.orders.service import OrdersService

        fake_db = AsyncMock()
        fake_result = MagicMock()
        fake_result.mappings.return_value.first.return_value = None
        fake_db.execute = AsyncMock(return_value=fake_result)

        service = OrdersService(fake_db)
        with pytest.raises(AuthError) as excinfo:
            await service._assert_order_access(
                "order-user-a", user_id="user-b", store_ids=None
            )
        assert excinfo.value.status_code == 404

    @pytest.mark.asyncio
    async def test_assert_order_access_allows_owner_customer(self) -> None:
        from unittest.mock import AsyncMock, MagicMock

        from app.modules.orders.service import OrdersService

        fake_db = AsyncMock()
        fake_result = MagicMock()
        fake_result.mappings.return_value.first.return_value = {"user_id": "user-a"}
        fake_db.execute = AsyncMock(return_value=fake_result)

        service = OrdersService(fake_db)
        await service._assert_order_access(
            "order-user-a", user_id="user-a", store_ids=None
        )

    @pytest.mark.asyncio
    async def test_assert_order_access_allows_vendor_of_store(self) -> None:
        """Vendor of store X can access an order that has a store_order for store X."""
        from unittest.mock import AsyncMock, MagicMock

        from app.modules.orders.service import OrdersService

        fake_db = AsyncMock()
        # First call: orders lookup returns a row (customer check fails) → falls to vendor check
        fake_orders_result = MagicMock()
        fake_orders_result.mappings.return_value.first.return_value = {
            "user_id": "customer-other"
        }
        # Second call: store_orders lookup returns a matching store row
        fake_store_result = MagicMock()
        fake_store_result.mappings.return_value.first.return_value = {"1": 1}
        fake_db.execute = AsyncMock(side_effect=[fake_orders_result, fake_store_result])

        service = OrdersService(fake_db)
        await service._assert_order_access(
            "order-1", user_id="vendor-user", store_ids=["store-x"]
        )

    @pytest.mark.asyncio
    async def test_assert_order_access_rejects_vendor_of_other_store(self) -> None:
        """Vendor of store X cannot access an order whose store_orders are store Y."""
        from unittest.mock import AsyncMock, MagicMock

        from app.core.exceptions import AuthError
        from app.modules.orders.service import OrdersService

        fake_db = AsyncMock()
        fake_orders_result = MagicMock()
        fake_orders_result.mappings.return_value.first.return_value = {
            "user_id": "customer-other"
        }
        fake_store_result = MagicMock()
        fake_store_result.mappings.return_value.first.return_value = None
        fake_db.execute = AsyncMock(side_effect=[fake_orders_result, fake_store_result])

        service = OrdersService(fake_db)
        with pytest.raises(AuthError) as excinfo:
            await service._assert_order_access(
                "order-1", user_id="vendor-user", store_ids=["store-y"]
            )
        assert excinfo.value.status_code == 404


# ─── STEP 3: RLS policy files exist ─────────────────────────────────────────


class TestRlsMigrationFiles:
    """Ensure security-focused RLS migration files are present."""

    def test_security_rls_migration_exists(self) -> None:
        from pathlib import Path

        migration_dir = Path("backend/supabase/migrations")
        security_files = [
            p
            for p in migration_dir.glob("*.sql")
            if "security" in p.name.lower() or "isolation" in p.name.lower()
        ]
        assert len(security_files) >= 1, "No cross-store isolation RLS migration found"
