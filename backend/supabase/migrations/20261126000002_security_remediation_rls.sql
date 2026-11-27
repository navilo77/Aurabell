-- Migration: 20261126000002_security_remediation_rls.sql
-- Security Remediation: Cross-Store Isolation RLS Policies
-- Adds RLS policies for store_policies, product_variants, product_prices,
-- payments, promotions, and promotion_stores to enforce cross-store access control.

-- Enable RLS on tables that don't have it yet
ALTER TABLE public.store_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_prices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.promotions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.promotion_stores ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- STORE_POLICIES: Direct store-scoped (store_policies.store_id)
-- =============================================================================

-- Customers can read active policies for any store
CREATE POLICY "Store policies public read active"
ON public.store_policies
FOR SELECT
TO authenticated
USING (is_active = true);

-- Vendors (store_manager/admin) can CRUD policies for their own stores
CREATE POLICY "Store policies vendor CRUD own store"
ON public.store_policies
FOR ALL
TO authenticated
USING (
    store_policies.store_id IN (
        SELECT ur.store_id
        FROM public.user_roles ur
        JOIN public.roles r ON r.id = ur.role_id
        WHERE ur.user_id = auth.uid()
          AND r.name IN ('store_manager', 'admin')
          AND ur.store_id IS NOT NULL
    )
)
WITH CHECK (
    store_policies.store_id IN (
        SELECT ur.store_id
        FROM public.user_roles ur
        JOIN public.roles r ON r.id = ur.role_id
        WHERE ur.user_id = auth.uid()
          AND r.name IN ('store_manager', 'admin')
          AND ur.store_id IS NOT NULL
    )
);

-- =============================================================================
-- PRODUCT_VARIANTS: Indirect store-scoped via product_variants.product_id → products.store_id
-- =============================================================================

-- Customers can read active variants (for active products)
CREATE POLICY "Product variants public read active"
ON public.product_variants
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.products p
        WHERE p.id = product_variants.product_id
          AND p.status = 'active'
          AND p.store_id IN (
              SELECT s.id FROM public.stores s WHERE s.status = 'active'
          )
    )
);

-- Vendors can CRUD variants for products in their own stores
CREATE POLICY "Product variants vendor CRUD own store"
ON public.product_variants
FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.products p
        WHERE p.id = product_variants.product_id
          AND p.store_id IN (
              SELECT ur.store_id
              FROM public.user_roles ur
              JOIN public.roles r ON r.id = ur.role_id
              WHERE ur.user_id = auth.uid()
                AND r.name IN ('store_manager', 'admin')
                AND ur.store_id IS NOT NULL
          )
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.products p
        WHERE p.id = product_variants.product_id
          AND p.store_id IN (
              SELECT ur.store_id
              FROM public.user_roles ur
              JOIN public.roles r ON r.id = ur.role_id
              WHERE ur.user_id = auth.uid()
                AND r.name IN ('store_manager', 'admin')
                AND ur.store_id IS NOT NULL
          )
    )
);

-- =============================================================================
-- PRODUCT_PRICES: Indirect store-scoped via variant → product → store
-- =============================================================================

-- Customers can read active prices for active variants of active products
CREATE POLICY "Product prices public read active"
ON public.product_prices
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.product_variants pv
        JOIN public.products p ON p.id = pv.product_id
        WHERE pv.id = product_prices.variant_id
          AND pv.is_active = true
          AND p.status = 'active'
          AND p.store_id IN (
              SELECT s.id FROM public.stores s WHERE s.status = 'active'
          )
    )
);

-- Vendors can CRUD prices for variants in their own stores
CREATE POLICY "Product prices vendor CRUD own store"
ON public.product_prices
FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.product_variants pv
        JOIN public.products p ON p.id = pv.product_id
        WHERE pv.id = product_prices.variant_id
          AND p.store_id IN (
              SELECT ur.store_id
              FROM public.user_roles ur
              JOIN public.roles r ON r.id = ur.role_id
              WHERE ur.user_id = auth.uid()
                AND r.name IN ('store_manager', 'admin')
                AND ur.store_id IS NOT NULL
          )
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.product_variants pv
        JOIN public.products p ON p.id = pv.product_id
        WHERE pv.id = product_prices.variant_id
          AND p.store_id IN (
              SELECT ur.store_id
              FROM public.user_roles ur
              JOIN public.roles r ON r.id = ur.role_id
              WHERE ur.user_id = auth.uid()
                AND r.name IN ('store_manager', 'admin')
                AND ur.store_id IS NOT NULL
          )
    )
);

