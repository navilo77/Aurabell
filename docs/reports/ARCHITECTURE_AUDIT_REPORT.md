# AURA BELL — MULTI-STORE ARCHITECTURE AUDIT REPORT

**Generated:** 2026-11-26  
**Scope:** Full backend + frontend codebase audit  
**Mode:** Evidence-based investigation only (no code changes)

---

## 1. CURRENT STORE ARCHITECTURE AUDIT

### 1.1 Backend — Store Model & Database Schema

**Stores Table** (`backend/supabase/migrations/20261113000002_002_stores_catalog.sql:5-16`):
```sql
CREATE TABLE public.stores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL,
    slug VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    logo_url TEXT,
    primary_color VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Store Policies Table** (`backend/supabase/migrations/20261113000002_002_stores_catalog.sql:23-32`):
```sql
CREATE TABLE public.store_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES public.stores(id),
    policy_type VARCHAR(50) NOT NULL,
    policy_content JSONB NOT NULL DEFAULT '{}'::JSONB,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (store_id, policy_type)
);
```

**Service Layer** (`backend/app/modules/stores/service.py`):
- `StoresService` — CRUD + policy management
- Raw SQL via `text()` — no ORM models
- `get_store_by_slug()` returns store + active policies

**Router** (`backend/app/modules/stores/router.py`):
- `/stores` — CRUD (admin only, store_manager+super_admin)
- `/stores/{slug}` — public store detail
- `/stores/{slug}/categories` — store category tree
- Role-based access: `require_role("store_manager", "super_admin")`

### 1.2 Store-Aware Entities — Evidence

| Entity | Store-Aware? | Evidence |
|--------|--------------|----------|
| **Products** | ✅ YES | `products.store_id` FK, `UNIQUE (store_id, slug)` |
| **Categories** | ✅ YES | `categories.store_id` FK, `UNIQUE (store_id, slug)` |
| **Inventory** | ✅ YES | `warehouses.store_id` FK, balances per warehouse |
| **Pricing** | ✅ YES | `product_prices` via variant→product→store_id |
| **Cart** | ✅ YES | Cart items join products→stores, per-store breakdown in preview |
| **Orders** | ✅ YES | `store_orders` table per store per order, `order_id` + `store_id` UNIQUE |
| **Payments** | ⚠️ PARTIAL | `payments.order_id` only, no direct store_id (via order→store_orders) |
| **Users** | ⚠️ VIA ROLES | `user_roles.store_id` nullable, customers have no store_ids |
| **Community** | ❌ NO | No store_id in conversations/messages |

### 1.3 Store ID Usage Locations (Backend)

**Key Files:**
- `backend/app/core/auth.py:109,128` — JWT → `user_roles.store_id` → `User.store_ids`
- `backend/app/modules/products/service.py:96-102` — `_ensure_store()` validates store exists
- `backend/app/modules/categories/service.py:59,76,211` — store_id for slug uniqueness & tree
- `backend/app/modules/orders/service.py:313-357` — split orders grouped by `item.store_id`
- `backend/app/modules/cart/service.py:462-466` — cart items join stores for per-store preview
- `backend/app/modules/pricing/service.py:348` — price query filters `p.store_id = :store_id`
- `backend/app/modules/inventory/service.py` — via `warehouses.store_id`

---

## 2. FRONTEND — Store Architecture

### 2.1 Routing Structure (Hardcoded Store Routes)

**Current Routes** (`frontend/app/(storefront)/`):
```
/aura-skin-care/              → Hardcoded store page
/aura-skin-care/categories/[slug]
/aura-skin-care/products/[id]
/best-gadget/                 → Hardcoded store page
/best-gadget/categories/[slug]
/best-gadget/products/[id]
/brand-shops                  → Dynamic store directory
/shop/[id]                    → Product detail (store-agnostic)
/shop/cart                    → Shared cart
```

**Evidence of Hardcoded Store Slugs:**
- `frontend/app/(storefront)/aura-skin-care/page.tsx:18` — `const STORE_SLUG = "aura-skin-care";`
- `frontend/app/(storefront)/best-gadget/page.tsx:18` — `const STORE_SLUG = "best-gadget";`
- `frontend/lib/stores.ts:17-27` — `STORE_SLUG_MAP` with only 2 entries
- `frontend/lib/stores.ts:92` — `CANONICAL_STORE_SLUGS = ["best-gadget", "aura-skin-care"]`
- `frontend/components/hero-2d.tsx:27-32` — Finds stores by name contains "gadget"/"skin"
- `frontend/components/header.tsx:88-91` — Pathname checks for `/best-gadget`, `/aura-skin-care`
- `frontend/components/cart-drawer.tsx:210-221` — Store label by name contains "gadget"/"skin"
- `frontend/components/product-grid.tsx:69-78` — Badge logic: `store.name.toLowerCase().includes("gadget")`

### 2.2 Store Configuration System (`frontend/lib/stores.ts`)

```typescript
// Hardcoded themes (lines 39-47, 60-68)
const isGadget = slug === "best-gadget" || store.name.toLowerCase().includes("gadget");
theme: isGadget ? "gadget" : "skin",
accentColor: isGadget ? "#0284c7" : "#e11d48",
```

**Generic fallback** (lines 129-133, 146-150):
```typescript
generic: { accentColor: "#d4af37", ... }
function resolveStoreTheme(slug: string): StoreTheme {
    if (slug === "best-gadget") return "gadget";
    if (slug === "aura-skin-care") return "skin";
    return "generic";
}
```

### 2.3 Components with Store-Specific Logic

| Component | Hardcoded Logic |
|-----------|-----------------|
| `aura-skin-care/page.tsx` | STORE_SLUG constant, category tabs hardcoded (Serums, Creams, Cleansers, Treatments) |
| `best-gadget/page.tsx` | STORE_SLUG constant, category tabs hardcoded (Smartphones, Laptops, Audio, Accessories) |
| `hero-2d.tsx` | Finds stores by name matching "gadget"/"skin" |
| `product-grid.tsx` | Badge logic by name matching "gadget"/"skin" |
| `cart-drawer.tsx` | Store label by name matching |
| `header.tsx` | Route detection by pathname prefix |

---

## 3. STORE vs PLATFORM SEPARATION ANALYSIS

### 3.1 Current Classification

| Layer | Current State | Platform-Level | Store-Level | Store-Feature-Level |
|-------|---------------|----------------|-------------|---------------------|
| **Auth/Users** | Platform | ✅ profiles, roles, user_roles | ❌ | ❌ |
| **Stores** | Platform registry | ✅ stores table | ✅ store config | ❌ |
| **Catalog** | Store-scoped | ❌ | ✅ products, categories | ❌ |
| **Pricing** | Store-scoped | ❌ | ✅ product_prices, promotions | ❌ |
| **Inventory** | Store-scoped | ❌ warehouses | ✅ balances, reservations | ❌ |
| **Cart** | Platform (shared) | ✅ carts, cart_items | ⚠️ per-store preview | ❌ |
| **Orders** | Hybrid | ✅ orders (parent) | ✅ store_orders | ❌ |
| **Payments** | Platform | ✅ payments | ❌ | ❌ |
| **Community** | Platform | ✅ conversations, messages | ❌ | ❌ |
| **Frontend Routing** | Hardcoded | ❌ | ❌ Hardcoded routes | ❌ |
| **Frontend Theming** | Partial | ❌ | ⚠️ Config-driven but hardcoded slugs | ❌ |
| **Frontend Components** | Mixed | ❌ | ⚠️ Some generic, some store-specific | ❌ |

### 3.2 Separation Violations

1. **Frontend routes are hardcoded per store** — Adding a store requires new route folders
2. **Category tabs hardcoded per store page** — Serums/Creams vs Smartphones/Laptops
3. **Store detection by string matching** — "gadget" in name, "skin" in name
4. **No feature flag/capability model** — All stores assumed to have same features
5. **Community not store-scoped** — Global only

---

## 4. MULTI-STORE READINESS SCORE

| Dimension | Score | Evidence |
|-----------|-------|----------|
| **Database Isolation** | **READY** | All core entities have `store_id` FK, RLS policies enforce isolation |
| **Backend Isolation** | **READY** | Services validate store_id, queries filter by store_id |
| **API Isolation** | **READY** | Endpoints accept store_id/slug, role-based access via `user.store_ids` |
| **Frontend Isolation** | **NOT READY** | Hardcoded routes, hardcoded slugs, string-matching detection |
| **Routing Isolation** | **NOT READY** | `/aura-skin-care/`, `/best-gadget/` folders; no dynamic `[storeSlug]` |
| **Product Isolation** | **READY** | `products.store_id`, unique per store, RLS vendor CRUD own store |
| **Cart Isolation** | **READY** | Shared cart with per-store breakdown, items linked via variant→product→store |
| **Order Isolation** | **READY** | Split-order: `store_orders` per store, `order_items` per store_order |
| **Inventory Isolation** | **READY** | `warehouses.store_id`, balances per warehouse, reservations per store_order |
| **Pricing Isolation** | **READY** | Prices per variant, validated via `p.store_id = :store_id` |
| **Theme Isolation** | **PARTIALLY READY** | Config-driven but hardcoded slug map, generic fallback exists |
| **Feature Isolation** | **NOT READY** | No feature flags, all stores assumed identical capabilities |
| **Permission Isolation** | **READY** | `user_roles.store_id`, RLS policies, `require_role` with store scoping |
| **Configuration Isolation** | **PARTIALLY READY** | Store config in DB, but frontend hardcodes presentation logic |

---

## 5. HARD-CODED ASSUMPTIONS

### 5.1 Backend — Minimal Hardcoding

| Location | Assumption |
|----------|------------|
| `backend/app/modules/orders/service.py:62-63` | Delivery fee: Dhaka ৳70, else ৳120 (hardcoded district logic) |
| `backend/app/core/auth.py:128` | `user_roles.store_id` nullable — customers have no store scope |

### 5.2 Frontend — Extensive Hardcoding

| File | Line | Hardcoded Assumption |
|------|------|---------------------|
| `frontend/app/(storefront)/aura-skin-care/page.tsx` | 18 | `const STORE_SLUG = "aura-skin-care";` |
| `frontend/app/(storefront)/best-gadget/page.tsx` | 18 | `const STORE_SLUG = "best-gadget";` |
| `frontend/app/(storefront)/aura-skin-care/page.tsx` | 155-160 | Category tabs: Serums, Creams, Cleansers, Treatments |
| `frontend/app/(storefront)/best-gadget/page.tsx` | 155-160 | Category tabs: Smartphones, Laptops, Audio, Accessories |
| `frontend/lib/stores.ts` | 17-27 | `STORE_SLUG_MAP` only 2 entries |
| `frontend/lib/stores.ts` | 92 | `CANONICAL_STORE_SLUGS = ["best-gadget", "aura-skin-care"]` |
| `frontend/lib/stores.ts` | 39-47, 60-68 | Theme/colors by slug or name contains "gadget"/"skin" |
| `frontend/lib/stores.ts` | 136-144 | `BRAND_TAGLINES`, `BRAND_DESCRIPTIONS` only for 2 stores |
| `frontend/lib/stores.ts` | 146-150 | `resolveStoreTheme()` only knows 2 slugs |
| `frontend/components/hero-2d.tsx` | 27-32 | Finds stores by `name.toLowerCase().includes("gadget"/"skin")` |
| `frontend/components/product-grid.tsx` | 69-78 | Badge by `store.name.toLowerCase().includes("gadget"/"skin")` |
| `frontend/components/cart-drawer.tsx` | 210-221 | Store label by name matching |
| `frontend/components/header.tsx` | 88-91 | Route detection by pathname prefix |
| `frontend/components/header.tsx` | 156-166 | Nav link to `/brand-shops` hardcoded |

### 5.3 Conditional Logic Patterns Found

```typescript
// Pattern 1: String matching on store name
store.name.toLowerCase().includes("gadget")
store.name.toLowerCase().includes("skin")

