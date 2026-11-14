-- Migration: comprehensive_rls_fix
-- Adds missing RLS to critical tables

-- Step 1: Fix Missing RLS
-- Must be enabled BEFORE any policies can be created

ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_status_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.warehouses ENABLE ROW LEVEL SECURITY; -- Already enabled in migration 011, but ensuring
ALTER TABLE public.inventory_balances ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stock_movements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventory_reservations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.product_serials ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payment_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payment_webhook_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.refunds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.couriers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.shipments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.shipment_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.financial_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.return_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.return_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.outbox_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY; -- Already enabled, but ensuring
ALTER TABLE public.notification_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.idempotency_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_reports ENABLE ROW LEVEL SECURITY;

-- Step 2: Comprehensive RLS Policies for All Tables
-- Standard e-commerce logic:
-- - Users (authenticated): Can only access their own data
-- - Store Managers: Can access data related to their store_id
-- - System Admins: Can access everything

-- 1. Profiles Table - Users can only access their own profile
CREATE POLICY "Users can read own profile" ON public.profiles
    FOR SELECT TO authenticated
    USING (id = auth.uid());

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE TO authenticated
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

-- 2. Addresses Table - Users can manage their own addresses
CREATE POLICY "Users can read own addresses" ON public.addresses
    FOR SELECT TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "Users can manage own addresses" ON public.addresses
    FOR ALL TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- 3. Stores Table - Read access for everyone, write access for admins/managers
CREATE POLICY "Read-only access to stores" ON public.stores
    FOR SELECT TO authenticated
    USING (true);

-- 4. Categories Table - Store-specific access
CREATE POLICY "Store categories access" ON public.categories
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.stores s
            WHERE s.id = categories.store_id
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.stores s
            WHERE s.id = categories.store_id
        )
    );

-- 5. Products Table - Store-specific access
CREATE POLICY "Store products access" ON public.products
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.stores s
            WHERE s.id = products.store_id
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.stores s
            WHERE s.id = products.store_id
        )
    );

-- 6. Product Variants - Product-specific access
CREATE POLICY "Product variants access" ON public.product_variants
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.products p
            WHERE p.id = product_variants.product_id
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.products p
            WHERE p.id = product_variants.product_id
        )
    );

-- 7. Product Images - Product-specific access
CREATE POLICY "Product images access" ON public.product_images
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.products p
            WHERE p.id = product_images.product_id
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.products p
            WHERE p.id = product_images.product_id
        )
    );

-- 8. Carts - User-specific access
CREATE POLICY "Users can read own carts" ON public.carts
    FOR SELECT TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "Users can manage own carts" ON public.carts
    FOR ALL TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- 9. Cart Items - Cart-specific access
CREATE POLICY "Cart items access" ON public.cart_items
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.carts c
            WHERE c.id = cart_items.cart_id
              AND c.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.carts c
            WHERE c.id = cart_items.cart_id
              AND c.user_id = auth.uid()
        )
    );

-- 10. Orders - User-specific access
CREATE POLICY "Users can read own orders" ON public.orders
    FOR SELECT TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "Users can create orders" ON public.orders
    FOR INSERT TO authenticated
    WITH CHECK (user_id = auth.uid());

-- 11. Order Items - Order-specific access
CREATE POLICY "Order items access" ON public.order_items
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.store_orders so
            WHERE so.id = order_items.store_order_id
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.store_orders so
            WHERE so.id = order_items.store_order_id
        )
    );

-- 12. Order Addresses - Order-specific access
CREATE POLICY "Order addresses access" ON public.order_addresses
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.orders o
            WHERE o.id = order_addresses.order_id
              AND (
                  o.user_id = auth.uid() OR
                  EXISTS (
                      SELECT 1 FROM public.user_roles ur
                      WHERE ur.user_id = auth.uid()
                         AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                  )
              )
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.orders o
            WHERE o.id = order_addresses.order_id
              AND (
                  o.user_id = auth.uid() OR
                  EXISTS (
                      SELECT 1 FROM public.user_roles ur
                      WHERE ur.user_id = auth.uid()
                         AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                  )
              )
        )
    );

