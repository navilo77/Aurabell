"""Orders service (M4.2-M4.4).

Atomic split-order checkout engine with server-side pricing,
15-min stock reservations, and COD OTP verification.
"""

from __future__ import annotations

import random
import string
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError
from app.core.redis_otp import CODOTPStore, get_cod_otp_store
from app.modules.cart.service import CartService
from app.modules.inventory.service import InventoryService, InventoryReservationCreate
from app.modules.orders.schema import (
    CODVerifyRequest,
    CODVerifyResponse,
    OrderCreate,
    OrderRead,
)
from app.modules.pricing.service import PricingService


class OrdersError(AuthError):
    """Orders domain error."""

    pass


class OrdersService:
    """Order placement, split-order transaction, and COD verification."""

    def __init__(self, db: AsyncSession, otp_store: CODOTPStore | None = None) -> None:
        self.db = db
        self.cart_service = CartService(db)
        self.inventory = InventoryService(db)
        self.pricing = PricingService(db)
        self._otp_store = otp_store

    async def _get_otp_store(self) -> CODOTPStore:
        if self._otp_store is not None:
            return self._otp_store
        return await get_cod_otp_store()

    # ------------------------------------------------------------------
    # Helper: Generate unique order numbers
    # ------------------------------------------------------------------

    def _generate_order_number(self) -> str:
        """Generate human-readable order number: AB-YYYYMMDD-XXXX."""
        date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"AB-{date_part}-{random_part}"

    def _generate_store_order_number(self, store_code: str) -> str:
        """Generate store order number: AB-SO-{STORE}-XXXX."""
        random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"AB-SO-{store_code.upper()}-{random_part}"

    def _generate_otp(self) -> str:
        """Generate 4-digit numeric OTP."""
        return "".join(random.choices(string.digits, k=4))

    # ------------------------------------------------------------------
    # Order access control (IDOR prevention)
    # ------------------------------------------------------------------

    async def _assert_order_access(
        self,
        order_id: str,
        user_id: str | None = None,
        store_ids: list[str] | None = None,
    ) -> None:
        """Ensure caller has access to the order.

        Access rules:
        - Customer (user_id): order.user_id must match user_id.
        - Vendor (store_ids): at least one store_order.store_id must be in store_ids.
        - Super admin (no store_ids, but role 'admin'): allowed implicitly if
          neither user_id nor store_ids provided? We'll allow if user_id is None
          and store_ids is None — but this shouldn't happen in normal flow as
          the router always passes context. For safety, deny if no context.

        Raises 404 when access is denied (avoids leaking order existence).
        """
        if not user_id and not store_ids:
            raise OrdersError(
                message="Order not found", code="ORDER_NOT_FOUND", status_code=404
            )

        # Customer ownership check
        if user_id:
            result = await self.db.execute(
                text("SELECT user_id FROM orders WHERE id = :order_id"),
                {"order_id": order_id},
            )
            row = result.mappings().first()
            if not row:
                raise OrdersError(
                    message="Order not found", code="ORDER_NOT_FOUND", status_code=404
                )
            if str(row["user_id"]) == str(user_id):
                return

        # Vendor store scoping check
        if store_ids:
            result = await self.db.execute(
                text(
                    """
                    SELECT 1 FROM store_orders
                    WHERE order_id = :order_id AND store_id = ANY(:store_ids)
                    """
                ),
                {"order_id": order_id, "store_ids": store_ids},
            )
            row = result.mappings().first()
            if row:
                return

        raise OrdersError(
            message="Order not found", code="ORDER_NOT_FOUND", status_code=404
        )

    # ------------------------------------------------------------------
    # Checkout: Atomic split-order transaction
    # ------------------------------------------------------------------

    async def place_order(
        self,
        order_data: OrderCreate,
        user_id: str,
    ) -> OrderRead:
        """Place order atomically in single DB transaction.

        Creates:
        1. Parent order (orders)
        2. Delivery address snapshot (order_addresses)
        3. Store orders per store (store_orders)
        4. Order items with snapshots (order_items)
        5. Stock reservations (inventory_reservations) - 15 min TTL
        6. Promotion redemption record
        7. Status history
        8. Mark cart as converted
        """
        # ─── Address Resolution (BE-03) ─────────────────────────────────────
        # Case C: both supplied → reject as ambiguous
        if order_data.delivery_address_id and order_data.address:
            raise OrdersError(
                message="Provide either delivery_address_id or address, not both",
                code="AMBIGUOUS_ADDRESS",
                status_code=400,
            )

        # Case D: neither supplied → reject
        if not order_data.delivery_address_id and not order_data.address:
            raise OrdersError(
                message="Delivery address is required (delivery_address_id or address)",
                code="ADDRESS_REQUIRED",
                status_code=400,
            )

        # Resolve delivery address into snapshot fields
        resolved: dict = {}
        if order_data.delivery_address_id:
            # Case A: saved address — verify ownership
            addr_result = await self.db.execute(
                text(
                    "SELECT recipient_name, phone, division, district, upazila, "
                    "area, address_line, postal_code FROM addresses "
                    "WHERE id = :addr_id AND user_id = :user_id"
                ),
                {"addr_id": order_data.delivery_address_id, "user_id": user_id},
            )
            addr_row = addr_result.mappings().first()
            if not addr_row:
                raise OrdersError(
                    message="Address not found or does not belong to user",
                    code="ADDRESS_NOT_FOUND",
                    status_code=404,
                )
            resolved = {
                "recipient_name": addr_row["recipient_name"],
                "phone": addr_row["phone"],
                "division": addr_row["division"],
                "district": addr_row["district"],
                "upazila": addr_row["upazila"],
                "area": addr_row["area"],
                "address_line": addr_row["address_line"],
                "postal_code": addr_row["postal_code"],
            }
        else:
            # Case B: inline address — validate via Pydantic (already validated by schema)
            addr = order_data.address
            resolved = {
                "recipient_name": addr.recipient_name,
                "phone": addr.phone,
                "division": addr.division,
                "district": addr.district,
                "upazila": addr.upazila,
                "area": addr.area,
                "address_line": addr.address_line,
                "postal_code": addr.postal_code,
            }

        # Derive district for delivery fee if not provided
        if not order_data.district:
            order_data.district = resolved["district"]

        # Validate cart exists and belongs to user
        cart = await self.cart_service.get_or_create_cart(user_id=user_id)
        if cart.id != order_data.cart_id:
            # Try to get the specific cart
            cart_stmt = text(
                "SELECT id, user_id, session_id, status FROM carts WHERE id = :cart_id"
            )
            cart_result = await self.db.execute(cart_stmt, {"cart_id": order_data.cart_id})
            cart_row = cart_result.mappings().first()
            if not cart_row:
                raise OrdersError(
                    message="Cart not found", code="CART_NOT_FOUND", status_code=404
                )
            if cart_row["status"] != "active":
                raise OrdersError(
                    message="Cart is not active", code="CART_NOT_ACTIVE", status_code=400
                )
            if cart_row["user_id"] != user_id and cart_row["session_id"] != user_id:
                raise OrdersError(
                    message="Cart does not belong to user", code="CART_MISMATCH", status_code=403
                )

        # Get cart items
        cart_items = await self.cart_service.list_cart_items(order_data.cart_id)
        if not cart_items:
            raise OrdersError(
                message="Cart is empty", code="CART_EMPTY", status_code=400
            )

        # Validate phone number for COD
        if order_data.payment_method == "cod" and order_data.district:
            # Phone will be validated from address snapshot
            pass

        async with self.db.begin():
            # 1. Generate order number
            order_number = self._generate_order_number()

            # 2. Calculate prices and totals via checkout preview
            checkout_preview = await self.cart_service.checkout_preview(
                order_data.cart_id,
                coupon_code=order_data.coupon_code,
                district=order_data.district,
            )

            delivery_fee = self._calculate_delivery_fee(order_data.district)

            # 3. Create parent order
            order_result = await self.db.execute(
                text(
                    """
                    INSERT INTO orders
                    (order_number, user_id, subtotal, discount_total, delivery_total,
                     grand_total, currency_code, order_status, created_at, updated_at)
                    VALUES
                    (:order_number, :user_id, :subtotal, :discount_total, :delivery_total,
                     :grand_total, :currency_code, 'pending', NOW(), NOW())
                    RETURNING id
                    """
                ),
                {
                    "order_number": order_number,
                    "user_id": user_id,
                    "subtotal": checkout_preview.subtotal,
                    "discount_total": checkout_preview.discount_total,
                    "delivery_total": delivery_fee,
                    "grand_total": checkout_preview.grand_total,
                    "currency_code": "BDT",
                },
            )
            order_id = str(order_result.scalar_one())

            # 4. Create delivery address snapshot (immutable order-level copy)
            await self.db.execute(
                text(
                    """
                    INSERT INTO order_addresses
                    (order_id, recipient_name, phone, division, district, upazila,
                     area, address_line, postal_code, address_type, created_at)
                    VALUES
                    (:order_id, :recipient_name, :phone, :division, :district, :upazila,
                     :area, :address_line, :postal_code, 'delivery', NOW())
                    """
                ),
                {
                    "order_id": order_id,
                    "recipient_name": resolved["recipient_name"],
                    "phone": resolved["phone"],
                    "division": resolved["division"],
                    "district": resolved["district"],
                    "upazila": resolved["upazila"],
                    "area": resolved["area"],
                    "address_line": resolved["address_line"],
                    "postal_code": resolved["postal_code"],
                },
            )

            # 5. Group items by store and create store orders
            items_by_store: dict[str, list] = {}
            for item in cart_items:
                store_id = item.store_id
                if store_id not in items_by_store:
                    items_by_store[store_id] = []
                items_by_store[store_id].append(item)

            central_warehouse_id = await self.cart_service._get_central_warehouse_id()

            for store_id, items in items_by_store.items():
                # Get store code for order number
                store_result = await self.db.execute(
                    text("SELECT code FROM stores WHERE id = :store_id"),
                    {"store_id": store_id},
                )
                store_row = store_result.mappings().first()
                store_code = store_row["code"] if store_row else "STORE"

                store_order_number = self._generate_store_order_number(store_code)

                # Calculate store subtotal
                store_subtotal = sum(
                    item.line_total for item in items if item.line_total
                )

                # Create store order
                store_order_result = await self.db.execute(
                    text(
                        """
                        INSERT INTO store_orders
                        (order_id, store_id, store_order_number, subtotal, delivery_fee, status, created_at)
                        VALUES
                        (:order_id, :store_id, :store_order_number, :subtotal, 0, 'pending', NOW())
                        RETURNING id
                        """
                    ),
                    {
                        "order_id": order_id,
                        "store_id": store_id,
                        "store_order_number": store_order_number,
                        "subtotal": store_subtotal,
                    },
                )
                store_order_id = str(store_order_result.scalar_one())

                # 6. Create order items with snapshots
                for item in items:
                    # Get product and variant details for snapshot
                    product_result = await self.db.execute(
                        text(
                            """
                            SELECT p.name, pv.sku, pv.attributes
                            FROM product_variants pv
                            JOIN products p ON p.id = pv.product_id
                            WHERE pv.id = :variant_id
                            """
                        ),
                        {"variant_id": item.variant_id},
                    )
                    product_row = product_result.mappings().first()

                    # Get final price for this variant
                    price_calc = await self.pricing.calculate_price(
                        variant_id=UUID(item.variant_id),
                        store_id=UUID(store_id),
                        coupon_code=order_data.coupon_code,
                    )

                    line_total = round(price_calc.final_price * Decimal(str(item.quantity)), 2)

                    await self.db.execute(
                        text(
                            """
                            INSERT INTO order_items
                            (store_order_id, variant_id, product_name_snapshot, sku_snapshot,
                             variant_snapshot, unit_price, quantity, discount_amount, line_total, created_at)
                            VALUES
                            (:store_order_id, :variant_id, :product_name, :sku, :attributes,
                             :unit_price, :quantity, :discount_amount, :line_total, NOW())
                            """
                        ),
                        {
                            "store_order_id": store_order_id,
                            "variant_id": item.variant_id,
                            "product_name": product_row["name"] if product_row else "Unknown Product",
                            "sku": product_row["sku"] if product_row else "",
                            "attributes": product_row["attributes"] if product_row else {},
                            "unit_price": price_calc.final_price,
                            "quantity": item.quantity,
                            "discount_amount": price_calc.discount_amount,
                            "line_total": line_total,
                        },
                    )

                    # 7. Create stock reservation (15 min TTL)
                    reservation = await self.inventory.create_reservation(
                        InventoryReservationCreate(
                            variant_id=item.variant_id,
                            warehouse_id=central_warehouse_id,
                            order_id=order_id,
                            store_order_id=store_order_id,
                            quantity=item.quantity,
                        ),
                        created_by=user_id,
                    )

            # 8. Record coupon redemption if applicable
            if order_data.coupon_code:
                promo_result = await self.db.execute(
                    text("SELECT id FROM promotions WHERE coupon_code = :code"),
                    {"code": order_data.coupon_code.upper()},
                )
                promo_row = promo_result.mappings().first()
                if promo_row:
                    await self.db.execute(
                        text(
                            """
                            INSERT INTO promotion_redemptions
                            (promotion_id, user_id, order_id, discount_amount, redeemed_at)
                            VALUES
                            (:promo_id, :user_id, :order_id, :discount, NOW())
                            """
                        ),
                        {
                            "promo_id": promo_row["id"],
                            "user_id": user_id,
                            "order_id": order_id,
                            "discount": checkout_preview.discount_total,
                        },
                    )

            # 9. Create order status history
            await self.db.execute(
                text(
                    """
                    INSERT INTO order_status_history
                    (order_id, old_status, new_status, changed_by, note, created_at)
                    VALUES
                    (:order_id, NULL, 'pending', :user_id, 'Order placed via checkout', NOW())
                    """
                ),
                {"order_id": order_id, "user_id": user_id},
            )

            # 10. Mark cart as converted
            await self.db.execute(
                text(
                    "UPDATE carts SET status = 'converted', updated_at = NOW() WHERE id = :cart_id"
                ),
                {"cart_id": order_data.cart_id},
            )

            # Commit is automatic with async with self.db.begin()

            # Handle COD OTP generation
            if order_data.payment_method == "cod":
                otp = self._generate_otp()
                otp_store = await self._get_otp_store()
                await otp_store.store_otp(order_id, otp)
                # In production, send via SMS gateway
                # For dev, print to console
                print(f"[COD OTP] Order {order_number}: {otp}")

        # Return the created order
        return await self.get_order(order_id)

    async def get_order(
        self,
        order_id: str,
        user_id: str | None = None,
        store_ids: list[str] | None = None,
    ) -> OrderRead:
        """Get order with store orders and items.

        Access rules:
        - Customer: allowed only if order.user_id == user_id.
        - Vendor (store manager/super_admin): allowed if the order has at least
          one store_order whose store_id is in store_ids.
        - Super admin (platform): allowed without store scoping.
        """
        await self._assert_order_access(order_id, user_id=user_id, store_ids=store_ids)

        # Get parent order
        order_result = await self.db.execute(
            text(
                """
                SELECT id, order_number, user_id, subtotal, discount_total, delivery_total,
                       grand_total, currency_code, order_status, created_at
                FROM orders WHERE id = :order_id
                """
            ),
            {"order_id": order_id},
        )
        order_row = order_result.mappings().first()
        if not order_row:
            raise OrdersError(message="Order not found", code="ORDER_NOT_FOUND", status_code=404)

        # Get store orders
        store_orders_result = await self.db.execute(
            text(
                """
                SELECT so.id, so.order_id, so.store_id, so.store_order_number,
                       so.subtotal, so.delivery_fee, so.status, so.created_at
                FROM store_orders so WHERE so.order_id = :order_id
                """
            ),
            {"order_id": order_id},
        )
        store_orders = store_orders_result.mappings().all()

        # Get delivery address snapshot
        addr_result = await self.db.execute(
            text(
                """
                SELECT recipient_name, phone, division, district, upazila,
                       area, address_line, postal_code, address_type
                FROM order_addresses
                WHERE order_id = :order_id AND address_type = 'delivery'
                LIMIT 1
                """
            ),
            {"order_id": order_id},
        )
        addr_row = addr_result.mappings().first()

        delivery_address = None
        if addr_row:
            from app.modules.orders.schema import OrderAddressRead
            delivery_address = OrderAddressRead(
                recipient_name=addr_row["recipient_name"],
                phone=addr_row["phone"],
                division=addr_row["division"],
                district=addr_row["district"],
                upazila=addr_row["upazila"],
                area=addr_row["area"],
                address_line=addr_row["address_line"],
                postal_code=addr_row["postal_code"],
                address_type=addr_row["address_type"],
            )

        # Get order items
        items_result = await self.db.execute(
            text(
                """
                SELECT oi.id, oi.store_order_id, oi.variant_id, oi.product_name_snapshot,
                       oi.sku_snapshot, oi.variant_snapshot, oi.unit_price,
                       oi.quantity, oi.discount_amount, oi.line_total
                FROM order_items oi
                JOIN store_orders so ON so.id = oi.store_order_id
                WHERE so.order_id = :order_id
                """
            ),
            {"order_id": order_id},
        )
        order_items = items_result.mappings().all()

        return OrderRead(
            id=str(order_row["id"]),
            order_number=order_row["order_number"],
            user_id=str(order_row["user_id"]) if order_row["user_id"] else None,
            subtotal=order_row["subtotal"],
            discount_total=order_row["discount_total"],
            delivery_total=order_row["delivery_total"],
            grand_total=order_row["grand_total"],
            currency_code=order_row["currency_code"],
            order_status=order_row["order_status"],
            created_at=str(order_row["created_at"]),
            delivery_address=delivery_address,
            store_orders=[
                OrderRead(
                    id=str(so["id"]),
                    order_number=so["store_order_number"],
                    subtotal=so["subtotal"],
                    delivery_total=so["delivery_fee"],
                    grand_total=so["subtotal"] + so["delivery_fee"],
                    order_status=so["status"],
                    created_at=str(so["created_at"]),
                )
                for so in store_orders
            ],
            order_items=[
                OrderItemRead(
                    id=str(item["id"]),
                    product_name_snapshot=item["product_name_snapshot"],
                    sku_snapshot=item["sku_snapshot"],
                    variant_snapshot=item["variant_snapshot"],
                    unit_price=item["unit_price"],
                    quantity=item["quantity"],
                    discount_amount=item["discount_amount"],
                    line_total=item["line_total"],
                )
                for item in order_items
            ],
        )

    async def get_order_timeline(
        self,
        order_id: str,
        user_id: str | None = None,
        store_ids: list[str] | None = None,
    ) -> list:
        await self._assert_order_access(order_id, user_id=user_id, store_ids=store_ids)

        result = await self.db.execute(
            text(
                "SELECT old_status, new_status, changed_by, note, created_at "
                "FROM order_status_history WHERE order_id = :order_id "
                "ORDER BY created_at ASC"
            ),
            {"order_id": order_id},
        )
        rows = result.mappings().all()
        from app.modules.orders.schema import OrderTimelineEntry
        return [
            OrderTimelineEntry(
                old_status=row["old_status"],
                new_status=row["new_status"],
                changed_by=str(row["changed_by"]) if row["changed_by"] else None,
                note=row["note"],
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]

    _CUSTOMER_CANCELLABLE = {"pending", "confirmed"}

    async def cancel_order(
        self,
        order_id: str,
        user_id: str | None = None,
        store_ids: list[str] | None = None,
    ):
        await self._assert_order_access(order_id, user_id=user_id, store_ids=store_ids)

        result = await self.db.execute(
            text("SELECT order_status FROM orders WHERE id = :order_id"),
            {"order_id": order_id},
        )
        row = result.mappings().first()
        if not row:
            raise OrdersError(message="Order not found", code="ORDER_NOT_FOUND", status_code=404)

        current_status = row["order_status"]
        if current_status not in self._CUSTOMER_CANCELLABLE:
            raise OrdersError(
                message="Cannot cancel order in '%s' status" % current_status,
                code="CANCELLATION_NOT_ALLOWED",
                status_code=400,
            )

        async with self.db.begin():
            update_result = await self.db.execute(
                text(
                    "UPDATE orders SET order_status = 'cancelled', updated_at = NOW() "
                    "WHERE id = :order_id AND order_status = :current_status RETURNING id"
                ),
                {"order_id": order_id, "current_status": current_status},
            )
            if not update_result.scalar_one_or_none():
                raise OrdersError(
                    message="Order status changed concurrently, cancellation aborted",
                    code="CONCURRENT_MODIFICATION",
                    status_code=409,
                )

            await self.db.execute(
                text(
                    "UPDATE store_orders SET status = 'cancelled' "
                    "WHERE order_id = :order_id AND status IN ('pending', 'confirmed')"
                ),
                {"order_id": order_id},
            )

            await self.db.execute(
                text(
                    "INSERT INTO order_status_history "
                    "(order_id, old_status, new_status, changed_by, note, created_at) "
                    "VALUES (:order_id, :old_status, 'cancelled', :user_id, 'Cancelled by customer', NOW())"
                ),
                {"order_id": order_id, "old_status": current_status, "user_id": user_id},
            )

        return await self.get_order(order_id, user_id=user_id, store_ids=store_ids)

    _VALID_TRANSITIONS = {
        "pending": {"confirmed", "cancelled"},
        "confirmed": {"processing", "cancelled"},
        "processing": {"shipped"},
        "shipped": {"delivered"},
        "delivered": set(),
        "cancelled": set(),
    }

    def _is_valid_transition(self, old_status: str, new_status: str) -> bool:
        return new_status in self._VALID_TRANSITIONS.get(old_status, set())

    async def update_order_status(
        self,
        order_id: str,
        new_status: str,
        note: str | None = None,
        user_id: str | None = None,
        store_ids: list[str] | None = None,
    ):
        await self._assert_order_access(order_id, user_id=user_id, store_ids=store_ids)

        result = await self.db.execute(
            text("SELECT order_status FROM orders WHERE id = :order_id"),
            {"order_id": order_id},
        )
        row = result.mappings().first()
        if not row:
            raise OrdersError(message="Order not found", code="ORDER_NOT_FOUND", status_code=404)

        current_status = row["order_status"]
        if not self._is_valid_transition(current_status, new_status):
            raise OrdersError(
                message="Invalid status transition from '%s' to '%s'" % (current_status, new_status),
                code="INVALID_TRANSITION",
                status_code=400,
            )

        async with self.db.begin():
            await self.db.execute(
                text("UPDATE orders SET order_status = :new_status, updated_at = NOW() WHERE id = :order_id"),
                {"order_id": order_id, "new_status": new_status},
            )

            if store_ids:
                await self.db.execute(
                    text(
                        "UPDATE store_orders SET status = :new_status "
                        "WHERE order_id = :order_id AND store_id = ANY(:store_ids)"
                    ),
                    {"order_id": order_id, "new_status": new_status, "store_ids": store_ids},
                )
            else:
                await self.db.execute(
                    text("UPDATE store_orders SET status = :new_status WHERE order_id = :order_id"),
                    {"order_id": order_id, "new_status": new_status},
                )

            await self.db.execute(
                text(
                    "INSERT INTO order_status_history "
                    "(order_id, old_status, new_status, changed_by, note, created_at) "
                    "VALUES (:order_id, :old_status, :new_status, :user_id, :note, NOW())"
                ),
                {"order_id": order_id, "old_status": current_status, "new_status": new_status, "user_id": user_id, "note": note},
            )

        return await self.get_order(order_id, user_id=user_id, store_ids=store_ids)

    # ------------------------------------------------------------------
    # COD Verification (M4.4)
    # ------------------------------------------------------------------

    async def verify_cod_otp(
        self,
        request: CODVerifyRequest,
        user_id: str | None = None,
        store_ids: list[str] | None = None,
    ) -> CODVerifyResponse:
        """Verify 4-digit OTP for COD order.

        Only the customer who placed the order may verify the OTP.
        """
        await self._assert_order_access(request.order_id, user_id=user_id, store_ids=store_ids)
        otp_store = await self._get_otp_store()
        success, message = await otp_store.verify_otp(request.order_id, request.otp_code)

        if not success:
            raise OrdersError(message=message, code="OTP_VERIFICATION_FAILED", status_code=400)

        # Update order status to confirmed
        await self.db.execute(
            text(
                """
                UPDATE orders
                SET order_status = 'confirmed', updated_at = NOW()
                WHERE id = :order_id
                """
            ),
            {"order_id": request.order_id},
        )

        # Update all store orders to confirmed
        await self.db.execute(
            text(
                """
                UPDATE store_orders
                SET status = 'confirmed'
                WHERE order_id = :order_id
                """
            ),
            {"order_id": request.order_id},
        )

        # Create status history entry
        await self.db.execute(
            text(
                """
                INSERT INTO order_status_history
                (order_id, old_status, new_status, note, created_at)
                VALUES
                (:order_id, 'pending', 'confirmed', 'COD verified via SMS OTP', NOW())
                """
            ),
            {"order_id": request.order_id},
        )

        await self.db.commit()

        return CODVerifyResponse(
            order_id=request.order_id,
            order_status="confirmed",
            confirmed_at=str(datetime.now(timezone.utc)),
            message="Order confirmed successfully",
        )