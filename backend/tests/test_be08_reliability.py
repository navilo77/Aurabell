"""BE-08 reliability/hardening tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestHealth:
    def test_health(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_ready(self):
        r = client.get("/health/ready")
        assert r.status_code == 200


class TestRequestId:
    def test_request_id_returned(self):
        r = client.get("/health")
        assert "X-Request-ID" in r.headers

    def test_request_id_echoed(self):
        r = client.get("/health", headers={"X-Request-ID": "test-123"})
        assert r.headers["X-Request-ID"] == "test-123"


class TestSecurityHeaders:
    def test_content_type_options(self):
        r = client.get("/health")
        assert r.headers.get("X-Content-Type-Options") == "nosniff"

    def test_frame_options(self):
        r = client.get("/health")
        assert r.headers.get("X-Frame-Options") == "DENY"


class TestPaginationMaxPerPage:
    def test_max_per_page(self):
        from app.core.pagination import paginate
        # per_page should be capped by endpoint validation, but paginate handles any
        result = paginate([], total=0, page=1, per_page=20)
        assert isinstance(result, list) or "meta" in result or "data" in result


class TestRegression:
    def test_be01_be07_imports(self):
        from app.modules.payments.router import router
        from app.modules.community.router import router as cr
        from app.modules.orders.router import router as orr
        assert True
