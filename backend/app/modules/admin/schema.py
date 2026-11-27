"""Admin module schemas (BE-05)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class UserRoleInfo(BaseModel):
    """Role assignment info for a user."""

    role_id: str
    role_name: str
    store_id: str | None = None
    store_name: str | None = None
    assigned_by: str | None = None
    created_at: datetime | None = None


class AdminUserRead(BaseModel):
    """Admin view of a user."""

    id: str
    email: str
    full_name: str | None = None
    phone: str | None = None
    status: str
    roles: list[UserRoleInfo] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AdminUserListResponse(BaseModel):
    """Paginated user list for admin."""

    data: list[AdminUserRead]
    meta: dict[str, Any]


class RoleAssignRequest(BaseModel):
    """Request to assign a role to a user."""

    role_id: str = Field(..., description="Role UUID to assign")
    store_id: str | None = Field(None, description="Store UUID (null for global role)")


class RoleRemoveRequest(BaseModel):
    """Request to remove a role from a user."""

    role_id: str = Field(..., description="Role UUID to remove")
    store_id: str | None = Field(None, description="Store UUID (null for global role)")


class AccountStatusUpdate(BaseModel):
    """Request to activate/deactivate a user account."""

    status: str = Field(..., description="New status: 'active' or 'inactive'/'suspended'")


class AdminDashboardStats(BaseModel):
    """Admin dashboard statistics."""

    total_users: int = 0
    total_stores: int = 0
    active_stores: int = 0
    total_products: int = 0
    active_products: int = 0
    total_orders: int = 0
    pending_orders: int = 0
    total_revenue: Decimal = Decimal("0.00")
    currency_code: str = "BDT"


class AdminReportParams(BaseModel):
    """Report query parameters."""

    date_from: str | None = None
    date_to: str | None = None
    store_id: str | None = None


class OrderStatusDistribution(BaseModel):
    """Order count by status."""

    status: str
    count: int


class AdminSalesReport(BaseModel):
    """Sales report response."""

    total_orders: int = 0
    total_revenue: Decimal = Decimal("0.00")
    total_discount: Decimal = Decimal("0.00")
    total_delivery: Decimal = Decimal("0.00")
    currency_code: str = "BDT"
    status_distribution: list[OrderStatusDistribution] = []
    date_from: str | None = None
    date_to: str | None = None
    store_id: str | None = None


class AdminInventorySummary(BaseModel):
    """Inventory summary for a store or platform."""

    total_variants: int = 0
    total_on_hand: int = 0
    total_reserved: int = 0
    low_stock_count: int = 0
    store_id: str | None = None


class RoleRead(BaseModel):
    """Role read response."""

    id: str
    name: str
    description: str | None = None


class StoreReadAdmin(BaseModel):
    """Store read for admin (includes status)."""

    id: str
    name: str
    slug: str
    status: str
    created_at: str | None = None
