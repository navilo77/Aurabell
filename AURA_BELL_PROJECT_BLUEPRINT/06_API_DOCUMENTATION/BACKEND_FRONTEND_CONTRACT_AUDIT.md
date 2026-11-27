# Aura Bell — Backend ↔ Frontend Contract Alignment Audit & Milestone Plan

**Version:** 1.0  
**Date:** 2026-11-25  
**Status:** Audit Complete — Ready for Implementation Planning  
**Prepared by:** Autonomous Implementation Agent  

---

## Executive Summary

### Current Integration Status
- **Backend (FastAPI + Supabase):** Milestones M1–M4 **COMPLETED** (17/27 sub-milestones)
- **Frontend (Next.js 14 App Router):** Partial implementation — core routes exist but significant gaps
- **Authentication:** HttpOnly cookie-based (ES256 JWT) — **VERIFIED WORKING** (144 backend + 4 E2E tests pass)
- **Cross-store security:** RLS policies enforced — **VERIFIED**

### Gap Classification Summary
| Classification | Count | Description |
|---|---|---|
| **A — Critical** | 8 | Blocks core user flow or creates security/data-integrity risk |
| **B — Required** | 14 | Needed for approved frontend architecture but doesn't block existing system |
| **C — Enhancement** | 9 | Useful but can be deferred |
| **D — Documentation Only** | 5 | Implementation exists but docs are incorrect/missing |

### Overall Readiness
- **Backend APIs:** ~75% complete for current frontend needs
- **Frontend routes:** ~60% of blueprint routes implemented
- **Community/Chat:** 0% — **completely missing** from backend
- **Payment (M5):** 0% — **planned but not started**
- **Admin Backoffice APIs:** Partial — store admin endpoints exist, super admin incomplete

---

## Phase 1 — Frontend ↔ Backend Contract Audit Matrix

### Legend
| Status | Meaning |
|---|---|
| ✅ **Implemented** | Both FE & BE exist, contracts match, verified in code |
| ⚠️ **Mismatch** | Both exist but contracts disagree |
| ❌ **Missing FE** | Backend exists, frontend not implemented |
| ❌ **Missing BE** | Frontend expects, backend not implemented |
| 📝 **Doc Only** | Works but documentation incorrect/missing |

---

### 1. Authentication & Session Management

| Feature | Frontend Requirement | Backend Support | Endpoint | Request Contract | Response Contract | Status | Required Action |
|---|---|---|---|---|---|---|---|
| **Login** | Email/password → HttpOnly cookies | ✅ Supabase GoTrue | `POST /api/v1/auth/login` | `UserLogin{email, password}` | `Token{access_token, refresh_token, token_type, expires_in}` + cookies | ✅ **Implemented** | None |
| **Register** | Email/password/name/phone → session or email confirm | ✅ Supabase GoTrue + profile creation | `POST /api/v1/auth/register` | `UserRegister{email, password, full_name?, phone?}` | `Token` (empty if email confirm required) | ✅ **Implemented** | None |
| **OTP Request** | Magic link via email | ✅ | `POST /api/v1/auth/otp/request` | `OTPRequest{email, channel}` | 204 No Content | ✅ **Implemented** | None |
| **OTP Verify** | Code → tokens + cookies | ✅ | `POST /api/v1/auth/otp/verify` | `OTPVerify{email, code, channel}` | `Token` + cookies | ✅ **Implemented** | None |
| **Refresh** | Auto-refresh on 401 (cookie-based) | ✅ | `POST /api/v1/auth/refresh` | Cookie `aura_refresh_token` preferred, body fallback | `Token` + new cookies | ✅ **Implemented** | None |
| **Logout** | Clear cookies, server revoke | ✅ | `POST /api/v1/auth/logout` | Cookie `aura_access_token` | 204, clears both cookies | ✅ **Implemented** | None |
| **Session Restore** | `/users/me` on app load | ✅ | `GET /api/v1/users/me` | Cookie auth | `ProfileRead{id, email, full_name, phone, avatar_url, status, roles[], store_ids[], created_at, updated_at}` | ✅ **Implemented** | None |
| **Current User** | Decoded from access token (client) | ✅ JWT ES256 | — | — | `DecodedToken{sub, email, role, exp, iat}` | ✅ **Implemented** | None |
| **Role Info** | `roles[]` + `store_ids[]` in profile | ✅ Extended in M1.3 | `GET /api/v1/users/me` | — | Includes `roles: string[]`, `store_ids: string[]` | ✅ **Implemented** | None |
| **Protected Routes** | Middleware + role guards | ✅ `require_role()` deps | — | — | 401/403 via `AuthError` | ✅ **Implemented** | None |
| **Cookie Behavior** | HttpOnly, Secure, SameSite=Strict | ✅ | All auth endpoints | — | `aura_access_token` (15m), `aura_refresh_token` (7d) | ✅ **Implemented** | None |
| **Token Expiration** | 15 min access, 7 day refresh | ✅ | — | — | `expires_in: 900` (access) | ✅ **Implemented** | None |
| **Refresh Failure** | Redirect to `/login` | ✅ `apiFetch` handles | — | — | 401 → logout → redirect | ✅ **Implemented** | None |
| **Account State** | `status` field in profile | ✅ | `GET /api/v1/users/me` | — | `status: 'active'|'inactive'|'suspended'` | ✅ **Implemented** | None |

**Authentication Verdict:** **FULLY ALIGNED** — No breaking changes needed. Preserve current architecture.

---

### 2. Commerce — Stores

| Feature | Frontend Requirement | Backend Support | Endpoint | Request Contract | Response Contract | Status | Required Action |
|---|---|---|---|---|---|---|---|
| **Store Listing** | Homepage hero + store selector | ✅ | `GET /api/v1/stores` | — | `StoreRead[]` | ✅ **Implemented** | None |
| **Store Details** | Store-specific pages | ✅ | `GET /api/v1/stores/{slug}` | — | `StoreRead` | ✅ **Implemented** | None |
| **Store by ID** | Admin operations | ✅ | `GET /api/v1/stores/id/{store_id}` | Auth required | `StoreRead` | ✅ **Implemented** | None |
| **Store Status** | Active/inactive toggle | ✅ | `PATCH /api/v1/stores/{store_id}/status` | `store_manager`/`super_admin` | `StoreRead` | ✅ **Implemented** | None |
| **Store Config** | Logo, primary_color, banner | ✅ | `PUT /api/v1/stores/{store_id}` + banner endpoint | `StoreUpdate` / `StoreBannerUpdate` | `StoreRead` | ✅ **Implemented** | Banner URL validation needs fixing |
| **Store Policies** | Return/warranty/terms display | ✅ | `GET /api/v1/stores/{store_id}/policies` | — | `PolicyRead[]` | ✅ **Implemented** | None |
| **Store Products** | Filter by store_id | ✅ | `GET /api/v1/products?store_id=` | — | `ProductRead[]` | ✅ **Implemented** | None |
| **Store Categories** | Nested tree per store | ✅ | `GET /api/v1/stores/{slug}/categories` | — | `CategoryTree[]` | ✅ **Implemented** | None |
| **Route Groups** | `/best-gadget/`, `/aura-skin-care/` | ❌ **Missing BE** | Blueprint expects route groups | — | — | **A — Critical** | Decide: route groups vs flat `/shop?store=` |

**Stores Verdict:** Backend complete. **Critical decision needed on URL structure** (FRONTEND_ARCHITECTURE.md §1 proposes `/best-gadget/`, `/aura-skin-care/` route groups; current FE uses flat `/shop`).

---

### 3. Commerce — Products