// Pattern 2: Slug constant
const STORE_SLUG = "aura-skin-care"

// Pattern 3: Pathname prefix
pathname.startsWith("/best-gadget")
pathname.startsWith("/aura-skin-care")

// Pattern 4: Hardcoded slug map
STORE_SLUG_MAP = { "best-gadget": "best-gadget", "aura-skin-care": "aura-skin-care" }
```

---

## 6. FEATURE MODULARITY AUDIT — VIRTUAL TRY-ON SCENARIO

### 6.1 Current Architecture for New Feature

To add **Virtual Try-On** for a Fashion store, changes needed:

| Layer | Files to Modify | Risk |
|-------|-----------------|------|
| **Database** | New table `virtual_try_on_sessions` with `store_id`, `product_id`, `user_id` | Low — additive |
| **Backend Service** | New `VirtualTryOnService` in `modules/virtual-try-on/` | Low — new module |
| **Backend Router** | New router `/virtual-try-on` | Low — new endpoint |
| **Product Model** | Add `virtual_try_on_enabled` boolean to products | Medium — schema change |
| **Store Model** | Add `features` JSONB column to stores | Medium — schema change |
| **Frontend Routing** | **NEW ROUTE FOLDER** `/fashion-brand/` (current pattern) | **HIGH** — violates DRY |
| **Frontend Product Detail** | Add try-on button/component in `/shop/[id]/page.tsx` | Medium |
| **Frontend Store Page** | New store page with fashion-specific UI | **HIGH** — duplicate pattern |
| **Frontend Components** | New `VirtualTryOn` component, integrate in product card/detail | Medium |

### 6.2 Where Virtual Try-On Logically Belongs

| Option | Assessment |
|--------|------------|
| **Platform Feature** | ❌ Not all stores need it |
| **Store Feature** | ✅ Enable per-store via config |
| **Product-Level Capability** | ✅ Some products support it, others don't |
| **Store Configuration** | ✅ `store.features.virtual_try_on = true` |
| **Feature Flag** | ✅ Best for gradual rollout |

### 6.3 Recommended Architecture

```
Store (DB)
├── features: JSONB { virtual_try_on: true, wishlist: true, comparison: false }
└── theme: { accent_color, logo_url, ... }

