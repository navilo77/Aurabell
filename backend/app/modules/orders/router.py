"""Orders router (M4.2-M4.4).

Order placement, checkout preview, and COD verification endpoints.
Registered under /api/v1/orders in main.py.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, User
from app.core.database import get_db
from app.core.exceptions import AuthError
from app.modules.orders.schema import (
    CODVerifyRequest,
    CODVerifyResponse,
    OrderCreate,
    OrderRead,
    OrderStatusUpdateRequest,
    OrderTimelineEntry,
)
from app.modules.orders.service import OrdersService

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_orders_service(db: AsyncSession = Depends(get_db)) -> OrdersService:
    return OrdersService(db)


def _user_context(user: User) -> tuple[str | None, list[str] | None]:
    """Derive (user_id, store_ids) for ownership enforcement.

    - Customer: (user_id, None)
    - Store manager / super_admin: (user_id, store_ids)
    """
    if "customer" in user.roles:
        return user.id, None
    return user.id, user.store_ids or None


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
    user: User = Depends(get_current_user),
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
    user_id = str(user.id)
    user_id_ctx, _store_ids = _user_context(user)
    try:
        return await service.place_order(data, user_id_ctx)
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
    user: User = Depends(get_current_user),
):
    """Verify 4-digit OTP for COD order.

    On success:
    - Order status changes to 'confirmed'
    - All store orders confirmed
    - Status history recorded

    Maximum 3 attempts, 5-minute expiry.
    """
    user_id, store_ids = _user_context(user)
    try:
        return await service.verify_cod_otp(
            request, user_id=user_id, store_ids=store_ids
        )
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


# ─── Order List ─────────────────────────────────────────────────────────────────


@router.get(
    "",
    summary="List user's orders",
)
async def list_orders(
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: str | None = Query(default=None, description="Filter by order status"),
    format: str | None = Query(None, description="Response format: 'v2' for paginated {data, meta}"),
    service: OrdersService = Depends(get_orders_service),
    user: User = Depends(get_current_user),
):
    """List all orders for the current user with pagination and optional filtering."""
    user_id = str(user.id)

    # Build WHERE clause
    where_clauses = ["user_id = :user_id"]
    params: dict = {"user_id": user_id}

    if status:
        where_clauses.append("order_status = :status")
        params["status"] = status

    where_sql = " AND ".join(where_clauses)

    # Count total
    count_query = f"SELECT COUNT(*) FROM orders WHERE {where_sql}"
    count_result = await service.db.execute(text(count_query), params)
    total = count_result.scalar() or 0

    # Fetch orders with pagination
    offset = (page - 1) * per_page
    result = await service.db.execute(
        text(
            f"""
            SELECT id, order_number, user_id, subtotal, discount_total, delivery_total,
                   grand_total, currency_code, order_status, created_at
            FROM orders
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {**params, "limit": per_page, "offset": offset},
    )
    orders = result.mappings().all()
    order_list = [
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

# ─── Order Timeline ─────────────────────────────────────────────────────────────


@router.get(
    "/{order_id}/timeline",
    response_model=list[OrderTimelineEntry],
    summary="Get order status timeline",
)
async def get_order_timeline(
    order_id: str = Path(..., description="Order UUID"),
    service: OrdersService = Depends(get_orders_service),
    user: User = Depends(get_current_user),
):
    """Get chronological status history for an order."""
    user_id, store_ids = _user_context(user)
    try:
        return await service.get_order_timeline(order_id, user_id=user_id, store_ids=store_ids)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


# ─── Admin Order Status Update (BE-04) ──────────────────────────────────────────


admin_router = APIRouter(prefix="/admin/orders", tags=["Admin - Orders"])


@admin_router.patch(
    "/{order_id}/status",
    response_model=OrderRead,
    summary="Update order status (store admin)",
)
async def update_order_status(
    order_id: str = Path(..., description="Order UUID"),
    data: OrderStatusUpdateRequest = ...,
    service: OrdersService = Depends(get_orders_service),
    user: User = Depends(get_current_user),
):
    """Update order status (store manager / super admin)."""
    user_id, store_ids = _user_context(user)
    try:
        return await service.update_order_status(
            order_id, data.status, note=data.note, user_id=user_id, store_ids=store_ids
        )
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@router.post(
    "/{order_id}/cancel",
    response_model=OrderRead,
    summary="Cancel an order",
)
async def cancel_order(
    order_id: str = Path(..., description="Order UUID"),
    service: OrdersService = Depends(get_orders_service),
    user: User = Depends(get_current_user),
):
    """Cancel an order (only PENDING or CONFIRMED orders can be cancelled by customer)."""
    user_id, store_ids = _user_context(user)
    try:
        return await service.cancel_order(order_id, user_id=user_id, store_ids=store_ids)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@router.get(
    "/{order_id}",
    response_model=OrderRead,
    summary="Get order details",
)
async def get_order(
    order_id: str = Path(..., description="Order UUID"),
    service: OrdersService = Depends(get_orders_service),
    user: User = Depends(get_current_user),
):
    """Get order details with store orders and items."""
    user_id, store_ids = _user_context(user)
    try:
        return await service.get_order(
            order_id, user_id=user_id, store_ids=store_ids
        )
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e