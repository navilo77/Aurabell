"""Users service - profile and address CRUD operations."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import User
from app.core.exceptions import AuthError
from app.modules.users.schema import (
    AddressCreate,
    AddressRead,
    AddressUpdate,
    ProfileRead,
    ProfileUpdate,
)


class UsersService:
    """User profile and address management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─── Profile ────────────────────────────────────────────────────────────

    async def get_profile(self, user: User) -> ProfileRead:
        """Get current user's profile."""
        result = await self.db.execute(
            select(
                "id",
                "email",
                "full_name",
                "phone",
                "avatar_url",
                "status",
                "created_at",
                "updated_at",
            ).select_from(
                # Using raw SQL since we don't have ORM models yet
                "profiles"
            ).where("id = :user_id"),
            {"user_id": user.id},
        )
        row = result.mappings().first()
        if not row:
            raise AuthError(message="Profile not found", code="PROFILE_NOT_FOUND", status_code=404)

        return ProfileRead(
            id=str(row["id"]),
            email=row["email"],
            full_name=row["full_name"],
            phone=row["phone"],
            avatar_url=row["avatar_url"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def update_profile(self, user: User, data: ProfileUpdate) -> ProfileRead:
        """Update current user's profile."""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_profile(user)

        update_data["updated_at"] = datetime.utcnow()

        await self.db.execute(
            update("profiles")
            .where("id = :user_id")
            .values(**update_data),
            {"user_id": user.id},
        )
        await self.db.commit()

        return await self.get_profile(user)

    # ─── Addresses ──────────────────────────────────────────────────────────

    async def list_addresses(self, user: User) -> Sequence[AddressRead]:
        """List all addresses for current user."""
        result = await self.db.execute(
            select(
                "id",
                "user_id",
                "recipient_name",
                "phone",
                "division",
                "district",
                "upazila",
                "area",
                "address_line",
                "postal_code",
                "is_default",
                "created_at",
            )
            .select_from("addresses")
            .where("user_id = :user_id")
            .order_by("created_at"),
            {"user_id": user.id},
        )
        rows = result.mappings().all()
        return [
            AddressRead(
                id=str(row["id"]),
                user_id=str(row["user_id"]),
                recipient_name=row["recipient_name"],
                phone=row["phone"],
                division=row["division"],
                district=row["district"],
                upazila=row["upazila"],
                area=row["area"],
                address_line=row["address_line"],
                postal_code=row["postal_code"],
                is_default=row["is_default"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def create_address(self, user: User, data: AddressCreate) -> AddressRead:
        """Create a new address for current user."""
        # If this is the first address or is_default=True, unset other defaults
        if data.is_default:
            await self.db.execute(
                update("addresses")
                .where("user_id = :user_id")
                .values(is_default=False),
                {"user_id": user.id},
            )

        result = await self.db.execute(
            insert("addresses")
            .values(
                user_id=user.id,
                recipient_name=data.recipient_name,
                phone=data.phone,
                division=data.division,
                district=data.district,
                upazila=data.upazila,
                area=data.area,
                address_line=data.address_line,
                postal_code=data.postal_code,
                is_default=data.is_default,
            )
            .returning(
                "id",
                "user_id",
                "recipient_name",
                "phone",
                "division",
                "district",
                "upazila",
                "area",
                "address_line",
                "postal_code",
                "is_default",
                "created_at",
            ),
        )
        await self.db.commit()

        row = result.mappings().first()
        return AddressRead(
            id=str(row["id"]),
            user_id=str(row["user_id"]),
            recipient_name=row["recipient_name"],
            phone=row["phone"],
            division=row["division"],
            district=row["district"],
            upazila=row["upazila"],
            area=row["area"],
            address_line=row["address_line"],
            postal_code=row["postal_code"],
            is_default=row["is_default"],
            created_at=row["created_at"],
        )

    async def get_address(self, user: User, address_id: str) -> AddressRead:
        """Get a specific address by ID (must belong to user)."""
        result = await self.db.execute(
            select(
                "id",
                "user_id",
                "recipient_name",
                "phone",
                "division",
                "district",
                "upazila",
                "area",
                "address_line",
                "postal_code",
                "is_default",
                "created_at",
            )
            .select_from("addresses")
            .where("id = :address_id AND user_id = :user_id"),
            {"address_id": address_id, "user_id": user.id},
        )
        row = result.mappings().first()
        if not row:
            raise AuthError(message="Address not found", code="ADDRESS_NOT_FOUND", status_code=404)

        return AddressRead(
            id=str(row["id"]),
            user_id=str(row["user_id"]),
            recipient_name=row["recipient_name"],
            phone=row["phone"],
            division=row["division"],
            district=row["district"],
            upazila=row["upazila"],
            area=row["area"],
            address_line=row["address_line"],
            postal_code=row["postal_code"],
            is_default=row["is_default"],
            created_at=row["created_at"],
        )

    async def update_address(self, user: User, address_id: str, data: AddressUpdate) -> AddressRead:
        """Update an address (must belong to user)."""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_address(user, address_id)

        # If setting as default, unset other defaults
        if update_data.get("is_default"):
            await self.db.execute(
                update("addresses")
                .where("user_id = :user_id")
                .values(is_default=False),
                {"user_id": user.id},
            )

        await self.db.execute(
            update("addresses")
            .where("id = :address_id AND user_id = :user_id")
            .values(**update_data),
            {"address_id": address_id, "user_id": user.id},
        )
        await self.db.commit()

        return await self.get_address(user, address_id)

    async def delete_address(self, user: User, address_id: str) -> None:
        """Delete an address (must belong to user)."""
        result = await self.db.execute(
            delete("addresses")
            .where("id = :address_id AND user_id = :user_id")
            .returning("id"),
            {"address_id": address_id, "user_id": user.id},
        )
        if not result.scalar_one_or_none():
            raise AuthError(message="Address not found", code="ADDRESS_NOT_FOUND", status_code=404)
        await self.db.commit()