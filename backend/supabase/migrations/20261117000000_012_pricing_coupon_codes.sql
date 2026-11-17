-- Migration 012: Coupon codes for server-side promotion validation.
-- Additive migration; existing promotions remain automatic promotions.

ALTER TABLE public.promotions
ADD COLUMN coupon_code VARCHAR(50);

CREATE UNIQUE INDEX uq_promotions_coupon_code
ON public.promotions (UPPER(coupon_code))
WHERE coupon_code IS NOT NULL;
