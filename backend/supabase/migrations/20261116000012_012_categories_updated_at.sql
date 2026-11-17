-- Migration 012: Add categories.updated_at (Gap Fix 6)
-- Migration 002 created public.categories but omitted the updated_at column,
-- while every other catalog table (stores, products, carts, orders, etc.)
-- includes it. The categories service queries and writes updated_at, so
-- SELECTs fail with UndefinedColumnError.
-- DO NOT EDIT after applied to any environment.

ALTER TABLE public.categories
    ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE TRIGGER categories_updated_at
    BEFORE UPDATE ON public.categories
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();