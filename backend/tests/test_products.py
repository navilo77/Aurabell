"""Tests for Products module - M1.2 Catalog Management.

Covers product CRUD, SKU/slug generation, variants, images, and public listing.
Includes a regression test for the _generate_unique_slug infinite-loop fix.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import text

from app.core.exceptions import AuthError
from app.modules.products.service import ProductsService
from app.modules.products.schema import (
    ImageCreate,
    ProductCreate,
    ProductUpdate,
    VariantCreate,
)


async def _seed_store(db_session) -> str:
    """Insert a store row and return its id."""
    sid = str(uuid4())
    await db_session.execute(
        text(
            "INSERT INTO stores (id, name, slug, status) "
            "VALUES (:id, :name, :slug, 'active')"
        ),
        {"id": sid, "name": f"Store {sid[:6]}", "slug": f"store-{sid[:8]}"},
    )
    return sid


def _base_create(name: str, store_id: str) -> ProductCreate:
    return ProductCreate(
        store_id=store_id,
        name=name,
        status="active",
        description="desc",
        brand="BrandX",
    )


class TestProductsCRUD:
    """Core Product CRUD operations tests."""

    @pytest.mark.asyncio
    async def test_create_product_auto_slug(self, db_session):
        """Test product creation with automatic slug generation."""
        store_id = await _seed_store(db_session)
        service = ProductsService(db_session)
        data = _base_create("Beautiful Product", store_id)

        result = await service.create_product(data)
        assert result.id is not None
        assert result.name == "Beautiful Product"
        assert result.slug == "beautiful-product"
        assert result.status == "active"

    @pytest.mark.asyncio
    async def test_get_product(self, db_session):
        """Test retrieving a product by ID."""
        store_id = await _seed_store(db_session)
        service = ProductsService(db_session)
        created = await service.create_product(_base_create("Get Product", store_id))

        retrieved = await service.get_product(created.id)
        assert retrieved.id == created.id
        assert retrieved.name == "Get Product"

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, db_session):
        """Test retrieving a nonexistent product raises AuthError."""
        service = ProductsService(db_session)
        with pytest.raises(AuthError) as exc_info:
            await service.get_product(str(uuid4()))
        assert exc_info.value.code == "NOT_FOUND"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_product(self, db_session):
        """Test updating product fields."""
        store_id = await _seed_store(db_session)
        service = ProductsService(db_session)
        created = await service.create_product(_base_create("Original", store_id))

        updated = await service.update_product(
            created.id,
            ProductUpdate(name="Updated Name", status="draft"),
        )
        assert updated.id == created.id
        assert updated.name == "Updated Name"
        assert updated.status == "draft"

    @pytest.mark.asyncio
    async def test_update_product_no_fields(self, db_session):
        """Test updating with no fields returns current product unchanged."""
        store_id = await _seed_store(db_session)
        service = ProductsService(db_session)
        created = await service.create_product(_base_create("No Change", store_id))

        updated = await service.update_product(created.id, ProductUpdate())
        assert updated.name == "No Change"

    @pytest.mark.asyncio
    async def test_delete_product_soft(self, db_session):
        """Test soft delete sets status to archived."""
        store_id = await _seed_store(db_session)
        service = ProductsService(db_session)
        created = await service.create_product(_base_create("To Archive", store_id))

        await service.delete_product(created.id)

        # Soft delete keeps the row but marks archived
        retrieved = await service.get_product(created.id)
        assert retrieved.status == "archived"

    @pytest.mark.asyncio
    async def test_delete_product_not_found(self, db_session):
        """Test soft delete of nonexistent product raises AuthError."""
        service = ProductsService(db_session)
        with pytest.raises(AuthError) as exc_info:
            await service.delete_product(str(uuid4()))
        assert exc_info.value.code == "NOT_FOUND"


class TestProductsSlugGeneration:
    """Slug generation and uniqueness tests (regression for infinite-loop fix)."""

    @pytest.mark.asyncio
    async def test_duplicate_slug_auto_suffix(self, db_session):
        """Regression: creating two products with the same name must not hang.

        Before the fix, _generate_unique_slug had an indentation bug causing an
        infinite loop (and a NameError on an unreachable line) when the base
        slug already existed. This test would hang forever without the fix.
        """
        store_id = await _seed_store(db_session)
        service = ProductsService(db_session)

        first = await service.create_product(_base_create("Duplicate Name", store_id))
        assert first.slug == "duplicate-name"

        # Second product with identical name must receive a suffixed slug.
        second = await service.create_product(_base_create("Duplicate Name", store_id))
        assert second.slug == "duplicate-name-1"

        # Third must get a further suffix.
        third = await service.create_product(_base_create("Duplicate Name", store_id))
        assert third.slug == "duplicate-name-2"

    @pytest.mark.asyncio
    async def test_explicit_duplicate_slug_conflict(self, db_session):
        """Test explicit duplicate slug raises a conflict."""
        store_id = await _seed_store(db_session)
        service = ProductsService(db_session)

        await service.create_product(
            ProductCreate(store_id=store_id, name="A", slug="same-slug", status="active")
        )
        with pytest.raises(AuthError) as exc_info:
            await service.create_product(
                ProductCreate(store_id=store_id, name="B", slug="same-slug", status="active")
            )
        assert exc_info.value.code == "CONFLICT"
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_update_product_duplicate_slug_conflict(self, db_session):
        """Test updating a product to a duplicate slug raises conflict."""
        store_id = await _seed_store(db_session)
        service = ProductsService(db_session)

        await service.create_product(
            ProductCreate(store_id=store_id, name="A", slug="slug-a", status="active")
        )
        product_b = await service.create_product(
            ProductCreate(store_id=store_id, name="B", slug="slug-b", status="active")
        )

        with pytest.raises(AuthError) as exc_info:
            await service.update_product(product_b.id, ProductUpdate(slug="slug-a"))
        assert exc_info.value.code == "CONFLICT"


class TestProductsVariantsAndImages:
    """Variant and image handling tests."""

    @pytest.mark.asyncio
    async def test_create_product_with_variants_and_images(self, db_session):
        """Test product with nested variants and images."""
        store_id = await _seed_store(db_session)
        service = ProductsService(db_session)

        data = ProductCreate(
            store_id=store_id,
            name="Variant Product",
            status="active",
            variants=[
                VariantCreate(variant_name="Red/S", attributes={"color": "red", "size": "S"}),
                VariantCreate(variant_name="Blue/M", attributes={"color": "blue", "size": "M"}),
            ],
            images=[
                ImageCreate(image_url="https://example.com/img1.png", sort_order=0, is_primary=True),
            ],
        )
        result = await service.create_product(data)

        assert len(result.variants) == 2
        assert len(result.images) == 1
        # Auto-generated SKUs should be non-empty and unique
        skus = [v.sku for v in result.variants]
        assert all(skus)
        assert len(set(skus)) == len(skus)
        assert result.images[0].is_primary is True

    @pytest.mark.asyncio
    async def test_auto_sku_uniqueness(self, db_session):
        """Test that auto-generated SKUs are unique across variants."""
        store_id = await _seed_store(db_session)
        service = ProductsService(db_session)

        # Same attributes for two variants forces SKU collision resolution
        data = ProductCreate(
            store_id=store_id,
            name="SKU Test",
            status="active",
            variants=[
                VariantCreate(variant_name="V1", attributes={"size": "M"}),
                VariantCreate(variant_name="V2", attributes={"size": "M"}),
            ],
        )
        result = await service.create_product(data)
        skus = [v.sku for v in result.variants]
        assert len(set(skus)) == 2


class TestProductsPublicListing:
    """Public product listing tests (active-only filtering)."""

    @pytest.mark.asyncio
    async def test_list_public_products_active_only(self, db_session):
        """Test that public listing returns only active products."""
        store_id = await _seed_store(db_session)
        service = ProductsService(db_session)

        await service.create_product(
            ProductCreate(store_id=store_id, name="Active P", status="active", slug="active-p")
        )
        await service.create_product(
            ProductCreate(store_id=store_id, name="Draft P", status="draft", slug="draft-p")
        )
        await service.create_product(
            ProductCreate(store_id=store_id, name="Archived P", status="archived", slug="archived-p")
        )

        products = await service.list_public_products(store_id=store_id)
        statuses = {p.status for p in products}
        assert statuses == {"active"}
        assert all(p.status == "active" for p in products)

    @pytest.mark.asyncio
    async def test_list_public_products_by_store(self, db_session):
        """Test listing is filtered by store_id."""
        store_a = await _seed_store(db_session)
        store_b = await _seed_store(db_session)
        service = ProductsService(db_session)

        await service.create_product(
            ProductCreate(store_id=store_a, name="StoreA P", status="active")
        )
        await service.create_product(
            ProductCreate(store_id=store_b, name="StoreB P", status="active")
        )

        products_a = await service.list_public_products(store_id=store_a)
        assert len(products_a) == 1
        assert products_a[0].store_id == store_a

        products_b = await service.list_public_products(store_id=store_b)
        assert len(products_b) == 1
        assert products_b[0].store_id == store_b

    @pytest.mark.asyncio
    async def test_list_public_products_search(self, db_session):
        """Test public listing search filter by name."""
        store_id = await _seed_store(db_session)
        service = ProductsService(db_session)

        await service.create_product(
            ProductCreate(store_id=store_id, name="Summer Dress", status="active", slug="summer-dress")
        )
        await service.create_product(
            ProductCreate(store_id=store_id, name="Winter Coat", status="active", slug="winter-coat")
        )

        results = await service.list_public_products(store_id=store_id, search="Summer")
        assert len(results) == 1
        assert results[0].name == "Summer Dress"