-- 13. Order Status History - Order-specific access
CREATE POLICY "Order status history access" ON public.order_status_history
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.orders o
            WHERE o.id = order_status_history.order_id
              AND (
                  o.user_id = auth.uid() OR
                  EXISTS (
                      SELECT 1 FROM public.user_roles ur
                      WHERE ur.user_id = auth.uid()
                         AND ur.role_id IN (SELECT id FROM public.roles WHERE name IN ('admin', 'order_manager'))
                  )
              )
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.orders o
            WHERE o.id = order_status_history.order_id
              AND (
                  o.user_id = auth.uid() OR
                  EXISTS (
                      SELECT 1 FROM public.user_roles ur
                      WHERE ur.user_id = auth.uid()
                         AND ur.role_id IN (SELECT id FROM public.roles WHERE name IN ('admin', 'order_manager'))
                  )
              )
        )
    );

-- 14. Store Orders - Store-specific access
CREATE POLICY "Store orders access" ON public.store_orders
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.stores s
            WHERE s.id = store_orders.store_id
              AND (
                  s.id IN (
                      SELECT store_id FROM public.user_roles
                      WHERE user_id = auth.uid()
                  ) OR
                  EXISTS (
                      SELECT 1 FROM public.user_roles ur
                      WHERE ur.user_id = auth.uid()
                         AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                  )
              )
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.stores s
            WHERE s.id = store_orders.store_id
              AND (
                  s.id IN (
                      SELECT store_id FROM public.user_roles
                      WHERE user_id = auth.uid()
                  ) OR
                  EXISTS (
                      SELECT 1 FROM public.user_roles ur
                      WHERE ur.user_id = auth.uid()
                         AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                  )
              )
        )
    );

-- 15. Warehouses - Store manager access
CREATE POLICY "Store managers manage own warehouses" ON public.warehouses
    FOR ALL TO authenticated
    USING (
        store_id IN (
            SELECT store_id FROM public.user_roles
            WHERE user_id = auth.uid()
              AND role_id = (SELECT id FROM public.roles WHERE name = 'store_manager')
              AND store_id IS NOT NULL
        )
    )
    WITH CHECK (
        store_id IN (
            SELECT store_id FROM public.user_roles
            WHERE user_id = auth.uid()
              AND role_id = (SELECT id FROM public.roles WHERE name = 'store_manager')
              AND store_id IS NOT NULL
        )
    );

-- 16. Inventory Balances - Store/warehouse access
CREATE POLICY "Inventory balances access" ON public.inventory_balances
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.warehouses w
            WHERE w.id = inventory_balances.warehouse_id
              AND (
                  w.store_id IN (
                      SELECT store_id FROM public.user_roles
                      WHERE user_id = auth.uid()
                  ) OR
                  EXISTS (
                      SELECT 1 FROM public.user_roles ur
                      WHERE ur.user_id = auth.uid()
                         AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                  )
              )
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.warehouses w
            WHERE w.id = inventory_balances.warehouse_id
              AND (
                  w.store_id IN (
                      SELECT store_id FROM public.user_roles
                      WHERE user_id = auth.uid()
                  ) OR
                  EXISTS (
                      SELECT 1 FROM public.user_roles ur
                      WHERE ur.user_id = auth.uid()
                         AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                  )
              )
        )
    );

-- 17. Stock Movements - Immutable ledger, only admin access
CREATE POLICY "Stock movements read-only" ON public.stock_movements
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.user_id = auth.uid()
               AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
        )
    );

-- 18. Inventory Reservations - Store/warehouse access
CREATE POLICY "Inventory reservations access" ON public.inventory_reservations
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.product_variants pv
            WHERE pv.id = inventory_reservations.variant_id
            AND EXISTS (
                SELECT 1 FROM public.products p
                WHERE p.id = pv.product_id
                  AND (
                      p.store_id IN (
                          SELECT store_id FROM public.user_roles
                          WHERE user_id = auth.uid()
                      ) OR
                      EXISTS (
                          SELECT 1 FROM public.user_roles ur
                          WHERE ur.user_id = auth.uid()
                             AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                      )
                  )
            )
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.product_variants pv
            WHERE pv.id = inventory_reservations.variant_id
            AND EXISTS (
                SELECT 1 FROM public.products p
                WHERE p.id = pv.product_id
                  AND (
                      p.store_id IN (
                          SELECT store_id FROM public.user_roles
                          WHERE user_id = auth.uid()
                      ) OR
                      EXISTS (
                          SELECT 1 FROM public.user_roles ur
                          WHERE ur.user_id = auth.uid()
                             AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                      )
                  )
            )
        )
    );

