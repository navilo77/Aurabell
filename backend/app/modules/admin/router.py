"""Admin router (BE-05)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import User, get_current_user, require_role
from app.core.database import get_db
from app.core.exceptions import AuthError
from app.modules.admin.schema import (
    AccountStatusUpdate,
    AdminDashboardStats,
    AdminInventorySummary,
    AdminSalesReport,
    AdminUserRead,
    RoleAssignRequest,
    RoleRead,
    RoleRemoveRequest,
)
from app.modules.admin.service import AdminError, AdminService

router = APIRouter(prefix="/admin", tags=["Admin"])


def get_admin_service(db: AsyncSession = Depends(get_db)):
    return AdminService(db)


# ─── User Management ────────────────────────────────────────────────────────────


@router.get(
    "/users",
    summary="List users (admin)",
)
async def list_users(
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
    role: str | None = Query(None, description="Filter by role name"),
    store_id: str | None = Query(None, description="Filter by store ID"),
    status: str | None = Query(None, description="Filter by account status"),
    search: str | None = Query(None, description="Search by name or email"),
    format: str | None = Query(None, description="Response format: 'v2' for paginated {data, meta}"),
    service: AdminService = Depends(get_admin_service),
    user: User = Depends(require_role("super_admin")),
):
    """List users with pagination and filtering. Super-admin only."""
    users, total = await service.list_users(
        page=page, per_page=per_page, role_filter=role,
        store_id=store_id, status_filter=status, search=search,
    )
    from app.core.pagination import paginate
    return paginate(users, total, page, per_page, format)


@router.get(
    "/users/{user_id}",
    response_model=AdminUserRead,
    summary="Get user by ID (admin)",
)
async def get_user(
    user_id: str,
    service: AdminService = Depends(get_admin_service),
    user: User = Depends(require_role("super_admin")),
):
    """Get a single user by ID. Super-admin only."""
    try:
        data = await service.get_user(user_id)
        from app.modules.admin.schema import UserRoleInfo
        return AdminUserRead(
            id=data["id"],
            email=data["email"],
            full_name=data["full_name"],
            phone=data["phone"],
            status=data["status"],
            roles=[UserRoleInfo(**r) for r in data["roles"]],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.patch(
    "/users/{user_id}/status",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Activate/deactivate user account",
)
async def update_user_status(
    user_id: str,
    data: AccountStatusUpdate,
    service: AdminService = Depends(get_admin_service),
    user: User = Depends(require_role("super_admin")),
):
    """Activate or deactivate a user account. Super-admin only."""
    try:
        await service.update_account_status(user_id, data.status)
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.post(
    "/users/{user_id}/roles",
    status_code=status.HTTP_201_CREATED,
    summary="Assign role to user",
)
async def assign_role(
    user_id: str,
    data: RoleAssignRequest,
    service: AdminService = Depends(get_admin_service),
    user: User = Depends(get_current_user),
):
    """Assign a role to a user. Requires super_admin role."""
    if "super_admin" not in user.roles and "admin" not in user.roles:
        raise HTTPException(status_code=403, detail={"detail": "Insufficient permissions", "code": "FORBIDDEN"})
    try:
        await service.assign_role(user_id, data.role_id, data.store_id, str(user.id))
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.delete(
    "/users/{user_id}/roles",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove role from user",
)
async def remove_role(
    user_id: str,
    data: RoleRemoveRequest,
    service: AdminService = Depends(get_admin_service),
    user: User = Depends(get_current_user),
):
    """Remove a role from a user. Requires super_admin role."""
    if "super_admin" not in user.roles and "admin" not in user.roles:
        raise HTTPException(status_code=403, detail={"detail": "Insufficient permissions", "code": "FORBIDDEN"})
    try:
        await service.remove_role(user_id, data.role_id, data.store_id)
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.get(
    "/roles",
    response_model=list[RoleRead],
    summary="List all roles",
)
async def list_roles(
    service: AdminService = Depends(get_admin_service),
    user: User = Depends(require_role("super_admin")),
):
    """List all roles. Super-admin only."""
    try:
        roles = await service.list_roles()
        return [RoleRead(**r) for r in roles]
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


# ─── Dashboard ──────────────────────────────────────────────────────────────────


@router.get(
    "/dashboard",
    response_model=AdminDashboardStats,
    summary="Admin dashboard stats",
)
async def get_dashboard(
    store_id: str | None = Query(None, description="Scope to a store"),
    service: AdminService = Depends(get_admin_service),
    user: User = Depends(get_current_user),
):
    """Get dashboard statistics. Store managers see only their store; super-admin sees all."""
    # Store managers can only see their own store
    if "super_admin" not in user.roles and "admin" not in user.roles:
        if store_id and store_id not in (user.store_ids or []):
            raise HTTPException(status_code=403, detail={"detail": "Access denied to this store", "code": "FORBIDDEN"})
        # If no store_id provided, use first assigned store
        if not store_id and user.store_ids:
            store_id = user.store_ids[0]
    try:
        stats = await service.get_dashboard_stats(store_id)
        from decimal import Decimal
        return AdminDashboardStats(
            total_users=stats["total_users"],
            total_stores=stats["total_stores"],
            active_stores=stats["active_stores"],
            total_products=stats["total_products"],
            active_products=stats["active_products"],
            total_orders=stats["total_orders"],
            pending_orders=stats["pending_orders"],
            total_revenue=Decimal(str(stats["total_revenue"])),
        )
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


# ─── Reports ────────────────────────────────────────────────────────────────────


@router.get(
    "/reports/sales",
    response_model=AdminSalesReport,
    summary="Sales report",
)
async def get_sales_report(
    date_from: str | None = Query(None, description="Start date (ISO format)"),
    date_to: str | None = Query(None, description="End date (ISO format)"),
    store_id: str | None = Query(None, description="Scope to a store"),
    service: AdminService = Depends(get_admin_service),
    user: User = Depends(get_current_user),
):
    """Get sales report with status distribution. Store-scoped for store managers."""
    if "super_admin" not in user.roles and "admin" not in user.roles:
        if store_id and store_id not in (user.store_ids or []):
            raise HTTPException(status_code=403, detail={"detail": "Access denied to this store", "code": "FORBIDDEN"})
        if not store_id and user.store_ids:
            store_id = user.store_ids[0]
    try:
        report = await service.get_sales_report(date_from, date_to, store_id)
        from app.modules.admin.schema import OrderStatusDistribution
        return AdminSalesReport(
            total_orders=report["total_orders"],
            total_revenue=report["total_revenue"],
            total_discount=report["total_discount"],
            total_delivery=report["total_delivery"],
            status_distribution=[OrderStatusDistribution(**s) for s in report["status_distribution"]],
            date_from=report["date_from"],
            date_to=report["date_to"],
            store_id=report["store_id"],
        )
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e


@router.get(
    "/reports/inventory",
    response_model=AdminInventorySummary,
    summary="Inventory summary report",
)
async def get_inventory_report(
    store_id: str | None = Query(None, description="Scope to a store"),
    service: AdminService = Depends(get_admin_service),
    user: User = Depends(get_current_user),
):
    """Get inventory summary. Store-scoped for store managers."""
    if "super_admin" not in user.roles and "admin" not in user.roles:
        if store_id and store_id not in (user.store_ids or []):
            raise HTTPException(status_code=403, detail={"detail": "Access denied to this store", "code": "FORBIDDEN"})
        if not store_id and user.store_ids:
            store_id = user.store_ids[0]
    try:
        summary = await service.get_inventory_summary(store_id)
        return AdminInventorySummary(**summary)
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail={"detail": e.message, "code": e.code}) from e
