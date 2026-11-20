"""Tests for Categories module - M1.2 Catalog Management.

Covers category CRUD and hierarchical tree operations.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import text

from app.core.exceptions import AuthError
from app.modules.categories.service import CategoriesService
from app.modules.categories.schema import CategoryCreate, CategoryUpdate


async def _seed_store(db_session) -> tuple[str, str]:
    """Insert a store row; returns (store_id, store_slug)."""
    sid = str(uuid4())
    slug = f"store-{sid[:8]}"
    await db_session.execute(
        text(
            "INSERT INTO stores (id, name, slug, status) "
            "VALUES (:id, :name, :slug, 'active')"
        ),
        {"id": sid, "name": f"Store {sid[:6]}", "slug": slug},
    )
    return sid, slug


class TestCategoriesCRUD:
    """Core Category CRUD operations tests."""

    @pytest.mark.asyncio
    async def test_create_category_auto_slug(self, db_session):
        """Test category creation with automatic slug generation."""
        store_id, store_slug = await _seed_store(db_session)
        service = CategoriesService(db_session)

        data = CategoryCreate(store_id=store_id, name="Beauty Care")
        created = await service.create_category(data)
        assert created.id is not None
        assert created.slug == "beauty-care"
        assert created.store_id == store_id

    @pytest.mark.asyncio
    async def test_create_category_explicit_slug(self, db_session):
        """Test category creation with explicit slug."""
        store_id, _ = await _seed_store(db_session)
        service = CategoriesService(db_session)

        created = await service.create_category(
            CategoryCreate(store_id=store_id, name="Health", slug="health", sort_order=5)
        )
        assert created.slug == "health"
        assert created.sort_order == 5

    @pytest.mark.asyncio
    async def test_create_category_duplicate_slug_conflict(self, db_session):
        """Test creating a duplicate category slug raises conflict.

        Auto-slug generation appends a numeric suffix for conflicts; an explicit
        duplicate slug is what triggers the CONFLICT error path.
        """
        store_id, _ = await _seed_store(db_session)
        service = CategoriesService(db_session)

        await service.create_category(
            CategoryCreate(store_id=store_id, name="Fashion", slug="fashion")
        )
        with pytest.raises(AuthError) as exc_info:
            await service.create_category(
                CategoryCreate(store_id=store_id, name="Fashion Two", slug="fashion")
            )
        assert exc_info.value.code == "CONFLICT"
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_create_category_auto_slug_suffix(self, db_session):
        """Test auto-slug generation appends a suffix on conflict."""
        store_id, _ = await _seed_store(db_session)
        service = CategoriesService(db_session)

        first = await service.create_category(CategoryCreate(store_id=store_id, name="Fashion"))
        second = await service.create_category(CategoryCreate(store_id=store_id, name="Fashion"))
        assert first.slug == "fashion"
        assert second.slug == "fashion-1"

    @pytest.mark.asyncio
    async def test_get_category(self, db_session):
        """Test retrieving a category by ID."""
        store_id, _ = await _seed_store(db_session)
        service = CategoriesService(db_session)
        created = await service.create_category(CategoryCreate(store_id=store_id, name="Gadget"))

        retrieved = await service.get_category(created.id)
        assert retrieved.id == created.id
        assert retrieved.name == "Gadget"

    @pytest.mark.asyncio
    async def test_get_category_not_found(self, db_session):
        """Test retrieving a nonexistent category raises AuthError."""
        service = CategoriesService(db_session)
        with pytest.raises(AuthError) as exc_info:
            await service.get_category(str(uuid4()))
        assert exc_info.value.code == "NOT_FOUND"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_category(self, db_session):
        """Test updating category fields."""
        store_id, _ = await _seed_store(db_session)
        service = CategoriesService(db_session)
        created = await service.create_category(CategoryCreate(store_id=store_id, name="Old"))

        updated = await service.update_category(
            created.id,
            CategoryUpdate(name="New", sort_order=9),
        )
        assert updated.id == created.id
        assert updated.name == "New"
        assert updated.sort_order == 9

    @pytest.mark.asyncio
    async def test_delete_category_soft(self, db_session):
        """Test soft delete deactivates a category."""
        store_id, _ = await _seed_store(db_session)
        service = CategoriesService(db_session)
        created = await service.create_category(CategoryCreate(store_id=store_id, name="Hidden"))

        await service.delete_category(created.id)

        retrieved = await service.get_category(created.id)
        assert retrieved.is_active is False

    @pytest.mark.asyncio
    async def test_delete_category_not_found(self, db_session):
        """Test soft delete of nonexistent category raises AuthError."""
        service = CategoriesService(db_session)
        with pytest.raises(AuthError) as exc_info:
            await service.delete_category(str(uuid4()))
        assert exc_info.value.code == "NOT_FOUND"


class TestCategoriesTree:
    """Hierarchical category tree tests."""

    @pytest.mark.asyncio
    async def test_get_store_categories_tree(self, db_session):
        """Test building a nested tree for a store via slug."""
        store_id, store_slug = await _seed_store(db_session)
        service = CategoriesService(db_session)

        parent = await service.create_category(
            CategoryCreate(store_id=store_id, name="Root", slug="root", sort_order=0)
        )
        child = await service.create_category(
            CategoryCreate(
                store_id=store_id,
                parent_id=parent.id,
                name="Child",
                slug="child",
                sort_order=1,
            )
        )

        tree = await service.get_store_categories_tree(store_slug)
        assert len(tree) == 1
        root = tree[0]
        assert root.id == parent.id
        assert len(root.children) == 1
        assert root.children[0].id == child.id

    @pytest.mark.asyncio
    async def test_get_public_category_tree_includes_all_stores(self, db_session):
        """Test public category tree returns a flat list of all stores."""
        store_id, _ = await _seed_store(db_session)
        service = CategoriesService(db_session)

        created = await service.create_category(CategoryCreate(store_id=store_id, name="Only", slug="only"))
        tree = await service.get_public_category_tree()
        found = [n for n in tree if n.id == created.id]
        assert len(found) == 1
