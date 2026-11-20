-- Migration: 20261120000001_security_cross_store_isolation_rls.sql
-- Tighten Row-Level Security policies to enforce cross-store tenant isolation.
-- Replaces overly-permissive policies on order_items, products, categories.

-- ── order_items: scope access via store_orders → orders/store scoping ──
-- Old policy allowed ANY authenticated user to read/write order_items of ANY
-- store_order (policy only checked store_order existence, not user membership).
-- New policies restrict access to the order owner (customer) or vendors whose
-- store_ids match the store_order's store_id.

DROP POLICY IF EXISTS "Order items access" ON public.order_items;

CREATE POLICY "Order items owner read"
ON public.order_items
FOR SELECT
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.store_orders so
        JOIN public.orders o ON o.id = so.order_id
        WHERE so.id = order_items.store_order_id
          AND o.user_id = auth.uid()
    )
);

CREATE POLICY "Order items vendor CRUD"
ON public.order_items
FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM public.store_orders so
        WHERE so.id = order_items.store_order_id
          AND so.store_id IN (
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
        SELECT 1 FROM public.store_orders so
        WHERE so.id = order_items.store_order_id
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

-- ── products: store-scoped vendor CRUD; customer read active products ──
-- Old policy allowed ANY authenticated user full CRUD on products of ANY store.
-- New policies restrict vendor CRUD to the vendor's own store(s); customers may
-- only SELECT active products.

DROP POLICY IF EXISTS "Store products access" ON public.products;

CREATE POLICY "Products public read active"
ON public.products
FOR SELECT
TO authenticated
USING (status = 'active');

CREATE POLICY "Products vendor CRUD own store"
ON public.products
FOR ALL
TO authenticated
USING (
    products.store_id IN (
        SELECT ur.store_id
        FROM public.user_roles ur
        JOIN public.roles r ON r.id = ur.role_id
        WHERE ur.user_id = auth.uid()
          AND r.name IN ('store_manager', 'admin')
          AND ur.store_id IS NOT NULL
    )
)
WITH CHECK (
    products.store_id IN (
        SELECT ur.store_id
        FROM public.user_roles ur
        JOIN public.roles r ON r.id = ur.role_id
        WHERE ur.user_id = auth.uid()
          AND r.name IN ('store_manager', 'admin')
          AND ur.store_id IS NOT NULL
    )
);

-- ── categories: store-scoped vendor CRUD; customer read ──
-- Same pattern as products.

DROP POLICY IF EXISTS "Store categories access" ON public.categories;

CREATE POLICY "Categories public read"
ON public.categories
FOR SELECT
TO authenticated
USING (is_active = true);

CREATE POLICY "Categories vendor CRUD own store"
ON public.categories
FOR ALL
TO authenticated
USING (
    categories.store_id IN (
        SELECT ur.store_id
        FROM public.user_roles ur
        JOIN public.roles r ON r.id = ur.role_id
        WHERE ur.user_id = auth.uid()
          AND r.name IN ('store_manager', 'admin')
          AND ur.store_id IS NOT NULL
    )
)
WITH CHECK (
    categories.store_id IN (
        SELECT ur.store_id
        FROM public.user_roles ur
        JOIN public.roles r ON r.id = ur.role_id
        WHERE ur.user_id = auth.uid()
          AND r.name IN ('store_manager', 'admin')
          AND ur.store_id IS NOT NULL
    )
);
