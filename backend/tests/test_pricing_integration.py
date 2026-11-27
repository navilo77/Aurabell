"""Database integration coverage for the pricing milestone."""

from __future__ import annotations

import os
import socket
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import User, require_role
from app.modules.pricing.schema import PriceCreate, PromotionCreate
from app.modules.pricing.service import PricingError, PricingService

def _local_database_available() -> bool:
    url = make_url(
        os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@127.0.0.1:54330/postgres",
        )
    )
    if url.host not in {"localhost", "127.0.0.1", "::1"}:
        return False
    try:
        with socket.create_connection((url.host or "127.0.0.1", url.port or 5432), timeout=1):
            return True
    except OSError:
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _local_database_available(), reason="Local PostgreSQL is unavailable"),
]


@pytest.mark.asyncio
async def test_price_coupon_scopes_duplicate_code_and_admin_permission(
    db_session: AsyncSession,
    platform_admin_user: User,
) -> None:
    suffix = uuid4().hex
    store_ids: list[UUID] = []
    product_ids: list[UUID] = []
    variant_ids: list[UUID] = []
    promotion_ids: list[UUID] = []
    service = PricingService(db_session)

    try:
        for suffix_part in ("a", "b"):
            result = await db_session.execute(
                text("""
                    INSERT INTO public.stores (name, slug)
                    VALUES (:name, :slug)
                    RETURNING id
                """),
                {"name": f"Pricing {suffix_part} {suffix}", "slug": f"pricing-{suffix_part}-{suffix}"},
            )
            store_ids.append(result.scalar_one())

        for index, store_id in enumerate((store_ids[0], store_ids[0], store_ids[1])):
            product_result = await db_session.execute(
                text("""
                    INSERT INTO public.products (store_id, name, slug, status)
                    VALUES (:store_id, :name, :slug, 'active')
                    RETURNING id
                """),
                {
                    "store_id": store_id,
                    "name": f"Pricing product {index} {suffix}",
                    "slug": f"pricing-product-{index}-{suffix}",
                },
            )
            product_id = product_result.scalar_one()
            product_ids.append(product_id)
            variant_result = await db_session.execute(
                text("""
                    INSERT INTO public.product_variants (product_id, sku)
                    VALUES (:product_id, :sku)
                    RETURNING id
                """),
                {"product_id": product_id, "sku": f"pricing-{index}-{suffix}"},
            )
            variant_id = variant_result.scalar_one()
            variant_ids.append(variant_id)

        await db_session.commit()
        for variant_id in variant_ids:
            await service.create_price(
                PriceCreate(
                    variant_id=variant_id,
                    selling_price=Decimal("100.00"),
                    compare_at_price=Decimal("120.00"),
                ),
                platform_admin_user,
            )

        now = datetime.now(timezone.utc)
        promotion = await service.create_promotion(
            PromotionCreate(
                name=f"Scoped coupon {suffix}",
                coupon_code=f"SAVE-{suffix[:12]}",
                discount_type="percentage",
                discount_value=Decimal("15.00"),
                start_at=now - timedelta(hours=1),
                end_at=now + timedelta(hours=1),
            ),
            platform_admin_user,
        )
        promotion_ids.append(promotion.id)
        await service.add_product_to_promotion(promotion.id, product_ids[0], platform_admin_user)
        await service.add_store_to_promotion(promotion.id, store_ids[0], platform_admin_user)

        price = await service.calculate_price(
            variant_ids[0],
            store_ids[0],
            promotion.coupon_code,
        )
        assert price.currency_code == "BDT"
        assert price.selling_price == Decimal("100.00")
        assert price.final_price == Decimal("85.00")

        with pytest.raises(PricingError, match="invalid, expired"):
            await service.calculate_price(variant_ids[1], store_ids[0], promotion.coupon_code)
        with pytest.raises(PricingError, match="invalid, expired"):
            await service.calculate_price(variant_ids[2], store_ids[1], promotion.coupon_code)

        expired = await service.create_promotion(
            PromotionCreate(
                name=f"Expired coupon {suffix}",
                coupon_code=f"OLD-{suffix[:12]}",
                discount_type="fixed",
                discount_value=Decimal("10.00"),
                start_at=now - timedelta(days=2),
                end_at=now - timedelta(days=1),
            ),
            platform_admin_user,
        )
        promotion_ids.append(expired.id)
        with pytest.raises(PricingError, match="invalid, expired"):
            await service.calculate_price(variant_ids[0], store_ids[0], expired.coupon_code)

        with pytest.raises(PricingError) as duplicate:
            await service.create_promotion(
                PromotionCreate(
                    name=f"Duplicate coupon {suffix}",
                    coupon_code=promotion.coupon_code,
                    discount_type="fixed",
                    discount_value=Decimal("5.00"),
                    start_at=now - timedelta(hours=1),
                    end_at=now + timedelta(hours=1),
                ),
                platform_admin_user,
            )
        assert duplicate.value.code == "DUPLICATE_COUPON_CODE"

        checker = require_role("admin", "owner")
        # Mock request for require_role
        from unittest.mock import MagicMock
        mock_request = MagicMock()
        await checker(request=mock_request, user=User(id="admin-id", email="admin@example.com", roles=["admin"]))
        with pytest.raises(HTTPException) as denied:
            await checker(request=mock_request, user=User(id="customer-id", email="customer@example.com", roles=["customer"]))
        assert denied.value.status_code == 403
    finally:
        await db_session.rollback()
        for variant_id in variant_ids:
            await db_session.execute(
                text("DELETE FROM public.product_prices WHERE variant_id = :variant_id"),
                {"variant_id": variant_id},
            )
            await db_session.execute(
                text("DELETE FROM public.product_variants WHERE id = :variant_id"),
                {"variant_id": variant_id},
            )
        for promotion_id in promotion_ids:
            await db_session.execute(
                text("DELETE FROM public.promotions WHERE id = :promotion_id"),
                {"promotion_id": promotion_id},
            )
        for product_id in product_ids:
            await db_session.execute(
                text("DELETE FROM public.products WHERE id = :product_id"),
                {"product_id": product_id},
            )
        for store_id in store_ids:
            await db_session.execute(
                text("DELETE FROM public.stores WHERE id = :store_id"),
                {"store_id": store_id},
            )
        await db_session.commit()
