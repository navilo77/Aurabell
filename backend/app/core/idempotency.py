"""Idempotency middleware for mutating API requests.

Checks the ``Idempotency-Key`` header on POST/PUT/PATCH/DELETE requests.
- Same key + same request → cached original result (no duplicate work)
- Same key + different request body → 409
- Same key + concurrent in-flight request → 409
- Records expire after 24 hours.

The ``public.idempotency_keys`` table (migration 007) provides storage.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.database import async_session_factory
from sqlalchemy import text


def _compute_request_hash(method: str, path: str, body: bytes) -> str:
    h = hashlib.sha256()
    h.update(method.encode())
    h.update(b":")
    h.update(path.encode())
    h.update(b":")
    h.update(body)
    return h.hexdigest()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(value) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only mutating methods with an Idempotency-Key header are protected
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        body = await request.body()
        request_hash = _compute_request_hash(request.method, request.url.path, body)
        endpoint = request.url.path

        async with async_session_factory() as session:
            now = _utcnow()

            result = await session.execute(
                text("""
                    SELECT status, response_data, request_hash, expires_at
                    FROM public.idempotency_keys
                    WHERE key = :key AND endpoint = :endpoint
                """),
                {"key": idempotency_key, "endpoint": endpoint},
            )
            row = result.fetchone()

            if row:
                status, response_data, stored_hash, expires_at = row
                expires_at = _ensure_utc(expires_at)

                if expires_at and expires_at < now:
                    # Expired: remove and treat as a new request
                    await session.execute(
                        text("""
                            DELETE FROM public.idempotency_keys
                            WHERE key = :key AND endpoint = :endpoint
                        """),
                        {"key": idempotency_key, "endpoint": endpoint},
                    )
                    await session.commit()
                elif status == "completed" and stored_hash == request_hash:
                    # Cached successful response — return without re-executing
                    if response_data:
                        return Response(
                            content=json.dumps(response_data) if not isinstance(response_data, str) else response_data,
                            status_code=200,
                            headers={"Content-Type": "application/json"},
                        )
                    return Response(status_code=200)
                elif status == "processing":
                    # Concurrent identical request still in flight
                    return Response(
                        content=json.dumps({"detail": "Concurrent identical request", "code": "IDEMPOTENCY_CONFLICT"}),
                        status_code=409,
                        headers={"Content-Type": "application/json"},
                    )
                elif stored_hash != request_hash:
                    # Same key, different request payload
                    return Response(
                        content=json.dumps({"detail": "Idempotency key conflict: different request", "code": "IDEMPOTENCY_CONFLICT"}),
                        status_code=409,
                        headers={"Content-Type": "application/json"},
                    )

            # Insert a processing record so concurrent duplicates see 'processing'
            expires_at = now + timedelta(hours=24)
            await session.execute(
                text("""
                    INSERT INTO public.idempotency_keys
                        (key, user_id, endpoint, request_hash, status, expires_at)
                    VALUES (:key, NULL, :endpoint, :request_hash, 'processing', :expires_at)
                """),
                {
                    "key": idempotency_key,
                    "endpoint": endpoint,
                    "request_hash": request_hash,
                    "expires_at": expires_at,
                },
            )
            await session.commit()

        # Execute the endpoint
        response = await call_next(request)

        # Capture the response body so we can cache it
        if hasattr(response, "body") and response.body:
            response_body = response.body
        else:
            response_body = b"".join([chunk async for chunk in response.body_iterator])

        async with async_session_factory() as session:
            if response.status_code < 400:
                try:
                    response_data = json.loads(response_body) if response_body else None
                except (json.JSONDecodeError, ValueError):
                    response_data = None
                await session.execute(
                    text("""
                        UPDATE public.idempotency_keys
                        SET status = 'completed', response_data = :response_data
                        WHERE key = :key AND endpoint = :endpoint AND status = 'processing'
                    """),
                    {
                        "key": idempotency_key,
                        "endpoint": endpoint,
                        "response_data": json.dumps(response_data) if response_data is not None else None,
                    },
                )
            else:
                await session.execute(
                    text("""
                        UPDATE public.idempotency_keys
                        SET status = 'failed'
                        WHERE key = :key AND endpoint = :endpoint AND status = 'processing'
                    """),
                    {"key": idempotency_key, "endpoint": endpoint},
                )
            await session.commit()

        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
