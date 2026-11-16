"""Categories router - Admin CRUD and Public tree endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_role
from app.core.database import get_db
from app.core.exceptions import AuthError
from app.modules.categories.schema import (
    CategoryCreate,
    CategoryRead,
    CategoryTree,
    CategoryUpdate,
)
from app.modules.categories.service import CategoriesService

admin_router = APIRouter(prefix="/admin/categories", tags=["Admin - Categories"])
public_router = APIRouter(prefix="/categories", tags=["Public - Categories"])


def get_categories_service(db: AsyncSession = Depends(get_db)):
    return CategoriesService(db)


# ─── Admin CRUD ───────────────────────────────────────────────────────────────

@admin_router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Category slug already exists for this store"},
        404: {"description": "Store or parent category not found"},
    },
    summary="Create a new category",
)
async def create_category(
    data: CategoryCreate,
    service: CategoriesService = Depends(get_categories_service),
    _user=Depends(require_role("store_manager", "super_admin")),
):
    """Create a new category (root or child)."""
    try:
        return await service.create_category(data)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@admin_router.get(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Get category by ID",
)
async def get_category(
    category_id: str = Path(..., description="Category UUID"),
    service: CategoriesService = Depends(get_categories_service),
    _user=Depends(require_role("store_manager", "super_admin")),
):
    """Get a category by ID."""
    try:
        return await service.get_category(category_id)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@admin_router.patch(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Update category",
)
async def update_category(
    data: CategoryUpdate,
    category_id: str = Path(..., description="Category UUID"),
    service: CategoriesService = Depends(get_categories_service),
    _user=Depends(require_role("store_manager", "super_admin")),
):
    """Update a category. All fields optional (partial update)."""
    try:
        return await service.update_category(category_id, data)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@admin_router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete category (soft)",
)
async def delete_category(
    category_id: str = Path(..., description="Category UUID"),
    service: CategoriesService = Depends(get_categories_service),
    _user=Depends(require_role("store_manager", "super_admin")),
):
    """Soft delete a category (sets is_active = false)."""
    try:
        await service.delete_category(category_id)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


# ─── Public Tree ──────────────────────────────────────────────────────────────

@public_router.get(
    "",
    response_model=list[CategoryTree],
    summary="Get public category tree",
)
async def get_public_category_tree(
    service: CategoriesService = Depends(get_categories_service),
):
    """Get the nested category tree across all stores (active only)."""
    return await service.get_public_category_tree()


@public_router.get(
    "/store/{slug}",
    response_model=list[CategoryTree],
    summary="Get store category tree",
)
async def get_store_category_tree(
    slug: str,
    service: CategoriesService = Depends(get_categories_service),
):
    """Get the nested category tree for a specific store."""
    try:
        return await service.get_store_categories_tree(slug)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e