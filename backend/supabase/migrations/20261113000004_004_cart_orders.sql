-- Migration 004: Cart & Orders
-- Part of Aura Bell M1.2 — see DATABASE_MIGRATION_STRATEGY.md
-- DO NOT EDIT after applied to any environment.

CREATE TABLE public.carts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id),
    session_id VARCHAR(150),
    status VARCHAR(30) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'converted', 'abandoned')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (user_id IS NOT NULL OR session_id IS NOT NULL)
);

CREATE TABLE public.cart_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cart_id UUID NOT NULL REFERENCES public.carts(id) ON DELETE CASCADE,
    variant_id UUID NOT NULL REFERENCES public.product_variants(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (cart_id, variant_id)
);

CREATE TABLE public.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) NOT NULL UNIQUE,
    user_id UUID NOT NULL REFERENCES public.profiles(id),
    subtotal NUMERIC(12,2) NOT NULL CHECK (subtotal >= 0),
    discount_total NUMERIC(12,2) NOT NULL DEFAULT 0,
    delivery_total NUMERIC(12,2) NOT NULL DEFAULT 0,
    grand_total NUMERIC(12,2) NOT NULL CHECK (grand_total >= 0),
    currency_code CHAR(3) NOT NULL DEFAULT 'BDT',
    order_status VARCHAR(30) NOT NULL DEFAULT 'pending'
        CHECK (order_status IN (
            'pending', 'confirmed', 'processing',
            'completed', 'cancelled'
        )),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.store_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES public.orders(id),
    store_id UUID NOT NULL REFERENCES public.stores(id),
    store_order_number VARCHAR(50) NOT NULL UNIQUE,
    subtotal NUMERIC(12,2) NOT NULL CHECK (subtotal >= 0),
    delivery_fee NUMERIC(12,2) NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (order_id, store_id)
);

CREATE TABLE public.order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_order_id UUID NOT NULL REFERENCES public.store_orders(id),
    variant_id UUID REFERENCES public.product_variants(id),
    product_name_snapshot VARCHAR(255) NOT NULL,
    sku_snapshot VARCHAR(100),
    variant_snapshot JSONB NOT NULL DEFAULT '{}'::JSONB,
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    line_total NUMERIC(12,2) NOT NULL CHECK (line_total >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.order_addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES public.orders(id),
    recipient_name VARCHAR(150) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    division VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    upazila VARCHAR(100),
    area VARCHAR(150),
    address_line TEXT NOT NULL,
    postal_code VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Gap Fix 3: Separate billing and delivery addresses per order
ALTER TABLE public.order_addresses
ADD COLUMN address_type VARCHAR(15) NOT NULL DEFAULT 'delivery'
    CHECK (address_type IN ('billing', 'delivery', 'both'));

CREATE UNIQUE INDEX uq_order_addresses_order_type
ON public.order_addresses(order_id, address_type);

CREATE TABLE public.order_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES public.orders(id),
    old_status VARCHAR(30),
    new_status VARCHAR(30) NOT NULL,
    changed_by UUID REFERENCES public.profiles(id),
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.inventory_reservations
ADD CONSTRAINT fk_reservation_order
FOREIGN KEY (order_id)
REFERENCES public.orders(id);

-- Gap Fix 2 Part B: store_order_id FK (table already exists in this migration)
ALTER TABLE public.inventory_reservations
ADD CONSTRAINT fk_reservation_store_order
FOREIGN KEY (store_order_id)
REFERENCES public.store_orders(id)
ON DELETE CASCADE;

-- Gap Fix 4B: Promotion redemptions (requires orders table)
CREATE TABLE public.promotion_redemptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    promotion_id UUID NOT NULL REFERENCES public.promotions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id),
    order_id UUID NOT NULL REFERENCES public.orders(id),
    discount_amount NUMERIC(12,2) NOT NULL CHECK (discount_amount >= 0),
    redeemed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (promotion_id, order_id)
);

CREATE INDEX idx_promotion_redemptions_user_promo
ON public.promotion_redemptions(user_id, promotion_id);