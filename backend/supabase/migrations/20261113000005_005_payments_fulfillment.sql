-- Migration 005: Payments & Fulfillment
-- Part of Aura Bell M1.2 — see DATABASE_MIGRATION_STRATEGY.md
-- DO NOT EDIT after applied to any environment.

CREATE TABLE public.payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES public.orders(id),
    provider VARCHAR(50) NOT NULL,
    provider_reference VARCHAR(150),
    payment_method VARCHAR(40) NOT NULL,
    amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    currency_code CHAR(3) NOT NULL DEFAULT 'BDT',
    status VARCHAR(30) NOT NULL DEFAULT 'pending'
        CHECK (status IN (
            'pending', 'authorized', 'paid',
            'failed', 'partially_refunded', 'refunded'
        )),
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES public.payments(id),
    provider_transaction_id VARCHAR(150),
    transaction_type VARCHAR(30) NOT NULL,
    amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    status VARCHAR(30) NOT NULL,
    response_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.payment_webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL,
    provider_event_id VARCHAR(200) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    processing_status VARCHAR(30) NOT NULL DEFAULT 'received',
    processed_at TIMESTAMPTZ,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (provider, provider_event_id)
);

CREATE TABLE public.refunds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES public.payments(id),
    amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    reason TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    provider_reference VARCHAR(150),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES public.stores(id),
    category VARCHAR(80) NOT NULL,
    amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    currency_code CHAR(3) NOT NULL DEFAULT 'BDT',
    description TEXT,
    expense_date DATE NOT NULL,
    created_by UUID REFERENCES public.profiles(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.couriers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL,
    code VARCHAR(80) NOT NULL UNIQUE,
    api_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE public.shipments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_order_id UUID NOT NULL REFERENCES public.store_orders(id),
    courier_id UUID REFERENCES public.couriers(id),
    tracking_number VARCHAR(150),
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    delivery_fee NUMERIC(12,2) NOT NULL DEFAULT 0,
    booked_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.shipment_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id UUID NOT NULL REFERENCES public.shipments(id),
    status VARCHAR(30) NOT NULL,
    description TEXT,
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_data JSONB
);

-- Gap Fix 1: Financial entries (reconciliation & audit ledger)
CREATE TABLE public.financial_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_type VARCHAR(40) NOT NULL
        CHECK (entry_type IN (
            'sale', 'refund', 'payment', 'payout', 'expense', 'adjustment',
            'courier_fee', 'platform_fee', 'tax_collected', 'tax_remitted'
        )),
    direction VARCHAR(10) NOT NULL
        CHECK (direction IN ('credit', 'debit')),
    reference_type VARCHAR(50) NOT NULL
        CHECK (reference_type IN (
            'order', 'store_order', 'payment', 'refund', 'expense',
            'shipment', 'return', 'adjustment', 'payout'
        )),
    reference_id UUID NOT NULL,
    store_id UUID REFERENCES public.stores(id) ON DELETE SET NULL,
    amount NUMERIC(14,2) NOT NULL CHECK (amount >= 0),
    currency CHAR(3) NOT NULL DEFAULT 'BDT',
    status VARCHAR(20) NOT NULL DEFAULT 'posted'
        CHECK (status IN ('posted', 'voided', 'pending_reconciliation')),
    reconciled_at TIMESTAMPTZ,
    notes TEXT,
    created_by UUID REFERENCES public.profiles(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_financial_entries_reference
ON public.financial_entries(reference_type, reference_id);

CREATE INDEX idx_financial_entries_store_status
ON public.financial_entries(store_id, status);

CREATE INDEX idx_financial_entries_created_at
ON public.financial_entries(created_at DESC);