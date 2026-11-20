-- Migration: 20261117174530_secure_catalog_rls
-- Secure catalog tables with RLS for e-commerce
-- Ensures public can only browse, store managers manage by store, admins have full access

-- ── Enable RLS on catalog tables ──────────────────────────────────────────--

ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_prices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.promotions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.promotion_redemptions ENABLE ROW LEVEL SECURITY;

-- ── Drop existing overly-permissive policies from comprehensive_rls_fix ─────

DROP POLICY IF EXISTS "Store categories access" ON public.categories;
DROP POLICY IF EXISTS "Store products access" ON public.products;
DROP POLICY IF EXISTS "Product variants access" ON public.product_variants;
DROP POLICY IF EXISTS "Product images access" ON public.product_images;

-- ── Categories policies ───────────────────────────────────────────────────

-- Public/Anonymous: can only SELECT (browse categories)
CREATE POLICY "Categories public read" ON public.categories
    FOR SELECT TO anon USING (true);

-- Store Managers: can CRUD categories where store_id matches their assigned store
CREATE POLICY "Categories store manager CRUD" ON public.categories
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'store_manager'
              AND ur.store_id = categories.store_id
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'store_manager'
              AND ur.store_id = categories.store_id
        )
    );

-- Admins: can do everything on categories
CREATE POLICY "Categories admin ALL" ON public.categories
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

-- ── Products policies ─────────────────────────────────────────────────────

-- Public/Anonymous: can only SELECT (browse products)
CREATE POLICY "Products public read" ON public.products
    FOR SELECT TO anon USING (true);

-- Store Managers: can CRUD products where store_id matches their assigned store
CREATE POLICY "Products store manager CRUD" ON public.products
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'store_manager'
              AND ur.store_id = products.store_id
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            JOIN public.roles r ON ur.role_id = r.id
            WHERE ur.user_id = auth.uid()
              AND r.name = 'store_manager'
              AND ur.store_id = products.store_id
        )
    );

-- Admins: can do everything on products
CREATE POLICY "Products admin ALL" ON public.products
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

-- ── Product Variants policies ─────────────────────────────────────────────

-- Store Managers: can CRUD variants where product's store_id matches their store
CREATE POLICY "Product variants store manager CRUD" ON public.product_variants
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.products p
            WHERE p.id = product_variants.product_id
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
            WHERE p.id = product_variants.product_id
              AND EXISTS (
                  SELECT 1 FROM public.user_roles ur
                  JOIN public.roles r ON ur.role_id = r.id
                  WHERE ur.user_id = auth.uid()
                    AND r.name = 'store_manager'
                    AND ur.store_id = p.store_id
              )
        )
    );

-- Admins: can do everything on product variants
CREATE POLICY "Product variants admin ALL" ON public.product_variants
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

-- ── Product Images policies ───────────────────────────────────────────────

-- Public/Anonymous: can only SELECT (browse images)
CREATE POLICY "Product images public read" ON public.product_images
    FOR SELECT TO anon USING (true);

-- Store Managers: can CRUD images where product's store_id matches their store
CREATE POLICY "Product images store manager CRUD" ON public.product_images
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.products p
            WHERE p.id = product_images.product_id
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
            WHERE p.id = product_images.product_id
              AND EXISTS (
                  SELECT 1 FROM public.user_roles ur
                  JOIN public.roles r ON ur.role_id = r.id
                  WHERE ur.user_id = auth.uid()
                    AND r.name = 'store_manager'
                    AND ur.store_id = p.store_id
              )
        )
    );

-- Admins: can do everything on product images
CREATE POLICY "Product images admin ALL" ON public.product_images
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

-- ── Product Prices policies ───────────────────────────────────────────────

-- Store Managers: can CRUD prices where variant's product's store_id matches their store
CREATE POLICY "Product prices store manager CRUD" ON public.product_prices
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.product_variants pv
            WHERE pv.id = product_prices.variant_id
              AND EXISTS (
                  SELECT 1 FROM public.products p
                  WHERE p.id = pv.product_id
                    AND EXISTS (
                        SELECT 1 FROM public.user_roles ur
                        JOIN public.roles r ON ur.role_id = r.id
                        WHERE ur.user_id = auth.uid()
                          AND r.name = 'store_manager'
                          AND ur.store_id = p.store_id
                    )
              )
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.product_variants pv
            WHERE pv.id = product_prices.variant_id
              AND EXISTS (
                  SELECT 1 FROM public.products p
                  WHERE p.id = pv.product_id
                    AND EXISTS (
                        SELECT 1 FROM public.user_roles ur
                        JOIN public.roles r ON ur.role_id = r.id
                        WHERE ur.user_id = auth.uid()
                          AND r.name = 'store_manager'
                          AND ur.store_id = p.store_id
                    )
              )
        )
    );

-- Admins: can do everything on product prices
CREATE POLICY "Product prices admin ALL" ON public.product_prices
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

-- ── Promotions policies ───────────────────────────────────────────────────

-- Store Managers: can CRUD promotions linked to their store via promotion_stores
CREATE POLICY "Promotions store manager CRUD" ON public.promotions
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.promotion_stores ps
            WHERE ps.promotion_id = promotions.id
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
            WHERE ps.promotion_id = promotions.id
              AND EXISTS (
                  SELECT 1 FROM public.user_roles ur
                  JOIN public.roles r ON ur.role_id = r.id
                  WHERE ur.user_id = auth.uid()
                    AND r.name = 'store_manager'
                    AND ur.store_id = ps.store_id
              )
        )
    );

-- Admins: can do everything on promotions
CREATE POLICY "Promotions admin ALL" ON public.promotions
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

-- ── Promotion Redemptions policies ─────────────────────────────────────────

-- Store Managers: can CRUD redemptions where linked order's store_id matches their store
CREATE POLICY "Promotion redemptions store manager CRUD" ON public.promotion_redemptions
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.orders o
            WHERE o.id = promotion_redemptions.order_id
              AND EXISTS (
                  SELECT 1 FROM public.store_orders so
                  WHERE so.order_id = o.id
                    AND EXISTS (
                        SELECT 1 FROM public.user_roles ur
                        JOIN public.roles r ON ur.role_id = r.id
                        WHERE ur.user_id = auth.uid()
                          AND r.name = 'store_manager'
                          AND ur.store_id = so.store_id
                    )
              )
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.orders o
            WHERE o.id = promotion_redemptions.order_id
              AND EXISTS (
                  SELECT 1 FROM public.store_orders so
                  WHERE so.order_id = o.id
                    AND EXISTS (
                        SELECT 1 FROM public.user_roles ur
                        JOIN public.roles r ON ur.role_id = r.id
                        WHERE ur.user_id = auth.uid()
                          AND r.name = 'store_manager'
                          AND ur.store_id = so.store_id
                    )
              )
        )
    );

-- Admins: can do everything on promotion redemptions
CREATE POLICY "Promotion redemptions admin ALL" ON public.promotion_redemptions
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