"""Cart router (M4.1 Shared Cart).

Supports both authenticated and guest (session-based) carts.
Registered under /api/v1/cart in main.py.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, get_optional_user
from app.core.database import get_db
from app.core.exceptions import AuthError
from app.modules.cart.schema import (
    CartItemCreate,
    CartItemRead,
    CartRead,
    CheckoutPreview,
)
from app.modules.cart.service import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])


def get_cart_service(db: AsyncSession = Depends(get_db)) -> CartService:
    return CartService(db)


# ─── Cart Management ───────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=CartRead,
    summary="Get or create a cart",
)
async def get_or_create_cart(
    session_id: str | None = Query(None, description="Guest session ID"),
    service: CartService = Depends(get_cart_service),
    user: dict | None = Depends(get_optional_user),
):
    """Return an existing active cart, or create a new one.

    - Authenticated user: cart identified by user_id
    - Guest: cart identified by session_id (UUID from client)
    """
    user_id = str(user["id"]) if user else None
    try:
        return await service.get_or_create_cart(
            user_id=user_id,
            session_id=session_id,
        )
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@router.post(
    "/merge-guest",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Merge guest cart into user cart on login",
)
async def merge_guest_cart(
    guest_session_id: str = Query(..., description="Guest session UUID"),
    service: CartService = Depends(get_cart_service),
    user: dict = Depends(get_current_user),
):
    """Merge guest cart items into user's cart and mark guest cart abandoned."""
    user_id = str(user["id"])
    await service.merge_guest_cart_to_user(guest_session_id, user_id)
    return None


# ─── Cart Item Operations ──────────────────────────────────────────────────────


@router.get(
    "/{cart_id}/items",
    response_model=list[CartItemRead],
    summary="List cart items with stock validation",
)
async def list_cart_items(
    cart_id: str = Path(..., description="Cart UUID"),
    service: CartService = Depends(get_cart_service),
):
    """Return all items in a cart with stock status."""
    return await service.list_cart_items(cart_id)


@router.post(
    "/{cart_id}/items",
    response_model=CartItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to cart",
)
async def add_item(
    cart_id: str = Path(..., description="Cart UUID"),
    data: CartItemCreate = ...,
    service: CartService = Depends(get_cart_service),
):
    """Add a product variant to the cart.

    Validates variant exists, is active, and product is active.
    If item already in cart, quantity is increased.
    """
    try:
        return await service.add_item(cart_id, data.variant_id, data.quantity)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@router.patch(
    "/{cart_id}/items/{variant_id}",
    response_model=CartItemRead,
    summary="Update cart item quantity",
)
async def update_item_quantity(
    cart_id: str = Path(..., description="Cart UUID"),
    variant_id: str = Path(..., description="Product variant UUID"),
    data: CartItemCreate = ...,
    service: CartService = Depends(get_cart_service),
):
    """Update a cart item's quantity.

    If quantity is 0 or less, the item is removed.
    """
    try:
        return await service.update_item_quantity(cart_id, variant_id, data.quantity)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@router.delete(
    "/{cart_id}/items/{variant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove item from cart",
)
async def remove_item(
    cart_id: str = Path(..., description="Cart UUID"),
    variant_id: str = Path(..., description="Product variant UUID"),
    service: CartService = Depends(get_cart_service),
):
    """Remove a cart item entirely."""
    deleted = await service.remove_item(cart_id, variant_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Cart item not found", "code": "ITEM_NOT_FOUND"},
        )
    return None


# ─── Checkout Preview ──────────────────────────────────────────────────────────


@router.get(
    "/{cart_id}/checkout-preview",
    response_model=CheckoutPreview,
    summary="Checkout preview with server-side pricing",
)
async def checkout_preview(
    cart_id: str = Path(..., description="Cart UUID"),
    coupon_code: str | None = Query(None, description="Optional coupon code"),
    district: str | None = Query(None, description="District for delivery fee calc"),
    service: CartService = Depends(get_cart_service),
):
    """Calculate a checkout preview using server-side PricingService.

    Returns per-store breakdown and grand totals with flat delivery fee.
    Delivery fee: Dhaka Metro ৳70, outside Dhaka ৳120 (DEC-OWN-003).
    """
    try:
        return await service.checkout_preview(
            cart_id,
            coupon_code=coupon_code,
            district=district,
        )
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e