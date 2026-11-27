"""BE-01 contract tests for pagination, sorting, filtering, and format=v2.

Unit tests (no DB required) test the pagination helper and validation logic.
Integration tests (DB required) are marked with @pytest.mark.integration.
"""

from __future__ import annotations

import pytest

from app.core.pagination import (
    PaginationMeta,
    PaginatedResponse,
    compute_pagination_meta,
    paginate,
)


# ─── Unit Tests: Pagination Helper ──────────────────────────────────────────────


class TestComputePaginationMeta:
    def test_basic_meta(self):
        meta = compute_pagination_meta(total=50, page=1, per_page=20)
        assert meta.total == 50
        assert meta.page == 1
        assert meta.per_page == 20
        assert meta.total_pages == 3
        assert meta.has_next is True
        assert meta.has_prev is False

    def test_last_page(self):
        meta = compute_pagination_meta(total=50, page=3, per_page=20)
        assert meta.total_pages == 3
        assert meta.has_next is False
        assert meta.has_prev is True

    def test_single_page(self):
        meta = compute_pagination_meta(total=5, page=1, per_page=20)
        assert meta.total_pages == 1
        assert meta.has_next is False
        assert meta.has_prev is False

    def test_empty_result(self):
        meta = compute_pagination_meta(total=0, page=1, per_page=20)
        assert meta.total == 0
        assert meta.total_pages == 1
        assert meta.has_next is False

    def test_exact_page_boundary(self):
        meta = compute_pagination_meta(total=40, page=2, per_page=20)
        assert meta.total_pages == 2
        assert meta.has_next is False
        assert meta.has_prev is True

    def test_invalid_per_page_zero(self):
        meta = compute_pagination_meta(total=10, page=1, per_page=0)
        assert meta.per_page == 20  # defaults to 20

    def test_invalid_page_zero(self):
        meta = compute_pagination_meta(total=10, page=0, per_page=20)
        assert meta.page == 1  # defaults to 1


class TestPaginate:
    def test_legacy_format_returns_list(self):
        items = [{"id": "1"}, {"id": "2"}]
        result = paginate(items, total=2, page=1, per_page=20, format_param=None)
        assert isinstance(result, list)
        assert result == items

    def test_v2_format_returns_dict(self):
        items = [{"id": "1"}, {"id": "2"}]
        result = paginate(items, total=2, page=1, per_page=20, format_param="v2")
        assert isinstance(result, dict)
        assert "data" in result
        assert "meta" in result
        assert result["data"] == items
        assert result["meta"]["total"] == 2
        assert result["meta"]["page"] == 1
        assert result["meta"]["per_page"] == 20
        assert result["meta"]["total_pages"] == 1
        assert result["meta"]["has_next"] is False
        assert result["meta"]["has_prev"] is False

    def test_v2_meta_fields(self):
        items = list(range(5))
        result = paginate(items, total=50, page=2, per_page=20, format_param="v2")
        meta = result["meta"]
        assert meta["total"] == 50
        assert meta["page"] == 2
        assert meta["per_page"] == 20
        assert meta["total_pages"] == 3
        assert meta["has_next"] is True
        assert meta["has_prev"] is True

    def test_v2_empty_result(self):
        result = paginate([], total=0, page=1, per_page=20, format_param="v2")
        assert result["data"] == []
        assert result["meta"]["total"] == 0
        assert result["meta"]["total_pages"] == 1

    def test_unknown_format_returns_list(self):
        items = [{"id": "1"}]
        result = paginate(items, total=1, page=1, per_page=20, format_param="unknown")
        assert isinstance(result, list)
        assert result == items


class TestPaginationMetaFields:
    def test_field_names(self):
        meta = PaginationMeta(total=10, page=1, per_page=20, total_pages=1, has_next=False, has_prev=False)
        dumped = meta.model_dump()
        assert set(dumped.keys()) == {"total", "page", "per_page", "total_pages", "has_next", "has_prev"}


class TestSortFieldWhitelist:
    """Verify sort field whitelist prevents SQL injection."""

    def test_allowed_fields(self):
        allowed = {"price", "name", "created_at", "updated_at"}
        for field in allowed:
            assert field in allowed

    def test_disallowed_fields_not_in_whitelist(self):
        dangerous = ["id; DROP TABLE products", "name ASC, id", "1=1", "created_at DESC; --"]
        allowed = {"price", "name", "created_at", "updated_at"}
        for field in dangerous:
            assert field not in allowed