Product (DB)
├── capabilities: JSONB { virtual_try_on: true, ar_model_url: "..." }
└── store_id FK

Frontend
├── /[storeSlug]/          → Dynamic route (single folder)
├── /[storeSlug]/products/[id]  → Checks product.capabilities.virtual_try_on
└── Components/
    ├── VirtualTryOn.tsx   → Renders if capability enabled
    └── ProductCard.tsx    → Shows badge if capability enabled
```

### 6.4 Can New Feature Be Added Without Core Changes?

**Currently: NO** — Frontend requires new route folder per store, hardcoded category tabs, string-matching theming.

**With Recommended Changes: YES** — Dynamic routing + feature flags + capability model.

---

## 7. FEATURE FLAG / CAPABILITY MODEL

### 7.1 Current State

**No feature flag system exists.** Stores table has only:
- `name`, `slug`, `description`, `logo_url`, `primary_color`, `status`

**Promotions** have store mapping (`promotion_stores`) but that's for discounts, not features.

### 7.2 Required Capability Model

```sql
-- Add to stores table
ALTER TABLE public.stores ADD COLUMN features JSONB NOT NULL DEFAULT '{}'::JSONB;

-- Example store.features:
{
    "virtual_try_on": true,
    "wishlist": true,
    "reviews": true,
    "comparison": false,
    "loyalty_program": true,
    "subscription": false
}

