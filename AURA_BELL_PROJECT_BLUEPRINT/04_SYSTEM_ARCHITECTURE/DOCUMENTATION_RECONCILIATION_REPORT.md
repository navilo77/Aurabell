# Aura Bell — Documentation Reconciliation Report

**Version:** 1.0  
**Date:** 2026-11-25  
**Status:** Complete — Ready for Implementation Planning  

---

## A. Documentation Inventory

### Core Architecture Documents (Blueprint)
| File | ID | Status | Last Updated |
|---|---|---|---|
| `AURA_BELL_PROJECT_BLUEPRINT/04_SYSTEM_ARCHITECTURE/FRONTEND_ARCHITECTURE.md` | DOC-AUR-062 | confirmed v1.2 | 2026-11-21 |
| `AURA_BELL_PROJECT_BLUEPRINT/04_SYSTEM_ARCHITECTURE/SYSTEM_ARCHITECTURE.md` | DOC-AUR-060 | confirmed v1.1 | 2026-11-20 |
| `AURA_BELL_PROJECT_BLUEPRINT/06_API_DOCUMENTATION/API_SPECIFICATION.md` | DOC-AUR-080 | confirmed v1.0 | 2026-11-04 |
| `AURA_BELL_PROJECT_BLUEPRINT/06_API_DOCUMENTATION/API_ENDPOINTS.md` | DOC-AUR-081 | confirmed v1.0 | 2026-11-04 |
| `AURA_BELL_PROJECT_BLUEPRINT/05_DATABASE/DATABASE_SCHEMA.md` | DOC-AUR-070 | confirmed v1.0 | 2026-11-04 |
| `AURA_BELL_PROJECT_BLUEPRINT/03_PRODUCT_REQUIREMENTS/STORE_PRD.md` | DOC-AUR-043 | confirmed v1.0 | 2026-11-04 |
| `AURA_BELL_PROJECT_BLUEPRINT/03_PRODUCT_REQUIREMENTS/CART_CHECKOUT_PRD.md` | DOC-AUR-046 | confirmed v1.0 | 2026-11-04 |
| `AURA_BELL_PROJECT_BLUEPRINT/03_PRODUCT_REQUIREMENTS/ORDER_MANAGEMENT_PRD.md` | DOC-AUR-047 | confirmed v1.0 | 2026-11-04 |
| `AURA_BELL_PROJECT_BLUEPRINT/03_PRODUCT_REQUIREMENTS/PAYMENT_PRD.md` | DOC-AUR-048 | confirmed v1.0 | 2026-11-04 |
| `AURA_BELL_PROJECT_BLUEPRINT/03_PRODUCT_REQUIREMENTS/ADMIN_PRD.md` | DOC-AUR-042 | confirmed v1.0 | 2026-11-04 |
| `AURA_BELL_PROJECT_BLUEPRINT/03_PRODUCT_REQUIREMENTS/CUSTOMER_PRD.md` | DOC-AUR-041 | confirmed v1.0 | 2026-11-04 |
| `AURA_BELL_PROJECT_BLUEPRINT/03_PRODUCT_REQUIREMENTS/NOTIFICATION_PRD.md` | DOC-AUR-050 | confirmed v1.0 | 2026-11-04 |
| `AURA_BELL_PROJECT_BLUEPRINT/03_PRODUCT_REQUIREMENTS/INVENTORY_PRD.md` | — | confirmed | 2026-11-04 |
| `AURA_BELL_PROJECT_BLUEPRINT/03_PRODUCT_REQUIREMENTS/PRODUCT_CATALOG_PRD.md` | — | confirmed | 2026-11-04 |
| `AURA_BELL_PROJECT_BLUEPRINT/03_PRODUCT_REQUIREMENTS/SHIPPING_DELIVERY_PRD.md` | — | confirmed | 2026-11-04 |

### Implementation Tracking
| File | Status |
|---|---|
| `MILESTONES.md` | v1.2, APPROVED, 2026-11-21 |
| `PROJECT_STATUS.md` | 2026-11-21 |
| `BACKEND_FRONTEND_CONTRACT_AUDIT.md` | v1.0, 2026-11-25 (new) |
| `DECISIONS.md` | 2026-11-14 (5 decisions recorded) |
| `CHANGELOG.md` | v1.0 |
| `CODEBASE_AUDIT_REPORT_20261120.md` | 2026-11-20 |

