"""Payment service (BE-07)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import User
from app.core.exceptions import AuthError
from app.modules.payments.adapter import AmarPayGateway, PaymentVerifyResult


class PaymentError(AuthError):
    pass


INTERNAL_STATUS_MAP = {
    "2": "paid",
    "Successful": "paid",
}


class PaymentService:
    def __init__(self, db: AsyncSession, gateway: AmarPayGateway | None = None) -> None:
        self.db = db
        self.gateway = gateway

    def _check_store_access(self, store_id: str, user: User) -> None:
        """Verify user has access to the store (store_manager must own store; super_admin bypasses)."""
        if "super_admin" not in user.roles:
            if "store_manager" in user.roles:
                if store_id not in (user.store_ids or []):
                    raise AuthError(
                        message="Access denied to store",
                        code="PERMISSION_DENIED",
                        status_code=403,
                    )
            else:
                raise AuthError(
                    message="Insufficient permissions for store operation",
                    code="PERMISSION_DENIED",
                    status_code=403,
                )

    async def _get_order_store_ids(self, order_id: str) -> list[str]:
        """Get store IDs associated with an order via store_orders."""
        result = await self.db.execute(
            text("SELECT store_id FROM store_orders WHERE order_id = :oid"),
            {"oid": order_id},
        )
        return [str(row[0]) for row in result.fetchall()]

    async def _check_store_access_for_order(self, order_id: str, user: User) -> None:
        """Check if user has access to at least one store in the order."""
        store_ids = await self._get_order_store_ids(order_id)
        if not store_ids:
            return
        if "super_admin" not in user.roles:
            if "store_manager" in user.roles:
                user_store_ids = set(user.store_ids or [])
                if not user_store_ids.intersection(store_ids):
                    raise AuthError(
                        message="Access denied to order's stores",
                        code="PERMISSION_DENIED",
                        status_code=403,
                    )
            else:
                raise AuthError(
                    message="Insufficient permissions for order operation",
                    code="PERMISSION_DENIED",
                    status_code=403,
                )

    async def _check_payment_store_access(self, payment: dict, user: User) -> None:
        """Check if user has access to the payment via its order's stores."""
        order_id = str(payment["order_id"])
        await self._check_store_access_for_order(order_id, user)

    def _get_gateway(self) -> AmarPayGateway:
        if self.gateway is not None:
            return self.gateway
        from app.core.config import settings

        store_id = getattr(settings, "AMARPAY_STORE_ID", None)
        signature_key = getattr(settings, "AMARPAY_SIGNATURE_KEY", None)
        base_url = getattr(settings, "AMARPAY_BASE_URL", "https://sandbox.aamarpay.com")
        environment = getattr(settings, "AMARPAY_ENVIRONMENT", "sandbox")
        if not store_id or not signature_key:
            raise PaymentError(message="AmarPay not configured", code="GATEWAY_NOT_CONFIGURED", status_code=503)
        return AmarPayGateway(store_id=store_id, signature_key=signature_key, base_url=base_url, environment=environment)

    async def _get_order(self, order_id: str, user_id: str) -> dict:
        result = await self.db.execute(
            text("SELECT id, user_id, total_amount, currency_code, status FROM orders WHERE id = :oid"),
            {"oid": order_id},
        )
        row = result.mappings().first()
        if not row:
            raise PaymentError(message="Order not found", code="ORDER_NOT_FOUND", status_code=404)
        if str(row["user_id"]) != str(user_id):
            raise PaymentError(message="Order not found", code="ORDER_NOT_FOUND", status_code=404)
        return dict(row)

    async def initiate_payment(self, order_id: str, user_id: str, user_email: str, user_name: str, user_phone: str = "01700000000", address: str = "Dhaka") -> dict:
        order = await self._get_order(order_id, user_id)

        # Verify order is payable
        if order["status"] not in ("pending", "confirmed"):
            raise PaymentError(message="Order is not payable", code="ORDER_NOT_PAYABLE", status_code=400)

        amount = Decimal(str(order["total_amount"]))
        currency = order["currency_code"] or "BDT"

        # Check for existing pending payment
        existing = await self.db.execute(
            text("SELECT id, status, provider_reference FROM payments WHERE order_id = :oid AND status = 'pending'"),
            {"oid": order_id},
        )
        existing_row = existing.mappings().first()
        if existing_row:
            # Reuse existing pending payment
            payment_id = str(existing_row["id"])
            tran_id = str(existing_row["provider_reference"]) if existing_row["provider_reference"] else payment_id
        else:
            # Create new payment record
            tran_id = f"AB-{order_id[:8]}-{int(datetime.now(timezone.utc).timestamp())}"
            async with self.db.begin():
                result = await self.db.execute(
                    text(
                        "INSERT INTO payments (order_id, provider, provider_reference, payment_method, amount, currency_code, status) "
                        "VALUES (:oid, 'amarpay', :ref, 'amarpay', :amount, :currency, 'pending') RETURNING id"
                    ),
                    {"oid": order_id, "ref": tran_id, "amount": float(amount), "currency": currency},
                )
                payment_id = str(result.scalar_one())

        gateway = self._get_gateway()
        init_result = await gateway.initiate_payment(
            tran_id=tran_id,
            amount=str(amount),
            currency=currency,
            cus_name=user_name,
            cus_email=user_email,
            cus_phone=user_phone,
            cus_add1=address,
            cus_add2=address,
            cus_city="Dhaka",
            cus_country="Bangladesh",
            success_url=f"{_base_url()}/api/v1/payments/callback/success",
            fail_url=f"{_base_url()}/api/v1/payments/callback/fail",
            cancel_url=f"{_base_url()}/api/v1/payments/callback/cancel",
            desc=f"Order {order_id}",
            opt_a=order_id,
            opt_b=payment_id,
        )

        if not init_result.success:
            raise PaymentError(message=init_result.error or "Payment initiation failed", code="GATEWAY_ERROR", status_code=502)

        # Update payment record with gateway transaction id
        if init_result.transaction_id:
            await self.db.execute(
                text("UPDATE payments SET provider_reference = :ref WHERE id = :pid"),
                {"ref": init_result.transaction_id, "pid": payment_id},
            )
            await self.db.commit()

        return {
            "payment_id": payment_id,
            "payment_url": init_result.payment_url,
            "transaction_id": init_result.transaction_id or tran_id,
        }

    async def verify_payment(self, tran_id: str) -> dict:
        gateway = self._get_gateway()
        verify_result = await gateway.verify_transaction(tran_id)

        if not verify_result.success:
            raise PaymentError(message=verify_result.error or "Verification failed", code="GATEWAY_ERROR", status_code=502)

        # Map gateway status to internal
        internal_status = None
        if verify_result.status_code == "2" or verify_result.pay_status == "Successful":
            internal_status = "paid"
        elif verify_result.pay_status in ("Failed", "Cancelled"):
            internal_status = "failed"
        else:
            internal_status = "pending"

        # Find payment by tran_id
        result = await self.db.execute(
            text("SELECT id, order_id, amount, status FROM payments WHERE provider_reference = :ref OR provider_reference = :tran"),
            {"ref": tran_id, "tran": tran_id},
        )
        payment = result.mappings().first()
        if not payment:
            raise PaymentError(message="Payment not found", code="PAYMENT_NOT_FOUND", status_code=404)

        payment_id = str(payment["id"])
        order_id = str(payment["order_id"])

        # Amount check
        if verify_result.amount and Decimal(verify_result.amount) != Decimal(str(payment["amount"])):
            raise PaymentError(message="Amount mismatch", code="AMOUNT_MISMATCH", status_code=400)

        # Update payment status (idempotent: don't revert paid)
        if payment["status"] == "paid":
            # Already paid, don't change
            pass
        else:
            async with self.db.begin():
                await self.db.execute(
                    text("UPDATE payments SET status = :status, paid_at = :paid_at WHERE id = :pid"),
                    {"status": internal_status, "paid_at": datetime.now(timezone.utc) if internal_status == "paid" else None, "pid": payment_id},
                )
                if internal_status == "paid":
                    # Update order status via existing state machine (pending -> confirmed)
                    await self.db.execute(
                        text("UPDATE orders SET status = 'confirmed' WHERE id = :oid AND status = 'pending'"),
                        {"oid": order_id},
                    )

        return {
            "payment_id": payment_id,
            "order_id": order_id,
            "status": internal_status,
            "gateway_status": verify_result.pay_status,
            "amount": verify_result.amount,
        }

    async def handle_callback(self, payload: dict) -> dict:
        """Handle AmarPay success/fail/cancel callback or IPN."""
        tran_id = payload.get("mer_txnid") or payload.get("tran_id")
        if not tran_id:
            raise PaymentError(message="Missing transaction ID", code="INVALID_CALLBACK", status_code=400)

        # Verify server-side
        return await self.verify_payment(tran_id)

    async def get_payment(self, payment_id: str, user: User) -> dict:
        result = await self.db.execute(
            text("SELECT * FROM payments WHERE id = :pid"),
            {"pid": payment_id},
        )
        row = result.mappings().first()
        if not row:
            raise PaymentError(message="Payment not found", code="PAYMENT_NOT_FOUND", status_code=404)
        # Customer access: verify ownership via order
        if "customer" in user.roles or "store_manager" not in user.roles:
            order_result = await self.db.execute(
                text("SELECT user_id FROM orders WHERE id = :oid"),
                {"oid": str(row["order_id"])},
            )
            order_row = order_result.mappings().first()
            if not order_row or str(order_row["user_id"]) != str(user.id):
                raise PaymentError(message="Payment not found", code="PAYMENT_NOT_FOUND", status_code=404)
        else:
            # Store manager / super_admin: check store access via order's store_orders
            await self._check_store_access_for_order(str(row["order_id"]), user)
        return dict(row)