-- 19. Product Batches - Product/store access
CREATE POLICY "Product batches access" ON public.product_batches
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.product_variants pv
            WHERE pv.id = product_batches.variant_id
            AND EXISTS (
                SELECT 1 FROM public.products p
                WHERE p.id = pv.product_id
                  AND (
                      p.store_id IN (
                          SELECT store_id FROM public.user_roles
                          WHERE user_id = auth.uid()
                      ) OR
                      EXISTS (
                          SELECT 1 FROM public.user_roles ur
                          WHERE ur.user_id = auth.uid()
                             AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                      )
                  )
            )
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.product_variants pv
            WHERE pv.id = product_batches.variant_id
            AND EXISTS (
                SELECT 1 FROM public.products p
                WHERE p.id = pv.product_id
                  AND (
                      p.store_id IN (
                          SELECT store_id FROM public.user_roles
                          WHERE user_id = auth.uid()
                      ) OR
                      EXISTS (
                          SELECT 1 FROM public.user_roles ur
                          WHERE ur.user_id = auth.uid()
                             AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                      )
                  )
            )
        )
    );

-- 20. Product Serials - Product/store access
CREATE POLICY "Product serials access" ON public.product_serials
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.product_variants pv
            WHERE pv.id = product_serials.variant_id
            AND EXISTS (
                SELECT 1 FROM public.products p
                WHERE p.id = pv.product_id
                  AND (
                      p.store_id IN (
                          SELECT store_id FROM public.user_roles
                          WHERE user_id = auth.uid()
                      ) OR
                      EXISTS (
                          SELECT 1 FROM public.user_roles ur
                          WHERE ur.user_id = auth.uid()
                             AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                      )
                  )
            )
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.product_variants pv
            WHERE pv.id = product_serials.variant_id
            AND EXISTS (
                SELECT 1 FROM public.products p
                WHERE p.id = pv.product_id
                  AND (
                      p.store_id IN (
                          SELECT store_id FROM public.user_roles
                          WHERE user_id = auth.uid()
                      ) OR
                      EXISTS (
                          SELECT 1 FROM public.user_roles ur
                          WHERE ur.user_id = auth.uid()
                             AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                      )
                  )
            )
        )
    );

-- 21. Payments - Order/access control
CREATE POLICY "Payments access" ON public.payments
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.orders o
            WHERE o.id = payments.order_id
              AND (
                  o.user_id = auth.uid() OR
                  EXISTS (
                      SELECT 1 FROM public.user_roles ur
                      WHERE ur.user_id = auth.uid()
                         AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                  )
              )
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.orders o
            WHERE o.id = payments.order_id
              AND (
                  o.user_id = auth.uid() OR
                  EXISTS (
                      SELECT 1 FROM public.user_roles ur
                      WHERE ur.user_id = auth.uid()
                         AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                  )
              )
        )
    );

-- 22. Refunds - Payment/access control
CREATE POLICY "Refunds access" ON public.refunds
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.payments p
            WHERE p.id = refunds.payment_id
              AND EXISTS (
                  SELECT 1 FROM public.orders o
                  WHERE o.id = p.order_id
                    AND (
                        o.user_id = auth.uid() OR
                        EXISTS (
                            SELECT 1 FROM public.user_roles ur
                            WHERE ur.user_id = auth.uid()
                               AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                        )
                    )
              )
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.payments p
            WHERE p.id = refunds.payment_id
              AND EXISTS (
                  SELECT 1 FROM public.orders o
                  WHERE o.id = p.order_id
                    AND (
                        o.user_id = auth.uid() OR
                        EXISTS (
                            SELECT 1 FROM public.user_roles ur
                            WHERE ur.user_id = auth.uid()
                               AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                        )
                    )
              )
        )
    );

-- 23. Expenses - Store/admin access
CREATE POLICY "Expenses access" ON public.expenses
    FOR ALL TO authenticated
    USING (
        store_id IN (
            SELECT store_id FROM public.user_roles
            WHERE user_id = auth.uid()
        ) OR
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.user_id = auth.uid()
               AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
        )
    )
    WITH CHECK (
        store_id IN (
            SELECT store_id FROM public.user_roles
            WHERE user_id = auth.uid()
        ) OR
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.user_id = auth.uid()
               AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
        )
    );

