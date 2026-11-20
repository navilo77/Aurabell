"""Products service — Product, Variant, and Image CRUD with SKU generation."""

from __future__ import annotations

import json
import re
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError
from app.modules.products.schema import (
    ImageCreate,
    ImageRead,       # <-- এটি যোগ করো
    ProductCreate,
    ProductRead,
    ProductUpdate,
    VariantCreate,
    VariantRead,     # <-- এটি যোগ করো
)



# ─── Helpers ──────────────────────────────────────────────────────────────────


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "product"


def _sku_prefix(name: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", name)
    if not words:
        return "PRD"
    prefix = "".join(w[0].upper() for w in words[:4])
    return prefix[:4]


def _attr_part(value: object) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "", str(value).strip())
    return token[:3].upper() if token else "XXX"


class ProductsService:
    """Product catalog management and SKU generation service."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─── SKU Generation ────────────────────────────────────────────────────

    def _build_base_sku(self, product_name: str, attributes: dict) -> str:
        prefix = _sku_prefix(product_name)
        parts = [_attr_part(attributes[key]) for key in sorted(attributes.keys())]
        if parts:
            return f"{prefix}-{'-'.join(parts)}"
        return prefix

    async def _generate_unique_sku(self, base_sku: str) -> str:
        slug = base_sku
        counter = 2
        while True:
            existing = await self.db.execute(
                text("SELECT id FROM product_variants WHERE sku = :sku"),
                {"sku": slug},
            )
            if not existing.scalar_one_or_none():
                return slug
            slug = f"{base_sku}-{counter}"
            counter += 1

    # ─── Slug ───────────────────────────────────────────────────────────────

    async def _generate_unique_slug(self, store_id: str, base_slug: str) -> str:
        slug = base_slug
        counter = 1
        while True:
            existing = await self.db.execute(
                text(
                    "SELECT id FROM products "
                    "WHERE store_id = :store_id AND slug = :slug"
                ),
                {"store_id": store_id, "slug": slug},
            )
            if not existing.scalar_one_or_none():
                return slug
            slug = f"{base_slug}-{counter}"
            counter += 1

    # ─── Referential Checks ─────────────────────────────────────────────────

    async def _ensure_store(self, store_id: str) -> None:
        result = await self.db.execute(
            text("SELECT id FROM stores WHERE id = :store_id"),
            {"store_id": store_id},
        )
        if not result.scalar_one_or_none():
            raise AuthError(message="Store not found", code="NOT_FOUND", status_code=404)

    async def _ensure_category(self, category_id: str | None) -> None:
        if not category_id:
            return
        result = await self.db.execute(
            text("SELECT id FROM categories WHERE id = :category_id"),
            {"category_id": category_id},
        )
        if not result.scalar_one_or_none():
            raise AuthError(message="Category not found", code="NOT_FOUND", status_code=404)

    # ─── Row Mappers ────────────────────────────────────────────────────────

    def _row_to_read(
        self,
        row,
        variants: list,
        images: list,
    ) -> ProductRead:
        return ProductRead(
            id=str(row["id"]),
            store_id=str(row["store_id"]),
            category_id=str(row["category_id"]) if row["category_id"] else None,
            name=row["name"],
            slug=row["slug"],
            description=row["description"],
            brand=row["brand"],
            product_type=row["product_type"],
            status=row["status"],
            is_featured=row["is_featured"],
            created_at=str(row["created_at"]) if row["created_at"] else None,
            updated_at=str(row["updated_at"]) if row["updated_at"] else None,
            variants=variants,
            images=images,
        )

    async def _get_variants(self, product_id: str) -> list:
        result = await self.db.execute(
            text(
                "SELECT id, product_id, sku, variant_name, attributes, barcode, "
                "is_active, created_at "
                "FROM product_variants WHERE product_id = :product_id "
                "ORDER BY created_at"
            ),
            {"product_id": product_id},
        )
        rows = result.mappings().all()
        return [
            VariantRead(
                id=str(r["id"]),
                product_id=str(r["product_id"]),
                sku=r["sku"],
                variant_name=r["variant_name"],
                attributes=r["attributes"],
                barcode=r["barcode"],
                is_active=r["is_active"],
                created_at=str(r["created_at"]) if r["created_at"] else None,
            )
            for r in rows
        ]

    async def _get_images(self, product_id: str) -> list:
        result = await self.db.execute(
            text(
                "SELECT id, product_id, image_url, alt_text, sort_order, is_primary "
                "FROM product_images WHERE product_id = :product_id "
                "ORDER BY sort_order"
            ),
            {"product_id": product_id},
        )
        rows = result.mappings().all()
        return [
            ImageRead(
                id=str(r["id"]),
                product_id=str(r["product_id"]),
                image_url=r["image_url"],
                alt_text=r["alt_text"],
                sort_order=r["sort_order"],
                is_primary=r["is_primary"],
            )
            for r in rows
        ]

    async def _get_product_full(self, product_id: str) -> ProductRead:
        result = await self.db.execute(
            text(
                "SELECT id, store_id, category_id, name, slug, description, brand, "
                "product_type, status, is_featured, created_at, updated_at "
                "FROM products WHERE id = :product_id"
            ),
            {"product_id": product_id},
        )
        row = result.mappings().first()
        if not row:
            raise AuthError(
                message="Product not found", code="NOT_FOUND", status_code=404
            )
        variants = await self._get_variants(product_id)
        images = await self._get_images(product_id)
        return self._row_to_read(row, variants, images)

    # ─── Private Insert Helpers ─────────────────────────────────────────────

    async def _insert_variant(
        self, product_id: str, product_name: str, variant_data: VariantCreate
    ) -> str:
        sku = variant_data.sku
        if not sku:
            sku = await self._generate_unique_sku(
                self._build_base_sku(product_name, variant_data.attributes)
            )
        result = await self.db.execute(
            text(
                "INSERT INTO product_variants "
                "(product_id, sku, variant_name, attributes, barcode) "
                "VALUES (:product_id, :sku, :variant_name, :attributes, :barcode) "
                "RETURNING id"
            ),
            {
                "product_id": product_id,
                "sku": sku,
                "variant_name": variant_data.variant_name,
                "attributes": json.dumps(variant_data.attributes) if variant_data.attributes else "{}",
                "barcode": variant_data.barcode,
            },
        )
        return str(result.scalar_one_or_none())

    async def _insert_image(
        self, product_id: str, image_data: ImageCreate
    ) -> str:
        result = await self.db.execute(
            text(
                "INSERT INTO product_images "
                "(product_id, image_url, alt_text, sort_order, is_primary) "
                "VALUES (:product_id, :image_url, :alt_text, :sort_order, :is_primary) "
                "RETURNING id"
            ),
            {
                "product_id": product_id,
                "image_url": image_data.image_url,
                "alt_text": image_data.alt_text,
                "sort_order": image_data.sort_order,
                "is_primary": image_data.is_primary,
            },
        )
        return str(result.scalar_one_or_none())

    # ─── Create ─────────────────────────────────────────────────────────────

    async def create_product(self, data: ProductCreate) -> ProductRead:
        await self._ensure_store(data.store_id)
        await self._ensure_category(data.category_id)

        slug = data.slug
        if not slug:
            slug = await self._generate_unique_slug(data.store_id, _slugify(data.name))
        else:
            existing = await self.db.execute(
                text(
                    "SELECT id FROM products "
                    "WHERE store_id = :store_id AND slug = :slug"
                ),
                {"store_id": data.store_id, "slug": slug},
            )
            if existing.scalar_one_or_none():
                raise AuthError(
                    message="Product with this slug already exists for this store",
                    code="CONFLICT",
                    status_code=409,
                )

        try:
            result = await self.db.execute(
                text(
                    "INSERT INTO products "
                    "(store_id, category_id, name, slug, description, brand, "
                    "product_type, status, is_featured) "
                    "VALUES (:store_id, :category_id, :name, :slug, :description, "
                    ":brand, :product_type, :status, :is_featured) "
                    "RETURNING id, store_id, category_id, name, slug, description, "
                    "brand, product_type, status, is_featured, created_at, updated_at"
                ),
                {
                    "store_id": data.store_id,
                    "category_id": data.category_id,
                    "name": data.name,
                    "slug": slug,
                    "description": data.description,
                    "brand": data.brand,
                    "product_type": data.product_type,
                    "status": data.status,
                    "is_featured": data.is_featured,
                },
            )
            product_row = result.mappings().first()
            product_id = str(product_row["id"])

            for variant_data in data.variants:
                await self._insert_variant(product_id, data.name, variant_data)

            for image_data in data.images:
                await self._insert_image(product_id, image_data)

            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return await self._get_product_full(product_id)

    # ─── Read ───────────────────────────────────────────────────────────────

    async def get_product(self, product_id: str) -> ProductRead:
        return await self._get_product_full(product_id)

    # ─── Update ─────────────────────────────────────────────────────────────

    async def update_product(
        self, product_id: str, data: ProductUpdate
    ) -> ProductRead:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self._get_product_full(product_id)

        if "slug" in update_data and update_data["slug"]:
            store_id = await self._get_store_id_for_product(product_id)
            existing = await self.db.execute(
                text(
                    "SELECT id FROM products "
                    "WHERE store_id = :store_id AND slug = :slug "
                    "AND id != :product_id"
                ),
                {
                    "store_id": store_id,
                    "slug": update_data["slug"],
                    "product_id": product_id,
                },
            )
            if existing.scalar_one_or_none():
                raise AuthError(
                    message="Product with this slug already exists for this store",
                    code="CONFLICT",
                    status_code=409,
                )

        update_data["updated_at"] = datetime.utcnow()

        set_clause = ", ".join(f"{key} = :{key}" for key in update_data)
        await self.db.execute(
            text(f"UPDATE products SET {set_clause} WHERE id = :product_id"),
            {"product_id": product_id, **update_data},
        )
        await self.db.commit()

        return await self._get_product_full(product_id)

    async def _get_store_id_for_product(self, product_id: str) -> str:
        result = await self.db.execute(
            text("SELECT store_id FROM products WHERE id = :product_id"),
            {"product_id": product_id},
        )
        store_id = result.scalar_one_or_none()
        if not store_id:
            raise AuthError(
                message="Product not found", code="NOT_FOUND", status_code=404
            )
        return str(store_id)

    # ─── Delete (Soft) ──────────────────────────────────────────────────────

    async def delete_product(self, product_id: str) -> None:
        result = await self.db.execute(
            text(
                "UPDATE products SET status = 'archived', updated_at = :updated_at "
                "WHERE id = :product_id RETURNING id"
            ),
            {"product_id": product_id, "updated_at": datetime.utcnow()},
        )
        if not result.scalar_one_or_none():
            raise AuthError(
                message="Product not found", code="NOT_FOUND", status_code=404
            )
        await self.db.commit()

    # ─── Public Listing ─────────────────────────────────────────────────────

    async def list_public_products(
        self,
        store_id: str | None = None,
        category_id: str | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ProductRead]:
        query = (
            "SELECT id, store_id, category_id, name, slug, description, brand, "
            "product_type, status, is_featured, created_at, updated_at "
            "FROM products WHERE status = 'active'"
        )
        params: dict = {"limit": limit, "offset": offset}

        if store_id:
            query += " AND store_id = :store_id"
            params["store_id"] = store_id
        if category_id:
            query += " AND category_id = :category_id"
            params["category_id"] = category_id
        if search:
            query += " AND name ILIKE :search"
            params["search"] = f"%{search}%"

        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"

        result = await self.db.execute(text(query), params)
        rows = result.mappings().all()

        products: list[ProductRead] = []
        for row in rows:
            pid = str(row["id"])
            variants = await self._get_variants(pid)
            images = await self._get_images(pid)
            products.append(self._row_to_read(row, variants, images))
        return products