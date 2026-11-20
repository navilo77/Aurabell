-- Migration: 20261117180011_secure_remaining_unrestricted_tables
-- Secure the remaining 6 unrestricted tables in the public schema
-- Ensures proper RLS enforcement for e-commerce operations

-- ── Enable RLS on all 6 tables ──────────────────────────────────────────--

ALTER TABLE public.stores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.store_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_attributes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.promotion_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.promotion_stores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.store_policies ENABLE ROW LEVEL SECURITY;

-- ── Drop existing overly-permissive policies ──────────────────────────────

DROP POLICY IF EXISTS "Read-only access to stores" ON public.stores;
DROP POLICY IF EXISTS "Store orders access" ON public.store_orders;

-- ── Stores policies ──────────────────────────────────────────────────────

-- Public/Anonymous: can only SELECT (browse store info)
CREATE POLICY "Stores public read" ON public.stores
    FOR SELECT TO anon USING (true);

-- Store Managers: can UPDATE their own store (store_id matches their role)
CREATE POLICY "Stores store manager UPDATE" ON public.stores
    FOR UPDATE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'store_manager'
              AND ur.store_id = stores.id
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'store_manager'
              AND ur.store_id = stores.id
        )
    );

-- Admins: can do everything on stores
CREATE POLICY "Stores admin ALL" ON public.stores
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'admin'
        )
    );

-- ── Store Orders policies ─────────────────────────────────────────────────

-- Users can SELECT their own orders (linked order's user_id matches authenticated user)
CREATE POLICY "Store orders user read" ON public.store_orders
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.orders o
            WHERE o.id = store_orders.order_id
              AND o.user_id = auth.uid()
        )
    );

-- Store Managers: can SELECT/UPDATE orders for their store
CREATE POLICY "Store orders store manager CRUD" ON public.store_orders
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'store_manager'
              AND ur.store_id = store_orders.store_id
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'store_manager'
              AND ur.store_id = store_orders.store_id
        )
    );

-- Admins: can do everything on store_orders
CREATE POLICY "Store orders admin ALL" ON public.store_orders
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'admin'
        )
    );

-- ── Product Attributes policies ───────────────────────────────────────────

-- Public/Anonymous: can only SELECT (browse product attributes)
CREATE POLICY "Product attributes public read" ON public.product_attributes
    FOR SELECT TO anon USING (true);

-- Store Managers: can CRUD attributes where product's store_id matches their store
CREATE POLICY "Product attributes store manager CRUD" ON public.product_attributes
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.products p
            WHERE p.id = product_attributes.product_id
              AND EXISTS (
                  SELECT 1 FROM public.user_roles ur
                  JOIN public.roles r ON ur.role_id = r.id
                  WHERE ur.user_id = auth.uid()
                    AND r.name = 'store_manager'
                    AND ur.store_id = p.store_id
              )
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.products p
            WHERE p.id = product_attributes.product_id
              AND EXISTS (
                  SELECT 1 FROM public.user_roles ur
                  JOIN public.roles r ON ur.role_id = r.id
                  WHERE ur.user_id = auth.uid()
                    AND r.name = 'store_manager'
                    AND ur.store_id = p.store_id
              )
        )
    );

-- Admins: can do everything on product_attributes
CREATE POLICY "Product attributes admin ALL" ON public.product_attributes
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'admin'
        )
    );

-- ── Promotion Products policies ────────────────────────────────────────────

-- No anon access (not in the read-only set)
-- Store Managers: can CRUD where promotion linked to their store via promotion_stores
CREATE POLICY "Promotion products store manager CRUD" ON public.promotion_products
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.promotion_stores ps
            WHERE ps.promotion_id = promotion_products.promotion_id
              AND EXISTS (
                  SELECT 1 FROM public.user_roles ur
                  JOIN public.roles r ON ur.role_id = r.id
                  WHERE ur.user_id = auth.uid()
                    AND r.name = 'store_manager'
                    AND ur.store_id = ps.store_id
              )
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.promotion_stores ps
            WHERE ps.promotion_id = promotion_products.promotion_id
              AND EXISTS (
                  SELECT 1 FROM public.user_roles ur
                  JOIN public.roles r ON ur.role_id = r.id
                  WHERE ur.user_id = auth.uid()
                    AND r.name = 'store_manager'
                    AND ur.store_id = ps.store_id
              )
        )
    );

-- Admins: can do everything on promotion_products
CREATE POLICY "Promotion products admin ALL" ON public.promotion_products
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'admin'
        )
    );

-- ── Promotion Stores policies ─────────────────────────────────────────────

-- No anon access
-- Store Managers: can CRUD their store's promotion assignments
CREATE POLICY "Promotion stores store manager CRUD" ON public.promotion_stores
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'store_manager'
              AND ur.store_id = promotion_stores.store_id
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'store_manager'
              AND ur.store_id = promotion_stores.store_id
        )
    );

-- Admins: can do everything on promotion_stores
CREATE POLICY "Promotion stores admin ALL" ON public.promotion_stores
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'admin'
        )
    );

-- ── Store Policies policies ───────────────────────────────────────────────

-- No anon access
-- Store Managers: can CRUD their own store's policies
CREATE POLICY "Store policies store manager CRUD" ON public.store_policies
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'store_manager'
              AND ur.store_id = store_policies.store_id
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'store_manager'
              AND ur.store_id = store_policies.store_id
        )
    );

-- Admins: can do everything on store_policies
CREATE POLICY "Store policies admin ALL" ON public.store_policies
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'admin'
        )
    );