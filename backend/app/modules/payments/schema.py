"""Payment schemas (BE-07)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PaymentInitiateRequest(BaseModel):
    """Request to initiate payment for an order."""

    order_id: str = Field(..., description="Order UUID to pay for")


class PaymentRead(BaseModel):
    """Payment record response."""

    id: str
    order_id: str
    provider: str
    provider_reference: str | None = None
    payment_method: str
    amount: float
    currency_code: str
    status: str
    paid_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None


class PaymentInitiateResponse(BaseModel):
    """Response from payment initiation."""

    payment_id: str
    payment_url: str
    transaction_id: str | None = None


class PaymentVerifyRequest(BaseModel):
    """Verify a payment (optional body for IPN/callback)."""

    tran_id: str | None = None


class PaymentCallbackPayload(BaseModel):
    """AmarPay callback/IPN payload (loose)."""

    pg_txnid: str | None = None
    mer_txnid: str | None = None
    amount: str | None = None
    pay_status: str | None = None
    status_code: str | None = None
    store_id: str | None = None
    currency: str | None = None
    tran_id: str | None = None
    opt_a: str | None = None
    opt_b: str | None = None
    opt_c: str | None = None
    extra: dict[str, Any] | None = None
