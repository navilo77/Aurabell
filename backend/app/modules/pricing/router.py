"""Pricing calculation and administrator pricing endpoints."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import User, require_role
from app.core.database import get_db
from app.modules.pricing.schema import (
    PriceCalculationRead,
    PriceCreate,
    PriceRead,
    PriceCalculationRequest,
    PriceUpdate,
    PriceValidationRead,
    PriceValidationRequest,
    PromotionCreate,
    PromotionProductMap,
    PromotionRead,
    PromotionStoreMap,
    PromotionUpdate,
)
from app.modules.pricing.service import PricingService

router = APIRouter(tags=["Pricing"])


def get_pricing_service(db: AsyncSession = Depends(get_db)) -> PricingService:
    return PricingService(db)


Service = Annotated[PricingService, Depends(get_pricing_service)]


# ─── Admin Price CRUD (store-scoped) ──────────────────────────────────────


@router.post(
    "/admin/prices",
    response_model=PriceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a BDT price for a product variant",
)
async def create_price(data: PriceCreate, service: Service, user: User = Depends(require_role("store_manager", "super_admin"))) -> PriceRead:
    return await service.create_price(data, user)


@router.patch(
    "/admin/prices/{price_id}",
    response_model=PriceRead,
    summary="Update a product variant price",
)
async def update_price(
    price_id: UUID,
    data: PriceUpdate,
    service: Service,
    user: User = Depends(require_role("store_manager", "super_admin")),
) -> PriceRead:
    return await service.update_price(price_id, data, user)


@router.delete(
    "/admin/prices/{price_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a product variant price",
)
async def deactivate_price(price_id: UUID, service: Service, user: User = Depends(require_role("store_manager", "super_admin"))) -> Response:
    await service.deactivate_price(price_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ─── Admin Promotion CRUD (store-scoped via promotion_stores) ────────────────


@router.post(
    "/admin/promotions",
    response_model=PromotionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a promotion or coupon",
)
async def create_promotion(
    data: PromotionCreate,
    service: Service,
    user: User = Depends(require_role("store_manager", "super_admin")),
) -> PromotionRead:
    return await service.create_promotion(data, user)


@router.patch(
    "/admin/promotions/{promotion_id}",
    response_model=PromotionRead,
    summary="Update a promotion or coupon",
)
async def update_promotion(
    promotion_id: UUID,
    data: PromotionUpdate,
    service: Service,
    user: User = Depends(require_role("store_manager", "super_admin")),
) -> PromotionRead:
    return await service.update_promotion(promotion_id, data, user)


@router.delete(
    "/admin/promotions/{promotion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a promotion",
)
async def deactivate_promotion(
    promotion_id: UUID,
    service: Service,
    user: User = Depends(require_role("store_manager", "super_admin")),
) -> Response:
    await service.deactivate_promotion(promotion_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/admin/promotions/{promotion_id}/products",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Apply a promotion to a product",
)
async def add_promotion_product(
    promotion_id: UUID,
    data: PromotionProductMap,
    service: Service,
    user: User = Depends(require_role("store_manager", "super_admin")),
) -> Response:
    await service.add_product_to_promotion(promotion_id, data.product_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/admin/promotions/{promotion_id}/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a product from a promotion",
)
async def remove_promotion_product(
    promotion_id: UUID,
    product_id: UUID,
    service: Service,
    user: User = Depends(require_role("store_manager", "super_admin")),
) -> Response:
    await service.remove_product_from_promotion(promotion_id, product_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/admin/promotions/{promotion_id}/stores",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Apply a promotion to a store",
)
async def add_promotion_store(
    promotion_id: UUID,
    data: PromotionStoreMap,
    service: Service,
    user: User = Depends(require_role("store_manager", "super_admin")),
) -> Response:
    await service.add_store_to_promotion(promotion_id, data.store_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/admin/promotions/{promotion_id}/stores/{store_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a store from a promotion",
)
async def remove_promotion_store(
    promotion_id: UUID,
    store_id: UUID,
    service: Service,
    user: User = Depends(require_role("store_manager", "super_admin")),
) -> Response:
    await service.remove_store_from_promotion(promotion_id, store_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/pricing/calculate",
    response_model=PriceCalculationRead,
    summary="Calculate a variant price with applicable promotions",
)
async def calculate_price(
    service: Service,
    variant_id: UUID,
    store_id: UUID,
    coupon_code: Annotated[str | None, Query(max_length=50)] = None,
) -> PriceCalculationRead:
    request_data = PriceCalculationRequest(
        variant_id=variant_id,
        store_id=store_id,
        coupon_code=coupon_code,
    )
    return await service.calculate_price(
        request_data.variant_id,
        request_data.store_id,
        request_data.coupon_code,
    )


@router.get(
    "/pricing/validate",
    response_model=PriceValidationRead,
    summary="Validate a client-provided price against the current server price",
)
async def validate_price(
    service: Service,
    variant_id: UUID,
    store_id: UUID,
    provided_price: Annotated[Decimal, Query(ge=0, max_digits=12, decimal_places=2)],
    coupon_code: Annotated[str | None, Query(max_length=50)] = None,
) -> PriceValidationRead:
    data = PriceValidationRequest(
        variant_id=variant_id,
        store_id=store_id,
        provided_price=provided_price,
        coupon_code=coupon_code,
    )
    return await service.validate_price(data)
