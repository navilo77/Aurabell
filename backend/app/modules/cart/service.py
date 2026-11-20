"""Cart service (M4.1 Shared Cart).

Implements cart management with guest and authenticated user support,
automatic guest-to-user cart merging on login, and server-side pricing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError
from app.modules.cart.schema import (
    CartItemCreate,
    CartItemRead,
    CartRead,
    CheckoutPreview,
    CheckoutPreviewItem,
)
from app.modules.inventory.service import InventoryService
from app.modules.pricing.service import PricingService


class CartService:
    """Shared cart management: add/remove items, checkout preview, cart lifecycle."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.inventory = InventoryService(db)
        self.pricing = PricingService(db)

    async def _get_central_warehouse_id(self) -> str:
        """Get the ID of the Main Central Warehouse."""
        result = await self.db.execute(
            text("SELECT id FROM warehouses WHERE name = 'Main Central Warehouse' LIMIT 1")
        )
        row = result.mappings().first()
        if not row:
            raise AuthError(
                message="Main Central Warehouse not found",
                code="WAREHOUSE_NOT_FOUND",
                status_code=500,
            )
        return str(row["id"])

    # ------------------------------------------------------------------
    # Ownership enforcement (IDOR prevention)
    # ------------------------------------------------------------------

    async def _assert_cart_access(
        self,
        cart_id: str,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        """Ensure the caller owns the cart.

        A cart is accessible when:
        - It is bound to ``user_id`` and that matches the authenticated user, or
        - It is a guest cart bound to ``session_id`` and that matches the
          caller-provided guest session.

        Raises 404 (not 403) when access is denied so the endpoint does not
        leak the existence of other users' carts.
        """
        result = await self.db.execute(
            text("SELECT user_id, session_id FROM carts WHERE id = :cart_id"),
            {"cart_id": cart_id},
        )
        row = result.mappings().first()
        if not row:
            raise AuthError(
                message="Cart not found",
                code="CART_NOT_FOUND",
                status_code=404,
            )

        owner_user = str(row["user_id"]) if row["user_id"] else None
        owner_session = str(row["session_id"]) if row["session_id"] else None

        if user_id and owner_user == str(user_id):
            return
        if session_id and owner_session and owner_session == str(session_id):
            return

        raise AuthError(
            message="Cart not found",
            code="CART_NOT_FOUND",
            status_code=404,
        )

    # ------------------------------------------------------------------
    # Cart discovery / creation
    # ------------------------------------------------------------------

    async def get_or_create_cart(
        self,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> CartRead:
        """Return an existing active cart, or create a new one.

        At least one of ``user_id`` or ``session_id`` must be provided.
        """
        if not user_id and not session_id:
            raise AuthError(
                message="Either user_id or session_id is required",
                code="MISSING_IDENTIFIER",
                status_code=400,
            )

        # Try to find an existing active cart matching the identifier
        stmt = text(
            """
            SELECT id, user_id, session_id, status, created_at, updated_at
            FROM carts
            WHERE (user_id = :uid OR session_id = :sid) AND status = 'active'
            LIMIT 1
            """
        )
        result = await self.db.execute(stmt, {"uid": user_id, "sid": session_id})
        row = result.mappings().first()

        if row:
            return CartRead(
                id=str(row["id"]),
                user_id=str(row["user_id"]) if row["user_id"] else None,
                session_id=str(row["session_id"]) if row["session_id"] else None,
                status=row["status"],
                created_at=str(row["created_at"]) if row["created_at"] else None,
                updated_at=str(row["updated_at"]) if row["updated_at"] else None,
            )

        # Create a new cart
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            text(
                """
                INSERT INTO carts (user_id, session_id, status, created_at, updated_at)
                VALUES (:user_id, :session_id, 'active', :now, :now)
                RETURNING id, user_id, session_id, status, created_at, updated_at
                """
            ),
            {
                "user_id": user_id,
                "session_id": session_id,
                "now": now,
            },
        )
        row = result.mappings().first()
        return CartRead(
            id=str(row["id"]),
            user_id=str(row["user_id"]) if row["user_id"] else None,
            session_id=str(row["session_id"]) if row["session_id"] else None,
            status=row["status"],
            created_at=str(row["created_at"]) if row["created_at"] else None,
            updated_at=str(row["updated_at"]) if row["updated_at"] else None,
        )

    async def merge_guest_cart_to_user(
        self,
        guest_session_id: str,
        user_id: str,
    ) -> None:
        """Merge guest cart items into user's cart and deactivate guest cart.

        If a guest cart exists for the session, move its items to the user's
        cart (creating one if needed). The guest cart is then marked as abandoned.
        """
        # Get guest cart items
        guest_items = await self.db.execute(
            text(
                """
                SELECT variant_id, quantity
                FROM cart_items
                WHERE cart_id IN (
                    SELECT id FROM carts
                    WHERE session_id = :session_id AND status = 'active'
                )
                """
            ),
            {"session_id": guest_session_id},
        )
        guest_item_rows = guest_items.mappings().all()

        if not guest_item_rows:
            return  # No guest cart to merge

        # Get or create user cart
        user_cart = await self.get_or_create_cart(user_id=user_id)

        # Insert items into user cart, adding quantities if duplicates exist
        for item in guest_item_rows:
            variant_id = item["variant_id"]
            quantity = item["quantity"]

            # Check if variant already exists in user cart
            existing = await self.db.execute(
                text(
                    """
                    SELECT id, quantity
                    FROM cart_items
                    WHERE cart_id = :cart_id AND variant_id = :variant_id
                    """
                ),
                {"cart_id": user_cart.id, "variant_id": variant_id},
            )
            existing_row = existing.mappings().first()

            if existing_row:
                # Add quantities
                new_quantity = existing_row["quantity"] + quantity
                await self.db.execute(
                    text(
                        """
                        UPDATE cart_items
                        SET quantity = :new_quantity, updated_at = NOW()
                        WHERE id = :item_id
                        """
                    ),
                    {"new_quantity": new_quantity, "item_id": existing_row["id"]},
                )
            else:
                # Insert new item
                await self.db.execute(
                    text(
                        """
                        INSERT INTO cart_items (cart_id, variant_id, quantity, created_at, updated_at)
                        VALUES (:cart_id, :variant_id, :quantity, NOW(), NOW())
                        """
                    ),
                    {
                        "cart_id": user_cart.id,
                        "variant_id": variant_id,
                        "quantity": quantity,
                    },
                )

        # Mark guest cart as abandoned
        await self.db.execute(
            text(
                """
                UPDATE carts
                SET status = 'abandoned', updated_at = NOW()
                WHERE session_id = :session_id AND status = 'active'
                """
            ),
            {"session_id": guest_session_id},
        )
        await self.db.commit()

    # ------------------------------------------------------------------
    # Cart item operations
    # ------------------------------------------------------------------

    async def add_item(
        self,
        cart_id: str,
        variant_id: str,
        quantity: int = 1,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> CartItemRead:
        """Add a product variant to the cart.

        Validates that the variant exists, is active, and has sufficient stock.
        If the variant already exists in the cart, quantity is increased.
        """
        # Verify cart exists AND caller owns it (IDOR prevention)
        await self._assert_cart_access(cart_id, user_id=user_id, session_id=session_id)

        # Verify variant exists and is active
        variant_result = await self.db.execute(
            text(
                """
                SELECT id, is_active, product_id
                FROM product_variants
                WHERE id = :variant_id
                """
            ),
            {"variant_id": variant_id},
        )
        variant_row = variant_result.mappings().first()
        if not variant_row:
            raise AuthError(message="Product variant not found", code="VARIANT_NOT_FOUND", status_code=404)

        if not variant_row["is_active"]:
            raise AuthError(
                message="Product variant is not active",
                code="VARIANT_INACTIVE",
                status_code=400,
            )

        # Verify product is active
        product_result = await self.db.execute(
            text("SELECT id, status FROM products WHERE id = :product_id"),
            {"product_id": variant_row["product_id"]},
        )
        product_row = product_result.mappings().first()
        if not product_row or product_row["status"] != "active":
            raise AuthError(
                message="Product is not active",
                code="PRODUCT_INACTIVE",
                status_code=400,
            )

        # Check if item already in cart
        stmt = text(
            """
            SELECT id, quantity
            FROM cart_items
            WHERE cart_id = :cart_id AND variant_id = :variant_id
            """
        )
        result = await self.db.execute(stmt, {"cart_id": cart_id, "variant_id": variant_id})
        existing = result.mappings().first()

        now = datetime.now(timezone.utc)
        if existing:
            # Update existing item
            new_quantity = existing["quantity"] + quantity

            result = await self.db.execute(
                text(
                    """
                    UPDATE cart_items
                    SET quantity = :new_quantity, updated_at = :updated_at
                    WHERE id = :id
                    RETURNING id, cart_id, variant_id, quantity, created_at, updated_at
                    """
                ),
                {
                    "new_quantity": new_quantity,
                    "updated_at": now,
                    "id": existing["id"],
                },
            )
        else:
            # Insert new item
            result = await self.db.execute(
                text(
                    """
                    INSERT INTO cart_items (cart_id, variant_id, quantity, created_at, updated_at)
                    VALUES (:cart_id, :variant_id, :quantity, :now, :now)
                    RETURNING id, cart_id, variant_id, quantity, created_at, updated_at
                    """
                ),
                {
                    "cart_id": cart_id,
                    "variant_id": variant_id,
                    "quantity": quantity,
                    "now": now,
                },
            )

        row = result.mappings().first()
        return CartItemRead(
            id=str(row["id"]),
            cart_id=str(row["cart_id"]),
            variant_id=str(row["variant_id"]),
            quantity=row["quantity"],
            created_at=str(row["created_at"]) if row["created_at"] else None,
            updated_at=str(row["updated_at"]) if row["updated_at"] else None,
        )

    async def remove_item(
        self,
        cart_id: str,
        variant_id: str,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> bool:
        """Remove a cart item entirely. Returns True if a row was deleted."""
        await self._assert_cart_access(cart_id, user_id=user_id, session_id=session_id)
        result = await self.db.execute(
            text(
                "DELETE FROM cart_items WHERE cart_id = :cart_id AND variant_id = :variant_id"
            ),
            {"cart_id": cart_id, "variant_id": variant_id},
        )
        return result.rowcount > 0

    async def update_item_quantity(
        self,
        cart_id: str,
        variant_id: str,
        quantity: int,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> CartItemRead:
        """Update a cart item's quantity.

        If quantity is 0 or less, the item is removed.
        """
        await self._assert_cart_access(cart_id, user_id=user_id, session_id=session_id)
        if quantity <= 0:
            await self.remove_item(cart_id, variant_id, user_id=user_id, session_id=session_id)
            raise AuthError(
                message="Quantity updated to <= 0; item removed",
                code="ITEM_REMOVED",
                status_code=400,
            )

        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            text(
                """
                UPDATE cart_items
                SET quantity = :quantity, updated_at = :updated_at
                WHERE cart_id = :cart_id AND variant_id = :variant_id
                RETURNING id, cart_id, variant_id, quantity, created_at, updated_at
                """
            ),
            {
                "quantity": quantity,
                "updated_at": now,
                "cart_id": cart_id,
                "variant_id": variant_id,
            },
        )
        row = result.mappings().first()
        if row is None:
            raise AuthError(message="Cart item not found", code="ITEM_NOT_FOUND", status_code=404)

        return CartItemRead(
            id=str(row["id"]),
            cart_id=str(row["cart_id"]),
            variant_id=str(row["variant_id"]),
            quantity=row["quantity"],
            created_at=str(row["created_at"]) if row["created_at"] else None,
            updated_at=str(row["updated_at"]) if row["updated_at"] else None,
        )

    # ------------------------------------------------------------------
    # Checkout preview
    # ------------------------------------------------------------------

    async def checkout_preview(
        self,
        cart_id: str,
        coupon_code: str | None = None,
        district: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> CheckoutPreview:
        """Calculate a checkout preview for a cart with real server-side pricing.

        Returns per-store breakdown and totals using PricingService for validation.
        """
        await self._assert_cart_access(cart_id, user_id=user_id, session_id=session_id)

        # Get cart items with variant and store information
        stmt = text(
            """
            SELECT ci.id, ci.cart_id, ci.variant_id, ci.quantity,
                   pv.sku, pv.is_active,
                   p.id AS product_id, p.name AS product_name,
                   s.id AS store_id, s.name AS store_name
            FROM cart_items ci
            JOIN product_variants pv ON pv.id = ci.variant_id
            JOIN products p ON p.id = pv.product_id
            JOIN stores s ON s.id = p.store_id
            WHERE ci.cart_id = :cart_id
            """
        )
        result = await self.db.execute(stmt, {"cart_id": cart_id})
        cart_items = result.mappings().all()

        if not cart_items:
            return CheckoutPreview()

        preview_items: list[CheckoutPreviewItem] = []
        overall_subtotal = Decimal("0.00")

        for item in cart_items:
            variant_id = item["variant_id"]
            store_id = item["store_id"]
            product_name = item.get("product_name")
            sku = item.get("sku")

            # Get server-side price from PricingService
            try:
                price_calc = await self.pricing.calculate_price(
                    variant_id=UUID(variant_id),
                    store_id=UUID(store_id),
                    coupon_code=coupon_code,
                )
                unit_price = price_calc.final_price
                discount_amount = price_calc.discount_amount
            except Exception as e:
                # If pricing service fails, fallback to error - should not happen
                raise AuthError(
                    message=f"Failed to calculate price for variant {variant_id}: {str(e)}",
                    code="PRICE_CALCULATION_FAILED",
                    status_code=500,
                )

            # Check inventory availability
            central_warehouse_id = await self._get_central_warehouse_id()
            try:
                balance = await self.inventory.get_balance(
                    warehouse_id=central_warehouse_id,
                    variant_id=variant_id,
                )
                available_qty = balance.quantity_on_hand
                in_stock = available_qty > 0

                # Check if sufficient stock for cart quantity
                if available_qty < item["quantity"]:
                    in_stock = False
            except Exception:
                in_stock = False
                available_qty = 0

            line_total = round(unit_price * Decimal(str(item["quantity"])), 2)

            preview_items.append(
                CheckoutPreviewItem(
                    variant_id=variant_id,
                    sku=sku,
                    product_name=product_name,
                    quantity=item["quantity"],
                    unit_price=unit_price,
                    line_total=line_total,
                    discount_amount=discount_amount,
                    store_id=store_id,
                    store_name=item.get("store_name"),
                    in_stock=in_stock,
                    available_qty=available_qty,
                )
            )

            overall_subtotal += line_total

        # Calculate delivery fee based on district (DEC-OWN-003)
        delivery_total = Decimal("0.00")
        if district:
            if district.lower() in ["dhaka", "ঢাকা"]:
                delivery_total = Decimal("70.00")
            else:
                delivery_total = Decimal("120.00")

        discount_total = sum(
            Decimal(str(item.get("discount_amount", 0)))
            for item in preview_items
        )

        grand_total = round(overall_subtotal - discount_total + delivery_total, 2)

        return CheckoutPreview(
            items=preview_items,
            subtotal=round(overall_subtotal, 2),
            discount_total=round(discount_total, 2),
            delivery_total=round(delivery_total, 2),
            grand_total=round(grand_total, 2),
            currency_code="BDT",
        )

    # ------------------------------------------------------------------
    # Cart listing
    # ------------------------------------------------------------------

    async def list_cart_items(
        self,
        cart_id: str,
        user_id: str | None = None,
        session_id: str | None = None,
    ) -> list[CartItemRead]:
        """Return all items in a cart with stock validation."""
        await self._assert_cart_access(cart_id, user_id=user_id, session_id=session_id)
        stmt = text(
            """
            SELECT ci.id, ci.cart_id, ci.variant_id, ci.quantity,
                   pv.sku, pv.is_active,
                   p.name AS product_name, s.name AS store_name,
                   ci.created_at, ci.updated_at
            FROM cart_items ci
            JOIN product_variants pv ON pv.id = ci.variant_id
            JOIN products p ON p.id = pv.product_id
            JOIN stores s ON s.id = p.store_id
            WHERE ci.cart_id = :cart_id
            """
        )
        result = await self.db.execute(stmt, {"cart_id": cart_id})
        rows = result.mappings().all()

        cart_items = []
        for row in rows:
            variant_id = row["variant_id"]

            # Get inventory availability
            central_warehouse_id = await self._get_central_warehouse_id()
            in_stock = False
            available_qty = 0
            try:
                balance = await self.inventory.get_balance(
                    warehouse_id=central_warehouse_id,
                    variant_id=variant_id,
                )
                available_qty = balance.quantity_on_hand
                in_stock = available_qty >= row["quantity"]
            except Exception:
                pass

            cart_items.append(
                CartItemRead(
                    id=str(row["id"]),
                    cart_id=str(row["cart_id"]),
                    variant_id=str(row["variant_id"]),
                    quantity=row["quantity"],
                    product_name_snapshot=row.get("product_name"),
                    sku_snapshot=row.get("sku"),
                    unit_price=None,  # Will be populated by service layer if needed
                    line_total=None,
                    store_id=None,  # Will be populated by service layer if needed
                    store_name=row.get("store_name"),
                    in_stock=in_stock,
                    available_qty=available_qty,
                    created_at=str(row["created_at"]) if row["created_at"] else None,
                    updated_at=str(row["updated_at"]) if row["updated_at"] else None,
                )
            )

        return cart_items