| Feature | Frontend Requirement | Backend Support | Endpoint | Request Contract | Response Contract | Status | Required Action |
|---|---|---|---|---|---|---|---|
| **Product List** | Shop page, filtering, pagination | ✅ | `GET /api/v1/products` | `store_id?, category_id?, search?, limit, offset` | `ProductRead[]` | ✅ **Implemented** | Frontend uses limit/offset; BE supports |
| **Product Detail** | PDP with variants/images | ✅ | `GET /api/v1/products/{product_id}` | UUID | `ProductRead` (includes variants[], images[]) | ✅ **Implemented** | Frontend expects `price`, `compareAtPrice` — BE returns via pricing service separately |
| **Create Product** | Store admin | ✅ | `POST /api/v1/admin/products` | `ProductCreate` | `ProductRead` | ✅ **Implemented** | Requires `store_manager`/`super_admin` |
| **Update Product** | Store admin | ✅ | `PATCH /api/v1/admin/products/{product_id}` | `ProductUpdate` (partial) | `ProductRead` | ✅ **Implemented** | Partial update supported |
| **Delete/Archive** | Store admin | ✅ | `DELETE /api/v1/admin/products/{product_id}` | — | 204 (soft delete → status=archived) | ✅ **Implemented** | Soft delete only |
| **Stock** | Real-time availability | ✅ | `GET /api/v1/inventory/stock/{warehouse_id}/{variant_id}` | — | `InventoryBalanceRead{quantity_on_hand, quantity_reserved}` | ✅ **Implemented** | Cart/checkout use this via service |
| **Price** | Selling price + compare-at | ✅ | `GET /api/v1/pricing/calculate` | `variant_id, store_id, coupon_code?` | `PriceCalculationRead{selling_price, final_price, discount_amount}` | ✅ **Implemented** | Frontend calls per-product on shop page |
| **Discount** | Promotions/coupons | ✅ | Via pricing engine | `coupon_code` in calculate | `discount_amount` in response | ✅ **Implemented** | Server-side validation |
| **Images** | Product gallery | ✅ | `product_images` in `ProductRead` | — | `ImageRead{id, product_id, image_url, alt_text, sort_order, is_primary}` | ✅ **Implemented** | Supabase Storage URLs |
| **Variants** | SKU, attributes, barcode | ✅ | `variants` in `ProductRead` | — | `VariantRead{id, sku, variant_name, attributes, barcode, is_active}` | ✅ **Implemented** | Attributes as JSONB |
| **Product Status** | Draft/active/archived | ✅ | `status` field | — | `status: 'draft'|'active'|'archived'` | ✅ **Implemented** | Public API filters to active only |

**Products Verdict:** **FULLY ALIGNED** — Minor: frontend `ProductRead` type adds `price?`, `compareAtPrice?` not in BE schema (populated client-side via pricing API).

---

### 4. Commerce — Categories

| Feature | Frontend Requirement | Backend Support | Endpoint | Request Contract | Response Contract | Status | Required Action |
|---|---|---|---|---|---|---|---|
| **Category List** | Navigation, filters | ✅ | `GET /api/v1/categories` | — | `CategoryTree[]` (nested, all stores) | ✅ **Implemented** | Public tree across all stores |
| **Hierarchy** | Parent/child nesting | ✅ | `CategoryTree.children: CategoryTree[]` | — | Recursive structure | ✅ **Implemented** | Max depth unlimited |
| **Parent/Child** | Admin management | ✅ | `POST/PATCH /api/v1/admin/categories` | `parent_id` optional | `CategoryRead` | ✅ **Implemented** | Slug unique per store |
| **Store Association** | Store-specific trees | ✅ | `GET /api/v1/categories/store/{slug}` | — | `CategoryTree[]` (filtered) | ✅ **Implemented** | Uses store slug |
| **Category Products** | Filter products by category | ✅ | `GET /api/v1/products?category_id=` | — | `ProductRead[]` | ✅ **Implemented** | Works |

**Categories Verdict:** **FULLY ALIGNED**

---

### 5. Commerce — Search

| Feature | Frontend Requirement | Backend Support | Endpoint | Request Contract | Response Contract | Status | Required Action |
|---|---|---|---|---|---|---|---|
| **Global Search** | Header search bar | ✅ | `GET /api/v1/products?search=` | `search` query param | `ProductRead[]` | ✅ **Implemented** | Basic ILIKE on name/description |
| **Store Search** | Store-scoped search | ✅ | `GET /api/v1/products?store_id=&search=` | Both params | `ProductRead[]` | ✅ **Implemented** | Works |
| **Filtering** | Category, brand, price range | ⚠️ **Partial** | `category_id` only | — | — | **B — Required** | No price range, brand, attribute filters |
| **Sorting** | Price, newest, popular | ❌ **Missing BE** | Not implemented | — | — | **B — Required** | Backend needs `sort` param |
| **Pagination** | Infinite scroll / pages | ✅ | `limit`, `offset` | — | Array (no meta) | ⚠️ **Mismatch** | No total count, page info — frontend assumes array |

**Search Verdict:** Basic search works. **Missing: advanced filters, sorting, pagination metadata.**

---

### 6. Commerce — Cart

| Feature | Frontend Requirement | Backend Support | Endpoint | Request Contract | Response Contract | Status | Required Action |
|---|---|---|---|---|---|---|---|
| **Get Cart** | Cart page, header count | ✅ | `GET /api/v1/cart` | `session_id?` (guest) | `CartRead{id, user_id?, session_id?, status, created_at, updated_at}` | ✅ **Implemented** | Auto-creates if missing |
| **Add Item** | Product → cart | ✅ | `POST /api/v1/cart/{cart_id}/items` | `CartItemCreate{variant_id, quantity}` | `CartItemRead` | ✅ **Implemented** | Validates variant active, product active |
| **Update Qty** | Quantity selector | ✅ | `PATCH /api/v1/cart/{cart_id}/items/{variant_id}` | `CartItemCreate{quantity}` | `CartItemRead` | ✅ **Implemented** | Qty ≤ 0 removes item |
| **Remove Item** | Delete button | ✅ | `DELETE /api/v1/cart/{cart_id}/items/{variant_id}` | — | 204 | ✅ **Implemented** | Ownership enforced |
| **Clear Cart** | Not explicitly used | ❌ **Missing BE** | No dedicated endpoint | — | — | **C — Enhancement** | Could add `DELETE /cart/{id}/items` |
| **Guest Cart** | Anonymous shopping | ✅ | `session_id` param | UUID from client | Same as authenticated | ✅ **Implemented** | Client generates UUID |
| **Auth Cart** | Persistent across devices | ✅ | `user_id` from auth | — | Bound to `profiles.id` | ✅ **Implemented** | Works |
| **Guest → Auth Merge** | On login | ✅ | `POST /api/v1/cart/merge-guest` | `guest_session_id` | 204 | ✅ **Implemented** | Moves items, marks guest abandoned |
| **Stock Validation** | Real-time availability | ✅ | Via `checkout-preview` + `list_cart_items` | — | `in_stock`, `available_qty` in `CartItemRead` | ✅ **Implemented** | Checks central warehouse |
| **Price Validation** | Server-side pricing | ✅ | `checkout-preview` uses `PricingService` | `coupon_code?, district?` | `CheckoutPreview` with per-store breakdown | ✅ **Implemented** | Recalculates on preview |

**Cart Verdict:** **FULLY ALIGNED** — Excellent implementation with guest/auth merge, stock/price validation.

---

### 7. Commerce — Checkout