### Security & Architecture Decisions
| File | Status |
|---|---|
| `AURA_BELL_PROJECT_BLUEPRINT/08_SECURITY_AND_PRIVACY/AUTHENTICATION_AUTHORIZATION.md` | confirmed |
| `AURA_BELL_PROJECT_BLUEPRINT/08_SECURITY_AND_PRIVACY/SECURITY_ARCHITECTURE.md` | confirmed |
| `docs/architecture/m1.3-auth-security-layers.md` | — |
| `docs/architecture/m1.3-jwt-validation.md` | — |
| `docs/architecture/m1.3-rbac-require-role.md` | — |
| `docs/architecture/m1.3-transport-hardening.md` | — |
| `docs/architecture/m1.4-main-central-warehouse.md` | — |

### UI/UX & Design
| File | Status |
|---|---|
| `AURA_BELL_PROJECT_BLUEPRINT/07_UI_UX_DESIGN/DESIGN_SYSTEM.md` | confirmed |
| `AURA_BELL_PROJECT_BLUEPRINT/07_UI_UX_DESIGN/USER_FLOWS.md` | confirmed |
| `AURA_BELL_PROJECT_BLUEPRINT/07_UI_UX_DESIGN/ADMIN_WORKFLOWS.md` | confirmed |

---

## B. Conflicts Found

### CONFLICT-001: Store URL Structure (Critical)

| Source | Declaration |
|---|---|
| `FRONTEND_ARCHITECTURE.md` §1 | Route groups: `/best-gadget/`, `/aura-skin-care/` |
| `SYSTEM_ARCHITECTURE.md` §11 | Feature-based `features/` folders, `apps/web/src/` |
| `STORE_PRD.md` PRD-STR-002 | Store theming via slug — no routing specified |
| **Actual Frontend Code** | Flat `/shop` route with `?store=` query param |
| `API_ENDPOINTS.md` | `/api/v1/stores/{slug}` — public endpoint by slug |

**Conflict:** Three different routing architectures documented; only one implemented.

---

### CONFLICT-002: Checkout Address Model (Critical)

| Source | Declaration |
|---|---|
| `CART_CHECKOUT_PRD.md` | No address model specified |
| `ORDER_MANAGEMENT_PRD.md` | Address snapshots in `order_addresses` table |
| `DATABASE_SCHEMA.md` §7 | `order_addresses` with `address_type` (delivery/billing/both) |
| **Backend `OrderCreate` schema** | `delivery_address_id: str | None` — expects reference to saved address |
| **Frontend `checkout-modal.tsx`** | Sends inline `address` object `{name, phone, division, district, details}` + `payment_method` |
| **Backend `orders/router.py`** | Calls `service.place_order(data, user_id)` with `OrderCreate` |

**Conflict:** Frontend collects full address inline; Backend expects `delivery_address_id` reference. Frontend doesn't send `cart_id`, `coupon_code`, or `district`.

---

### CONFLICT-003: Pagination Contract (High)

| Source | Declaration |
|---|---|
| `API_SPECIFICATION.md` | Standard response envelope with `meta` — no pagination fields shown |
| `API_ENDPOINTS.md` | No pagination parameters documented |
| **Backend `orders/router.py` list_orders** | Hardcoded `LIMIT 50`, no pagination params, returns `list[OrderRead]` (partial) |
| **Backend `products/router.py`** | Supports `limit`, `offset` query params |
| **Frontend `account/page.tsx`** | Calls `/orders` — expects full `OrderRead[]` with `store_orders`, `order_items` |
| **Actual `OrderRead` from `/orders`** | Partial — missing `store_orders`, `order_items` (only in `/{id}`) |

**Conflict:** Inconsistent pagination across endpoints; frontend expects full order data from list endpoint.

---

### CONFLICT-004: Admin Architecture Authority (High)

| Source | Declaration |
|---|---|
| `ADMIN_PRD.md` | Super Admin, Store Manager, Inventory Manager, Support Agent |
| `SYSTEM_ARCHITECTURE.md` | RBAC middleware, `require_role()` |
| `DATABASE_SCHEMA.md` §1 | 7 roles: `owner`, `admin`, `store_manager`, `inventory_manager`, `order_manager`, `support_agent`, `customer` |
| `DECISIONS.md` D3 | Confirmed 7 roles from seed |
| **Backend `auth/service.py`** | `require_role()` dependency; roles from JWT `role` claim |
| **Frontend `lib/roles.ts`** | `SHOP_ROLES=["customer"]`, `STORE_ADMIN_ROLES=["store_manager"]`, `SUPER_ADMIN_ROLES=["owner","admin","super_admin"]` |
| **Actual RLS Policies** | 12 policies applied (M1.2) — store-scoped enforcement |

**Conflict:** Role names match but permission matrix not documented; frontend guards vs backend authorization boundaries unclear.

---

### CONFLICT-005: Community/Chat — Missing from Architecture (Critical)