-- =============================================================================
-- PAYMENTS: Order-level via payment → order → store_orders → store_id
-- =============================================================================

-- Customers can read their own payments (via order ownership)
CREATE POLICY "Payments customer read own"
ON public.payments
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.orders o
        WHERE o.id = payments.order_id
          AND o.user_id = auth.uid()
    )
);

-- Store vendors can read payments for orders in their stores (via store_orders)
CREATE POLICY "Payments vendor read own store orders"
ON public.payments
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.store_orders so
        WHERE so.order_id = payments.order_id
          AND so.store_id IN (
              SELECT ur.store_id
              FROM public.user_roles ur
              JOIN public.roles r ON r.id = ur.role_id
              WHERE ur.user_id = auth.uid()
                AND r.name IN ('store_manager', 'admin')
                AND ur.store_id IS NOT NULL
          )
    )
);

-- Platform/super_admin can manage payments (INSERT/UPDATE/DELETE) - restricted to super_admin
-- Note: Payments are typically created via payment gateway callbacks, not direct vendor CRUD
CREATE POLICY "Payments platform manage"
ON public.payments
FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.user_roles ur
        JOIN public.roles r ON r.id = ur.role_id
        WHERE ur.user_id = auth.uid()
          AND r.name IN ('super_admin', 'owner')
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.user_roles ur
        JOIN public.roles r ON r.id = ur.role_id
        WHERE ur.user_id = auth.uid()
          AND r.name IN ('super_admin', 'owner')
    )
);

-- =============================================================================
-- PROMOTIONS: Store-scoped via promotion_stores.store_id mapping
-- =============================================================================

-- Customers can read active promotions (for applicable stores)
-- Note: Promotion applicability is checked at price calculation time
CREATE POLICY "Promotions public read active"
ON public.promotions
FOR SELECT
TO authenticated
USING (
    is_active = true
    AND start_at <= NOW()
    AND end_at > NOW()
);

-- Vendors can CRUD promotions that are mapped to their stores
CREATE POLICY "Promotions vendor CRUD own store"
ON public.promotions
FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.promotion_stores ps
        WHERE ps.promotion_id = promotions.id
          AND ps.store_id IN (
              SELECT ur.store_id
              FROM public.user_roles ur
              JOIN public.roles r ON r.id = ur.role_id
              WHERE ur.user_id = auth.uid()
                AND r.name IN ('store_manager', 'admin')
                AND ur.store_id IS NOT NULL
          )
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.promotion_stores ps
        WHERE ps.promotion_id = promotions.id
          AND ps.store_id IN (
              SELECT ur.store_id
              FROM public.user_roles ur
              JOIN public.roles r ON r.id = ur.role_id
              WHERE ur.user_id = auth.uid()
                AND r.name IN ('store_manager', 'admin')
                AND ur.store_id IS NOT NULL
          )
    )
);

-- =============================================================================
-- PROMOTION_STORES: Store-scoped mapping table
-- =============================================================================

-- Customers can read promotion-store mappings (for applicable promotions)
CREATE POLICY "Promotion stores public read"
ON public.promotion_stores
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.promotions p
        WHERE p.id = promotion_stores.promotion_id
          AND p.is_active = true
          AND p.start_at <= NOW()
          AND p.end_at > NOW()
    )
);

-- Vendors can manage promotion-store mappings for their own stores
CREATE POLICY "Promotion stores vendor manage own store"
ON public.promotion_stores
FOR ALL
TO authenticated
USING (
    promotion_stores.store_id IN (
        SELECT ur.store_id
        FROM public.user_roles ur
        JOIN public.roles r ON r.id = ur.role_id
        WHERE ur.user_id = auth.uid()
          AND r.name IN ('store_manager', 'admin')
          AND ur.store_id IS NOT NULL
    )
)
WITH CHECK (
    promotion_stores.store_id IN (
        SELECT ur.store_id
        FROM public.user_roles ur
        JOIN public.roles r ON r.id = ur.role_id
        WHERE ur.user_id = auth.uid()
          AND r.name IN ('store_manager', 'admin')
          AND ur.store_id IS NOT NULL
    )
);