-- Add to products table
ALTER TABLE public.products ADD COLUMN capabilities JSONB NOT NULL DEFAULT '{}'::JSONB;

-- Example product.capabilities:
{
    "virtual_try_on": true,
    "ar_model_url": "https://cdn.../model.glb",
    "size_chart_url": "https://...",
    "personalization": false
}
```

### 7.3 Answer to Key Question

> **Can a new feature be enabled for a specific store without changing core platform?**

**Currently: NO** — Frontend hardcoding prevents it.

**With capability model + dynamic routing: YES** — 
1. Set `store.features.virtual_try_on = true` in DB
2. Set `product.capabilities.virtual_try_on = true` for eligible products
3. Frontend reads capability and renders `VirtualTryOn` component
4. Zero code changes to core platform

---

## 8. DATABASE DESIGN AUDIT

### 8.1 Entity Relationships & Store Isolation

```
stores (1) ──────< (N) products
    │                    │
    │                    └──< (N) product_variants
    │                              │
    │                              └──< (N) product_prices
    │                              └──< (N) product_images
    │
    ├────< (N) categories (self-referential parent_id)
    │
    ├────< (N) warehouses
    │         └──< (N) inventory_balances (warehouse_id, variant_id UNIQUE)
    │         └──< (N) inventory_reservations (store_order_id FK)
    │
    ├────< (N) store_policies (UNIQUE store_id, policy_type)
    │
    └────< (N) user_roles (store_id nullable)