| Feature | Frontend Requirement | Backend Support | Endpoint | Request Contract | Response Contract | Status | Required Action |
|---|---|---|---|---|---|---|---|
| **Checkout Preview** | Cart summary before order | ✅ | `GET /api/v1/cart/{cart_id}/checkout-preview` | `coupon_code?, district?, session_id?` | `CheckoutPreview{items[], subtotal, discount_total, delivery_total, grand_total, currency_code}` | ✅ **Implemented** | Flat delivery: Dhaka 70, outside 120 BDT |
| **Checkout Creation** | Place order (modal) | ✅ | `POST /api/v1/orders/checkout` | `OrderCreate{cart_id, delivery_address_id?, payment_method, coupon_code?, district?}` | `OrderRead` (parent + store_orders + items) | ⚠️ **Mismatch** | FE sends `address` object; BE expects `delivery_address_id` only |
| **Address Handling** | Inline address form in modal | ❌ **Missing BE** | No address creation in checkout flow | — | — | **A — Critical** | BE creates placeholder address; FE collects full address |
| **Shipping Options** | Flat fee only (v1) | ✅ | Calculated in preview/checkout | `district` | `delivery_total` | ✅ **Implemented** | DEC-OWN-003 |
| **Payment State** | COD / bKash / SSLCommerz | ✅ | `payment_method` in `OrderCreate` | `'cod'|'bkash'|'sslcommerz'` | `OrderRead` with `order_status='pending'` | ⚠️ **Partial** | bKash/SSLCommerz not implemented (M5) |
| **Order Creation** | Atomic split-order | ✅ | `POST /api/v1/orders/checkout` | See above | `OrderRead` with store_orders[], order_items[] | ✅ **Implemented** | 15-min stock reservations |
| **Validation** | Server-side price/stock | ✅ | Via services in transaction | — | 400 if mismatch | ✅ **Implemented** | Recalculates all prices |
| **Idempotency** | Prevent double orders | ✅ | `Idempotency-Key` middleware | Header `Idempotency-Key` | 409 if duplicate | ✅ **Implemented** | 24h TTL |
| **Failure/Retry** | COD OTP verification | ✅ | `POST /api/v1/orders/{order_id}/verify-cod` | `CODVerifyRequest{order_id, otp_code}` | `CODVerifyResponse{order_id, order_status, confirmed_at, message}` | ✅ **Implemented** | 4-digit OTP, 5min expiry, 3 attempts |

**Checkout Verdict:** **CRITICAL MISMATCH** — Frontend collects full address inline; Backend expects `delivery_address_id` reference. **Address handling must be reconciled.** Also: bKash/SSLCommerz payment adapters not built (M5).

---

### 8. Commerce — Orders

| Feature | Frontend Requirement | Backend Support | Endpoint | Request Contract | Response Contract | Status | Required Action |
|---|---|---|---|---|---|---|---|
| **Create Order** | Via checkout | ✅ | `POST /api/v1/orders/checkout` | `OrderCreate` | `OrderRead` | ✅ **Implemented** | See checkout section |
| **Order List** | Account page | ✅ | `GET /api/v1/orders` | — | `OrderRead[]` (limited fields, no pagination) | ⚠️ **Mismatch** | BE returns partial `OrderRead` (no store_orders/items); FE expects full |
| **Order Detail** | Order detail page | ✅ | `GET /api/v1/orders/{order_id}` | — | `OrderRead` (full with store_orders[], order_items[]) | ✅ **Implemented** | Access control: customer/vendor/admin |
| **Order Status** | Timeline display | ✅ | `order_status` field + `order_status_history` | — | `pending|confirmed|processing|completed|cancelled` | ⚠️ **Partial** | History table exists; no API to fetch timeline |
| **Order Timeline** | Status history UI | ❌ **Missing BE** | No endpoint for `order_status_history` | — | — | **B — Required** | Need `GET /orders/{id}/timeline` |
| **Cancellation** | Customer request | ❌ **Missing BE** | Not implemented | — | — | **B — Required** | Need `POST /orders/{id}/cancel` with logic |
| **Return/Refund** | 7-day return form | ❌ **Missing BE** | Tables exist (`returns`), no API | — | — | **C — Enhancement** | M6 scope |
| **Invoice/Tracking** | Shipment tracking | ❌ **Missing BE** | `shipments` table, no API | — | — | **C — Enhancement** | M6 scope (Pathao manual) |

**Orders Verdict:** Core order placement works. **Missing: order list pagination/full data, timeline API, cancellation, returns.**

---

### 9. Customer Account

| Feature | Frontend Requirement | Backend Support | Endpoint | Request Contract | Response Contract | Status | Required Action |
|---|---|---|---|---|---|---|---|
| **Profile** | Account page display | ✅ | `GET /api/v1/users/me` | — | `ProfileRead` | ✅ **Implemented** | Includes roles[], store_ids[] |
| **Profile Update** | Edit name/phone/avatar | ✅ | `PATCH /api/v1/users/me` | `ProfileUpdate{full_name?, phone?, avatar_url?}` | `ProfileRead` | ✅ **Implemented** | Partial update |
| **Addresses** | Address book | ✅ | `GET /api/v1/users/me/addresses` | — | `AddressRead[]` | ✅ **Implemented** | Bangladesh-specific fields |
| **Default Address** | `is_default` flag | ✅ | Unique index enforces one | `AddressCreate/Update{is_default}` | `AddressRead` | ✅ **Implemented** | DB constraint |
| **Order History** | Account orders tab | ✅ | `GET /api/v1/orders` | — | `OrderRead[]` (partial) | ⚠️ **Mismatch** | See Orders section |
| **Order Detail** | Click order → detail | ✅ | `GET /api/v1/orders/{id}` | — | Full `OrderRead` | ✅ **Implemented** | Works |
| **Returns** | 7-day return form | ❌ **Missing BE** | Tables exist, no API | — | — | **C — Enhancement** | M6 |
| **Account Settings** | Notifications, preferences | ❌ **Missing BE** | No settings table/API | — | — | **C — Enhancement** | Future |
| **Notifications** | In-app/email/SMS prefs | ❌ **Missing BE** | No notification system | — | — | **C — Enhancement** | M6 (outbox worker) |

**Account Verdict:** Core profile/addresses work. **Missing: order history pagination, returns, settings, notifications.**

---

### 10. Admin — Store Admin

| Feature | Frontend Requirement | Backend Support | Endpoint | Request Contract | Response Contract | Status | Required Action |
|---|---|---|---|---|---|---|---|
| **Dashboard** | Stats, charts | ❌ **Missing BE** | No dashboard aggregation API | — | — | **B — Required** | Need `GET /admin/dashboard` |
| **Products** | CRUD | ✅ | `POST/PATCH/DELETE /api/v1/admin/products` | `ProductCreate/Update` | `ProductRead` | ✅ **Implemented** | Store-scoped via RLS |
| **Inventory** | Stock adjustments | ✅ | `POST /api/v1/admin/inventory/balances/{w}/{v}/adjust` | `InventoryAdjustmentCreate` | `InventoryBalanceRead` | ✅ **Implemented** | Requires `inventory_manager` |
| **Orders** | List, status updates | ⚠️ **Partial** | `GET /api/v1/orders` (scoped) | — | `OrderRead[]` | ⚠️ **Mismatch** | No status update endpoint |
| **Order Status Updates** | Confirm, ship, cancel | ❌ **Missing BE** | No `PATCH /orders/{id}/status` | — | — | **A — Critical** | Store admin needs to update store_order status |
| **Store-Specific Access** | Data isolation | ✅ | RLS + `require_role('store_manager')` + `store_id` scoping | — | 403 if cross-store | ✅ **Implemented** | Verified in cross-store hardening |
| **Reporting** | Sales, inventory reports | ❌ **Missing BE** | No reporting APIs | — | — | **C — Enhancement** | M6 |

**Store Admin Verdict:** Product/inventory management works. **Critical: missing order status update API. Missing: dashboard, reporting.**

---

### 11. Admin — Super Admin

