"""Shared pagination utilities for BE-01 API contract stabilization.

Standardized offset pagination with metadata response.
AD-004 compliant.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""

    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number (1-based)")
    per_page: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated list response (v2 format)."""

    data: list[T] = Field(..., description="List of items")
    meta: PaginationMeta = Field(..., description="Pagination metadata")


def compute_pagination_meta(total: int, page: int, per_page: int) -> PaginationMeta:
    """Compute pagination metadata from total count, page, and per_page."""
    if per_page <= 0:
        per_page = 20
    if page <= 0:
        page = 1
    total_pages = max(1, (total + per_page - 1) // per_page)
    return PaginationMeta(
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


def paginate(items: list, total: int, page: int, per_page: int, format_param: str | None = None) -> list | dict[str, Any]:
    """Return either legacy list or v2 paginated response based on format param.

    Legacy (default): returns raw list of items.
    V2 (format=v2): returns {data: [...], meta: {...}}.
    """
    if format_param == "v2":
        return {
            "data": items,
            "meta": compute_pagination_meta(total, page, per_page).model_dump(),
        }
    return items
