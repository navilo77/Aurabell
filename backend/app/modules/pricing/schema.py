"""Request and response schemas for pricing and promotions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Money = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
PositiveMoney = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


def _normalize_coupon_code(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    if not normalized or len(normalized) > 50:
        raise ValueError("Coupon code must contain between 1 and 50 characters")
    if not all(char.isascii() and (char.isalnum() or char in "_-") for char in normalized):
        raise ValueError("Coupon code may contain only letters, numbers, underscores, and hyphens")
    return normalized


def _require_timezone(value: datetime | None) -> datetime | None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError("Datetime values must include a timezone")
    return value


class PriceCreate(BaseModel):
    variant_id: UUID
    currency_code: Literal["BDT"] = "BDT"
    selling_price: Money
    compare_at_price: Money | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None

    @field_validator("effective_from", "effective_until")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        return _require_timezone(value)

    @model_validator(mode="after")
    def validate_prices_and_period(self) -> PriceCreate:
        if self.compare_at_price is not None and self.compare_at_price < self.selling_price:
            raise ValueError("compare_at_price must be greater than or equal to selling_price")
        if (
            self.effective_from is not None
            and self.effective_until is not None
            and self.effective_until <= self.effective_from
        ):
            raise ValueError("effective_until must be later than effective_from")
        return self


class PriceUpdate(BaseModel):
    selling_price: Money | None = None
    compare_at_price: Money | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None

    @field_validator("effective_from", "effective_until")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        return _require_timezone(value)

    @model_validator(mode="after")
    def require_update(self) -> PriceUpdate:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        if any(
            getattr(self, field) is None
            for field in ("selling_price", "effective_from")
            if field in self.model_fields_set
        ):
            raise ValueError("Non-nullable price fields cannot be null")
        if (
            self.compare_at_price is not None
            and self.selling_price is not None
            and self.compare_at_price < self.selling_price
        ):
            raise ValueError("compare_at_price must be greater than or equal to selling_price")
        if (
            self.effective_from is not None
            and self.effective_until is not None
            and self.effective_until <= self.effective_from
        ):
            raise ValueError("effective_until must be later than effective_from")
        return self


class PriceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    variant_id: UUID
    currency_code: str
    selling_price: Decimal
    compare_at_price: Decimal | None
    effective_from: datetime
    effective_until: datetime | None
    is_active: bool
    created_at: datetime


class PromotionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    coupon_code: str | None = Field(default=None, max_length=50)
    discount_type: Literal["percentage", "fixed"]
    discount_value: PositiveMoney
    start_at: datetime
    end_at: datetime
    is_active: bool = True

    @field_validator("start_at", "end_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Datetime values must include a timezone")
        return value

    @field_validator("coupon_code")
    @classmethod
    def normalize_coupon_code(cls, value: str | None) -> str | None:
        return _normalize_coupon_code(value)

    @model_validator(mode="after")
    def validate_period_and_discount(self) -> PromotionCreate:
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be later than start_at")
        if self.discount_type == "percentage" and self.discount_value > 100:
            raise ValueError("percentage discount cannot exceed 100")
        return self


class PromotionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    coupon_code: str | None = Field(default=None, max_length=50)
    discount_type: Literal["percentage", "fixed"] | None = None
    discount_value: PositiveMoney | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    is_active: bool | None = None

    @field_validator("start_at", "end_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        return _require_timezone(value)

    @field_validator("coupon_code")
    @classmethod
    def normalize_coupon_code(cls, value: str | None) -> str | None:
        return _normalize_coupon_code(value)

    @model_validator(mode="after")
    def require_update(self) -> PromotionUpdate:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        if any(
            getattr(self, field) is None
            for field in ("name", "discount_type", "discount_value", "start_at", "end_at", "is_active")
            if field in self.model_fields_set
        ):
            raise ValueError("Non-nullable promotion fields cannot be null")
        if (
            self.discount_type == "percentage"
            and self.discount_value is not None
            and self.discount_value > 100
        ):
            raise ValueError("percentage discount cannot exceed 100")
        if (
            self.start_at is not None
            and self.end_at is not None
            and self.end_at <= self.start_at
        ):
            raise ValueError("end_at must be later than start_at")
        return self


class PromotionRead(BaseModel):
    id: UUID
    name: str
    coupon_code: str | None
    discount_type: str
    discount_value: Decimal
    start_at: datetime
    end_at: datetime
    is_active: bool


class PromotionProductMap(BaseModel):
    product_id: UUID


class PromotionStoreMap(BaseModel):
    store_id: UUID


class PriceCalculationRequest(BaseModel):
    variant_id: UUID
    store_id: UUID
    coupon_code: str | None = Field(default=None, max_length=50)

    @field_validator("coupon_code")
    @classmethod
    def normalize_coupon_code(cls, value: str | None) -> str | None:
        return _normalize_coupon_code(value)


class PriceCalculationRead(BaseModel):
    variant_id: UUID
    store_id: UUID
    currency_code: Literal["BDT"]
    selling_price: Decimal
    compare_at_price: Decimal | None
    discount_amount: Decimal
    final_price: Decimal
    promotion_id: UUID | None
    coupon_code: str | None


class PriceValidationRequest(PriceCalculationRequest):
    provided_price: Money


class PriceValidationRead(BaseModel):
    valid: bool
    expected_price: Decimal
    provided_price: Decimal
    currency_code: Literal["BDT"] = "BDT"
    promotion_id: UUID | None