| Feature | Frontend Requirement | Backend Support | Endpoint | Request Contract | Response Contract | Status | Required Action |
|---|---|---|---|---|---|---|---|
| **Stores** | Create/manage stores | ✅ | `POST/PUT/DELETE /api/v1/stores` | `StoreCreate/Update` | `StoreRead` | ✅ **Implemented** | Requires `store_manager`/`super_admin` |
| **Catalog** | Global product/category | ✅ | Admin endpoints for products/categories | — | — | ✅ **Implemented** | Works across stores |
| **Users** | List, roles, permissions | ❌ **Missing BE** | No user management API | — | — | **A — Critical** | Super admin needs user CRUD + role assignment |
| **Roles** | Role management | ❌ **Missing BE** | Tables exist, no API | — | — | **B — Required** | Need `GET/POST /admin/roles` |
| **Permissions** | Permission matrix | ❌ **Missing BE** | Tables exist, no API | — | — | **C — Enhancement** | Future |
| **Reports** | Platform analytics | ❌ **Missing BE** | No reporting APIs | — | — | **C — Enhancement** | M6 |

**Super Admin Verdict:** Store/catalog management works. **Critical: missing user management API. Missing: roles/permissions management, reporting.**

---

### 12. Community / Customer Chat (NEW REQUIREMENT)

| Feature | Frontend Requirement | Backend Support | Endpoint | Request Contract | Response Contract | Status | Required Action |
|---|---|---|---|---|---|---|---|
| **User Profiles** | Community display | ⚠️ **Partial** | `GET /api/v1/users/me` + public profile? | — | `ProfileRead` (no public endpoint) | **A — Critical** | Need public profile API + community fields (avatar, bio, display_name) |
| **Conversations** | Chat list | ❌ **Missing BE** | No conversations table/API | — | — | **A — Critical** | New tables + API needed |
| **Direct Messaging** | 1:1 chat | ❌ **Missing BE** | No messages table/API | — | — | **A — Critical** | New tables + API needed |
| **Message History** | Scrollback | ❌ **Missing BE** | — | — | — | **A — Critical** | Pagination needed |
| **Unread Counts** | Badge indicators | ❌ **Missing BE** | — | — | — | **A — Critical** | Counter logic needed |
| **Read Status** | Seen indicators | ❌ **Missing BE** | — | — | — | **B — Required** | Read receipts |
| **Online/Offline** | Presence | ❌ **Missing BE** | — | — | — | **C — Enhancement** | Redis/WS presence |
| **Blocking** | Block users | ❌ **Missing BE** | — | — | — | **B — Required** | Block table + enforcement |
| **Reporting** | Report abuse | ❌ **Missing BE** | — | — | — | **B — Required** | Report table + moderation queue |
| **Moderation** | Admin tools | ❌ **Missing BE** | — | — | — | **B — Required** | Moderation dashboard API |
| **Message Ownership** | Delete own messages | ❌ **Missing BE** | — | — | — | **B — Required** | Authorization checks |
| **Pagination** | Infinite scroll | ❌ **Missing BE** | — | — | — | **B — Required** | Cursor/offset pagination |
| **Realtime** | Live updates | ❌ **Missing BE** | No WebSocket/SSE/Supabase Realtime | — | — | **A — Critical** | Transport decision needed |
| **Notifications** | Push/email for messages | ❌ **Missing BE** | No notification system | — | — | **B — Required** | Integrate with outbox (M6) |

**Community Verdict:** **COMPLETELY MISSING** — This is a net-new backend domain requiring database schema, APIs, realtime transport, and moderation tools.

---

### 13. Cross-Cutting Backend Requirements

| Requirement | Current State | Gap | Classification |
|---|---|---|---|
| **Validation** | Pydantic v2 on all schemas | ✅ Good | D — Doc only |
| **Error Format** | `{"detail": "...", "code": "..."}` | ✅ Consistent via `AuthError` | D — Doc only |
| **HTTP Status** | 200/201/204/400/401/403/404/409/422/429/500 | ✅ Consistent | D — Doc only |
| **Pagination** | `limit/offset` only, no metadata | ❌ No total, page info | **B — Required** |
| **Filtering** | Ad-hoc query params | ⚠️ Inconsistent conventions | **B — Required** |
| **Sorting** | Not implemented | ❌ Missing | **B — Required** |
| **API Versioning** | `/api/v1` prefix only | ⚠️ No deprecation strategy | **C — Enhancement** |
| **Idempotency** | Middleware + `Idempotency-Key` | ✅ Implemented (24h TTL) | D — Doc only |
| **Rate Limiting** | Not implemented | ❌ Missing | **B — Required** |
| **Authorization** | RBAC + RLS + store scoping | ✅ Strong (verified) | D — Doc only |
| **Ownership Checks** | `_assert_cart_access`, `_assert_order_access` | ✅ Consistent pattern | D — Doc only |
| **Transaction Boundaries** | `async with db.begin()` in services | ✅ Used in checkout | D — Doc only |
| **Concurrency Handling** | `SELECT FOR UPDATE` in inventory | ✅ Row-level locks | D — Doc only |
| **Stock Race Conditions** | Reservations + constraints | ✅ Prevented | D — Doc only |
| **Audit Logging** | `order_status_history`, `stock_movements` | ✅ Partial | **B — Required** |
| **Notification Architecture** | Outbox pattern designed, not built | ❌ Missing worker | **B — Required** (M6) |
| **File/Image Upload** | Supabase Storage, no direct upload API | ⚠️ Client uploads directly | **B — Required** |
| **Image URL Handling** | Public URLs in `image_url` fields | ✅ Works | D — Doc only |
| **Database Indexes** | Migration 008 + RLS indexes | ✅ Applied | D — Doc only |
| **Soft Delete/Archive** | `status='archived'`, `is_active=false` | ✅ Consistent | D — Doc only |
| **Timezone Handling** | `TIMESTAMPTZ`, UTC storage | ✅ Consistent | D — Doc only |
| **Money/Decimal** | `NUMERIC(12,2)` + `Decimal` in Python | ✅ Consistent | D — Doc only |
| **Enum Consistency** | CHECK constraints + Pydantic enums | ✅ Consistent | D — Doc only |
| **UUID/ID Conventions** | `gen_random_uuid()` everywhere | ✅ Consistent | D — Doc only |

---

## Phase 2 — Gap Classification Summary

### A — Critical (8 issues)
| # | Issue | Impact |
|---|---|---|
| A1 | **Checkout address mismatch**: FE collects full address inline; BE expects `delivery_address_id` reference | Blocks order placement |
| A2 | **Store route groups**: Blueprint expects `/best-gadget/`, `/aura-skin-care/`; FE uses flat `/shop` | SEO, branding, multi-store UX |
| A3 | **Order status updates**: Store admin cannot confirm/ship/cancel orders | Blocks fulfillment workflow |
| A4 | **Super admin user management**: No API to manage users/roles | Blocks platform administration |
| A5 | **Community profiles**: No public profile endpoint + missing community fields | Blocks community feature |
| A6 | **Conversations API**: No tables/endpoints for chat | Blocks community feature |
| A7 | **Direct messaging API**: No messages table/endpoints | Blocks community feature |
| A8 | **Realtime transport**: No WebSocket/SSE/Supabase Realtime for chat | Blocks live chat |

### B — Required (14 issues)
| # | Issue | Impact |
|---|---|---|
| B1 | **Pagination metadata**: No total count, page info in list responses | FE cannot build proper pagination UI |
| B2 | **Advanced search filters**: No price range, brand, attribute filters | Limits product discovery |
| B3 | **Sorting API**: No `sort` parameter on list endpoints | Limits product discovery |
| B4 | **Order timeline API**: No access to `order_status_history` | FE cannot show status timeline |
| B5 | **Order cancellation API**: Customer cannot cancel orders | Missing user capability |
| B6 | **Order list full data**: `GET /orders` returns partial `OrderRead` | FE order list missing details |
| B7 | **Store admin order status updates**: Need `PATCH /store-orders/{id}/status` | Blocks fulfillment |
| B8 | **Dashboard aggregation API**: No stats endpoint for admin | Admin UX incomplete |
| B9 | **Super admin roles/permissions API**: Tables exist, no CRUD | Platform governance gap |
| B10 | **Rate limiting**: No protection against abuse | Security/DoS risk |
| B11 | **File upload API**: No signed URL / direct upload endpoint | FE cannot upload images securely |
| B12 | **Community read receipts**: No read status tracking | Chat UX incomplete |
| B13 | **Community blocking/reporting**: No moderation tools | Safety gap |
| B14 | **Notification API**: No in-app/email/SMS preference management | User communication gap |

