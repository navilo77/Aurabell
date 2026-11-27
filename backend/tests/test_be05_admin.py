"""BE-05 contract tests for admin backend completion.

Unit tests (no DB required) test schema validation and authorization logic.
Integration tests (DB required) are marked with @pytest.mark.integration.
"""

from __future__ import annotations

import pytest

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
from app.modules.admin.service import AdminService


class TestAdminSchemas:
    """Verify admin schema validation."""

    def test_account_status_update_valid(self):
        req = AccountStatusUpdate(status="active")
        assert req.status == "active"

    def test_account_status_update_invalid(self):
        # Pydantic doesn't restrict values, service does
        req = AccountStatusUpdate(status="banned")
        assert req.status == "banned"

    def test_role_assign_request(self):
        req = RoleAssignRequest(role_id="role-1", store_id="store-1")
        assert req.role_id == "role-1"
        assert req.store_id == "store-1"

    def test_role_assign_request_global(self):
        req = RoleAssignRequest(role_id="role-1")
        assert req.store_id is None

    def test_role_remove_request(self):
        req = RoleRemoveRequest(role_id="role-1")
        assert req.role_id == "role-1"

    def test_admin_dashboard_stats_defaults(self):
        stats = AdminDashboardStats()
        assert stats.total_users == 0
        assert stats.total_revenue == 0

    def test_admin_sales_report_defaults(self):
        report = AdminSalesReport()
        assert report.total_orders == 0
        assert report.status_distribution == []

    def test_admin_inventory_summary_defaults(self):
        summary = AdminInventorySummary()
        assert summary.total_variants == 0
        assert summary.low_stock_count == 0

    def test_admin_user_read(self):
        user = AdminUserRead(id="1", email="test@test.com", status="active")
        assert user.roles == []

    def test_role_read(self):
        role = RoleRead(id="1", name="admin")
        assert role.description is None


class TestAdminServiceMethods:
    """Verify AdminService has required methods."""

    def test_has_list_users(self):
        assert hasattr(AdminService, "list_users")

    def test_has_get_user(self):
        assert hasattr(AdminService, "get_user")

    def test_has_assign_role(self):
        assert hasattr(AdminService, "assign_role")

    def test_has_remove_role(self):
        assert hasattr(AdminService, "remove_role")

    def test_has_update_account_status(self):
        assert hasattr(AdminService, "update_account_status")

    def test_has_list_roles(self):
        assert hasattr(AdminService, "list_roles")

    def test_has_get_dashboard_stats(self):
        assert hasattr(AdminService, "get_dashboard_stats")

    def test_has_get_sales_report(self):
        assert hasattr(AdminService, "get_sales_report")

    def test_has_get_inventory_summary(self):
        assert hasattr(AdminService, "get_inventory_summary")


class TestBE01Compatibility:
    """Verify BE-01 pagination still works."""

    def test_format_v2(self):
        from app.core.pagination import paginate
        result = paginate([{"id": "1"}], total=1, page=1, per_page=20, format_param="v2")
        assert "data" in result and "meta" in result

    def test_legacy(self):
        from app.core.pagination import paginate
        result = paginate([{"id": "1"}], total=1, page=1, per_page=20, format_param=None)
        assert isinstance(result, list)


class TestBE04Compatibility:
    """Verify BE-04 status transitions still work."""

    def test_valid_transition(self):
        from app.modules.orders.service import OrdersService
        svc = OrdersService.__new__(OrdersService)
        assert svc._is_valid_transition("pending", "confirmed") is True
        assert svc._is_valid_transition("shipped", "pending") is False

    def test_cancellable_statuses(self):
        from app.modules.orders.service import OrdersService
        svc = OrdersService.__new__(OrdersService)
        assert "pending" in svc._CUSTOMER_CANCELLABLE
        assert "processing" not in svc._CUSTOMER_CANCELLABLE