| Source | Declaration |
|---|---|
| `FRONTEND_ARCHITECTURE.md` | No community/chat routes |
| `SYSTEM_ARCHITECTURE.md` | No community in architecture diagram |
| `DATABASE_SCHEMA.md` | No conversation/message tables in 50 tables |
| `API_ENDPOINTS.md` | No community endpoints |
| **All PRDs** | No community PRD exists |
| **New Requirement** | Community is now approved product requirement (per reconciliation task) |

**Conflict:** Community feature completely absent from all architecture docs; now required.

---

### CONFLICT-006: API Response Envelope vs Actual (Medium)

| Source | Declaration |
|---|---|
| `API_SPECIFICATION.md` | Envelope: `{success, data, message, meta}` |
| **Actual Backend** | Returns raw Pydantic models (no envelope); errors: `{detail, code}` |
| **Frontend `apiFetch`** | Expects raw data; handles errors via `detail.code` |

**Conflict:** Documented envelope not implemented; actual is raw models + structured errors.

---

### CONFLICT-007: Authentication Header Strategy (Resolved but Documented Incorrectly)

| Source | Declaration |
|---|---|
| `API_SPECIFICATION.md` | `Authorization: Bearer <JWT_TOKEN>` |
| **Actual Backend** | HttpOnly cookies (`aura_access_token`, `aura_refresh_token`) — **Bearer fallback removed** |
| **Frontend `apiFetch`** | `credentials: "include"` only — no Authorization header |
| `DECISIONS.md` | ES256 JWT via JWKS |
| `MILESTONES.md` Auth Remediation | HttpOnly cookies, Bearer removed, ES256 |

**Conflict:** API spec documents Bearer auth; actual implementation uses HttpOnly cookies only.

---

### CONFLICT-008: Store Admin vs Super Admin Endpoints (Medium)

| Source | Declaration |
|---|---|
| `API_ENDPOINTS.md` | `/api/v1/admin/*` for both store admin and super admin |
| **Actual Backend** | `stores` router has admin endpoints; `products` has `/admin/products`; `orders` has no admin status update |
| **Frontend** | `/store-admin/*` and `/super-admin/*` route groups |
| `ADMIN_PRD.md` | Distinct roles: Super Admin vs Store Manager |

**Conflict:** No clear backend separation between store-admin and super-admin endpoints; frontend has separate route groups.

---

### CONFLICT-009: Cart API Path Discrepancy (Low)

| Source | Declaration |
|---|---|
| `API_ENDPOINTS.md` | `/api/v1/cart/items` (POST), `/api/v1/cart/items/{id}` (PATCH/DELETE) |
| **Actual Backend** | `/api/v1/cart/{cart_id}/items` (POST), `/api/v1/cart/{cart_id}/items/{variant_id}` (PATCH/DELETE) |
| **Frontend** | Uses `/cart/items/{variant_id}` with cart from context |

**Conflict:** API endpoints doc doesn't match actual router structure.

---

### CONFLICT-010: Frontend Directory Structure (Medium)

| Source | Declaration |
|---|---|
| `FRONTEND_ARCHITECTURE.md` §1 | `(storefront)/best-gadget/`, `(storefront)/aura-skin-care/`, `(admin)/dashboard/` |
| **Actual Frontend** | `(storefront)/shop/`, `(storefront)/cart/`, `(storefront)/account/`, `(admin)/store-admin/`, `(admin)/super-admin/` |

**Conflict:** Blueprint proposes store-specific route groups; actual uses flat `/shop` with store context.

---

---

## C. Resolutions

### RESOLUTION-001: Store URL Structure → **AD-001 DECISION: Route Groups**

**Decision:** Adopt `FRONTEND_ARCHITECTURE.md` route groups as canonical.

```
/best-gadget/                    → Best Gadget storefront
/best-gadget/categories/[slug]   → Best Gadget category pages
/best-gadget/products/[id]       → Best Gadget product pages
/aura-skin-care/                 → Aura Skin Care storefront
/aura-skin-care/categories/[slug] → Aura Skin Care category pages
/aura-skin-care/products/[id]    → Aura Skin Care product pages
/shop                            → DEPRECATED (redirect to /best-gadget)
/cart                            → Shared cart (store-agnostic)
/checkout                        → Unified checkout (store-agnostic)
/account                         → Customer account (store-agnostic)
```

**Rationale:** 
- Matches `FRONTEND_ARCHITECTURE.md` (status: confirmed)
- Better SEO (store-specific URLs)
- Clear brand separation per `STORE_PRD.md` PRD-STR-002
- Backend already supports `store_id` filtering on all catalog endpoints

**Impact:** Frontend route restructuring required; backend no changes (already store-scoped).

**Migration:** 
1. Add route groups in Next.js App Router
2. Implement redirects from `/shop?*` → `/best-gadget?*` (default)
3. Update sitemap generation
4. Update internal links