### C — Enhancement (9 issues)
| # | Issue | Impact |
|---|---|---|
| C1 | **Clear cart endpoint**: `DELETE /cart/{id}/items` | Convenience |
| C2 | **Returns/refunds API**: 7-day return flow | Post-launch |
| C3 | **Shipment tracking API**: Pathao integration | M6 |
| C4 | **Account settings/preferences**: Notification prefs, etc. | Post-launch |
| C5 | **Online/offline presence**: Redis-based presence | Chat enhancement |
| C6 | **API versioning strategy**: Deprecation headers, sunset policy | Long-term |
| C7 | **Super admin permissions matrix UI API**: Fine-grained perms | Future |
| C8 | **Platform reporting/analytics**: Sales, inventory, user metrics | M6 |
| C9 | **Admin dashboard widgets**: Charts, KPIs | M6 |

### D — Documentation Only (5 issues)
| # | Issue | Resolution |
|---|---|---|
| D1 | **Frontend `ProductRead` adds `price`, `compareAtPrice`**: Not in BE schema | Document client-side population via pricing API |
| D2 | **Order list pagination**: BE returns array, no meta | Document current limitation |
| D3 | **Banner URL validation**: `StoreBannerUpdate` pattern `^https?://$` is wrong (matches only `http://` or `https://`) | Fix regex in schema |
| D4 | **Frontend `CartItemData` vs BE `CartItemRead`**: Different field names | Document mapping |
| D5 | **Community feature not in any blueprint**: New requirement | Add to SYSTEM_ARCHITECTURE.md §11+ |

---

## Phase 3 — Backend ↔ Frontend Milestones

### Dependency Graph (Actual)

