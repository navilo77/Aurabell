"""Products router — Admin CRUD and Public listing."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_role
from app.core.database import get_db
from app.core.exceptions import AuthError
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
    _user = Depends(require_role("store_manager", "super_admin")),
):
    """Create a new product with variants and images."""
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
    _user = Depends(require_role("store_manager", "super_admin")),
):
    """Get a product by ID (admin view)."""
    try:
        return await service.get_product(product_id)
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
    _user = Depends(require_role("store_manager", "super_admin")),
):
    """Update a product. All fields optional (partial update)."""
    try:
        return await service.update_product(product_id, data)
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
    _user = Depends(require_role("store_manager", "super_admin")),
):
    """Soft delete a product (sets status='archived')."""
    try:
        await service.delete_product(product_id)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


# ─── Public ────────────────────────────────────────────────────────────────────────


public_router = APIRouter(prefix="/products", tags=["Public - Products"])


@public_router.get(
    "",
    response_model=list[ProductRead],
    summary="List products (public)",
)
async def list_public_products(
    store_id: str | None = Query(None),
    category_id: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ProductsService = Depends(get_products_service),
):
    """Public product listing with optional filtering."""
    return await service.list_public_products(
        store_id=store_id,
        category_id=category_id,
        search=search,
        limit=limit,
        offset=offset,
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