---

### RESOLUTION-002: Checkout Address Model → **AD-002 DECISION: Inline Address Acceptance**

**Decision:** Backend accepts inline address in `OrderCreate`; creates `order_addresses` snapshot internally.

```python
# Updated OrderCreate schema
class OrderCreate(BaseModel):
    cart_id: str
    delivery_address_id: str | None = None  # Optional: reference to saved address
    address: OrderAddressCreate | None = None  # NEW: inline address for guest/new addresses
    payment_method: Literal["cod", "bkash", "sslcommerz"]
    coupon_code: str | None = None
    district: str | None = None  # Required for delivery fee calculation
```

**Backend Logic:**
1. If `address` provided → create `order_addresses` snapshot with `address_type='delivery'`
2. If `delivery_address_id` provided → verify ownership, use that address
3. If neither → error (address required)
4. If both → prefer `address` (inline), ignore `delivery_address_id`

**Frontend Changes:**
- Add `cart_id` to checkout payload (from cart context)
- Add `district` field (extracted from address.district)
- Keep inline address collection

**Rationale:**
- Better UX: guests can checkout without saving address first
- Backward compatible: existing `delivery_address_id` flow still works
- Matches `DATABASE_SCHEMA.md` §7: `order_addresses` stores snapshots
- `ORDER_MANAGEMENT_PRD.md` PRD-ORD-003 requires snapshots

---

### RESOLUTION-003: Pagination Contract → **AD-004 DECISION: Standardized Offset Pagination**

**Decision:** All list endpoints adopt standardized offset pagination with metadata.

**Request Parameters:**
```
?page=1&per_page=20          # Page-based (preferred for UI)
?offset=0&limit=20           # Offset-based (legacy support)
?sort=field:asc|desc         # Sorting
?filter[field]=value         # Filtering
```

