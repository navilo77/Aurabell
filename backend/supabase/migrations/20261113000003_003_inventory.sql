-- Migration 003: Inventory
-- Part of Aura Bell M1.2 — see DATABASE_MIGRATION_STRATEGY.md
-- DO NOT EDIT after applied to any environment.

CREATE TABLE public.warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES public.stores(id),
    name VARCHAR(150) NOT NULL,
    location TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.inventory_balances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID NOT NULL REFERENCES public.warehouses(id),
    variant_id UUID NOT NULL REFERENCES public.product_variants(id),
    quantity_on_hand INTEGER NOT NULL DEFAULT 0,
    quantity_reserved INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (quantity_on_hand >= 0),
    CHECK (quantity_reserved >= 0),
    CHECK (quantity_reserved <= quantity_on_hand),
    UNIQUE (warehouse_id, variant_id)
);

CREATE TABLE public.stock_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID NOT NULL REFERENCES public.warehouses(id),
    variant_id UUID NOT NULL REFERENCES public.product_variants(id),
    movement_type VARCHAR(40) NOT NULL,
    quantity_delta INTEGER NOT NULL,
    reference_type VARCHAR(50),
    reference_id UUID,
    note TEXT,
    created_by UUID REFERENCES public.profiles(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.inventory_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    variant_id UUID NOT NULL REFERENCES public.product_variants(id),
    warehouse_id UUID NOT NULL REFERENCES public.warehouses(id),
    order_id UUID,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    status VARCHAR(30) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'consumed', 'released', 'expired')),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Gap Fix 2 Part A: store_order_id column (FK added later in Migration 004)
ALTER TABLE public.inventory_reservations
ADD COLUMN store_order_id UUID;

CREATE INDEX idx_inventory_reservations_store_order_active
ON public.inventory_reservations(store_order_id)
WHERE status = 'active';

COMMENT ON COLUMN public.inventory_reservations.order_id IS
    'DEPRECATED: Use store_order_id instead. Kept for backward compatibility during migration.';

CREATE TABLE public.product_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    variant_id UUID NOT NULL REFERENCES public.product_variants(id),
    batch_number VARCHAR(100) NOT NULL,
    manufacture_date DATE,
    expiry_date DATE NOT NULL,
    quantity_received INTEGER NOT NULL
        CHECK (quantity_received >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (variant_id, batch_number)
);

CREATE TABLE public.product_serials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    variant_id UUID NOT NULL REFERENCES public.product_variants(id),
    serial_number VARCHAR(150) NOT NULL UNIQUE,
    status VARCHAR(30) NOT NULL DEFAULT 'available'
        CHECK (status IN ('available', 'reserved', 'sold', 'returned', 'damaged')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);