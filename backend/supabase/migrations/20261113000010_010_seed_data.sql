-- Migration 010: Seed Data
-- Part of Aura Bell M1.2 — see DATABASE_MIGRATION_STRATEGY.md
-- DO NOT EDIT after applied to any environment.

INSERT INTO public.roles (name, description)
VALUES
('owner', 'Platform owner'),
('admin', 'Platform administrator'),
('store_manager', 'Store management'),
('inventory_manager', 'Inventory management'),
('order_manager', 'Order management'),
('support_agent', 'Customer support'),
('customer', 'Customer account')
ON CONFLICT (name) DO NOTHING;

INSERT INTO public.stores (name, slug, description)
VALUES
(
    'Best Gadget',
    'best-gadget',
    'Gadgets and electronics store'
),
(
    'Aura Skin Care',
    'aura-skin-care',
    'Skincare and beauty store'
)
ON CONFLICT (slug) DO NOTHING;