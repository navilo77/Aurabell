"""Stores router - store management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user, require_role
from app.core.exceptions import AuthError
from app.modules.stores.schema import (
    PolicyRead,
    ReturnPolicyCreate,
    StoreBannerUpdate,
    StoreCreate,
    StoreRead,
    StoreUpdate,
    TermsConditionsCreate,
    WarrantyPolicyCreate,
)
from app.modules.stores.service import StoresService
from app.core.database import get_db

router = APIRouter(prefix="/stores", tags=["Stores"])


def get_stores_service(db = Depends(get_db)):
    return StoresService(db)


# ─── Store CRUD ───────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=StoreRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Store with this slug already exists"},
        400: {"description": "Invalid store data"},
    },
    summary="Create a new store",
)
async def create_store(
    data: StoreCreate,
    service: StoresService = Depends(get_stores_service),
    user = Depends(require_role("store_manager", "super_admin")),
):
    """Create a new store."""
    try:
        return await service.create_store(data)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@router.get(
    "",
    response_model=list[StoreRead],
    summary="List all stores",
)
async def list_stores(
    service: StoresService = Depends(get_stores_service),
):
    """List all stores."""
    return await service.list_stores()


@router.get(
    "/id/{store_id}",
    response_model=StoreRead,
    summary="Get store by ID",
)
async def get_store(
    store_id: str,
    service: StoresService = Depends(get_stores_service),
    user = Depends(get_current_user),
):
    """Get store by ID."""
    try:
        return await service.get_store(store_id)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@router.get(
    "/{slug}",
    response_model=StoreRead,
    summary="Get store by slug",
)
async def get_store_by_slug(
    slug: str,
    service: StoresService = Depends(get_stores_service),
):
    """Get store by slug."""
    try:
        return await service.get_store_by_slug(slug)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@router.put(
    "/{store_id}",
    response_model=StoreRead,
    summary="Update store",
)
async def update_store(
    store_id: str,
    data: StoreUpdate,
    service: StoresService = Depends(get_stores_service),
    user = Depends(get_current_user),
):
    """Update store."""
    try:
        return await service.update_store(store_id, data)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@router.delete(
    "/{store_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete store",
)
async def delete_store(
    store_id: str,
    service: StoresService = Depends(get_stores_service),
    user = Depends(require_role("store_manager", "super_admin")),
):
    """Delete store."""
    try:
        await service.delete_store(store_id)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@router.patch(
    "/{store_id}/status",
    response_model=StoreRead,
    summary="Update store status",
)
async def update_store_status(
    store_id: str,
    status: str,
    service: StoresService = Depends(get_stores_service),
    user = Depends(require_role("store_manager", "super_admin")),
):
    """Update store status (active/inactive)."""
    try:
        return await service.update_store_status(store_id, status)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


# ─── Store Banner Management ───────────────────────────────────────────────────

@router.put(
    "/{store_id}/banner",
    response_model=StoreRead,
    summary="Update store banner",
)
async def update_store_banner(
    store_id: str,
    data: StoreBannerUpdate,
    service: StoresService = Depends(get_stores_service),
    user = Depends(require_role("store_manager", "super_admin")),
):
    """Update store banner."""
    # Note: StoreBannerUpdate is a separate schema for banner URL validation
    # The actual implementation would handle banner upload/update logic
    # For now, we'll delegate to update_store with banner_url
    from pydantic import ValidationError
    from sqlalchemy import text
    from app.core.database import get_db

    db = get_db

    # Validate banner URL format
    if not data.banner_url.startswith("http://") and not data.banner_url.startswith("https://"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Invalid banner URL format", "code": "INVALID_BANNER_URL"},
        )

    try:
        # Update banner_url directly via SQL since schema doesn't have banner_url field
        await db.execute(
            text("UPDATE stores SET banner_url = :banner_url, updated_at = NOW() WHERE id = :store_id"),
            {"banner_url": data.banner_url, "store_id": store_id},
        )
        await db.commit()
        return await service.get_store(store_id)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": str(e), "code": "BANNER_UPDATE_ERROR"},
        ) from e


# ─── Store Policies ───────────────────────────────────────────────────────────────

@router.post(
    "/{store_id}/policies/return",
    response_model=PolicyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create return policy for store",
)
async def create_return_policy(
    store_id: str,
    data: ReturnPolicyCreate,
    service: StoresService = Depends(get_stores_service),
    user = Depends(get_current_user),
):
    """Create return policy for store."""
    try:
        return await service.create_return_policy(store_id, data)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@router.post(
    "/{store_id}/policies/warranty",
    response_model=PolicyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create warranty policy for store",
)
async def create_warranty_policy(
    store_id: str,
    data: WarrantyPolicyCreate,
    service: StoresService = Depends(get_stores_service),
    user = Depends(get_current_user),
):
    """Create warranty policy for store."""
    try:
        return await service.create_warranty_policy(store_id, data)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@router.post(
    "/{store_id}/policies/terms",
    response_model=PolicyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create terms and conditions for store",
)
async def create_terms_conditions(
    store_id: str,
    data: TermsConditionsCreate,
    service: StoresService = Depends(get_stores_service),
    user = Depends(get_current_user),
):
    """Create terms and conditions for store."""
    try:
        return await service.create_terms_conditions(store_id, data)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e


@router.get(
    "/{store_id}/policies",
    response_model=list[PolicyRead],
    summary="Get all policies for a store",
)
async def get_store_policies(
    store_id: str,
    service: StoresService = Depends(get_stores_service),
    user = Depends(get_current_user),
):
    """Get all policies for a store."""
    try:
        return await service.get_store_policies(store_id)
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"detail": e.message, "code": e.code},
        ) from e
