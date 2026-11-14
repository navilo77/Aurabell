"""Users router - profile and address endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import User, get_current_user
from app.core.database import get_db
from app.core.exceptions import AuthError
from app.modules.users.schema import (
    AddressCreate,
    AddressRead,
    AddressUpdate,
    ProfileRead,
    ProfileUpdate,
)
from app.modules.users.service import UsersService

router = APIRouter(prefix="/users", tags=["Users"])


# ─── Profile ────────────────────────────────────────────────────────────────


@router.get(
    "/me",
    response_model=ProfileRead,
    summary="Get current user profile",
)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileRead:
    """Return the authenticated user's profile."""
    service = UsersService(db)
    return await service.get_profile(user)


@router.patch(
    "/me",
    response_model=ProfileRead,
    summary="Update current user profile",
)
async def update_profile(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileRead:
    """Update the authenticated user's profile."""
    service = UsersService(db)
    return await service.update_profile(user, data)


# ─── Addresses ──────────────────────────────────────────────────────────────


@router.get(
    "/me/addresses",
    response_model=list[AddressRead],
    summary="List current user's addresses",
)
async def list_addresses(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AddressRead]:
    """Return all addresses for the authenticated user."""
    service = UsersService(db)
    return await service.list_addresses(user)


@router.post(
    "/me/addresses",
    response_model=AddressRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create new address for current user",
)
async def create_address(
    data: AddressCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AddressRead:
    """Create a new address for the authenticated user."""
    service = UsersService(db)
    return await service.create_address(user, data)


@router.get(
    "/me/addresses/{address_id}",
    response_model=AddressRead,
    summary="Get specific address",
)
async def get_address(
    address_id: str = Path(..., description="Address UUID"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AddressRead:
    """Get a specific address by ID (must belong to user)."""
    service = UsersService(db)
    return await service.get_address(user, address_id)


@router.patch(
    "/me/addresses/{address_id}",
    response_model=AddressRead,
    summary="Update address",
)
async def update_address(
    data: AddressUpdate,
    address_id: str = Path(..., description="Address UUID"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AddressRead:
    """Update an address (must belong to user)."""
    service = UsersService(db)
    return await service.update_address(user, address_id, data)


@router.delete(
    "/me/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete address",
)
async def delete_address(
    address_id: str = Path(..., description="Address UUID"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an address (must belong to user)."""
    service = UsersService(db)
    await service.delete_address(user, address_id)