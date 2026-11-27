"""AmarPay payment gateway adapter (BE-07)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import settings


@dataclass
class PaymentInitResult:
    success: bool
    payment_url: str | None = None
    transaction_id: str | None = None
    raw_response: dict | None = None
    error: str | None = None


@dataclass
class PaymentVerifyResult:
    success: bool
    status_code: str | None = None
    pay_status: str | None = None
    amount: str | None = None
    transaction_id: str | None = None
    raw_response: dict | None = None
    error: str | None = None


class AmarPayGateway:
    """AmarPay gateway adapter. All AmarPay-specific logic lives here."""

    def __init__(
        self,
        store_id: str,
        signature_key: str,
        base_url: str,
        environment: str = "sandbox",
    ) -> None:
        self.store_id = store_id
        self.signature_key = signature_key
        self.base_url = base_url.rstrip("/")
        self.environment = environment

    def _init_url(self) -> str:
        return f"{self.base_url}/jsonpost.php"

    def _verify_url(self) -> str:
        return f"{self.base_url}/api/v1/trxcheck/request.php"

    async def initiate_payment(
        self,
        *,
        tran_id: str,
        amount: str,
        currency: str,
        cus_name: str,
        cus_email: str,
        cus_phone: str,
        cus_add1: str,
        cus_add2: str,
        cus_city: str,
        cus_country: str,
        success_url: str,
        fail_url: str,
        cancel_url: str,
        desc: str,
        opt_a: str | None = None,
        opt_b: str | None = None,
        opt_c: str | None = None,
    ) -> PaymentInitResult:
        payload: dict[str, Any] = {
            "store_id": self.store_id,
            "signature_key": self.signature_key,
            "cus_name": cus_name,
            "cus_email": cus_email,
            "cus_phone": cus_phone,
            "cus_add1": cus_add1,
            "cus_add2": cus_add2,
            "cus_city": cus_city,
            "cus_country": cus_country,
            "amount": amount,
            "tran_id": tran_id,
            "currency": currency,
            "success_url": success_url,
            "fail_url": fail_url,
            "cancel_url": cancel_url,
            "desc": desc,
            "type": "json",
        }
        if opt_a is not None:
            payload["opt_a"] = opt_a
        if opt_b is not None:
            payload["opt_b"] = opt_b
        if opt_c is not None:
            payload["opt_c"] = opt_c

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self._init_url(), json=payload)
                data = resp.json()
        except Exception as exc:
            return PaymentInitResult(success=False, error=str(exc))

        if data.get("result") == "true" and data.get("payment_url"):
            return PaymentInitResult(
                success=True,
                payment_url=data["payment_url"],
                transaction_id=data.get("pg_txnid"),
                raw_response=data,
            )
        return PaymentInitResult(success=False, raw_response=data, error=data.get("error") or "initiation failed")

    async def verify_transaction(self, tran_id: str) -> PaymentVerifyResult:
        params = {
            "request_id": tran_id,
            "store_id": self.store_id,
            "signature_key": self.signature_key,
            "type": "json",
        }
        url = f"{self._verify_url()}?{urlencode(params)}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
                data = resp.json()
        except Exception as exc:
            return PaymentVerifyResult(success=False, error=str(exc))

        return PaymentVerifyResult(
            success=True,
            status_code=data.get("status_code"),
            pay_status=data.get("pay_status"),
            amount=data.get("amount"),
            transaction_id=data.get("pg_txnid"),
            raw_response=data,
        )
