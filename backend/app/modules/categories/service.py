"""Categories service - parent-child category tree management."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError
from app.modules.categories.schema import (
    CategoryCreate,
    CategoryRead,
    CategoryTree,
    CategoryUpdate,
)


def _build_tree(flat_categories: list[dict]) -> list[CategoryTree]:
    """Convert a flat list of category rows into a nested CategoryTree list."""
    nodes: dict[str, CategoryTree] = {}
    roots: list[CategoryTree] = []

    for row in flat_categories:
        node = CategoryTree(
            id=str(row["id"]),
            store_id=str(row["store_id"]),
            parent_id=str(row["parent_id"]) if row["parent_id"] else None,
            name=row["name"],
            slug=row["slug"],
            description=row["description"],
            image_url=row["image_url"],
            sort_order=row["sort_order"],
            is_active=row["is_active"],
            created_at=str(row["created_at"]) if row["created_at"] else None,
            updated_at=str(row["updated_at"]) if row["updated_at"] else None,
            children=[],
        )
        nodes[str(row["id"])] = node

    for row in flat_categories:
        node = nodes[str(row["id"])]
        if row["parent_id"] is None:
            roots.append(node)
        else:
            parent = nodes.get(str(row["parent_id"]))
            if parent is not None:
                parent.children.append(node)

    return roots


class CategoriesService:
    """Category hierarchy and tree management service."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _generate_unique_slug(self, store_id: str, base_slug: str) -> str:
        slug = base_slug
        counter = 1
        while True:
            existing = await self.db.execute(
                text(
                    "SELECT id FROM categories "
                    "WHERE store_id = :store_id AND slug = :slug"
                ),
                {"store_id": store_id, "slug": slug},
            )
            if not existing.scalar_one_or_none():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    async def _resolve_store_id(self, slug: str) -> str:
        result = await self.db.execute(
            text("SELECT id FROM stores WHERE slug = :slug"),
            {"slug": slug},
        )
        store_id = result.scalar_one_or_none()
        if not store_id:
            raise AuthError(
                message="Store not found",
                code="NOT_FOUND",
                status_code=404,
            )
        return str(store_id)

    async def create_category(self, data: CategoryCreate) -> CategoryRead:
        slug = data.slug
        if not slug:
            slug = await self._generate_unique_slug(
                data.store_id,
                data.name.lower().replace(" ", "-").replace("_", "-"),
            )
        else:
            existing = await self.db.execute(
                text(
                    "SELECT id FROM categories "
                    "WHERE store_id = :store_id AND slug = :slug"
                ),
                {"store_id": data.store_id, "slug": slug},
            )
            if existing.scalar_one_or_none():
                raise AuthError(
                    message="Category with this slug already exists",
                    code="CONFLICT",
                    status_code=409,
                )

        result = await self.db.execute(
            text(
                "INSERT INTO categories "
                "(store_id, parent_id, name, slug, description, image_url, sort_order) "
                "VALUES (:store_id, :parent_id, :name, :slug, :description, :image_url, :sort_order) "
                "RETURNING id, store_id, parent_id, name, slug, description, "
                "image_url, sort_order, is_active, created_at, updated_at"
            ),
            {
                "store_id": data.store_id,
                "parent_id": data.parent_id,
                "name": data.name,
                "slug": slug,
                "description": data.description,
                "image_url": data.image_url,
                "sort_order": data.sort_order,
            },
        )
        await self.db.commit()

        row = result.mappings().first()
        return self._row_to_read(row)

    async def get_category(self, category_id: str) -> CategoryRead:
        result = await self.db.execute(
            text(
                "SELECT id, store_id, parent_id, name, slug, description, "
                "image_url, sort_order, is_active, created_at, updated_at "
                "FROM categories WHERE id = :category_id"
            ),
            {"category_id": category_id},
        )
        row = result.mappings().first()
        if not row:
            raise AuthError(
                message="Category not found",
                code="NOT_FOUND",
                status_code=404,
            )
        return self._row_to_read(row)

    async def update_category(
        self, category_id: str, data: CategoryUpdate
    ) -> CategoryRead:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_category(category_id)

        if "slug" in update_data and update_data["slug"]:
            store_id = await self._get_store_id_for_category(category_id)
            existing = await self.db.execute(
                text(
                    "SELECT id FROM categories "
                    "WHERE store_id = :store_id AND slug = :slug "
                    "AND id != :category_id"
                ),
                {
                    "store_id": store_id,
                    "slug": update_data["slug"],
                    "category_id": category_id,
                },
            )
            if existing.scalar_one_or_none():
                raise AuthError(
                    message="Category with this slug already exists",
                    code="CONFLICT",
                    status_code=409,
                )

        update_data["updated_at"] = datetime.utcnow()

        set_clause = ", ".join(f"{key} = :{key}" for key in update_data)
        await self.db.execute(
            text(
                f"UPDATE categories SET {set_clause} WHERE id = :category_id"
            ),
            {"category_id": category_id, **update_data},
        )
        await self.db.commit()

        return await self.get_category(category_id)

    async def delete_category(self, category_id: str) -> None:
        result = await self.db.execute(
            text(
                "UPDATE categories SET is_active = false, updated_at = :updated_at "
                "WHERE id = :category_id RETURNING id"
            ),
            {"category_id": category_id, "updated_at": datetime.utcnow()},
        )
        if not result.scalar_one_or_none():
            raise AuthError(
                message="Category not found",
                code="NOT_FOUND",
                status_code=404,
            )
        await self.db.commit()

    async def get_store_categories_tree(self, slug: str) -> list[CategoryTree]:
        store_id = await self._resolve_store_id(slug)
        result = await self.db.execute(
            text(
                "SELECT id, store_id, parent_id, name, slug, description, "
                "image_url, sort_order, is_active, created_at, updated_at "
                "FROM categories "
                "WHERE store_id = :store_id AND is_active = true "
                "ORDER BY sort_order, created_at"
            ),
            {"store_id": store_id},
        )
        rows = result.mappings().all()
        return _build_tree([dict(r) for r in rows])

    async def get_public_category_tree(self) -> list[CategoryTree]:
        result = await self.db.execute(
            text(
                "SELECT id, store_id, parent_id, name, slug, description, "
                "image_url, sort_order, is_active, created_at, updated_at "
                "FROM categories "
                "WHERE is_active = true "
                "ORDER BY store_id, sort_order, created_at"
            ),
        )
        rows = result.mappings().all()
        return _build_tree([dict(r) for r in rows])

    async def _get_store_id_for_category(self, category_id: str) -> str:
        result = await self.db.execute(
            text("SELECT store_id FROM categories WHERE id = :category_id"),
            {"category_id": category_id},
        )
        store_id = result.scalar_one_or_none()
        if not store_id:
            raise AuthError(
                message="Category not found",
                code="NOT_FOUND",
                status_code=404,
            )
        return str(store_id)

    @staticmethod
    def _row_to_read(row) -> CategoryRead:
        return CategoryRead(
            id=str(row["id"]),
            store_id=str(row["store_id"]),
            parent_id=str(row["parent_id"]) if row["parent_id"] else None,
            name=row["name"],
            slug=row["slug"],
            description=row["description"],
            image_url=row["image_url"],
            sort_order=row["sort_order"],
            is_active=row["is_active"],
            created_at=str(row["created_at"]) if row["created_at"] else None,
            updated_at=str(row["updated_at"]) if row["updated_at"] else None,
        )