"""Products router — Admin CRUD and Public listing."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import User, get_current_user, require_role
from app.core.database import get_db
from app.core.exceptions import PermissionDenied
from app.core.pagination import paginate
from app.modules.products.schema import (
    ImageCreate,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    VariantCreate,
)
from app.modules.products.service import ProductsService


def get_products_service(db: AsyncSession = Depends(get_db)):
    return ProductsService(db)


# ─── Admin CRUD ───────────────────────────────────────────────────────────────


admin_router = APIRouter(prefix="/admin/products", tags=["Admin - Products"])


@admin_router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Product slug already exists for this store"},
        404: {"description": "Store or category not found"},
    },
    summary="Create a new product",
)
async def create_product(
    data: ProductCreate,
    service: ProductsService = Depends(get_products_service),
    user: User = Depends(require_role("store_manager", "super_admin")),
):
    """Create a new product with variants and images."""
    # Check store access for store_manager
    if "super_admin" not in user.roles and "store_manager" in user.roles:
        if data.store_id not in (user.store_ids or []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=PermissionDenied(
                    required_roles=["store_manager", "super_admin"],
                    user_roles=user.roles,
                ).message,
            )
    try:
        return await service.create_product(data)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@admin_router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Get product by ID",
)
async def get_product(
    product_id: UUID = Path(..., description="Product UUID"),
    service: ProductsService = Depends(get_products_service),
    user: User = Depends(require_role("store_manager", "super_admin")),
):
    """Get a product by ID (admin view)."""
    try:
        return await service.get_product(product_id, user)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@admin_router.patch(
    "/{product_id}",
    response_model=ProductRead,
    summary="Update product",
)
async def update_product(
    data: ProductUpdate,
    product_id: UUID = Path(..., description="Product UUID"),
    service: ProductsService = Depends(get_products_service),
    user: User = Depends(require_role("store_manager", "super_admin")),
):
    """Update a product. All fields optional (partial update)."""
    try:
        return await service.update_product(product_id, data, user)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@admin_router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product (soft)",
)
async def delete_product(
    product_id: UUID = Path(..., description="Product UUID"),
    service: ProductsService = Depends(get_products_service),
    user: User = Depends(require_role("store_manager", "super_admin")),
):
    """Soft delete a product (sets status='archived')."""
    try:
        await service.delete_product(product_id, user)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


# ─── Public ────────────────────────────────────────────────────────────────────────


public_router = APIRouter(prefix="/products", tags=["Public - Products"])


@public_router.get(
    "",
    summary="List products (public)",
)
async def list_public_products(
    store_id: str | None = Query(None),
    category_id: str | None = Query(None),
    search: str | None = Query(None, description="Search in name, description, brand"),
    brand: str | None = Query(None, description="Filter by brand"),
    min_price: float | None = Query(None, ge=0, description="Minimum price filter"),
    max_price: float | None = Query(None, ge=0, description="Maximum price filter"),
    sort: str | None = Query(None, description="Sort: price:asc, price:desc, created_at:desc, name:asc"),
    format: str | None = Query(None, description="Response format: 'v2' for paginated {data, meta}"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ProductsService = Depends(get_products_service),
):
    """Public product listing with filtering, sorting, and pagination."""
    page = (offset // limit) + 1 if limit > 0 else 1
    return await service.list_public_products(
        store_id=store_id,
        category_id=category_id,
        search=search,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        limit=limit,
        offset=offset,
        page=page,
        format_param=format,
    )


@public_router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Get product by ID (public)",
)
async def get_public_product(
    product_id: UUID = Path(..., description="Product UUID"),
    service: ProductsService = Depends(get_products_service),
):
    """Get product detail (only active products)."""
    try:
        product = await service.get_product(product_id)
        if product.status != "active":
            raise AuthError(message="Product not found", code="NOT_FOUND", status_code=404)
        return product
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e