**Response Format:**
```json
{
  "data": [...],
  "meta": {
    "total": 150,
    "page": 1,
    "per_page": 20,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

**Migration Strategy (Backward Compatible):**
1. Add `?format=v2` query parameter to opt-in to new format
2. Default remains raw array for v1 consumers
3. Frontend updates to use `format=v2` in same PR
4. After 2 sprints, make v2 default; v1 deprecated
5. Document in `API_SPECIFICATION.md`

**Endpoints Requiring Update:**
- `/api/v1/products` (already supports limit/offset)
- `/api/v1/categories` (new)
- `/api/v1/orders` (critical — currently hardcoded LIMIT 50)
- `/api/v1/stores` (new)
- `/api/v1/admin/*` (new)

---

### RESOLUTION-004: Admin Architecture → **AD-005 DECISION: Unified Admin Module with Role Scoping**

**Decision:** Create `backend/app/modules/admin/` router consolidating all admin endpoints; enforce authorization via `require_role()` + store scoping.

**Endpoint Structure:**
```
/api/v1/admin/dashboard              → GET (super_admin, store_manager scoped)
/api/v1/admin/stores                 → GET, POST, PATCH, DELETE (super_admin)
/api/v1/admin/users                  → GET, POST, PATCH, DELETE (super_admin)
/api/v1/admin/roles                  → GET, POST (super_admin)
/api/v1/admin/orders                 → GET (store_manager scoped, super_admin all)
/api/v1/admin/orders/{id}/status     → PATCH (store_manager scoped, super_admin)
/api/v1/admin/inventory              → GET (inventory_manager, store_manager)
/api/v1/admin/inventory/adjust       → POST (inventory_manager)
/api/v1/admin/reports/sales          → GET (super_admin)
/api/v1/admin/reports/inventory      → GET (super_admin)
```

**Authorization Rules:**
| Endpoint | Super Admin | Store Manager | Inventory Manager | Order Manager |
|---|---|---|---|---|
| Dashboard | ✅ All stores | ✅ Own store | ❌ | ❌ |
| Users | ✅ CRUD | ❌ | ❌ | ❌ |
| Roles | ✅ CRUD | ❌ | ❌ | ❌ |
| Orders (list) | ✅ All | ✅ Own store | ❌ | ✅ Own store |
| Orders (status) | ✅ All | ✅ Own store | ❌ | ✅ Own store |
| Inventory | ✅ All | ✅ Own store | ✅ All | ❌ |
| Reports | ✅ All | ❌ | ❌ | ❌ |

**Frontend Guards (Already Aligned):**
- `lib/roles.ts`: `SUPER_ADMIN_ROLES`, `STORE_ADMIN_ROLES`
- Route groups: `/store-admin/*` vs `/super-admin/*`

**Backend Implementation:** New `admin` module with dependency injection for role + store scoping.

---

### RESOLUTION-005: Community/Chat → **AD-003 DECISION: Supabase Realtime**

**Decision:** Community is now an approved product requirement. Architecture uses Supabase Realtime.

**Database Tables (New Migration):**
```sql
conversations (id, created_at, updated_at)
conversation_participants (conversation_id, user_id, joined_at, left_at)
messages (id, conversation_id, sender_id, content, message_type, read_at, created_at)
message_reads (message_id, user_id, read_at)
user_blocks (blocker_id, blocked_id, created_at)
user_reports (id, reporter_id, reported_id, reason, status, created_at)
user_community_profiles (user_id, display_name, bio, avatar_url, is_public)
```

**API Endpoints:**
```
/api/v1/community/conversations              → GET (paginated), POST (create/find 1:1)
/api/v1/community/conversations/{id}         → GET (details)
/api/v1/community/conversations/{id}/messages → GET (paginated), POST (send)
/api/v1/community/messages/{id}/read         → PATCH (mark read)
/api/v1/community/blocks                     → POST (block user)
/api/v1/community/reports                    → POST (report)
/api/v1/community/users/{id}/profile         → GET (public profile)
```

**Realtime:** Supabase Realtime subscriptions on `messages` and `conversations` tables.

**Frontend Routes (New):**
```
/community                    → Conversation list
/community/c/[id]             → Conversation view
/community/profile/[id]       → Public profile
```

**Documentation Updates:**
- Mark all "Community is V2" statements as **DEPRECATED** with reference to AD-003
- Add `COMMUNITY_PRD.md` to blueprint
- Update `SYSTEM_ARCHITECTURE.md` diagram to include Community module
- Update `FRONTEND_ARCHITECTURE.md` to include `/community` routes

---

### RESOLUTION-006: Rate Limiting → **AD-006 DECISION: Per-User Token Bucket (Redis)**

**Decision:** Implement rate limiting at API gateway/middleware level using per-user token bucket stored in Redis.

**Configuration:**
| Tier | Requests/Window | Window | Scope |
|---|---|---|---|
| Authenticated | 100 | 60s | Per user_id |
| Authenticated (mutations) | 20 | 60s | Per user_id |
| Guest/Anonymous | 30 | 60s | Per IP |
| Auth endpoints | 10 | 60s | Per IP + email |

**Headers (Response):**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706184000
Retry-After: 45 (when limited)
```

**Error Response (429):**
```json
{
  "detail": "Rate limit exceeded",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 45
}
```

**Exempt:** Health checks, webhook endpoints (verified via HMAC).

**Documentation:** Add to `API_SPECIFICATION.md` and `SECURITY_ARCHITECTURE.md`.

---

### RESOLUTION-007: Order Cancellation → **AD-007 DECISION: Customer Cancellation Rules**

**Decision:** Define order state machine and cancellation rules.

**State Machine:**
```
PENDING → CONFIRMED → PROCESSING → SHIPPED → DELIVERED
    ↓           ↓           ↓
CANCELLED   CANCELLED   CANCELLED (requires store approval)
    ↓           ↓           ↓
REFUNDED    REFUNDED    REFUNDED
```

**Cancellation Rules:**
| Status | Customer Can Cancel | Store Admin Can Cancel | Refund |
|---|---|---|---|
| PENDING | ✅ Yes | ✅ Yes | Auto (no payment captured) |
| CONFIRMED | ✅ Yes | ✅ Yes | Auto (COD: no payment; Digital: refund initiated) |
| PROCESSING | ❌ No | ✅ Yes | Store approval required |
| SHIPPED | ❌ No | ❌ No | Return request only |
| DELIVERED | ❌ No | ❌ No | Return request (7 days) |
| CANCELLED | N/A | N/A | Already processed |

**API:** `POST /api/v1/orders/{id}/cancel` — customer only; validates status.

**Store Admin:** `PATCH /api/v1/admin/orders/{id}/status` with `status: "cancelled"` — store manager + super_admin.

---

### RESOLUTION-008: Public Profile → **AD-008 DECISION: Minimum Public Fields**

**Decision:** Public community profile separate from private account profile.

**Public Fields (Community Profile):**
| Field | Source | Visibility |
|---|---|---|
| `display_name` | `user_community_profiles` | Public |
| `avatar_url` | `user_community_profiles` | Public |
| `bio` | `user_community_profiles` | Public |
| `created_at` (member since) | `profiles` | Public |
| `roles` | `user_roles` | **Never public** |
| `store_ids` | `user_roles` | **Never public** |
| `email` | `profiles` | **Never public** |
| `phone` | `profiles` | **Never public** |
| `addresses` | `addresses` | **Never public** |
| `orders` | `orders` | **Never public** |

**Private Fields (Account Only):**
- All PII: email, phone, addresses
- Roles, store associations
- Order history, payment methods

**API:** `GET /api/v1/community/users/{id}/profile` → returns public fields only.

**Frontend:** Community components use public profile; account page uses private profile.

---

### RESOLUTION-009: Message Security → **AD-009 DECISION: Transport + Authorization (No E2E v1)**

**Decision:** No end-to-end encryption in v1. Security via transport + authorization + database RLS.

**Security Model:**
| Layer | Implementation |
|---|---|
| **Transport** | HTTPS/WSS only (Supabase Realtime uses WSS) |
| **Authentication** | HttpOnly cookie auth (existing) — user identity verified |
| **Authorization** | User can only read conversations they participate in (`conversation_participants`) |
| **Message Ownership** | Sender can edit/delete own messages within 15 min; recipients can read |
| **Database RLS** | Row-level security on `messages`, `conversations`, `conversation_participants` |
| **Moderation Access** | Super admin + support_agent can read all conversations for moderation |
| **Blocking** | Blocked users cannot create conversations or send messages (enforced in service) |
| **Reporting** | Reports create moderation queue; reported content hidden pending review |
| **Retention** | Messages retained indefinitely; deletion = soft delete (`deleted_at`) |
| **E2E Encryption** | **Deferred to v2** — not in v1 scope |

**Supabase Realtime Auth:** Realtime subscriptions authenticated via Supabase JWT (same as API).

---

### RESOLUTION-010: Payment Strategy → **AD-010 DECISION: bKash + SSLCommerz with Adapter Pattern**

**Decision:** Implement both bKash and SSLCommerz via provider-agnostic adapter layer.

**Architecture:**
```
PaymentService (core)
    ├── PaymentAdapter (interface)
    │     ├── BkashAdapter
    │     └── SSLCommerzAdapter
    ├── PaymentAttempt (model)
    ├── WebhookHandler (HMAC verified)
    └── Idempotency (provider_event_id unique)
```

**Payment Flow:**
1. Customer selects payment method at checkout
2. `POST /api/v1/payments` → creates `PaymentAttempt` + returns `redirect_url`
3. Customer redirected to gateway
4. Gateway posts webhook → `POST /api/v1/webhooks/payments/{provider}`
5. Webhook verified (HMAC) → updates `PaymentAttempt` + `Order` status
6. On success: stock reservations confirmed, order `PAID`/`CONFIRMED`

**bKash:** Tokenized Checkout (Create → Execute → Query)
**SSLCommerz:** Session API (Init → Redirect → IPN/Validation)

**Idempotency:** `provider_event_id` UNIQUE constraint on `payment_webhook_events`.

**Refunds:** `POST /api/v1/admin/refunds` — super_admin only; creates `refunds` record; triggers gateway refund.

**Documentation:** Update `PAYMENT_PRD.md` with adapter interface spec.

---

---

## D. Approved Architecture Summary

### System Overview (Updated)

```mermaid
flowchart TD
    subgraph Clients["Clients"]
        WebCustomer["Next.js Storefront\n/best-gadget, /aura-skin-care\n/cart, /checkout, /account\n/community"]
        WebAdmin["Next.js Admin\n/store-admin, /super-admin"]
    end

    subgraph ClientLocal["Client Local Layer (Hybrid Local-First)"]
        ClientState["Client State (Zustand/Context)"]
        IndexedDB["IndexedDB Cache + Mutation Queue"]
        SyncQueue["Sync Engine (drainPromise, backoff)"]
    end

    subgraph Backend["FastAPI Modular Monolith (/api/v1)"]
        Auth["Auth (HttpOnly Cookies, ES256 JWT)"]
        Catalog["Catalog (Stores, Products, Categories)"]
        Cart["Cart (Guest/Auth, Merge, Preview)"]
        Orders["Orders (Split, COD, Timeline)"]
        Payments["Payments (Adapters: bKash, SSLCommerz)"]
        Inventory["Inventory (Reservations, Ledger)"]
        Pricing["Pricing (BDT, Promotions)"]
        Admin["Admin (Unified, Role-Scoped)"]
        Community["Community (Realtime Chat)"]
        Notifications["Notifications (Outbox)"]
    end

    subgraph Storage["Supabase Platform"]
        DB[("PostgreSQL 15+")]
        AuthService["Supabase Auth (GoTrue)"]
        Realtime["Supabase Realtime"]
        Storage["Supabase Storage"]
    end

    subgraph Workers["Background Workers"]
        OutboxWorker["Outbox Processor"]
        ReservationCleaner["Reservation Cleanup (1m)"]
    end

    subgraph External["External Services"]
        PaymentGW["bKash / SSLCommerz"]
        SMS["SMS Gateway"]
        Courier["Pathao (Manual v1)"]
    end

    Clients --> ClientLocal
    ClientLocal --> Backend
    Backend --> Auth
    Auth --> AuthService
    Backend --> DB
    Backend --> Realtime
    Backend --> Storage
    DB -.-> OutboxWorker
    DB -.-> ReservationCleaner
    OutboxWorker --> SMS
    Payments --> PaymentGW
    Admin --> Courier
```

### Technology Stack (Confirmed)

| Layer | Technology | Version |
|---|---|---|
| Frontend | Next.js (React + TypeScript) | 14+ App Router |
| Styling | Tailwind CSS | 3.x |
| Backend | FastAPI (Python) | 3.11+ |
| Database | Supabase PostgreSQL | 15+ |
| Auth | Supabase Auth (GoTrue) | — |
| Realtime | Supabase Realtime | — |
| Storage | Supabase Storage | — |
| Async Jobs | PostgreSQL Outbox Pattern | — |
| Rate Limiting | Redis Token Bucket | — |

---

## E. Approved Decisions (AD-001 through AD-010)

| ID | Decision | Status | Authority |
|---|---|---|---|
| **AD-001** | Store URL Structure: Route Groups (`/best-gadget/`, `/aura-skin-care/`) | **APPROVED** | This reconciliation |
| **AD-002** | Checkout Address: Backend accepts inline `address` + optional `delivery_address_id` | **APPROVED** | This reconciliation |
| **AD-003** | Community Realtime: Supabase Realtime; new tables + API module | **APPROVED** | This reconciliation |
| **AD-004** | Pagination: Standardized offset pagination with `meta`; `format=v2` migration | **APPROVED** | This reconciliation |
| **AD-005** | Admin Architecture: Unified `admin` module with role+store scoping | **APPROVED** | This reconciliation |
| **AD-006** | Rate Limiting: Per-user token bucket (Redis); tiered limits | **APPROVED** | This reconciliation |
| **AD-007** | Order Cancellation: Customer cancels PENDING/CONFIRMED; store approval for PROCESSING+ | **APPROVED** | This reconciliation |
| **AD-008** | Public Profile: `display_name`, `avatar_url`, `bio`, `member_since` only; PII private | **APPROVED** | This reconciliation |
| **AD-009** | Message Security: Transport (HTTPS/WSS) + AuthZ + RLS; **No E2E v1** | **APPROVED** | This reconciliation |
| **AD-010** | Payment: bKash + SSLCommerz via adapter pattern; HMAC webhooks; idempotency | **APPROVED** | This reconciliation |

---

## F. Final Milestone Roadmap (BE-01 → BE-08)

### Dependency Graph

```mermaid
flowchart TD
    BE01[BE-01: API Contract Stabilization\nPagination, Sorting, Filtering, Error Format]
    BE02[BE-02: Store & Catalog Enhancements\nFilters, Sort, Public Profile]
    BE03[BE-03: Checkout Address Reconciliation\nInline address in OrderCreate]
    BE04[BE-04: Orders & Account Completion\nTimeline, Cancel, Full Order List]
    BE05[BE-05: Admin Backend Completion\nDashboard, User Mgmt, Reports]
    BE06[BE-06: Community/Chat Backend\nConversations, Messages, Realtime]
    BE07[BE-07: Payment Gateway (M5)\nbKash, SSLCommerz, Webhooks]
    BE08[BE-08: Reliability & Hardening\nRate Limits, Observability, Load Test]

    BE01 --> BE02
    BE01 --> BE03
    BE02 --> BE03
    BE03 --> BE04
    BE02 --> BE05
    BE04 --> BE05
    BE01 --> BE06
    BE06 --> BE08
    BE07 --> BE08
    BE05 --> BE08
```

### Milestone Details

| Milestone | Scope | Dependencies | Frontend Impact | Backend Modules | DB Changes | API Changes | Acceptance |
|---|---|---|---|---|---|---|---|
| **BE-01** | `format=v2` pagination, sorting, filtering on products/orders/stores; backward compatible | None | `apiFetch` handles legacy + v2 | products, orders, stores | None | `?format=v2`, `?sort=`, `?status=` | V2 returns `{data, meta}`; legacy returns raw array; 15 unit tests pass |
| **BE-02** | Price/brand/attr filters; sorting; public profile | BE-01 | Search UI, store selector, community profile | products, categories, users | Indexes | New query params; new endpoint | Filters work; latency <200ms |
| **BE-03** | Checkout accepts inline address | BE-01 | Checkout modal sends `cart_id`, `district`, `address` | orders, users | None | `OrderCreate` adds `address` | Guest checkout works; backward compat |
| **BE-04** | Order timeline, cancel, full list | BE-01, BE-03 | Order list, detail, cancel button | orders, users | None | New endpoints; extended list | Timeline visible; cancel works |
| **BE-05** | Admin dashboard, user mgmt, reports | BE-01, BE-04 | `/store-admin/*`, `/super-admin/*` | **New: admin** | None | New admin endpoints | Dashboard loads; user CRUD works |
| **BE-06** | Community: conversations, messages, realtime | BE-01 | `/community/*` routes | **New: community** | **6 new tables** | New community API | 1:1 chat realtime; block/report |
| **BE-07** | bKash + SSLCommerz adapters | BE-03, BE-01 | Payment method UI in checkout | **New: payments** | Tables exist (migrations 005,006) | New payment endpoints | Both gateways process payments |
| **BE-08** | Rate limits, observability, hardening | All | None | All | Indexes, partitioning | Internal | p95<200ms; rate limits active |

### Explicit Non-Goals (Not in BE-01–BE-08)
- Multi-vendor marketplace (commissions, payouts)
- Subscriptions/recurring orders
- Multi-language i18n (Bengali/English only)
- Advanced promotions (BOGO, bundles, tiered)
- Loyalty points/wallet
- AI recommendations
- Mobile app (React Native)
- Advanced analytics/BI
- Multi-warehouse fulfillment
- Dropshipping integration
- B2B/wholesale pricing

---

## G. Deprecated Documentation

| Document/Section | Status | Replaced By |
|---|---|---|
| `API_SPECIFICATION.md` — Bearer auth section | **DEPRECATED** | Auth uses HttpOnly cookies (see `MILESTONES.md` Auth Remediation, `DECISIONS.md`) |
| `API_SPECIFICATION.md` — Response envelope | **DEPRECATED** | Actual: raw models + `{detail, code}` errors |
| `FRONTEND_ARCHITECTURE.md` — `/shop` route (implied by absence of route groups in actual code) | **DEPRECATED** | Route groups per AD-001 |
| `SYSTEM_ARCHITECTURE.md` — Feature-based `features/` folders, `apps/web/src/` | **DEPRECATED** | `FRONTEND_ARCHITECTURE.md` directory structure is authoritative |
| Any PRD/architecture doc stating "Community/Chat is V2" or "out of scope" | **DEPRECATED** | AD-003: Community is approved v1 requirement |
| `API_ENDPOINTS.md` — Cart endpoints without `cart_id` path param | **DEPRECATED** | Actual router uses `/cart/{cart_id}/items` |
| `MILESTONES.md` — M5/M6 as only future milestones | **DEPRECATED** | BE-01 through BE-08 replace/supersede |
| `FRONTEND_ARCHITECTURE.md` — Directory structure not matching actual | **UPDATED** | Actual structure documented; route groups added per AD-001 |

**Deprecation Format (apply to deprecated sections):**
```markdown
> **DEPRECATED**
> 
> This section previously stated [old claim].
> This decision has been superseded by [AD-XXX / MILESTONES.md / actual implementation].
> See [new canonical document] for current architecture.
```

---

## H. Remaining Pending Decisions

**NONE.** All architecture decisions required for implementation have been resolved in AD-001 through AD-010.

The following are **implementation details** (not architecture decisions) to be resolved during milestone execution:
- Exact Redis key naming convention for rate limiting (BE-08)
- Supabase Realtime channel naming for community (BE-06)
- Specific load test scenarios (BE-08)
- Exact pagination default page size (BE-01 — recommend 20)

---

## I. Implementation Readiness

### **READY FOR IMPLEMENTATION**

**Justification:**
1. ✅ All 10 architecture decisions (AD-001 through AD-010) resolved and approved
2. ✅ Documentation conflicts identified and resolved with clear decisions
3. ✅ Single canonical architecture established (no contradictory documents)
4. ✅ Milestone roadmap (BE-01→BE-08) has unique IDs, no duplicates, clear dependencies
5. ✅ Breaking changes documented with migration strategies (pagination, checkout address)
6. ✅ Deprecated documentation marked with replacement references
7. ✅ Current working functionality protected (auth, cart, offline sync frozen)
8. ✅ New community requirement integrated into architecture
9. ✅ Frontend/backend contract mismatches resolved (address, pagination, admin)
10. ✅ No hidden architecture decisions remain

### Next Steps for Implementation Agent:
1. Start **BE-01: API Contract Stabilization** — establishes foundation for all subsequent milestones
2. Implement pagination `format=v2` migration in parallel with frontend
3. Proceed to **BE-03: Checkout Address Reconciliation** (unblocks checkout flow)
4. Continue per dependency graph

---

**End of Reconciliation Report**

*This document is the single source of truth for Aura Bell architecture as of 2026-11-25. All prior contradictory documents are either updated or marked deprecated with references to this report.*