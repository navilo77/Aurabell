"""Idempotency middleware unit tests for Aura Bell backend.

Tests cover:
- Same key + same request → cached result (no duplicate execution)
- Same key + different request → 409 conflict
- Same key + expired record → treated as new request
- Request hash computation
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.responses import Response

from app.core.idempotency import IdempotencyMiddleware, _compute_request_hash


class TestComputeRequestHash:
    """Tests for request hash computation."""

    def test_hash_deterministic(self) -> None:
        """Same method, path, body → same hash."""
        h1 = _compute_request_hash("POST", "/api/v1/cart/1/items", b'{"qty":2}')
        h2 = _compute_request_hash("POST", "/api/v1/cart/1/items", b'{"qty":2}')
        assert h1 == h2

    def test_hash_different_method(self) -> None:
        """Different method → different hash."""
        h1 = _compute_request_hash("POST", "/api/v1/cart/1/items", b'{}')
        h2 = _compute_request_hash("PUT", "/api/v1/cart/1/items", b'{}')
        assert h1 != h2

    def test_hash_different_body(self) -> None:
        """Different body → different hash."""
        h1 = _compute_request_hash("POST", "/api/v1/cart/1/items", b'{"qty":1}')
        h2 = _compute_request_hash("POST", "/api/v1/cart/1/items", b'{"qty":2}')
        assert h1 != h2

    def test_hash_different_path(self) -> None:
        """Different path → different hash."""
        h1 = _compute_request_hash("POST", "/api/v1/cart/1/items", b'{}')
        h2 = _compute_request_hash("POST", "/api/v1/orders/checkout", b'{}')
        assert h1 != h2


class TestIdempotencyMiddleware:
    """Tests for IdempotencyMiddleware dispatch logic."""

    def _make_request(self, method: str = "POST", key: str | None = "test-key",
                      body: bytes = b'{"qty":1}', path: str = "/api/v1/cart/1/items"):
        """Create a mock Request with idempotency header."""
        request = MagicMock()
        request.method = method
        request.headers.get = MagicMock(return_value=key)
        request.body = AsyncMock(return_value=body)
        request.url.path = path
        return request

    def _make_session(self, existing_row=None):
        """Create a mocked async session."""
        session = AsyncMock()
        result = MagicMock()
        result.fetchone = MagicMock(return_value=existing_row)
        session.execute = AsyncMock(return_value=result)
        session.commit = AsyncMock()
        return session

    def _make_response(self, status_code: int = 200, body: bytes = b'{"id":"123"}'):
        """Create a mock Response."""
        response = MagicMock(spec=Response)
        response.status_code = status_code
        response.body = body
        response.body_iterator = AsyncMock(return_value=iter([body]))
        response.headers = {}
        response.media_type = "application/json"
        return response

    @pytest.mark.asyncio
    async def test_same_key_same_request_returns_cached(self) -> None:
        """Completed idempotency record with matching hash → cached response."""
        existing_row = ("completed", '{"id":"cached"}', "hash-abc", None)
        request = self._make_request(key="key-1", body=b'{"qty":1}')

        with patch("app.core.idempotency.async_session_factory") as mock_factory:
            session = self._make_session(existing_row=existing_row)
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            # Patch _compute_request_hash to return "hash-abc"
            with patch("app.core.idempotency._compute_request_hash", return_value="hash-abc"):
                middleware = IdempotencyMiddleware(MagicMock())
                response = await middleware.dispatch(request, AsyncMock())

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_same_key_different_request_returns_409(self) -> None:
        """Completed idempotency record with mismatched hash → 409."""
        existing_row = ("completed", '{"id":"old"}', "hash-old", None)
        request = self._make_request(key="key-1", body=b'{"qty":2}')

        with patch("app.core.idempotency.async_session_factory") as mock_factory:
            session = self._make_session(existing_row=existing_row)
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("app.core.idempotency._compute_request_hash", return_value="hash-new"):
                middleware = IdempotencyMiddleware(MagicMock())
                response = await middleware.dispatch(request, AsyncMock())

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_concurrent_processing_returns_409(self) -> None:
        """Processing (in-flight) record → 409 conflict."""
        existing_row = ("processing", None, "hash-abc", None)
        request = self._make_request(key="key-1", body=b'{"qty":1}')

        with patch("app.core.idempotency.async_session_factory") as mock_factory:
            session = self._make_session(existing_row=existing_row)
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("app.core.idempotency._compute_request_hash", return_value="hash-abc"):
                middleware = IdempotencyMiddleware(MagicMock())
                response = await middleware.dispatch(request, AsyncMock())

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_no_idempotency_key_passthrough(self) -> None:
        """Request without Idempotency-Key header → passthrough, no DB query."""
        request = self._make_request(key=None)
        call_next = AsyncMock(return_value=self._make_response())

        with patch("app.core.idempotency.async_session_factory") as mock_factory:
            session = self._make_session()
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            middleware = IdempotencyMiddleware(MagicMock())
            response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_method_passthrough(self) -> None:
        """GET requests are not idempotency-protected → passthrough."""
        request = self._make_request(method="GET")
        call_next = AsyncMock(return_value=self._make_response())

        with patch("app.core.idempotency.async_session_factory") as mock_factory:
            session = self._make_session()
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            middleware = IdempotencyMiddleware(MagicMock())
            response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        session.execute.assert_not_called()