orders (1) ──────< (N) store_orders (UNIQUE order_id, store_id)
    │                    └──< (N) order_items
    │
    └──< (N) payments

carts (1) ──────< (N) cart_items
    │                    └── variant_id → product_variants → products → stores
```

### 8.2 Cross-Store Data Leakage Risk — Evidence

| Risk | Current Protection | Evidence |
|------|-------------------|----------|
| User sees other store's products | **RLS + Service validation** | `categories:217` filters `store_id = :store_id`, `products:348` filters `p.store_id = :store_id` |
| Vendor edits other store's products | **RLS Policy** | `20261120000001_security_cross_store_isolation_rls.sql:72-95` — `products.store_id IN (SELECT ur.store_id...)` |
| Cart mixes stores incorrectly | **Per-store preview** | `cart:462-466` joins stores, `checkout_preview` groups by `store_id` |
| Order sees other store's items | **RLS on order_items** | `20261120000001_security_cross_store_isolation_rls.sql:13-57` — via `store_orders.store_id` |
| User sees other store's orders | **Order access control** | `orders:75-129` — `_assert_order_access` checks `user_id` OR `store_ids` |
| Inventory cross-store | **Warehouse per store** | `inventory_balances` via `warehouses.store_id` |

### 8.3 Critical Finding: User Access Control

**Can a user see another store's product/cart/order?**

**Products:** 
- Public API (`/products`) accepts optional `store_id` filter — if omitted, returns ALL stores' active products
- RLS `Products public read active` allows any authenticated user to read active products
- **Risk: LOW** — This is intentional for marketplace browsing

**Cart:**
- `cart_items` JOIN `products` → `stores` — cart shows store_name per item
- User owns cart via `carts.user_id` or `session_id`
- **Risk: NONE** — Cart is user-scoped, items naturally belong to their stores

**Orders:**
- Customer: `orders.user_id = auth.uid()` (RLS + service check)
- Vendor: `store_orders.store_id IN (user.store_ids)` (RLS + service check)
- **Risk: NONE** — Properly isolated

---

## 9. FRONTEND ROUTING AUDIT

### 9.1 Current Patterns

| Pattern | Example | Scalable? |
|---------|---------|-----------|
| Hardcoded store folder | `/aura-skin-care/page.tsx` | ❌ NO |
| Hardcoded category folder | `/aura-skin-care/categories/[slug]/page.tsx` | ❌ NO |
| Dynamic product detail | `/shop/[id]/page.tsx` | ✅ YES |
| Dynamic brand directory | `/brand-shops/page.tsx` | ✅ YES |

### 9.2 Safest Multi-Store Route Pattern

**Recommended:** `/[storeSlug]/` (single dynamic route folder)

```
/[storeSlug]/page.tsx                    → Store home (dynamic)
/[storeSlug]/categories/[slug]/page.tsx  → Category listing
/[storeSlug]/products/[id]/page.tsx      → Product detail
/shop/[id]/page.tsx                      → Store-agnostic product detail (shared cart)
/brand-shops/page.tsx                    → Store directory (keep)
```

**Why not `/store/[storeSlug]`?** — Adds unnecessary segment, `/aura-skin-care` is cleaner.

**Why not `/shop/[storeSlug]`?** — Conflicts with `/shop/[id]` product detail.

---

## 10. VIRTUAL TRY-ON SCENARIO — CONCRETE TRACE

### 10.1 User Journey Trace

```
User
  ↓
