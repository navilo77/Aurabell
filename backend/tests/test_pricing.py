"""Focused tests for pricing validation and discount calculation."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.pricing.schema import PriceCreate, PromotionCreate
from app.modules.pricing.service import PricingService


class _Result:
    def __init__(self, rows=None, row=None, scalar=None):
        self._rows = rows or []
        self._row = row
        self._scalar = scalar

    def mappings(self):
        return self

    def all(self):
        return self._rows

    def one_or_none(self):
        return self._row

    def one(self):
        return self._row

    def scalar_one_or_none(self):
        return self._scalar


def _price_db(*promotions):
    variant_id, product_id, store_id = uuid4(), uuid4(), uuid4()
    price = {
        "variant_id": variant_id,
        "currency_code": "BDT",
        "selling_price": Decimal("100.00"),
        "compare_at_price": Decimal("120.00"),
        "product_id": product_id,
        "store_id": store_id,
    }
    db = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[
                _Result(row=price),
                _Result(rows=list(promotions)),
            ]
        )
    )
    return db, variant_id, store_id


def test_price_create_rejects_non_bdt_and_invalid_compare_price():
    with pytest.raises(ValidationError):
        PriceCreate(
            variant_id=uuid4(),
            currency_code="USD",
            selling_price=Decimal("10.00"),
        )
    with pytest.raises(ValidationError):
        PriceCreate(
            variant_id=uuid4(),
            selling_price=Decimal("10.00"),
            compare_at_price=Decimal("9.00"),
        )


def test_promotion_normalizes_coupon_and_rejects_over_100_percent():
    promotion = PromotionCreate(
        name="Welcome",
        coupon_code=" welcome10 ",
        discount_type="percentage",
        discount_value=Decimal("10.00"),
        start_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
    )
    assert promotion.coupon_code == "WELCOME10"

    with pytest.raises(ValidationError):
        PromotionCreate(
            name="Invalid",
            discount_type="percentage",
            discount_value=Decimal("100.01"),
            start_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            end_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
        )


@pytest.mark.asyncio
async def test_calculation_uses_best_non_stacking_active_discount():
    db, variant_id, store_id = _price_db(
        {
            "id": uuid4(),
            "coupon_code": None,
            "discount_type": "percentage",
            "discount_value": Decimal("10.00"),
        },
        {
            "id": uuid4(),
            "coupon_code": None,
            "discount_type": "fixed",
            "discount_value": Decimal("20.00"),
        },
        {
            "id": uuid4(),
            "coupon_code": None,
            "discount_type": "fixed",
            "discount_value": Decimal("500.00"),
        },
    )

    result = await PricingService(db).calculate_price(variant_id, store_id)

    assert result.currency_code == "BDT"
    assert result.selling_price == Decimal("100.00")
    assert result.discount_amount == Decimal("100.00")
    assert result.final_price == Decimal("0.00")


@pytest.mark.asyncio
async def test_client_price_validation_reports_tampering():
    db, variant_id, store_id = _price_db()
    from app.modules.pricing.schema import PriceValidationRequest

    result = await PricingService(db).validate_price(
        PriceValidationRequest(
            variant_id=variant_id,
            store_id=store_id,
            provided_price=Decimal("1.00"),
        )
    )

    assert result.valid is False
    assert result.expected_price == Decimal("100.00")
