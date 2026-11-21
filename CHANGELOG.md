# CHANGELOG — Aura Bell

All notable changes to the Aura Bell project are documented in this file.

---

## [Unreleased] — 2026-11-20

### Added

- **M4.1: Multi-Store Shared Shopping Cart** — Add/update/remove items across Best Gadget and Aura Skin Care stores in a single cart; real-time stock and active status validation on cart load
- **M4.2: Server-Side Checkout Calculation Engine** — Server-side price recalculation from DB; flat delivery fees (Dhaka Metro 70 BDT / outside Dhaka 120 BDT); grand total = (Subtotal − Discount) + Delivery Total; coupon code support
- **M4.3: Split Order Transaction Engine** — Atomic parent order → store order split; immutable item snapshots (name, SKU, variant JSONB); delivery/billing address snapshots; 15-minute atomic stock reservation; promotion redemption records; status history; cart conversion
- **M4.4: COD Fraud Prevention & Verification** — 4-digit SMS OTP generation on COD order; 5-minute expiry with 3-attempt limit; OTP verification endpoint (`POST /api/v1/orders/{order_id}/verify-cod`); order status transition pending → confirmed
- **Cross-Store Security & Hardening** — IDOR fixes with server-side store scoping; store-scoped Auth model with `user_roles.store_id` FK; updated RLS policies for cross-store tenant isolation; 403 Forbidden on unauthorized cross-store access
- **Auth Remediation** — HttpOnly cookie-based auth (`aura_access_token`, `aura_refresh_token` with `HttpOnly`, `Secure`, `SameSite=Strict`); Bearer fallback removed from `get_current_user`; JWT algorithm RS256 → ES256; `ProfileRead` extended with `roles` and `store_ids`; `/auth/logout` unprotected, clears both cookies, returns 204; frontend `apiFetch` uses `credentials: "include"` only, no `Authorization: Bearer` header; offline sync hardening (IndexedDB v2, `drainPromise` lock, account-scoped mutations, idempotency key header, backoff+jitter, dead-letter); idempotency middleware (`Idempotency-Key`, 24h TTL, keyed by key + endpoint + request hash)

### Improved

- Backend cart module rewritten with SQLAlchemy 2.0 Core + Pydantic v2
- Guest cart (session_id) and authenticated cart (user_id) support with guest-to-user merge on login
- Server-side pricing via `PricingService.calculate_price()` with tamper-proof validation
- Frontend auth: removed `getAccessToken` import and `Authorization: Bearer` header; added shared refresh promise lock, 401→refresh→retry, refresh failure→logout→redirect; middleware cookie-presence check; role-guard fetches `/users/me` for roles

### Fixed

- `stores/router.py` UTF-16LE → UTF-8 encoding fix (commit f888f76)
- `text()` native datetime → `str()` wrapping for `StoreRead`/`PolicyRead` (commit e1bceb9)
- `backend/app/core/security.py` JWT algorithm `RS256` → `ES256` (lines 120, 161; docstring line 90)
- `backend/app/modules/auth/router.py` logout — return injected `response` object so `delete_cookie` headers persist
- Backend test files updated: removed Bearer fallback test cases, updated `get_current_user` call signatures

### Tests

- **148 tests passing** (144 backend across M1–M4 + auth remediation, 4 E2E browser tests E1–E6)
- Real ES256 JWT verification against live Supabase: valid token accepted, invalid signature rejected, unsupported RS256 rejected

---

## [1.0.0] — 2026-11-17

### Added

- **M1.1:** Backend repository scaffolding (FastAPI, Pydantic v2, SQLAlchemy 2.0 Async, Docker)
- **M1.2:** Supabase PostgreSQL DDL migrations — 50 tables, enums, constraints, triggers, RLS policies (12)
- **M1.3:** Supabase Auth (GoTrue) integration — JWT validation, RBAC (`require_role`), user profiles & addresses
- **M1.4:** Base seed data — 7 system roles, default warehouse, Best Gadget & Aura Skin Care stores
- **M2.1:** Store management & policy engine — CRUD, slug routing, store-specific policies
- **M2.2:** Category hierarchy & dynamic attributes — parent-child tree, ingredients, specs
- **M2.3:** Product catalog & variant generator — SKU generation, image upload to Supabase Storage
- **M2.4:** Server-side pricing engine — BDT currency, coupons, tamper-proof validation
- **M3.1:** Warehouse stock balances — `quantity_on_hand`/`quantity_reserved`, zero-negative invariant
- **M3.2:** Atomic stock reservation engine — `SELECT FOR UPDATE` row locking, 15-minute TTL
- **M3.3:** Automatic reservation cleanup worker — 1-minute cron for expired reservations
- **M3.4:** Immutable stock movement ledger — append-only audit trail
- **M3.5:** Specialized tracking — batch/expiry for skincare, IMEI/serial for gadgets

### Tests

- M2.1: 20/20 stores tests passing
- M3: 18 inventory tests passing (all sub-modules)

---