Store (Fashion Brand)  ←── Store.features.virtual_try_on = true
  ↓
Product (Dress)  ←── Product.capabilities.virtual_try_on = true, ar_model_url
  ↓
Product Detail (/fashion-brand/products/abc123)
  ↓
Virtual Try-On Component  ←── Reads product.capabilities, loads AR model
  ↓
Add to Cart  ←── Cart item: variant_id, quantity, store_id (via product)
  ↓
Cart (/shop/cart)  ←── Groups by store_id, shows Fashion Brand section
  ↓
Checkout Preview  ←── PricingService validates price per variant+store
  ↓
Order Placement  ←── Split-order: store_orders for Fashion Brand
  ↓
Stock Reservation  ←── inventory_reservations with store_order_id
  ↓
Payment  ←── payments.order_id → orders → store_orders
```

### 10.2 Architecture Conflict Points

| Step | Current Conflict | Resolution |
|------|-----------------|------------|
| Store Page | Requires new `/fashion-brand/` folder | Dynamic `[storeSlug]` route |
| Category Tabs | Hardcoded in store page | Dynamic from categories API |
| Product Detail | `/shop/[id]` works but no try-on UI | Add capability check in component |
| Theming | String-match "fashion" → generic | Use `store.features` + `store.theme` |
| Cart | Works (store_id from product) | No change needed |
| Orders | Works (split-order by store_id) | No change needed |

---

## 11. CHANGE IMPACT ANALYSIS

| Area | Current State | Risk | Required Future Change |
|------|---------------|------|------------------------|
| **Store Registry** | DB table + service + router | LOW | Add `features` JSONB, `theme` config |
| **Products** | Store-scoped, RLS protected | LOW | Add `capabilities` JSONB |
| **Categories** | Store-scoped tree | LOW | No change (already dynamic) |
| **Cart** | Shared, per-store breakdown | LOW | No change |
| **Orders** | Split-order per store | LOW | No change |
| **Frontend Routing** | Hardcoded folders per store | **CRITICAL** | Migrate to `/[storeSlug]/` dynamic routes |
| **Frontend Theming** | Hardcoded slug map + string match | **HIGH** | Config-driven from store.features/theme |
| **Frontend Components** | Mixed generic + store-specific | **HIGH** | Capability-based rendering |
| **Database** | Proper FKs, RLS, indexes | LOW | Add `features`, `capabilities` columns |
| **Feature System** | Non-existent | **HIGH** | Implement capability model |
| **Virtual Try-On** | Not implemented | MEDIUM | New module + capability integration |

---

## 12. DO NOT OVER-ENGINEER — PRAGMATIC APPROACH

### 12.1 What NOT to Build

- ❌ Plugin system / micro-frontends
- ❌ Event bus for store features
- ❌ Complex feature flag service with targeting rules
- ❌ Separate microservices per store
- ❌ Abstract "Store Engine" framework

### 12.2 Minimum Viable Architecture

**Principle:** Minimum complexity + strong isolation + future extensibility

| Layer | Change | Effort |
|-------|--------|--------|
| **DB** | Add `stores.features JSONB`, `products.capabilities JSONB` | 1 migration |
| **Backend** | No schema changes needed for core; new feature modules additive | Low |
| **Frontend Routing** | Single dynamic `[storeSlug]` route replacing hardcoded folders | Medium (1-time) |
| **Frontend Theming** | Replace `stores.ts` hardcoded maps with API-driven config | Low |
| **Frontend Components** | Capability-based conditional rendering | Low per feature |

---

## 13. FINAL VERDICT

### A. Current Architecture — Multi-Store Readiness

**Backend: READY** — Strong isolation via `store_id` FKs, RLS policies, service-layer validation, split-order architecture.

**Database: READY** — Proper relational design, foreign keys, unique constraints, indexes, RLS.

**Frontend: NOT READY** — Hardcoded routes, hardcoded slugs, string-matching theming, duplicate store pages.

**Overall: PARTIALLY READY** — Backend solid, frontend blocks new store addition.

### B. Biggest Risks (Top 10)

1. **Frontend hardcoded routes** — Every new store = new route folder + duplicated pages
2. **String-matching store detection** — `"gadget"` in name, `"skin"` in name — fragile
3. **No feature/capability model** — Cannot enable Virtual Try-On per store/product
4. **Hardcoded category tabs** — Serums/Creams vs Smartphones/Laptops per store page
5. **Hardcoded theme/color map** — Only 2 stores in `STORE_SLUG_MAP`, `BRAND_TAGLINES`
6. **No dynamic store slug routing** — `/[storeSlug]/` pattern not implemented
7. **Cart/Order frontend components** — Store label by name matching, not store_id
8. **Community not store-scoped** — Global only, no per-store community
9. **Seed data only 2 stores** — `010_seed_data.sql` hardcodes Best Gadget + Aura Skin Care
10. **Hero2D/ProductGrid/Header** — All use string matching for store-specific UI

### C. Must Fix Before New Stores

| Priority | Item | Reason |
|----------|------|--------|
| **P0** | Dynamic `[storeSlug]` routing | Enables new stores without code deployment |
| **P0** | Remove hardcoded `STORE_SLUG` constants | Single source of truth: store.slug from DB |
| **P0** | Replace string-matching with `store_id`/`slug` lookup | Reliable, not fragile |
| **P1** | Add `stores.features JSONB` column | Enables per-store feature toggles |
| **P1** | Add `products.capabilities JSONB` column | Enables per-product feature eligibility |
| **P1** | Dynamic category tabs from API | Categories vary per store |

### D. Can Wait (Nice to Have)

| Item | Reason |
|------|--------|
| Community store-scoping | Not blocking store launch |
| Advanced feature flag targeting (user segments, %) | Simple boolean JSONB sufficient for v1 |
| Store-specific webhooks/events | Not needed for core commerce |
| Multi-currency per store | Single currency (BDT) currently |

### E. Virtual Try-On Readiness

**Current: NOT READY** — Frontend cannot render it without new route folder + hardcoded logic.

**With P0/P1 Fixes: READY** — 
1. Set `store.features.virtual_try_on = true`
2. Set `product.capabilities.virtual_try_on = true` + `ar_model_url`
3. Product detail component checks capability → renders `<VirtualTryOn />`
4. Zero core changes

### F. Recommended Target Architecture

```
Aura Bell Platform
│
├── Core Platform (Shared)
│   ├── Auth & Users (profiles, roles, user_roles)
│   ├── Cart (shared, per-store breakdown)
│   ├── Orders (parent + split store_orders)
│   ├── Payments (per order)
│   ├── Inventory (warehouses per store)
│   ├── Pricing (per variant per store)
│   └── Community (global — can extend later)
│
├── Store Engine (Registry + Configuration)
│   ├── stores table (features JSONB, theme config)
│   ├── Store CRUD API
│   ├── Store Features API (GET /stores/:id/features)
│   └── Dynamic Routing: /[storeSlug]/*
│
└── Stores (Tenant Data)
    ├── Best Gadget
    │   ├── products (capabilities: comparison=true)
    │   ├── categories
    │   └── features: { comparison: true, wishlist: true }
    │
    ├── Aura Skin Care
    │   ├── products (capabilities: skin_quiz=true)
    │   ├── categories
    │   └── features: { skin_quiz: true, loyalty: true }
    │
    └── Fashion Brand (Future)
        ├── products (capabilities: virtual_try_on=true, ar_model_url)
        ├── categories
        └── features: { virtual_try_on: true, size_chart: true }
```

### G. Migration Plan

#### Phase 1: Database & Backend Foundation (Week 1)
| Task | Files | Risk | Impact |
|------|-------|------|--------|
| Add `stores.features JSONB` | Migration + `stores/schema.py` | LOW | Enables feature toggles |
| Add `products.capabilities JSONB` | Migration + `products/schema.py` | LOW | Enables product capabilities |
| Seed Fashion Brand store | `010_seed_data.sql` or admin API | LOW | Test data |

#### Phase 2: Frontend Dynamic Routing (Week 2-3)
| Task | Files | Risk | Impact |
|------|-------|------|--------|
| Create `/[storeSlug]/` route folder | `frontend/app/(storefront)/[storeSlug]/` | MEDIUM | Replaces hardcoded folders |
| Migrate store home page | `page.tsx` → dynamic from store config | MEDIUM | Single page for all stores |
| Migrate category page | `categories/[slug]/page.tsx` | MEDIUM | Dynamic categories |
| Update `hero-2d.tsx` | Use store config, not string match | LOW | Generic component |
| Update `product-grid.tsx` | Use store config, badges from features | LOW | Generic component |
| Update `header.tsx` | Dynamic store detection | LOW | Generic component |
| Update `cart-drawer.tsx` | Store label from store config | LOW | Generic component |

#### Phase 3: Feature Integration (Week 3-4)
| Task | Files | Risk | Impact |
|------|-------|------|--------|
| Virtual Try-On backend module | `modules/virtual-try-on/` | LOW | New feature |
| Virtual Try-On frontend component | `components/VirtualTryOn.tsx` | LOW | Capability-driven |
| Product detail capability check | `shop/[id]/page.tsx` | LOW | Renders if capable |
| Admin UI for features | Super-admin store edit | MEDIUM | Manage features |

#### Phase 4: Cleanup & Polish (Week 4)
| Task | Files | Risk | Impact |
|------|-------|------|--------|
| Delete hardcoded store folders | `/aura-skin-care/`, `/best-gadget/` | LOW | Remove tech debt |
| Remove `STORE_SLUG_MAP`, `CANONICAL_STORE_SLUGS` | `lib/stores.ts` | LOW | Single source of truth |
| Remove string-matching logic | All components | LOW | Reliable lookup |
| E2E test new store onboarding | — | — | Validate flow |

---

### H. Architecture Lock Recommendation

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE LOCK STATUS                         │
├─────────────────────────────────────────────────────────────────────┤
│  STORE ARCHITECTURE STATUS:     PARTIALLY READY  (Backend ✅,       │
│                                  Frontend ❌)                       │
│  MULTI-STORE STATUS:            PARTIALLY READY  (Backend ✅,       │
│                                  Frontend ❌)                       │
│  FEATURE MODULARITY:            NOT READY       (No capability     │
│                                  model, hardcoded features)         │
│  VIRTUAL TRY-ON READINESS:      NOT READY       (Frontend blocks   │
│                                  dynamic feature enablement)        │
└─────────────────────────────────────────────────────────────────────┘
```

---

### I. IMMEDIATE ACTIONS — Code Change vs No Code Change

| Action | Code Change? | Do Now? |
|--------|--------------|---------|
| Add `stores.features` JSONB column | **YES** (migration) | ✅ YES — P0 |
| Add `products.capabilities` JSONB column | **YES** (migration) | ✅ YES — P0 |
| Create dynamic `[storeSlug]` route | **YES** (frontend) | ✅ YES — P0 |
| Delete `/aura-skin-care/` folder | **YES** (frontend) | ✅ YES — Phase 2 |
| Delete `/best-gadget/` folder | **YES** (frontend) | ✅ YES — Phase 2 |
| Remove `STORE_SLUG_MAP` | **YES** (frontend) | ✅ YES — Phase 2 |
| Virtual Try-On backend module | **YES** (new module) | ⏳ After Phase 1 |
| Virtual Try-On frontend component | **YES** (new component) | ⏳ After Phase 2 |
| **Audit only / investigate** | **NO** | ✅ DONE |

---

**Report Complete.** Backend is production-ready for multi-store. Frontend requires dynamic routing migration before new stores can be added without code deployment.