-- Migration 008: Indexes & Triggers
-- Part of Aura Bell M1.2 — see DATABASE_MIGRATION_STRATEGY.md
-- DO NOT EDIT after applied to any environment.

CREATE INDEX idx_addresses_user
ON public.addresses(user_id);

CREATE INDEX idx_categories_store
ON public.categories(store_id, is_active);

CREATE INDEX idx_products_store_status
ON public.products(store_id, status);

CREATE INDEX idx_products_category
ON public.products(category_id);

CREATE INDEX idx_variants_product
ON public.product_variants(product_id);

CREATE INDEX idx_inventory_movements_variant
ON public.stock_movements(variant_id, created_at DESC);

CREATE INDEX idx_inventory_reservations_expiry
ON public.inventory_reservations(status, expires_at);

CREATE INDEX idx_carts_user
ON public.carts(user_id);

CREATE INDEX idx_orders_user_date
ON public.orders(user_id, created_at DESC);

CREATE INDEX idx_store_orders_store_status
ON public.store_orders(store_id, status);

CREATE INDEX idx_order_items_store_order
ON public.order_items(store_order_id);

CREATE INDEX idx_payments_order
ON public.payments(order_id);

CREATE INDEX idx_shipments_tracking
ON public.shipments(tracking_number);

CREATE INDEX idx_support_tickets_user
ON public.support_tickets(user_id, status);

CREATE INDEX idx_outbox_pending
ON public.outbox_events(available_at)
WHERE status = 'pending';

CREATE TRIGGER profiles_updated_at
BEFORE UPDATE ON public.profiles
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER stores_updated_at
BEFORE UPDATE ON public.stores
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER products_updated_at
BEFORE UPDATE ON public.products
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER carts_updated_at
BEFORE UPDATE ON public.carts
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER cart_items_updated_at
BEFORE UPDATE ON public.cart_items
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER orders_updated_at
BEFORE UPDATE ON public.orders
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER support_tickets_updated_at
BEFORE UPDATE ON public.support_tickets
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Gap Fix 5: Stock movements immutability (critical audit ledger protection)
CREATE OR REPLACE FUNCTION public.prevent_stock_movement_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'stock_movements is an immutable ledger. UPDATE and DELETE operations are not allowed.';
END;
$$;

CREATE TRIGGER prevent_stock_movement_mutation
BEFORE UPDATE OR DELETE ON public.stock_movements
FOR EACH ROW EXECUTE FUNCTION public.prevent_stock_movement_mutation();