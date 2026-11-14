-- Migration 011: Warehouse RLS + Central Warehouse Seed
-- Part of Aura Bell M1.4 — see MILESTONES.md
-- DO NOT EDIT after applied to any environment.
-- RLS MUST be enabled BEFORE seeding data.

-- ─── RLS Policies for warehouses ───────────────────────────────────────────

ALTER TABLE public.warehouses ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Store managers manage own warehouses"
ON public.warehouses FOR ALL TO authenticated
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

-- ─── Seed Data (after RLS) ──────────────────────────────────────────────────

-- Link central warehouse to Best Gadget (slug: best-gadget) per Decision D2
-- Best Gadget is the primary revenue store, inserted first in migration 010
INSERT INTO public.warehouses (store_id, name, location)
SELECT id, 'Main Central Warehouse', 'Dhaka, Bangladesh'
FROM public.stores WHERE slug = 'best-gadget'
ON CONFLICT DO NOTHING;