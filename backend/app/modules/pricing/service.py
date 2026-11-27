"""Database-backed pricing calculations and administration."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import User
from app.core.exceptions import AuthError
from app.modules.pricing.schema import (
    PriceCalculationRead,
    PriceCreate,
    PriceRead,
    PriceUpdate,
    PriceValidationRead,
    PriceValidationRequest,
    PromotionCreate,
    PromotionRead,
    PromotionUpdate,
)

_CENT = Decimal("0.01")


class PricingError(AuthError):
    """Pricing-domain error carrying the HTTP status used by the router."""

    def __init__(self, message: str, code: str, status_code: int) -> None:
        super().__init__(message=message, code=code)
        self.status_code = status_code


def _money(value: Decimal) -> Decimal:
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


class PricingService:
    """Price, promotion, and server-side validation operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _check_store_access(self, store_id: UUID | str, user: User) -> None:
        """Verify user has access to the store (store_manager must own store; super_admin bypasses)."""
        store_id_str = str(store_id)
        if "super_admin" not in user.roles:
            if "store_manager" in user.roles:
                if store_id_str not in (user.store_ids or []):
                    raise AuthError(
                        message="Access denied to store",
                        code="PERMISSION_DENIED",
                        status_code=403,
                    )
            else:
                raise AuthError(
                    message="Insufficient permissions for store operation",
                    code="PERMISSION_DENIED",
                    status_code=403,
                )

    async def _get_variant_store_id(self, variant_id: UUID) -> UUID | None:
        """Get the store_id for a variant via variant -> product -> store."""
        result = await self.db.execute(
            text("""
                SELECT p.store_id
                FROM public.product_variants v
                JOIN public.products p ON p.id = v.product_id
                WHERE v.id = :variant_id
            """),
            {"variant_id": variant_id},
        )
        return result.scalar_one_or_none()

    async def _get_price_store_id(self, price_id: UUID) -> UUID | None:
        """Get the store_id for a price via price -> variant -> product -> store."""
        result = await self.db.execute(
            text("""
                SELECT p.store_id
                FROM public.product_prices pp
                JOIN public.product_variants v ON v.id = pp.variant_id
                JOIN public.products p ON p.id = v.product_id
                WHERE pp.id = :price_id
            """),
            {"price_id": price_id},
        )
        return result.scalar_one_or_none()

    def _check_store_access_by_variant(self, variant_id: UUID, user: User) -> None:
        """Check store access for a variant's store."""
        store_id = self._get_variant_store_id(variant_id)
        # Note: this is called after the variant check, so we need to run it
        # Actually, let's just pass the user and check inside

    # ─── Price CRUD ──────────────────────────────────────────────────────────

    async def create_price(self, data: PriceCreate, user: User) -> PriceRead:
        # Check store access via variant
        store_id = await self._get_variant_store_id(data.variant_id)
        if store_id is None:
            raise PricingError("Product variant not found", "VARIANT_NOT_FOUND", 404)
        self._check_store_access(store_id, user)

        effective_from = data.effective_from or datetime.now(timezone.utc)
        if data.effective_until is not None and data.effective_until <= effective_from:
            raise PricingError(
                "effective_until must be later than effective_from",
                "INVALID_PRICE_PERIOD",
                422,
            )

        variant = await self.db.execute(
            text("SELECT id FROM public.product_variants WHERE id = :variant_id"),
            {"variant_id": data.variant_id},
        )
        if variant.scalar_one_or_none() is None:
            raise PricingError("Product variant not found", "VARIANT_NOT_FOUND", 404)

        try:
            result = await self.db.execute(
                text("""
                    INSERT INTO public.product_prices
                        (variant_id, currency_code, selling_price, compare_at_price,
                         effective_from, effective_until, is_active)
                    VALUES
                        (:variant_id, :currency_code, :selling_price, :compare_at_price,
                         COALESCE(:effective_from, NOW()), :effective_until, TRUE)
                    RETURNING id, variant_id, currency_code, selling_price, compare_at_price,
                              effective_from, effective_until, is_active, created_at
                """),
                {**data.model_dump(), "effective_from": data.effective_from},
            )
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise PricingError(
                "This variant already has an active price; update or deactivate it first",
                "ACTIVE_PRICE_EXISTS",
                409,
            ) from exc
        return PriceRead.model_validate(result.mappings().one())

    async def update_price(self, price_id: UUID, data: PriceUpdate, user: User) -> PriceRead:
        store_id = await self._get_price_store_id(price_id)
        if store_id is None:
            raise PricingError("Price not found", "PRICE_NOT_FOUND", 404)
        self._check_store_access(store_id, user)

        current = await self._get_price(price_id)
        changes = data.model_dump(exclude_unset=True)
        selling_price = changes.get("selling_price", current["selling_price"])
        compare_at_price = changes.get("compare_at_price", current["compare_at_price"])
        effective_from = changes.get("effective_from", current["effective_from"])
        effective_until = changes.get("effective_until", current["effective_until"])

        if compare_at_price is not None and compare_at_price < selling_price:
            raise PricingError(
                "compare_at_price must be greater than or equal to selling_price",
                "INVALID_PRICE_RANGE",
                422,
            )
        if effective_until is not None and effective_until <= effective_from:
            raise PricingError(
                "effective_until must be later than effective_from",
                "INVALID_PRICE_PERIOD",
                422,
            )

        set_clause = ", ".join(f"{key} = :{key}" for key in changes)
        result = await self.db.execute(
            text(f"""
                UPDATE public.product_prices
                SET {set_clause}
                WHERE id = :price_id
                RETURNING id, variant_id, currency_code, selling_price, compare_at_price,
                          effective_from, effective_until, is_active, created_at
            """),
            {"price_id": price_id, **changes},
        )
        row = result.mappings().one_or_none()
        if row is None:
            raise PricingError("Price not found", "PRICE_NOT_FOUND", 404)
        await self.db.commit()
        return PriceRead.model_validate(row)

    async def deactivate_price(self, price_id: UUID, user: User) -> None:
        store_id = await self._get_price_store_id(price_id)
        if store_id is None:
            raise PricingError("Active price not found", "PRICE_NOT_FOUND", 404)
        self._check_store_access(store_id, user)

        result = await self.db.execute(
            text("""
                UPDATE public.product_prices
                SET is_active = FALSE
                WHERE id = :price_id AND is_active = TRUE
                RETURNING id
            """),
            {"price_id": price_id},
        )
        if result.scalar_one_or_none() is None:
            raise PricingError("Active price not found", "PRICE_NOT_FOUND", 404)
        await self.db.commit()

    async def _get_price(self, price_id: UUID):
        result = await self.db.execute(
            text("""
                SELECT id, variant_id, currency_code, selling_price, compare_at_price,
                       effective_from, effective_until, is_active, created_at
                FROM public.product_prices
                WHERE id = :price_id
            """),
            {"price_id": price_id},
        )
        row = result.mappings().one_or_none()
        if row is None:
            raise PricingError("Price not found", "PRICE_NOT_FOUND", 404)
        return row

    # ─── Promotion CRUD ──────────────────────────────────────────────────────

    async def _check_promotion_store_access(self, promotion_id: UUID, user: User) -> None:
        """Check if user has access to at least one store mapped to the promotion."""
        result = await self.db.execute(
            text("""
                SELECT ps.store_id
                FROM public.promotion_stores ps
                WHERE ps.promotion_id = :promotion_id
            """),
            {"promotion_id": promotion_id},
        )
        store_ids = [str(row[0]) for row in result.fetchall()]
        if not store_ids:
            # Promotion not mapped to any store - only super_admin can manage
            if "super_admin" not in user.roles:
                raise AuthError(
                    message="Promotion not mapped to any accessible store",
                    code="PERMISSION_DENIED",
                    status_code=403,
                )
            return
        # Check if user has access to at least one of the promotion's stores
        if "super_admin" not in user.roles:
            if "store_manager" in user.roles:
                user_store_ids = set(user.store_ids or [])
                if not user_store_ids.intersection(store_ids):
                    raise AuthError(
                        message="Access denied to promotion's stores",
                        code="PERMISSION_DENIED",
                        status_code=403,
                    )
            else:
                raise AuthError(
                    message="Insufficient permissions for promotion operation",
                    code="PERMISSION_DENIED",
                    status_code=403,
                )

    async def create_promotion(self, data: PromotionCreate, user: User) -> PromotionRead:
        try:
            result = await self.db.execute(
                text("""
                    INSERT INTO public.promotions
                        (name, coupon_code, discount_type, discount_value,
                         start_at, end_at, is_active)
                    VALUES
                        (:name, :coupon_code, :discount_type, :discount_value,
                         :start_at, :end_at, :is_active)
                    RETURNING id, name, coupon_code, discount_type, discount_value,
                              start_at, end_at, is_active
                """),
                data.model_dump(),
            )
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise PricingError(
                "A promotion with this coupon code already exists",
                "DUPLICATE_COUPON_CODE",
                409,
            ) from exc
        return PromotionRead.model_validate(result.mappings().one())

    async def update_promotion(self, promotion_id: UUID, data: PromotionUpdate, user: User) -> PromotionRead:
        self._check_promotion_store_access(promotion_id, user)

        current_result = await self.db.execute(
            text("""
                SELECT id, name, coupon_code, discount_type, discount_value, start_at, end_at, is_active
                FROM public.promotions
                WHERE id = :promotion_id
            """),
            {"promotion_id": promotion_id},
        )
        current = current_result.mappings().one_or_none()
        if current is None:
            raise PricingError("Promotion not found", "PROMOTION_NOT_FOUND", 404)

        changes = data.model_dump(exclude_unset=True)
        discount_type = changes.get("discount_type", current["discount_type"])
        discount_value = changes.get("discount_value", current["discount_value"])
        start_at = changes.get("start_at", current["start_at"])
        end_at = changes.get("end_at", current["end_at"])
        if discount_type == "percentage" and discount_value > 100:
            raise PricingError("Percentage discount cannot exceed 100", "INVALID_DISCOUNT", 422)
        if end_at <= start_at:
            raise PricingError("end_at must be later than start_at", "INVALID_PROMOTION_PERIOD", 422)

        set_clause = ", ".join(f"{key} = :{key}" for key in changes)
        try:
            result = await self.db.execute(
                text(f"""
                    UPDATE public.promotions
                    SET {set_clause}
                    WHERE id = :promotion_id
                    RETURNING id, name, coupon_code, discount_type, discount_value,
                              start_at, end_at, is_active
                """),
                {"promotion_id": promotion_id, **changes},
            )
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise PricingError(
                "A promotion with this coupon code already exists",
                "DUPLICATE_COUPON_CODE",
                409,
            ) from exc
        return PromotionRead.model_validate(result.mappings().one())

    async def deactivate_promotion(self, promotion_id: UUID, user: User) -> None:
        self._check_promotion_store_access(promotion_id, user)

        result = await self.db.execute(
            text("""
                UPDATE public.promotions
                SET is_active = FALSE
                WHERE id = :promotion_id AND is_active = TRUE
                RETURNING id
            """),
            {"promotion_id": promotion_id},
        )
        if result.scalar_one_or_none() is None:
            raise PricingError("Active promotion not found", "PROMOTION_NOT_FOUND", 404)
        await self.db.commit()

    async def add_store_to_promotion(self, promotion_id: UUID, store_id: UUID, user: User) -> None:
        self._check_store_access(store_id, user)
        await self._add_mapping(
            promotion_id,
            store_id,
            target_table="promotion_stores",
            target_column="store_id",
            target_table_name="stores",
        )

    async def remove_store_from_promotion(self, promotion_id: UUID, store_id: UUID, user: User) -> None:
        self._check_store_access(store_id, user)
        self._check_promotion_store_access(promotion_id, user)
        await self._remove_mapping(
            promotion_id,
            store_id,
            target_table="promotion_stores",
            target_column="store_id",
        )

    async def add_product_to_promotion(self, promotion_id: UUID, product_id: UUID, user: User) -> None:
        await self._check_promotion_store_access(promotion_id, user)
        await self._add_mapping(
            promotion_id,
            product_id,
            target_table="promotion_products",
            target_column="product_id",
            target_table_name="products",
        )

    async def remove_product_from_promotion(self, promotion_id: UUID, product_id: UUID, user: User) -> None:
        await self._check_promotion_store_access(promotion_id, user)
        await self._remove_mapping(
            promotion_id,
            product_id,
            target_table="promotion_products",
            target_column="product_id",
        )

    async def _add_mapping(
        self,
        promotion_id: UUID,
        target_id: UUID,
        *,
        target_table: str,
        target_column: str,
        target_table_name: str,
    ) -> None:
        promotion = await self.db.execute(
            text("SELECT id FROM public.promotions WHERE id = :promotion_id"),
            {"promotion_id": promotion_id},
        )
        if promotion.scalar_one_or_none() is None:
            raise PricingError("Promotion not found", "PROMOTION_NOT_FOUND", 404)
        target = await self.db.execute(
            text(f"SELECT id FROM public.{target_table_name} WHERE id = :target_id"),
            {"target_id": target_id},
        )
        if target.scalar_one_or_none() is None:
            raise PricingError(
                f"{target_table_name[:-1].capitalize()} not found",
                f"{target_table_name[:-1].upper()}_NOT_FOUND",
                404,
            )
        existing = await self.db.execute(
            text(f"""
                SELECT 1 FROM public.{target_table}
                WHERE promotion_id = :promotion_id AND {target_column} = :target_id
            """),
            {"promotion_id": promotion_id, "target_id": target_id},
        )
        if existing.scalar_one_or_none() is not None:
            raise PricingError("Promotion mapping already exists", "MAPPING_EXISTS", 409)
        try:
            await self.db.execute(
                text(f"""
                    INSERT INTO public.{target_table} (promotion_id, {target_column})
                    VALUES (:promotion_id, :target_id)
                """),
                {"promotion_id": promotion_id, "target_id": target_id},
            )
        except IntegrityError as exc:
            await self.db.rollback()
            raise PricingError(
                "Promotion mapping conflicts with an existing or removed record",
                "MAPPING_CONFLICT",
                409,
            ) from exc
        await self.db.commit()

    async def _remove_mapping(
        self,
        promotion_id: UUID,
        target_id: UUID,
        *,
        target_table: str,
        target_column: str,
    ) -> None:
        result = await self.db.execute(
            text(f"""
                DELETE FROM public.{target_table}
                WHERE promotion_id = :promotion_id AND {target_column} = :target_id
                RETURNING promotion_id
            """),
            {"promotion_id": promotion_id, "target_id": target_id},
        )
        if result.scalar_one_or_none() is None:
            raise PricingError("Promotion mapping not found", "MAPPING_NOT_FOUND", 404)
        await self.db.commit()

    # ─── Price Calculation & Validation ──────────────────────────────────────

    async def calculate_price(
        self,
        variant_id: UUID,
        store_id: UUID,
        coupon_code: str | None = None,
    ) -> PriceCalculationRead:
        price_result = await self.db.execute(
            text("""
                SELECT pp.variant_id, pp.currency_code, pp.selling_price, pp.compare_at_price,
                       p.id AS product_id, p.store_id
                FROM public.product_prices AS pp
                JOIN public.product_variants AS v ON v.id = pp.variant_id
                JOIN public.products AS p ON p.id = v.product_id
                WHERE pp.variant_id = :variant_id
                  AND pp.currency_code = 'BDT'
                  AND pp.is_active = TRUE
                  AND pp.effective_from <= NOW()
                  AND (pp.effective_until IS NULL OR pp.effective_until > NOW())
                  AND v.is_active = TRUE
                  AND p.status = 'active'
                  AND p.store_id = :store_id
                ORDER BY pp.effective_from DESC
                LIMIT 1
            """),
            {"variant_id": variant_id, "store_id": store_id},
        )
        price = price_result.mappings().one_or_none()
        if price is None:
            raise PricingError(
                "No active BDT price is available for this variant and store",
                "PRICE_NOT_FOUND",
                404,
            )

        promotion_result = await self.db.execute(
            text("""
                SELECT promo.id, promo.coupon_code, promo.discount_type, promo.discount_value
                FROM public.promotions AS promo
                WHERE promo.is_active = TRUE
                  AND promo.start_at <= NOW()
                  AND promo.end_at > NOW()
                  AND (
                      (CAST(:coupon_code AS VARCHAR) IS NULL AND promo.coupon_code IS NULL)
                      OR (
                          CAST(:coupon_code AS VARCHAR) IS NOT NULL
                          AND UPPER(promo.coupon_code) = CAST(:coupon_code AS VARCHAR)
                      )
                  )
                  AND (
                      NOT EXISTS (
                          SELECT 1 FROM public.promotion_products AS pp_map
                          WHERE pp_map.promotion_id = promo.id
                      )
                      OR EXISTS (
                          SELECT 1 FROM public.promotion_products AS pp_map
                          WHERE pp_map.promotion_id = promo.id
                            AND pp_map.product_id = :product_id
                      )
                  )
                  AND (
                      NOT EXISTS (
                          SELECT 1 FROM public.promotion_stores AS ps_map
                          WHERE ps_map.promotion_id = promo.id
                      )
                      OR EXISTS (
                          SELECT 1 FROM public.promotion_stores AS ps_map
                          WHERE ps_map.promotion_id = promo.id
                            AND ps_map.store_id = :store_id
                      )
                  )
                ORDER BY promo.id
            """),
            {
                "coupon_code": coupon_code,
                "product_id": price["product_id"],
                "store_id": store_id,
            },
        )
        promotions = promotion_result.mappings().all()
        if coupon_code and not promotions:
            raise PricingError(
                "Coupon code is invalid, expired, inactive, or not applicable",
                "INVALID_PROMOTION",
                422,
            )

        selling_price = _money(Decimal(price["selling_price"]))
        best_promotion = None
        discount_amount = Decimal("0.00")
        for promotion in promotions:
            value = Decimal(promotion["discount_value"])
            discount = (
                selling_price * value / Decimal("100")
                if promotion["discount_type"] == "percentage"
                else value
            )
            discount = min(_money(discount), selling_price)
            if best_promotion is None or discount > discount_amount:
                discount_amount = discount
                best_promotion = promotion

        return PriceCalculationRead(
            variant_id=price["variant_id"],
            store_id=price["store_id"],
            currency_code="BDT",
            selling_price=selling_price,
            compare_at_price=price["compare_at_price"],
            discount_amount=discount_amount,
            final_price=_money(selling_price - discount_amount),
            promotion_id=best_promotion["id"] if best_promotion else None,
            coupon_code=best_promotion["coupon_code"] if best_promotion else None,
        )

    async def validate_price(self, data: PriceValidationRequest) -> PriceValidationRead:
        calculation = await self.calculate_price(data.variant_id, data.store_id, data.coupon_code)
        provided_price = _money(data.provided_price)
        return PriceValidationRead(
            valid=provided_price == calculation.final_price,
            expected_price=calculation.final_price,
            provided_price=provided_price,
            promotion_id=calculation.promotion_id,
            coupon_code=calculation.coupon_code,
        )
