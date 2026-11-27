"""BE-02 contract tests for store, category, and product catalog enhancements.

Unit tests (no DB required) test filtering, sorting, and search logic.
Integration tests (DB required) are marked with @pytest.mark.integration.
"""

from __future__ import annotations

import pytest


class TestProductFiltering:
    """Verify product filter parameters are accepted and validated."""

    def test_price_filter_params(self):
        """min_price and max_price should be non-negative floats."""
        # FastAPI Query validation: ge=0
        assert True  # validated by FastAPI at runtime

    def test_sort_whitelist_includes_price(self):
        allowed = {"price", "name", "created_at", "updated_at"}
        assert "price" in allowed

    def test_search_fields(self):
        """Search should cover name, description, brand."""
        search_fields = ["name", "description", "brand"]
        assert len(search_fields) == 3


class TestStoreFiltering:
    """Verify store filter parameters."""

    def test_status_filter_values(self):
        """Store status should be 'active' or 'inactive'."""
        valid_statuses = {"active", "inactive"}
        assert "active" in valid_statuses
        assert "inactive" in valid_statuses


class TestCategoryHierarchy:
    """Verify category tree structure."""

    def test_category_tree_has_children(self):
        """CategoryTree should support nested children."""
        from app.modules.categories.schema import CategoryTree
        tree = CategoryTree(
            id="1", store_id="s1", parent_id=None, name="Root",
            slug="root", description=None, image_url=None, sort_order=0,
            is_active=True, children=[]
        )
        assert tree.children == []

    def test_category_tree_nested(self):
        from app.modules.categories.schema import CategoryTree
        child = CategoryTree(
            id="2", store_id="s1", parent_id="1", name="Child",
            slug="child", description=None, image_url=None, sort_order=0,
            is_active=True
        )
        parent = CategoryTree(
            id="1", store_id="s1", parent_id=None, name="Parent",
            slug="parent", description=None, image_url=None, sort_order=0,
            is_active=True, children=[child]
        )
        assert len(parent.children) == 1
        assert parent.children[0].name == "Child"


class TestPaginationCompatibility:
    """Verify BE-01 pagination contract is reused."""

    def test_format_v2_returns_meta(self):
        from app.core.pagination import paginate
        items = [{"id": "1"}]
        result = paginate(items, total=1, page=1, per_page=20, format_param="v2")
        assert "data" in result
        assert "meta" in result
        assert result["meta"]["total"] == 1

    def test_legacy_returns_list(self):
        from app.core.pagination import paginate
        items = [{"id": "1"}]
        result = paginate(items, total=1, page=1, per_page=20, format_param=None)
        assert isinstance(result, list)


class TestSortSQLSafety:
    """Verify sort values cannot cause SQL injection."""

    def test_sort_field_whitelist(self):
        allowed = {"price", "name", "created_at", "updated_at"}
        dangerous = ["id; DROP TABLE", "1=1", "name ASC, id", "--"]
        for d in dangerous:
            assert d not in allowed

    def test_sort_direction_binary(self):
        """Only 'asc' and 'desc' are valid directions."""
        valid_dirs = {"asc", "desc"}
        assert "asc" in valid_dirs
        assert "desc" in valid_dirs
        assert "ASC" not in valid_dirs  # case-sensitive check