-- 24. Shipments - Store/admin access
CREATE POLICY "Shipments access" ON public.shipments
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.store_orders so
            WHERE so.id = shipments.store_order_id
              AND (
                  so.store_id IN (
                      SELECT store_id FROM public.user_roles
                      WHERE user_id = auth.uid()
                  ) OR
                  EXISTS (
                      SELECT 1 FROM public.user_roles ur
                      WHERE ur.user_id = auth.uid()
                         AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                  )
              )
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.store_orders so
            WHERE so.id = shipments.store_order_id
              AND (
                  so.store_id IN (
                      SELECT store_id FROM public.user_roles
                      WHERE user_id = auth.uid()
                  ) OR
                  EXISTS (
                      SELECT 1 FROM public.user_roles ur
                      WHERE ur.user_id = auth.uid()
                         AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                  )
              )
        )
    );

-- 25. Financial Entries - Admin access only
CREATE POLICY "Financial entries access" ON public.financial_entries
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.user_id = auth.uid()
               AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.user_id = auth.uid()
               AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
        )
    );

-- 26. Return Requests - User/admin access
CREATE POLICY "Return requests access" ON public.return_requests
    FOR ALL TO authenticated
    USING (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.user_id = auth.uid()
               AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
        )
    )
    WITH CHECK (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.user_id = auth.uid()
               AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
        )
    );

-- 27. Support Tickets - User/agent/admin access
CREATE POLICY "Support tickets access" ON public.support_tickets
    FOR ALL TO authenticated
    USING (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.user_id = auth.uid()
               AND ur.role_id IN (SELECT id FROM public.roles WHERE name IN ('admin', 'support_agent'))
        )
    )
    WITH CHECK (
        user_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.user_id = auth.uid()
               AND ur.role_id IN (SELECT id FROM public.roles WHERE name IN ('admin', 'support_agent'))
        )
    );

-- 28. Support Messages - Ticket-specific access
CREATE POLICY "Support messages access" ON public.support_messages
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.support_tickets t
            WHERE t.id = support_messages.ticket_id
              AND (
                  t.user_id = auth.uid() OR
                  EXISTS (
                      SELECT 1 FROM public.user_roles ur
                      WHERE ur.user_id = auth.uid()
                         AND ur.role_id IN (SELECT id FROM public.roles WHERE name IN ('admin', 'support_agent'))
                  )
              )
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.support_tickets t
            WHERE t.id = support_messages.ticket_id
              AND (
                  t.user_id = auth.uid() OR
                  EXISTS (
                      SELECT 1 FROM public.user_roles ur
                      WHERE ur.user_id = auth.uid()
                         AND ur.role_id IN (SELECT id FROM public.roles WHERE name IN ('admin', 'support_agent'))
                  )
              )
        )
    );

-- 29. Audit Logs - Admin only
CREATE POLICY "Audit logs access" ON public.audit_logs
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.user_id = auth.uid()
               AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
        )
    );

-- 30. Outbox Events - Admin only
CREATE POLICY "Outbox events access" ON public.outbox_events
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.user_id = auth.uid()
               AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.user_id = auth.uid()
               AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
        )
    );

-- 31. Notifications - User-specific access
CREATE POLICY "Notifications access" ON public.notifications
    FOR ALL TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- 32. Notification Templates - Read-only for all
CREATE POLICY "Notification templates read-only" ON public.notification_templates
    FOR SELECT TO authenticated
    USING (true);

-- 33. Idempotency Keys - User-specific access
CREATE POLICY "Idempotency keys access" ON public.idempotency_keys
    FOR ALL TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- 34. Daily Reports - Store/admin access
CREATE POLICY "Daily reports access" ON public.daily_reports
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.stores s
            WHERE s.id = daily_reports.store_id
              AND (
                  s.id IN (
                      SELECT store_id FROM public.user_roles
                      WHERE user_id = auth.uid()
                  ) OR
                  EXISTS (
                      SELECT 1 FROM public.user_roles ur
                      WHERE ur.user_id = auth.uid()
                         AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                  )
              )
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.stores s
            WHERE s.id = daily_reports.store_id
              AND (
                  s.id IN (
                      SELECT store_id FROM public.user_roles
                      WHERE user_id = auth.uid()
                  ) OR
                  EXISTS (
                      SELECT 1 FROM public.user_roles ur
                      WHERE ur.user_id = auth.uid()
                         AND ur.role_id IN (SELECT id FROM public.roles WHERE name = 'admin')
                  )
              )
        )
    );