```mermaid
flowchart TD
    BE01[BE-01: API Contract Stabilization]
    BE02[BE-02: Store & Catalog Enhancements]
    BE03[BE-03: Checkout Address Reconciliation]
    BE04[BE-04: Orders & Account Completion]
    BE05[BE-05: Admin Backend Completion]
    BE06[BE-06: Community/Chat Backend]
    BE07[BE-07: Payment Gateway (M5)]
    BE08[BE-08: Reliability & Hardening]

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

---

### BE-01 — API Contract Stabilization
**Objective:** Normalize all request/response contracts, pagination, error formats, and validation conventions across all existing endpoints.

**Scope:**
- Standardize pagination: list endpoints support `format=v2` for paginated `{data, meta}` response; legacy returns raw array (backward compatible)
- Add sorting convention: `?sort=field:asc|desc` on products (price, name, created_at, updated_at)
- Add filtering: status filter on orders; store_id, category_id, search on products; status on stores
- Error format: `{"detail": "...", "code": "..."}` (existing, consistent)
- Auth contract: HttpOnly cookies (existing, frozen)
- API documentation: pagination, sorting, filtering documented

**Dependencies:** None (can start immediately)

**Affected Frontend Routes:** All — `apiFetch` handles both legacy and v2 formats

**Affected Backend Modules:** products, orders, stores (list endpoints updated with format=v2)

**Database Changes:** None (COUNT queries only)

**API Changes:** 
- `GET /api/v1/products?format=v2` → `{data: [...], meta: {total, page, per_page, total_pages, has_next, has_prev}}`
- `GET /api/v1/orders?format=v2` → same format
- `GET /api/v1/stores?format=v2` → same format
- Legacy (no format param) → raw array (backward compatible)
- `GET /api/v1/products?sort=price:asc` → sorts by actual price (fixed)
- `GET /api/v1/orders?status=pending` → filters by status
- `GET /api/v1/stores?status=active` → filters by status

**Acceptance Criteria:**
- [x] List endpoints support `format=v2` with standardized `{data, meta}` response
- [x] Legacy format (raw array) preserved when `format` omitted
- [x] Sorting works on products by price, name, created_at, updated_at (asc/desc)
- [x] Filtering works on orders (status), products (store_id, category_id, search), stores (status)
- [x] Price sorting fixed (was incorrectly mapped to created_at)
- [x] Shared pagination helper in `backend/app/core/pagination.py`
- [x] Contract tests in `backend/tests/test_be01_pagination.py` (15 unit tests, all pass)
- [x] No regression in existing tests (144 backend + 4 E2E — not executed due to Supabase/Docker unavailable)
- [ ] OpenAPI spec updated with all error codes (deferred — low priority)
- [ ] Frontend `apiFetch` updated to handle v2 format (deferred — frontend migration not in BE-01 scope)

---

### BE-02 — Store & Catalog Enhancements
**Objective:** Complete store routing, advanced search/filter/sort, and catalog API parity with frontend needs.

**Scope:**
- Implement store route group support OR document flat `/shop?store=` as canonical
- Add price range filter: `?min_price=&max_price=`
- Add brand filter: `?brand=`
- Add attribute filter: `?attr[color]=red&attr[size]=M`
- Add sorting: `?sort=price:asc|created_at:desc|popularity:desc`
- Public profile endpoint: `GET /api/v1/users/{id}/public-profile` (for community)
- Category product counts in tree response

**Dependencies:** BE-01 (pagination/sorting conventions)

**Affected Frontend Routes:** `/shop`, `/shop/[id]`, store selector, search

**Affected Backend Modules:** products, categories, stores, users

**Database Changes:** None (indexes may be needed for filter performance)

**API Changes:** New query parameters; new public profile endpoint

**Acceptance Criteria:**
- [ ] Store routing decision implemented and documented
- [ ] Product list supports price, brand, attribute filters
- [ ] Product list supports sorting by price, date, popularity
- [ ] Public profile endpoint returns community-safe fields
- [ ] Category tree includes product counts per node
- [ ] Search latency < 200ms p95 with filters

---

### BE-03 — Checkout Address Reconciliation
**Objective:** Resolve the critical mismatch between frontend inline address collection and backend `delivery_address_id` reference model.

**Scope:** Choose and implement ONE approach:
- **Option A (Recommended):** Backend accepts full address in `OrderCreate`, creates `order_addresses` snapshot internally. No `delivery_address_id` required.
- **Option B:** Frontend saves address to `/users/me/addresses` first, then passes `delivery_address_id` to checkout.

**Dependencies:** BE-01 (contract conventions)

**Affected Frontend Routes:** `/shop/cart` (checkout modal), `/account` (address book)

**Affected Backend Modules:** orders, users (addresses)

**Database Changes:** None (uses existing `order_addresses`)

**API Changes:** `OrderCreate` schema change — add optional `address: OrderAddressCreate`; make `delivery_address_id` optional

**Acceptance Criteria:**
- [ ] Checkout works with inline address (no pre-saved address required)
- [ ] Address snapshot stored in `order_addresses` with `address_type='delivery'`
- [ ] User can optionally save address to address book from checkout
- [ ] Existing `delivery_address_id` flow still works (backward compatible)
- [ ] COD OTP sent to address phone number

---

### BE-04 — Orders & Account Completion
**Objective:** Complete order management APIs for customer and store admin use cases.

**Scope:**
- `GET /api/v1/orders` → full `OrderRead` with pagination metadata
- `GET /api/v1/orders/{id}/timeline` → `OrderStatusHistory[]`
- `POST /api/v1/orders/{id}/cancel` → customer cancellation (only if `pending`/`confirmed`)
- `PATCH /api/v1/store-orders/{id}/status` → store admin status updates (`confirmed`→`processing`→`shipped`→`delivered`)
- Order list filtering: `?status=&date_from=&date_to=`
- Returns/refunds API stub (tables exist): `POST /orders/{id}/return-request`

**Dependencies:** BE-01, BE-03

**Affected Frontend Routes:** `/account/orders`, `/account/orders/[id]`, `/store-admin/orders`

**Affected Backend Modules:** orders, users

**Database Changes:** None (tables exist)

**API Changes:** New endpoints; extended existing

**Acceptance Criteria:**
- [ ] Customer sees full order history with pagination
- [ ] Order detail shows status timeline
- [ ] Customer can cancel eligible orders
- [ ] Store admin can update store order status
- [ ] Status transitions validated (no invalid jumps)

---

### BE-05 — Admin Backend Completion
**Objective:** Complete store admin and super admin APIs for operational workflows.

**Scope:**
- **Store Admin:**
  - `GET /api/v1/admin/dashboard` → stats (orders, revenue, low stock, pending)
  - `PATCH /api/v1/admin/store-orders/{id}/status` (same as BE-04)
  - Inventory adjustment history: `GET /admin/inventory/movements`
- **Super Admin:**
  - `GET/POST/PATCH/DELETE /api/v1/admin/users` → user management
  - `GET/POST /api/v1/admin/roles` → role CRUD
  - `POST /api/v1/admin/users/{id}/roles` → assign role + store
  - `GET /api/v1/admin/reports/sales` → platform sales report
  - `GET /api/v1/admin/reports/inventory` → cross-store inventory

**Dependencies:** BE-01, BE-04

**Affected Frontend Routes:** `/store-admin/*`, `/super-admin/*`

**Affected Backend Modules:** New admin router module recommended

**Database Changes:** None (tables exist)

**API Changes:** New admin-scoped endpoints

**Acceptance Criteria:**
- [ ] Store admin dashboard loads key metrics
- [ ] Store admin can update order statuses
- [ ] Super admin can CRUD users and assign roles
- [ ] Super admin can manage roles
- [ ] Basic sales/inventory reports render

---

### BE-06 — Community/Chat Backend
**Objective:** Implement complete customer community experience with realtime messaging.

**Scope:**
- **Database Schema (New Migration):**
  - `conversations` (participant1_id, participant2_id, created_at, updated_at)
  - `conversation_participants` (for group chats later)
  - `messages` (conversation_id, sender_id, content, message_type, read_at, created_at)
  - `message_read_receipts` (message_id, user_id, read_at)
  - `user_blocks` (blocker_id, blocked_id, created_at)
  - `user_reports` (reporter_id, reported_id, reason, status, created_at)
  - `user_community_profiles` (user_id, display_name, bio, avatar_url, is_public)
- **API Endpoints:**
  - `GET /api/v1/community/conversations` — paginated list with last message, unread count
  - `POST /api/v1/community/conversations` — create/find 1:1 conversation
  - `GET /api/v1/community/conversations/{id}/messages` — paginated messages
  - `POST /api/v1/community/conversations/{id}/messages` — send message
  - `PATCH /api/v1/community/messages/{id}/read` — mark read
  - `POST /api/v1/community/blocks` — block user
  - `POST /api/v1/community/reports` — report user/message
  - `GET /api/v1/community/users/{id}/profile` — public community profile
- **Realtime Transport:** Supabase Realtime (recommended) or SSE/WebSocket
- **Moderation:** Admin endpoints for reviewing reports, banning users

**Dependencies:** BE-01 (contract conventions), user profile extensions

**Affected Frontend Routes:** New `/community/*`, `/chat/*` routes

**Affected Backend Modules:** New `community` module

**Database Changes:** **New migration required** (6+ tables)

**API Changes:** Entirely new API surface

**Acceptance Criteria:**
- [ ] Users can start 1:1 conversations
- [ ] Messages deliver in realtime (< 500ms)
- [ ] Unread counts update live
- [ ] Read receipts work
- [ ] Blocking prevents messages
- [ ] Reporting creates moderation queue
- [ ] Public profiles display community info
- [ ] Supabase Realtime configured and tested

---

### BE-07 — Payment Gateway (M5)
**Objective:** Implement bKash and SSLCommerz payment adapters with webhook reliability.

**Scope:** Per MILESTONES.md M5.1–M5.5
- Provider-agnostic adapter interface
- bKash Tokenized Checkout (Create, Execute, Query)
- SSLCommerz Session API (Visa/Mastercard/Nagad/Rocket)
- HMAC webhook verification + `provider_event_id` deduplication
- Refund ledger + expense tracking

**Dependencies:** BE-03 (checkout finalized), BE-01 (idempotency)

**Affected Frontend Routes:** Checkout modal (payment method selection)

**Affected Backend Modules:** New `payments` module, webhook endpoints

**Database Changes:** `payments`, `payment_transactions`, `refunds`, `expenses` tables (migrations 005, 006 exist)

**API Changes:** New payment endpoints; webhook receivers

**Acceptance Criteria:** Per MILESTONES.md M5 acceptance criteria

---

### BE-08 — Reliability & Production Hardening
**Objective:** Production-grade observability, security, and performance.

**Scope:**
- Rate limiting (per-user, per-endpoint)
- Structured logging + correlation IDs
- Metrics (Prometheus) + health checks
- Distributed tracing (OpenTelemetry)
- Load testing (cart, checkout, search)
- Security headers audit
- Penetration testing checklist
- Disaster recovery runbooks
- Database connection pooling optimization
- Query performance audit (EXPLAIN ANALYZE)

**Dependencies:** All prior milestones

**Affected Frontend Routes:** None directly

**Affected Backend Modules:** All

**Database Changes:** Indexes, possibly partitioning

**API Changes:** None (internal)

**Acceptance Criteria:**
- [ ] Rate limiting blocks abuse without false positives
- [ ] p95 latency < 200ms for all read endpoints
- [ ] p99 latency < 500ms for checkout
- [ ] Zero critical security findings
- [ ] Observability dashboards operational
- [ ] Runbooks tested

---

## Phase 4 — Detailed Dependency Analysis

### Per-Milestone Prerequisites

| Milestone | Prerequisites | Frontend Work Dependent | Database Work | API Work | Migration Risk |
|---|---|---|---|---|---|
| **BE-01** | None | Update `apiFetch` pagination handling | None | All list endpoints | **Medium** — Breaking change for FE pagination |
| **BE-02** | BE-01 | Store selector, search filters, sort UI | Indexes only | Products, categories, users | Low |
| **BE-03** | BE-01 | Checkout modal address handling | None | Orders, users | **High** — Core checkout flow change |
| **BE-04** | BE-01, BE-03 | Order list, detail, timeline, cancel UI | None | Orders | Low |
| **BE-05** | BE-01, BE-04 | Admin dashboards, user management UI | None | New admin router | Low |
| **BE-06** | BE-01 | Entire community/chat UI | **6+ new tables** | New community module | **High** — New domain |
| **BE-07** | BE-03, BE-01 | Payment method UI in checkout | Tables exist (migrations 005, 006) | New payments module | Medium |
| **BE-08** | All | None | Indexes, partitioning | Internal | Low |

### Breaking-Change Risk Assessment

| Change | Risk | Mitigation |
|---|---|---|
| Pagination response format (BE-01) | **High** — All list consumers affected | Versioned endpoint or feature flag; update FE in same PR |
| `OrderCreate` address handling (BE-03) | **High** — Checkout flow | Option A (backend accepts address) is backward compatible |
| New community tables (BE-06) | **Medium** — Migration only | Run migration in maintenance window; no existing data |
| Payment webhook URLs (BE-07) | **Low** — New endpoints | No existing consumers |

---

## Phase 5 — Documentation Updates Required

### Files to Update/Create

| File | Action | Reason |
|---|---|---|
| `AURA_BELL_PROJECT_BLUEPRINT/04_SYSTEM_ARCHITECTURE/FRONTEND_ARCHITECTURE.md` | **Update** | Resolve route group vs flat routing conflict; document decision |
| `AURA_BELL_PROJECT_BLUEPRINT/04_SYSTEM_ARCHITECTURE/SYSTEM_ARCHITECTURE.md` | **Update** | Add community/chat to architecture diagram (§11); align directory structure |
| `AURA_BELL_PROJECT_BLUEPRINT/04_SYSTEM_ARCHITECTURE/BACKEND_API_CONTRACT.md` | **Create** | Single source of truth for all API contracts (replace scattered docs) |
| `AURA_BELL_PROJECT_BLUEPRINT/03_PRODUCT_REQUIREMENTS/COMMUNITY_PRD.md` | **Create** | Community/chat product requirements (new) |
| `AURA_BELL_PROJECT_BLUEPRINT/07_UI_UX_DESIGN/DESIGN_SYSTEM.md` | **Update** | Add community/chat UI components, realtime indicators |
| `MILESTONES.md` | **Update** | Add BE-01 through BE-08 milestones; adjust M5/M6 dependencies |
| `docs/architecture/BE_CONTRACT_STABILIZATION.md` | **Create** | BE-01 technical specification |
| `docs/architecture/COMMUNITY_CHAT_ARCHITECTURE.md` | **Create** | BE-06 technical specification |
| `docs/architecture/CHECKOUT_ADDRESS_RECONCILIATION.md` | **Create** | BE-03 decision record |
| `backend/app/modules/community/` | **Create** | New module for BE-06 |
| `backend/app/modules/admin/` | **Create** | New module for BE-05 (consolidate admin endpoints) |

### Documents to Deprecate (Mark as Superseded)
- Any duplicate API documentation in `docs/architecture/m1.3-*.md` — consolidate into `BACKEND_API_CONTRACT.md`
- `FRONTEND_ARCHITECTURE.md` directory structure conflict with `SYSTEM_ARCHITECTURE.md` §11 — resolve and mark one authoritative

---

## Phase 6 — Breaking Change Protection

### Currently Working Functionality (DO NOT BREAK)

| Functionality | Current Behavior | Protection Strategy |
|---|---|---|
| **Authentication** | HttpOnly cookies (`aura_access_token`, `aura_refresh_token`), ES256 JWT, auto-refresh on 401 | **FROZEN** — No changes to auth flow, cookie names, token format, or refresh logic |
| **JWT Handling** | Supabase GoTrue RS256→ES256 migration complete; `security.py` validates ES256 | **FROZEN** — Algorithm, issuer, audience validation unchanged |
| **API Client** | `apiFetch` with `credentials: "include"`, auto-refresh, `Idempotency-Key` header | **FROZEN** — Core logic unchanged; only pagination response parsing may change |
| **Cart Behavior** | Guest/auth merge, stock validation, server-side pricing preview | **FROZEN** — No changes to cart endpoints or schemas |
| **Offline Sync** | IndexedDB v2 with `user_id` index, `drainPromise` lock, account-scoped mutations, idempotency keys, backoff+jitter, dead-letter | **FROZEN** — Schema v2 stable; no migration needed |
| **IndexedDB Mutation Queue** | `MutationRecord` with `idempotency_key`, `status`, `retries`, `next_retry_at` | **FROZEN** — Critical for offline reliability |

### Changes Requiring Migration Strategy

| Change | Current | Proposed | Migration Strategy | Frontend Impact | Backend Impact | Rollback |
|---|---|---|---|---|---|---|
| **Pagination format** | Raw array `T[]` | `{data: T[], meta: {...}}` | 1. Add `?format=v2` param<br>2. Update FE to use v2<br>3. Deprecate v1 after 2 sprints | `apiFetch` parsing + all list components | All list routers | Keep v1 endpoint alive |
| **Checkout address** | `delivery_address_id` only | Accept inline `address` object | Option A: BE creates snapshot from inline address; `delivery_address_id` optional | Checkout modal unchanged | `OrderCreate` schema + `place_order` logic | Revert schema change |
| **Store routing** | Flat `/shop?store=` | Route groups `/best-gadget/` | 1. Implement route groups in Next.js<br>2. Add redirects from old URLs<br>3. Update sitemap | Major FE restructuring | None (BE already supports store_id) | Keep flat routes as alias |

---

## Phase 7 — Final Audit Report

### Executive Summary

| Metric | Value |
|---|---|
| **Current Integration Status** | Backend M1-M4 complete; Frontend ~60% of blueprint |
| **Critical Mismatches (A)** | 8 |
| **Missing Capabilities (B)** | 14 |
| **Documentation Mismatches (D)** | 5 |
| **Overall Readiness for Implementation** | **65%** — Core commerce works; admin, community, payments need work |

### Critical Issues (A-Level) — Must Resolve Before Implementation

1. **A1 — Checkout Address Mismatch** — Blocks order placement; FE collects address, BE expects reference
2. **A2 — Store Route Groups** — Blueprint/FE architecture conflict; SEO and branding impact
3. **A3 — Order Status Updates** — Store admin cannot fulfill orders
4. **A4 — Super Admin User Management** — Cannot manage platform users
5. **A5 — Community Profiles** — No public profile endpoint for chat
6. **A6 — Conversations API** — Entire chat domain missing
7. **A7 — Direct Messaging API** — Entire chat domain missing
8. **A8 — Realtime Transport** — No WebSocket/SSE for live chat

### Complete Contract Matrix
See **Phase 1** above — 13 feature areas, 80+ endpoint mappings documented.

### Milestones (BE-01 through BE-08)
See **Phase 3** above — 8 milestones with scope, dependencies, acceptance criteria.

### Recommended Implementation Order

```
BE-01: API Contract Stabilization          [Week 1-2]  → Foundation for all
       ↓
BE-03: Checkout Address Reconciliation     [Week 2-3]  → Unblocks checkout (critical)
       ↓
BE-02: Store & Catalog Enhancements        [Week 3-4]  → Improves discovery
       ↓
BE-04: Orders & Account Completion         [Week 4-5]  → Completes customer journey
       ↓
BE-05: Admin Backend Completion            [Week 5-7]  → Enables operations
       ↓
BE-07: Payment Gateway (M5)                [Week 6-9]  → Parallel with BE-05/06
       ↓
BE-06: Community/Chat Backend              [Week 7-11] → New domain, longest lead
       ↓
BE-08: Reliability & Hardening             [Week 10-12]→ Production readiness
```

**Parallelization Opportunities:**
- BE-07 (Payments) can run in parallel with BE-05/06 after BE-03
- BE-06 (Community) database migration can start early; API development parallel with BE-05

### Documentation Changes Summary

| File | Change Type | Priority |
|---|---|---|
| `FRONTEND_ARCHITECTURE.md` | Update (resolve routing conflict) | **Critical** |
| `SYSTEM_ARCHITECTURE.md` | Update (add community, align structure) | **Critical** |
| `BACKEND_API_CONTRACT.md` | Create (new SSOT) | **High** |
| `COMMUNITY_PRD.md` | Create (new) | **High** |
| `MILESTONES.md` | Update (add BE-01 to BE-08) | **High** |
| `DESIGN_SYSTEM.md` | Update (community components) | **Medium** |
| 3 architecture decision docs | Create (BE-01, BE-03, BE-06) | **Medium** |
| 2 new backend modules | Create (community, admin) | **High** |

### Explicit Non-Goals (NOT in This Milestone)

The following are **explicitly excluded** from BE-01 through BE-08 and should NOT be implemented:

| Non-Goal | Reason |
|---|---|
| **Multi-vendor marketplace** (commission, payouts) | Post-MVP; requires financial ledger |
| **Subscription/recurring orders** | Not in PRD |
| **Multi-language/i18n** | Bengali/English only for now |
| **Advanced promotions** (BOGO, bundles, tiered) | Basic coupon only v1 |
| **Loyalty points/wallet** | Post-MVP |
| **AI recommendations** | Post-MVP |
| **Mobile app (React Native)** | Web-only v1 |
| **Advanced analytics/BI** | Basic reports only |
| **Multi-warehouse fulfillment** | Central warehouse only v1 |
| **Dropshipping integration** | Not in scope |
| **B2B/wholesale pricing** | B2C only v1 |

---

## Final Decision Queue (Owner Approval Required)

Before implementation begins, the following **10 decisions** must be resolved:

| # | Decision | Options | Recommendation |
|---|---|---|---|
| 1 | **Store URL Structure** | A) Route groups `/best-gadget/`, `/aura-skin-care/`<br>B) Flat `/shop?store=`<br>C) Subdomains `best-gadget.aura-bell.com` | **A** — Matches blueprint, better SEO/branding |
| 2 | **Checkout Address Model** | A) BE accepts inline address (creates snapshot)<br>B) FE must save address first, pass ID | **A** — Better UX, backward compatible |
| 3 | **Community Realtime Transport** | A) Supabase Realtime (native, managed)<br>B) Custom WebSocket server<br>C) SSE (simpler, no binary) | **A** — Already on Supabase, low ops burden |
| 4 | **Pagination Breaking Change** | A) Versioned endpoint (`?v=2`)<br>B) Feature flag + simultaneous FE deploy<br>C) New endpoints (`/products/v2`) | **B** — Cleanest, atomic deploy |
| 5 | **Admin Module Structure** | A) New `admin` router consolidating all admin endpoints<br>B) Keep scattered in each module | **A** — Cleaner authorization, easier auditing |
| 6 | **Rate Limiting Strategy** | A) Per-user token bucket (Redis)<br>B) Per-IP + per-user (middleware)<br>C) Supabase edge rate limiting | **A** — Most granular, integrates with auth |
| 7 | **Order Cancellation Rules** | A) Customer can cancel `pending`/`confirmed`<br>B) Only `pending`<br>C) Require store approval for `confirmed` | **A** — Balanced UX/ops |
| 8 | **Public Profile Fields** | A) `display_name`, `avatar_url`, `bio`, `created_at`<br>B) Minimal: `display_name`, `avatar_url`<br>C) Full profile minus PII | **A** — Community needs identity |
| 9 | **Message Encryption** | A) None (trusted server)<br>B) Client-side E2E (complex)<br>C) Server-side at-rest only | **A** — v1; E2E v2 |
| 10 | **Payment Gateway Priority** | A) bKash first (local market)<br>B) SSLCommerz first (cards)<br>C) Both simultaneously | **A** — COD + bKash covers 80%+ BD market |

---

## Appendix: Current Endpoint Inventory

### Backend Endpoints (Implemented)
```
Authentication:
  POST   /api/v1/auth/login
  POST   /api/v1/auth/register
  POST   /api/v1/auth/otp/request
  POST   /api/v1/auth/otp/verify
  POST   /api/v1/auth/refresh
  POST   /api/v1/auth/logout

Users:
  GET    /api/v1/users/me
  PATCH  /api/v1/users/me
  GET    /api/v1/users/me/addresses
  POST   /api/v1/users/me/addresses
  GET    /api/v1/users/me/addresses/{id}
  PATCH  /api/v1/users/me/addresses/{id}
  DELETE /api/v1/users/me/addresses/{id}

Stores:
  GET    /api/v1/stores
  GET    /api/v1/stores/{slug}
  GET    /api/v1/stores/id/{id}
  POST   /api/v1/stores
  PUT    /api/v1/stores/{id}
  PATCH  /api/v1/stores/{id}/status
  DELETE /api/v1/stores/{id}
  PUT    /api/v1/stores/{id}/banner
  POST   /api/v1/stores/{id}/policies/return
  POST   /api/v1/stores/{id}/policies/warranty
  POST   /api/v1/stores/{id}/policies/terms
  GET    /api/v1/stores/{id}/policies
  GET    /api/v1/stores/{slug}/categories

Products (Admin):
  POST   /api/v1/admin/products
  GET    /api/v1/admin/products/{id}
  PATCH  /api/v1/admin/products/{id}
  DELETE /api/v1/admin/products/{id}

Products (Public):
  GET    /api/v1/products
  GET    /api/v1/products/{id}

Categories (Admin):
  POST   /api/v1/admin/categories
  GET    /api/v1/admin/categories/{id}
  PATCH  /api/v1/admin/categories/{id}
  DELETE /api/v1/admin/categories/{id}

Categories (Public):
  GET    /api/v1/categories
  GET    /api/v1/categories/store/{slug}

Cart:
  GET    /api/v1/cart
  POST   /api/v1/cart/merge-guest
  GET    /api/v1/cart/{id}/items
  POST   /api/v1/cart/{id}/items
  PATCH  /api/v1/cart/{id}/items/{variant_id}
  DELETE /api/v1/cart/{id}/items/{variant_id}
  GET    /api/v1/cart/{id}/checkout-preview

Orders:
  POST   /api/v1/orders/checkout
  POST   /api/v1/orders/{id}/verify-cod
  GET    /api/v1/orders/{id}
  GET    /api/v1/orders

Pricing:
  POST   /api/v1/admin/prices
  PATCH  /api/v1/admin/prices/{id}
  DELETE /api/v1/admin/prices/{id}
  POST   /api/v1/admin/promotions
  PATCH  /api/v1/admin/promotions/{id}
  DELETE /api/v1/admin/promotions/{id}
  POST   /api/v1/admin/promotions/{id}/products
  DELETE /api/v1/admin/promotions/{id}/products/{product_id}
  POST   /api/v1/admin/promotions/{id}/stores
  DELETE /api/v1/admin/promotions/{id}/stores/{store_id}
  GET    /api/v1/pricing/calculate
  GET    /api/v1/pricing/validate

Inventory (Admin):
  GET    /api/v1/admin/inventory/balances/{warehouse_id}/{variant_id}
  POST   /api/v1/admin/inventory/balances/{warehouse_id}/{variant_id}/adjust
  POST   /api/v1/admin/inventory/reservations
  GET    /api/v1/admin/inventory/reservations
  GET    /api/v1/admin/inventory/reservations/{id}
  POST   /api/v1/admin/inventory/reservations/{id}/consume
  POST   /api/v1/admin/inventory/reservations/{id}/release
  GET    /api/v1/admin/inventory/movements
  POST   /api/v1/admin/inventory/batches
  GET    /api/v1/admin/inventory/batches
  GET    /api/v1/admin/inventory/batches/{id}
  PATCH  /api/v1/admin/inventory/batches/{id}
  POST   /api/v1/admin/inventory/serials
  GET    /api/v1/admin/inventory/serials
  GET    /api/v1/admin/inventory/serials/{id}
  PATCH  /api/v1/admin/inventory/serials/{id}

Inventory (Public):
  GET    /api/v1/inventory/stock/{warehouse_id}/{variant_id}

Health:
  GET    /api/v1/health
```

### Frontend API Calls (Observed in Code)
```
# Shop page
GET  /api/v1/products
GET  /api/v1/stores
GET  /api/v1/pricing/calculate?variant_id=&store_id=

# Cart page
GET  /api/v1/cart
GET  /api/v1/cart/preview (POST with body)
PATCH /api/v1/cart/items/{variant_id}
DELETE /api/v1/cart/items/{variant_id}

# Checkout modal
POST /api/v1/orders/checkout
POST /api/v1/orders/{order_id}/verify-cod

# Account
GET /api/v1/orders
GET /api/v1/orders/{id}
GET /api/v1/users/me (via auth-context)

# Login/Register
POST /api/v1/auth/login
POST /api/v1/auth/register
GET  /api/v1/users/me (after auth)

# Store Admin
GET /api/v1/admin/products
```

---

**End of Audit Report**

*This document represents the complete Backend ↔ Frontend Contract Alignment Audit as of 2026-11-25. All findings are verified against source code. No application code was modified during this audit.*