"""BE-07 contract tests for AmarPay payment gateway."""

from __future__ import annotations

import pytest

from app.modules.payments.schema import PaymentInitiateRequest, PaymentRead
from app.modules.payments.service import PaymentService, PaymentError, INTERNAL_STATUS_MAP
from app.modules.payments.adapter import AmarPayGateway, PaymentInitResult, PaymentVerifyResult


class TestPaymentSchemas:
    def test_initiate_requires_order_id(self):
        req = PaymentInitiateRequest(order_id="abc")
        assert req.order_id == "abc"

    def test_payment_read(self):
        from datetime import datetime
        p = PaymentRead(
            id="1", order_id="o1", provider="amarpay", payment_method="amarpay",
            amount=100.0, currency_code="BDT", status="pending", created_at=datetime.now()
        )
        assert p.status == "pending"


class TestPaymentServiceMethods:
    def test_has_initiate(self):
        assert hasattr(PaymentService, "initiate_payment")

    def test_has_verify(self):
        assert hasattr(PaymentService, "verify_payment")

    def test_has_handle_callback(self):
        assert hasattr(PaymentService, "handle_callback")

    def test_has_get_payment(self):
        assert hasattr(PaymentService, "get_payment")


class TestAmarPayGateway:
    def test_init_url(self):
        gw = AmarPayGateway(store_id="s", signature_key="k", base_url="https://sandbox.aamarpay.com")
        assert gw._init_url() == "https://sandbox.aamarpay.com/jsonpost.php"

    def test_verify_url(self):
        gw = AmarPayGateway(store_id="s", signature_key="k", base_url="https://sandbox.aamarpay.com")
        assert "trxcheck" in gw._verify_url()


class TestStatusMapping:
    def test_status_code_2_paid(self):
        assert INTERNAL_STATUS_MAP.get("2") == "paid"

    def test_successful_paid(self):
        assert INTERNAL_STATUS_MAP.get("Successful") == "paid"


class TestPaymentError:
    def test_is_auth_error(self):
        from app.core.exceptions import AuthError
        assert issubclass(PaymentError, AuthError)


class TestRegression:
    def test_be01(self):
        from app.core.pagination import compute_pagination_meta
        assert compute_pagination_meta(total=10, page=1, per_page=5).total_pages == 2

    def test_be06(self):
        from app.modules.community.schema import ConversationCreate
        assert ConversationCreate(recipient_id="x").recipient_id == "x"


class TestSecretsNotHardcoded:
    def test_no_hardcoded_store_id_in_adapter(self):
        import inspect
        src = inspect.getsource(AmarPayGateway)
        assert "aamarpaytest" not in src
        assert "dbb74894" not in src
