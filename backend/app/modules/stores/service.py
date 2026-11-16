"""Stores service - Store CRUD and policy management."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, insert, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import User
from app.core.exceptions import AuthError
from app.modules.stores.schema import (
    PolicyRead,
    ReturnPolicyCreate,
    StoreCreate,
    StoreRead,
    StoreUpdate,
    TermsConditionsCreate,
    WarrantyPolicyCreate,
)


class StoresService:
    """Store management and policy service."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─── Stores ───────────────────────────────────────────────────────────────

    async def create_store(self, data: StoreCreate) -> StoreRead:
        """Create a new store."""
        # Generate slug from name if not provided
        slug = data.slug
        if not slug:
            # Simple slug generation - convert to lowercase, replace spaces with hyphens
            slug = data.name.lower().replace(" ", "-").replace("_", "-")
            # Ensure uniqueness
            slug = await self._generate_unique_slug(slug)

        # Check if slug already exists
        existing = await self.db.execute(
            text("SELECT id FROM stores WHERE slug = :slug"),
            {"slug": slug},
        )
        if existing.scalar_one_or_none():
            raise AuthError(
                message="Store with this slug already exists",
                code="DUPLICATE_SLUG",
                status_code=409,
            )

        result = await self.db.execute(
            text(
                "INSERT INTO stores "
                "(name, slug, description, logo_url, primary_color, status) "
                "VALUES (:name, :slug, :description, :logo_url, :primary_color, :status) "
                "RETURNING id, name, slug, description, logo_url, primary_color, status, created_at, updated_at"
            ),
            {
                "name": data.name,
                "slug": slug,
                "description": data.description,
                "logo_url": data.logo_url,
                "primary_color": data.primary_color,
                "status": data.status,
            },
        )
        await self.db.commit()

        row = result.mappings().first()
        return StoreRead(
            id=str(row["id"]),
            name=row["name"],
            slug=row["slug"],
            description=row["description"],
            logo_url=row["logo_url"],
            primary_color=row["primary_color"],
            status=row["status"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    async def get_store(self, store_id: str) -> StoreRead:
        """Get store by ID."""
        result = await self.db.execute(
            text(
                "SELECT id, name, slug, description, logo_url, primary_color, status, "
                "created_at, updated_at FROM stores WHERE id = :store_id"
            ),
            {"store_id": store_id},
        )
        row = result.mappings().first()
        if not row:
            raise AuthError(message="Store not found", code="STORE_NOT_FOUND", status_code=404)

        return StoreRead(
            id=str(row["id"]),
            name=row["name"],
            slug=row["slug"],
            description=row["description"],
            logo_url=row["logo_url"],
            primary_color=row["primary_color"],
            status=row["status"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    async def list_stores(self) -> list[StoreRead]:
        """List all stores."""
        result = await self.db.execute(
            text(
                "SELECT id, name, slug, description, logo_url, primary_color, status, "
                "created_at, updated_at FROM stores ORDER BY created_at"
            ),
        )
        rows = result.mappings().all()
        return [
            StoreRead(
                id=str(row["id"]),
                name=row["name"],
                slug=row["slug"],
                description=row["description"],
                logo_url=row["logo_url"],
                primary_color=row["primary_color"],
                status=row["status"],
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
            )
            for row in rows
        ]

    async def update_store(self, store_id: str, data: StoreUpdate) -> StoreRead:
        """Update store."""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_store(store_id)

        # If slug is being updated, check uniqueness
        if "slug" in update_data:
            existing = await self.db.execute(
                text("SELECT id FROM stores WHERE slug = :new_slug AND id != :store_id"),
                {"new_slug": update_data["slug"], "store_id": store_id},
            )
            if existing.scalar_one_or_none():
                raise AuthError(
                    message="Store with this slug already exists",
                    code="DUPLICATE_SLUG",
                    status_code=409,
                )

        update_data["updated_at"] = datetime.utcnow()

        set_clause = ", ".join(f"{key} = :{key}" for key in update_data)
        await self.db.execute(
            text(f"UPDATE stores SET {set_clause} WHERE id = :store_id"),
            {"store_id": store_id, **update_data},
        )
        await self.db.commit()

        return await self.get_store(store_id)

    async def delete_store(self, store_id: str) -> None:
        """Delete store (cascade delete related policies)."""
        # Delete store policies first
        await self.db.execute(
            text("DELETE FROM store_policies WHERE store_id = :store_id"),
            {"store_id": store_id},
        )

        result = await self.db.execute(
            text("DELETE FROM stores WHERE id = :store_id RETURNING id"),
            {"store_id": store_id},
        )
        if not result.scalar_one_or_none():
            raise AuthError(message="Store not found", code="STORE_NOT_FOUND", status_code=404)
        await self.db.commit()

    async def get_store_by_slug(self, slug: str) -> StoreRead:
        """Get store by slug."""
        result = await self.db.execute(
            text(
                "SELECT id, name, slug, description, logo_url, primary_color, status, "
                "created_at, updated_at FROM stores WHERE slug = :slug"
            ),
            {"slug": slug},
        )
        row = result.mappings().first()
        if not row:
            raise AuthError(message="Store not found", code="STORE_NOT_FOUND", status_code=404)

        # Fetch active policies for this store (public detail view)
        policy_result = await self.db.execute(
            text(
                "SELECT id, store_id, policy_type, policy_content, is_active, "
                "created_at, updated_at FROM store_policies "
                "WHERE store_id = :store_id AND is_active = true"
            ),
            {"store_id": row["id"]},
        )
        policies = [
            PolicyRead(
                id=str(p["id"]),
                store_id=str(p["store_id"]),
                policy_type=p["policy_type"],
                policy_content=p["policy_content"],
                is_active=p["is_active"],
                created_at=str(p["created_at"]),
                updated_at=str(p["updated_at"]),
            )
            for p in policy_result.mappings().all()
        ]

        return StoreRead(
            id=str(row["id"]),
            name=row["name"],
            slug=row["slug"],
            description=row["description"],
            logo_url=row["logo_url"],
            primary_color=row["primary_color"],
            status=row["status"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            policies=policies,
        )

    async def _generate_unique_slug(self, base_slug: str) -> str:
        """Generate a unique slug by appending numbers if needed."""
        slug = base_slug
        counter = 1
        while True:
            existing = await self.db.execute(
                text("SELECT id FROM stores WHERE slug = :slug"),
                {"slug": slug},
            )
            if not existing.scalar_one_or_none():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    # ─── Store Policies ───────────────────────────────────────────────────────

    async def create_return_policy(self, store_id: str, data: ReturnPolicyCreate) -> PolicyRead:
        """Create return policy for store."""
        # Verify store exists
        store_result = await self.db.execute(
            text("SELECT id FROM stores WHERE id = :store_id"),
            {"store_id": store_id},
        )
        if not store_result.scalar_one_or_none():
            raise AuthError(message="Store not found", code="STORE_NOT_FOUND", status_code=404)

        result = await self.db.execute(
            text(
                "INSERT INTO store_policies "
                "(store_id, policy_type, policy_content, is_active) "
                "VALUES (:store_id, :policy_type, :policy_content, :is_active) "
                "RETURNING id, store_id, policy_type, policy_content, is_active, created_at, updated_at"
            ),
            {
                "store_id": store_id,
                "policy_type": "return",
                "policy_content": data.policy_content,
                "is_active": data.is_active,
            },
        )
        await self.db.commit()

        row = result.mappings().first()
        return PolicyRead(
            id=str(row["id"]),
            store_id=str(row["store_id"]),
            policy_type=row["policy_type"],
            policy_content=row["policy_content"],
            is_active=row["is_active"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    async def create_warranty_policy(self, store_id: str, data: WarrantyPolicyCreate) -> PolicyRead:
        """Create warranty policy for store."""
        # Verify store exists
        store_result = await self.db.execute(
            text("SELECT id FROM stores WHERE id = :store_id"),
            {"store_id": store_id},
        )
        if not store_result.scalar_one_or_none():
            raise AuthError(message="Store not found", code="STORE_NOT_FOUND", status_code=404)

        result = await self.db.execute(
            text(
                "INSERT INTO store_policies "
                "(store_id, policy_type, policy_content, is_active) "
                "VALUES (:store_id, :policy_type, :policy_content, :is_active) "
                "RETURNING id, store_id, policy_type, policy_content, is_active, created_at, updated_at"
            ),
            {
                "store_id": store_id,
                "policy_type": "warranty",
                "policy_content": data.policy_content,
                "is_active": data.is_active,
            },
        )
        await self.db.commit()

        row = result.mappings().first()
        return PolicyRead(
            id=str(row["id"]),
            store_id=str(row["store_id"]),
            policy_type=row["policy_type"],
            policy_content=row["policy_content"],
            is_active=row["is_active"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    async def create_terms_conditions(self, store_id: str, data: TermsConditionsCreate) -> PolicyRead:
        """Create terms and conditions for store."""
        # Verify store exists
        store_result = await self.db.execute(
            text("SELECT id FROM stores WHERE id = :store_id"),
            {"store_id": store_id},
        )
        if not store_result.scalar_one_or_none():
            raise AuthError(message="Store not found", code="STORE_NOT_FOUND", status_code=404)

        result = await self.db.execute(
            text(
                "INSERT INTO store_policies "
                "(store_id, policy_type, policy_content, is_active) "
                "VALUES (:store_id, :policy_type, :policy_content, :is_active) "
                "RETURNING id, store_id, policy_type, policy_content, is_active, created_at, updated_at"
            ),
            {
                "store_id": store_id,
                "policy_type": "terms_conditions",
                "policy_content": data.policy_content,
                "is_active": data.is_active,
            },
        )
        await self.db.commit()

        row = result.mappings().first()
        return PolicyRead(
            id=str(row["id"]),
            store_id=str(row["store_id"]),
            policy_type=row["policy_type"],
            policy_content=row["policy_content"],
            is_active=row["is_active"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    async def get_store_policies(self, store_id: str) -> list[PolicyRead]:
        """Get all policies for a store."""
        result = await self.db.execute(
            text(
                "SELECT id, store_id, policy_type, policy_content, is_active, "
                "created_at, updated_at FROM store_policies "
                "WHERE store_id = :store_id ORDER BY policy_type"
            ),
            {"store_id": store_id},
        )
        rows = result.mappings().all()
        return [
            PolicyRead(
                id=str(row["id"]),
                store_id=str(row["store_id"]),
                policy_type=row["policy_type"],
                policy_content=row["policy_content"],
                is_active=row["is_active"],
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
            )
            for row in rows
        ]

    async def update_store_status(self, store_id: str, status: str) -> StoreRead:
        """Update store status (active/inactive)."""
        if status not in ("active", "inactive"):
            raise AuthError(message="Invalid status", code="INVALID_STATUS", status_code=400)

        result = await self.db.execute(
            text(
                "UPDATE stores SET status = :status, updated_at = :updated_at "
                "WHERE id = :store_id "
                "RETURNING id, name, slug, description, logo_url, primary_color, status, created_at, updated_at"
            ),
            {"store_id": store_id, "status": status, "updated_at": datetime.utcnow()},
        )
        row = result.mappings().first()
        if not row:
            raise AuthError(message="Store not found", code="STORE_NOT_FOUND", status_code=404)

        return StoreRead(
            id=str(row["id"]),
            name=row["name"],
            slug=row["slug"],
            description=row["description"],
            logo_url=row["logo_url"],
            primary_color=row["primary_color"],
            status=row["status"],
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )