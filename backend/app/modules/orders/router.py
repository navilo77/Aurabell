"""Orders router (M4.2-M4.4).

Order placement, checkout preview, and COD verification endpoints.
Registered under /api/v1/orders in main.py.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.exceptions import AuthError
from app.modules.orders.schema import (
    CODVerifyRequest,
    CODVerifyResponse,
    OrderCreate,
    OrderRead,
)
from app.modules.orders.service import OrdersService

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_orders_service(db: AsyncSession = Depends(get_db)) -> OrdersService:
    return OrdersService(db)


# ─── Order Placement ────────────────────────────────────────────────────────────


@router.post(
    "/checkout",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Place order via atomic checkout",
)
async def place_order(
    data: OrderCreate,
    service: OrdersService = Depends(get_orders_service),
    user: dict = Depends(get_current_user),
):
    """Place an order atomically.

    Creates:
    - Parent order
    - Store orders per store
    - Order items with snapshots
    - Stock reservations (15 min TTL)
    - Promotion redemption record
    - Status history
    - Marks cart as converted

    If payment_method is 'cod', sends 4-digit SMS OTP for verification.
    """
    user_id = str(user["id"])
    try:
        return await service.place_order(data, user_id)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


# ─── COD Verification ──────────────────────────────────────────────────────────


@router.post(
    "/{order_id}/verify-cod",
    response_model=CODVerifyResponse,
    summary="Verify COD order with SMS OTP",
)
async def verify_cod_otp(
    request: CODVerifyRequest,
    order_id: str = Path(..., description="Order UUID"),
    service: OrdersService = Depends(get_orders_service),
    user: dict = Depends(get_current_user),
):
    """Verify 4-digit OTP for COD order.

    On success:
    - Order status changes to 'confirmed'
    - All store orders confirmed
    - Status history recorded

    Maximum 3 attempts, 5-minute expiry.
    """
    user_id = str(user["id"])
    try:
        return await service.verify_cod_otp(request)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


# ─── Order Details ───────────────────────────────────────────────────────────────


@router.get(
    "/{order_id}",
    response_model=OrderRead,
    summary="Get order details",
)
async def get_order(
    order_id: str = Path(..., description="Order UUID"),
    service: OrdersService = Depends(get_orders_service),
    user: dict = Depends(get_current_user),
):
    """Get order details with store orders and items."""
    try:
        return await service.get_order(order_id)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@router.get(
    "",
    response_model=list[OrderRead],
    summary="List user's orders",
)
async def list_orders(
    service: OrdersService = Depends(get_orders_service),
    user: dict = Depends(get_current_user),
):
    """List all orders for the current user."""
    user_id = str(user["id"])
    # TODO: Implement pagination and status filtering
    result = await service.db.execute(
        text(
            """
            SELECT id, order_number, user_id, subtotal, discount_total, delivery_total,
                   grand_total, currency_code, order_status, created_at
            FROM orders
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT 50
            """
        ),
        {"user_id": user_id},
    )
    orders = result.mappings().all()
    return [
        OrderRead(
            id=str(order["id"]),
            order_number=order["order_number"],
            user_id=str(order["user_id"]),
            subtotal=order["subtotal"],
            discount_total=order["discount_total"],
            delivery_total=order["delivery_total"],
            grand_total=order["grand_total"],
            currency_code=order["currency_code"],
            order_status=order["order_status"],
            created_at=str(order["created_at"]),
        )
        for order in orders
    ]