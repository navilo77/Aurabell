"""BE-04 contract tests for orders & account completion.

Unit tests (no DB required) test schema validation, status transitions, and cancellation rules.
Integration tests (DB required) are marked with @pytest.mark.integration.
"""

from __future__ import annotations

import pytest

from app.modules.orders.schema import (
    OrderTimelineEntry,
    OrderStatusUpdateRequest,
    OrderRead,
)
from app.modules.orders.service import OrdersService


class TestStatusTransitions:
    """Verify order status transition validation."""

    def test_valid_transitions(self):
        svc = OrdersService.__new__(OrdersService)
        # pending -> confirmed, cancelled
        assert svc._is_valid_transition("pending", "confirmed") is True
        assert svc._is_valid_transition("pending", "cancelled") is True
        # confirmed -> processing, cancelled
        assert svc._is_valid_transition("confirmed", "processing") is True
        assert svc._is_valid_transition("confirmed", "cancelled") is True
        # processing -> shipped
        assert svc._is_valid_transition("processing", "shipped") is True
        # shipped -> delivered
        assert svc._is_valid_transition("shipped", "delivered") is True

    def test_invalid_transitions(self):
        svc = OrdersService.__new__(OrdersService)
        # shipped -> pending (invalid)
        assert svc._is_valid_transition("shipped", "pending") is False
        # delivered -> processing (invalid)
        assert svc._is_valid_transition("delivered", "processing") is False
        # cancelled -> confirmed (invalid)
        assert svc._is_valid_transition("cancelled", "confirmed") is False
        # cancelled -> pending (invalid)
        assert svc._is_valid_transition("cancelled", "pending") is False
        # delivered -> shipped (invalid)
        assert svc._is_valid_transition("delivered", "shipped") is False
        # pending -> shipped (invalid skip)
        assert svc._is_valid_transition("pending", "shipped") is False

    def test_terminal_states_have_no_transitions(self):
        svc = OrdersService.__new__(OrdersService)
        assert svc._is_valid_transition("delivered", "cancelled") is False
        assert svc._is_valid_transition("cancelled", "pending") is False

    def test_unknown_status_has_no_transitions(self):
        svc = OrdersService.__new__(OrdersService)
        assert svc._is_valid_transition("unknown", "pending") is False


class TestCustomerCancellable:
    """Verify customer cancellation rules."""

    def test_cancellable_statuses(self):
        svc = OrdersService.__new__(OrdersService)
        assert "pending" in svc._CUSTOMER_CANCELLABLE
        assert "confirmed" in svc._CUSTOMER_CANCELLABLE

    def test_non_cancellable_statuses(self):
        svc = OrdersService.__new__(OrdersService)
        for status in ["processing", "shipped", "delivered", "cancelled"]:
            assert status not in svc._CUSTOMER_CANCELLABLE


class TestOrderTimelineEntry:
    """Verify OrderTimelineEntry schema."""

    def test_timeline_entry_fields(self):
        entry = OrderTimelineEntry(
            old_status="pending", new_status="confirmed",
            changed_by="user-1", note="COD verified", created_at="2026-01-01T00:00:00Z"
        )
        assert entry.old_status == "pending"
        assert entry.new_status == "confirmed"
        assert entry.changed_by == "user-1"

    def test_timeline_entry_null_old_status(self):
        entry = OrderTimelineEntry(
            old_status=None, new_status="pending",
            note="Order placed", created_at="2026-01-01T00:00:00Z"
        )
        assert entry.old_status is None


class TestOrderStatusUpdateRequest:
    """Verify OrderStatusUpdateRequest schema."""

    def test_status_required(self):
        req = OrderStatusUpdateRequest(status="processing")
        assert req.status == "processing"
        assert req.note is None

    def test_status_with_note(self):
        req = OrderStatusUpdateRequest(status="shipped", note="Dispatched via Pathao")
        assert req.note == "Dispatched via Pathao"


class TestOrderReadCompatibility:
    """Verify OrderRead still works with all existing fields."""

    def test_order_read_minimal(self):
        order = OrderRead(id="1", order_number="AB-001", order_status="pending", created_at="2026-01-01")
        assert order.delivery_address is None
        assert order.store_orders == []
        assert order.order_items == []

    def test_order_read_with_timeline_not_included(self):
        """Timeline is a separate endpoint, not part of OrderRead."""
        assert "timeline" not in OrderRead.model_fields


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


class TestBE03Compatibility:
    """Verify BE-03 address resolution still works."""

    def test_order_create_with_delivery_address_id(self):
        from app.modules.orders.schema import OrderCreate
        oc = OrderCreate(cart_id="c1", delivery_address_id="a1", payment_method="cod")
        assert oc.delivery_address_id == "a1"

    def test_order_create_with_inline_address(self):
        from app.modules.orders.schema import OrderCreate, OrderAddressCreate
        addr = OrderAddressCreate(recipient_name="J", phone="017", division="D", district="D", address_line="L")
        oc = OrderCreate(cart_id="c1", address=addr, payment_method="cod")
        assert oc.address is not None
