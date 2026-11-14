# AURA BELL — M1.3 & M1.4 Implementation Plan (Final)

Generated: 2026-11-14  
Based on: Direct file verification (not audit reports)

---

## A. Ground Truth (Re-verified)

| Item | Claim | File:Line | Actually Saw |
|------|-------|-----------|--------------|
| `config.py` lines | "57 lines" / "1-15" / "59" | `backend/app/core/config.py:1-59` | **59 lines**. NO JWT fields (SECRET_KEY, ALGORITHM, JWT_*). Only Supabase: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` (lines 30-32). |
| `requirements.txt` JWT libs | "python-jose, pyjwt present?" | `backend/requirements.txt:1-7` | **7 lines**. fastapi, uvicorn, pydantic, pydantic-settings, sqlalchemy, asyncpg, python-dotenv. **NO** python-jose, pyjwt, authlib, supabase-py. |
| Auth provider | "Supabase GoTrue" vs "custom JWT" | `AURA_BELL_PROJECT_BLUEPRINT/08_SECURITY_AND_PRIVACY/AUTHENTICATION_AUTHORIZATION.md:15-17` | **Supabase GoTrue mandated**: "Platform uses Supabase Auth for user signup, OTP, password management. Client gets cryptographic GoTrue JWT token." FastAPI validates signature, iss, exp. |
| JWT algorithm | HS256 vs RS256 | Blueprint says "verify signature" | **UNVERIFIED** — exact algorithm needs real token. Per blueprint, assume RS256/JWKS. Verify on Day 2. |
| `warehouses.store_id` | nullable? | `backend/supabase/migrations/20261113000003_003_inventory.sql:7` | **NOT NULL** (`store_id UUID NOT NULL REFERENCES public.stores(id)`). Central warehouse MUST link to a store. |
| `user_roles.store_id` | nullable? | `backend/supabase/migrations/20261113000001_001_core_identity.sql:65` | **NULLABLE** (`store_id UUID` — no NOT NULL). Can link role to store or be global. |
| `profiles.store_id` | exists? | `backend/supabase/migrations/20261113000001_001_core_identity.sql:17-27` | **NO** — profiles has no store_id column. |
| RLS on `warehouses` | exists? | `backend/supabase/migrations/20261113000009_009_rls_policies.sql:1-13` | **MISSING**. 8 tables have RLS (profiles, addresses, carts, cart_items, orders, order_addresses, notifications, support_tickets, support_messages). `warehouses` NOT listed. |

### Role Count Verification

| role_name | in_010_seed | in_MILESTONES_M1.4 | in_AUTH_SPEC_matrix | Verdict |
|-----------|-------------|---------------------|---------------------|---------|
| owner | ✅ | ❌ (Super Admin) | ✅ (Super Admin / Owner) | Seed has `owner`; docs map to `Super Admin` |
| admin | ✅ | ❌ | ❌ | Extra in seed only |
| store_manager | ✅ | ✅ (Store Manager) | ✅ (Store Manager) | Match |
| inventory_manager | ✅ | ✅ (Inventory Manager) | ✅ (Inventory Manager) | Match |
| order_manager | ✅ | ❌ | ❌ | Extra in seed only |
| support_agent | ✅ | ❌ | ✅ (Support Agent) | Match (matrix only) |
| customer | ✅ | ✅ (Customer) | ✅ (Customer) | Match |
| **Anonymous / Public** | ❌ | ❌ | ✅ | Matrix only |

**Conclusion**: Seed has 7 roles. M1.4 lists 4 "system roles". Auth spec matrix has **6 roles** (including Anonymous/Public). **Use seed's 7 roles as implementation truth**; docs need alignment.

---

## B. Decisions Needed Before Coding (Blocking)

| Decision | Status | Why Blocking | Source | Recommended Answer |
|----------|--------|--------------|--------|-------------------|
| **D1: Auth provider** | **CLOSED** | Determines JWT lib, validation method, token source | AUTHENTICATION_AUTHORIZATION.md:15-17 | **Supabase GoTrue**. Per blueprint, assume RS256/JWKS. Verify exact algorithm on Day 2. |
| **D2: Warehouse ownership** | **OPEN** | `store_id NOT NULL` — central warehouse must pick a store | 003_inventory.sql:7 | **Three options**: (i) Link to Best Gadget (first store, slug `best-gadget`) — **RECOMMENDED** (primary revenue store, simpler) (ii) Link to Aura Skin Care — no clear advantage (iii) Create "Platform Anchor" store — adds complexity, extra row. **Recommend (i)**. |
| **D3: Role count resolution** | **OPEN** | Seed has 7, M1.4 says 4, matrix has 6 | 010_seed_data.sql vs MILESTONES.md vs AUTH_SPEC.md | **Three options**: (A) Keep all 7 seeded roles; update MILESTONES.md M1.4 to list 7 — **RECOMMENDED** (truth in DB) (B) Drop 3 roles from seed (`admin`, `order_manager`, `support_agent`); keep only 4 — loses functionality (C) Keep 7 in DB but document only 4 as "system roles"; other 3 as "operational roles" — confusing. **Recommend (A)**. |
| **D4: aud/iss strict validation** | **OPEN** | GoTrue JWT has `iss=https://<project>.supabase.co/auth/v1` | AUTHENTICATION_AUTHORIZATION.md:17 | Validate `iss` matches `settings.SUPABASE_URL + "/auth/v1"`. Validate `aud` = "authenticated". |
| **D5: Test database strategy** | **CLOSED** | No test infra exists; must pick one before Day 1 | `backend/tests/` FILE NOT FOUND | **Supabase local Docker** (`supabase start`) — matches production, no testcontainers overhead. |

---

## C. M1.3 Work Plan — Code Tasks (Dependency Order)

| # | Task | Why Needed | Files | DoD | Size | Priority |
|---|------|------------|-------|-----|------|----------|
| 1 | Add JWT + Supabase deps | All auth needs JWKS validation + admin client | `requirements.txt` (add `python-jose[cryptography]`, `supabase>=2.0`) | `pip install` works; `from jose import jwt` + `from supabase import create_client` | S | P0 |
| 2 | Create `core/exceptions.py` | Unified auth/permission errors; needed by security.py | `backend/app/core/exceptions.py` (NEW) | `AuthError`, `PermissionDenied` raised and caught in tests | S | P0 |
| 3 | Create `core/security.py` | Central JWKS fetch + token verification | `backend/app/core/security.py` (NEW) | Unit test: valid token → payload; expired → **raises AuthError**; wrong sig → **raises AuthError** | M | P0 |
| 4 | Create `core/auth.py` with `get_current_user` | Base dependency for all protected routes | `backend/app/core/auth.py` (NEW) | Returns `User` (id, email, roles[]) from valid JWT; fetches roles from `user_roles`+`roles` tables; caches in `request.state.user` per request | M | P0 |
| 5 | Create `require_role(*roles)` factory | RBAC for all modules | `backend/app/core/auth.py` (same file) | `Depends(require_role("admin", "owner"))` → 403 if user lacks any role; unit test covers allow/deny | M | P0 |
| 6 | Create `modules/auth/schema.py` | Request/response models | `backend/app/modules/auth/schema.py` (NEW) | `Token`, `UserLogin`, `UserRegister`, `OTPRequest`, `OTPVerify` | S | P0 |
| 7 | Create `modules/auth/service.py` | Supabase Auth integration | `backend/app/modules/auth/service.py` (NEW) | `login(email, password) → Token`; `register(...) → Token`; `request_otp(email)`; `verify_otp(email, code) → Token`; uses `supabase.auth` | M | P0 |
| 8 | Create `modules/auth/router.py` | Auth endpoints | `backend/app/modules/auth/router.py` (NEW) | POST `/auth/login`, `/auth/register`, `/auth/otp/request`, `/auth/otp/verify`, `/auth/refresh` | M | P0 |
| 9 | Create `modules/users/schema.py` | Profile/address models | `backend/app/modules/users/schema.py` (NEW) | `ProfileRead`, `ProfileUpdate`, `AddressCreate`, `AddressRead`, `AddressUpdate` | S | P1 |
| 10 | Create `modules/users/service.py` | CRUD logic | `backend/app/modules/users/service.py` (NEW) | `get_profile(user_id)`, `update_profile(...)`, CRUD addresses (all scoped to `user_id` from auth) | M | P1 |
| 11 | Create `modules/users/router.py` | User endpoints | `backend/app/modules/users/router.py` (NEW) | GET/PUT `/users/me`; CRUD `/users/me/addresses` — all `Depends(get_current_user)` | M | P1 |
| 12 | Register routers in `main.py` | Wire up all endpoints | `backend/app/main.py` (MODIFY) | Include auth + users routers under `/api/v1`; add CORS + `TrustedHostMiddleware` | S | P0 |
| 13 | Add security middleware | HTTPS/HSTS/secure cookies | `backend/app/main.py` (MODIFY) | `Strict-Transport-Security` header; session cookie `secure=True, httponly=True, samesite="lax"` | M | P1 |

---

## D. M1.3 Documentation Tasks

| Path | Must Contain | Depends On |
|------|--------------|------------|
| `docs/architecture/m1.3-auth-security-layers.md` | Full security layer diagram (HTTPS → JWT → RBAC → RLS), JWKS flow, token lifecycle | Task 3, 4, 5 |
| `docs/architecture/m1.3-jwt-validation.md` | JWKS fetch/caching, `verify_token()` logic, `iss`/`aud`/`exp` checks, error codes | Task 3 |
| `docs/architecture/m1.3-rbac-require-role.md` | `require_role()` usage, role hierarchy, how roles loaded from DB, caching | Task 5 |
| `docs/architecture/m1.3-transport-hardening.md` | HSTS, secure cookies, CORS, TrustedHostMiddleware config, CSP basics | Task 13 |
| `docs/api/m1.3-auth-endpoints.md` | Auth endpoint specs (login, register, OTP, refresh) with request/response examples | Task 8 |
| `docs/api/m1.3-users-endpoints.md` | Profile/addresses CRUD specs with auth requirements | Task 11 |

---

## E. M1.4 Work Plan — Code Tasks

| # | Task | Why Needed | Files | DoD | Size | Priority |
|---|------|------------|-------|-----|------|----------|
| 1 | Create RLS + seed migration for `warehouses` | Table exists but no RLS; seed needs RLS first | `backend/supabase/migrations/20261113000011_011_warehouse_rls_seed.sql` (NEW) | **Single file, RLS FIRST then seed**: `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`; policy for store managers using `user_roles.store_id`; INSERT "Main Central Warehouse" linked to store per **D2** | S | P0 |
| 2 | Verify/adjust role seed | Seed has 7 roles; ensure all exist | `backend/supabase/migrations/20261113000010_010_seed_data.sql` (REVIEW) | Confirm 7 roles present; no duplicates; descriptions match | S | P0 |
| 3 | Add integration test for warehouse seed | Verify exactly one central warehouse exists | `backend/tests/test_seed.py` (NEW) | `assert count(warehouses where name='Main Central Warehouse') == 1` | S | P1 |

> **RLS + Seed in same migration (Task 1) — RLS block comes BEFORE INSERT.** Never seed a table without RLS.

### Warehouse RLS Policy (Correct SQL)

```sql
-- RLS FIRST
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

-- SEED AFTER RLS
INSERT INTO public.warehouses (store_id, name, location)
SELECT id, 'Main Central Warehouse', 'Dhaka, Bangladesh'
FROM public.stores WHERE slug = 'best-gadget'
ON CONFLICT DO NOTHING;
```

---

## F. M1.4 Documentation Tasks

| Path | Must Contain | Depends On |
|------|--------------|------------|
| `docs/runbooks/m1.4-seed-data.md` | Step-by-step: run migrations 001-011 → verify role count (7) → verify stores (2) → verify warehouse (1) | Task 1, 2 |
| `docs/architecture/m1.4-main-central-warehouse.md` | Why linked per **D2**, RLS policy rationale, future multi-warehouse plan | Task 1 |

---

## G. Conflicts to Resolve (Corrected)

| Conflict | Files | Rule Applied | Resolution |
|----------|-------|--------------|------------|
| M1.1/M1.2 completion status | MILESTONES.md (✅) vs MASTER_MILESTONES.md (☐) | "Is task done?" → MILESTONES.md | Update MASTER_MILESTONES.md checkboxes to ✅ with dates from MILESTONES.md |
| Seed milestone assignment | DATABASE_MIGRATIONS_v1.txt (M1.2) vs MILESTONES.md (M1.4) | "Migration number?" → DATABASE_MIGRATIONS_v1.txt | **M1.4 = migration 011 (warehouse seed only). Keep migration 010 as M1.2.** |
| Current phase | PROJECT_STATUS.md (M1.3) vs AI_MAP.md (M1 Ready) | Most recent date wins | Update AI_MAP.md to "M1.3 Core Identity & Auth Integration" |
| Table count | MILESTONES.md (50) vs MASTER_MILESTONES.md (43) | Migration files × tables = truth | 10 migrations × ~5 = ~50. Update MASTER_MILESTONES.md to 50. |
| Role count | 010_seed (7) vs MILESTONES.md M1.4 (4) | Seed is implemented truth | Update MILESTONES.md M1.4 to list all 7 roles. |

---

## H. First 3 Days (Corrected Sequence)

### Day 0 — Verify + Decide (NO CODE)
- [ ] Confirm Decisions in Section B with owner (D2, D3, D4 — D1 and D5 closed)
- [ ] Document answers in `DECISIONS.md` (temp file for team)
- [ ] **Runnable check**: None (decision day)

### Day 1 — Test Infra + Exceptions + Security Core
- [ ] Create `backend/tests/conftest.py` with async DB fixture (Supabase local via `supabase start`)
- [ ] Create `backend/tests/test_auth.py` with empty test class (structure only)
- [ ] **Task 1**: Add deps to `requirements.txt` (`python-jose[cryptography]`, `supabase>=2.0`)
- [ ] **Task 2**: Create `backend/app/core/exceptions.py`
- [ ] **Runnable**: `pytest backend/tests/test_auth.py -v --collect-only` shows test structure

### Day 2 — JWT Validation + Auth Dependencies
- [ ] **Task 3**: Create `backend/app/core/security.py` with:
  - `get_jwks()` → caches JWKS from `SUPABASE_URL + "/auth/v1/.well-known/jwks.json"`
  - `verify_token(token: str) → dict` using `jose.jwt.decode` with JWKS, validates `iss`, `aud`, `exp`; **raises AuthError on failure**
- [ ] **Task 4**: Create `backend/app/core/auth.py` with `get_current_user`:
  - Decode JWT → get `sub` (user_id) → query `profiles` + `user_roles` + `roles` → return `User(id, email, roles:List[str])`
  - Cache in `request.state.user`
- [ ] **Task 5**: Add `require_role(*roles)` factory in same file
- [ ] Write 3 tests in `test_auth.py`:
  - `test_verify_token_valid` (mock JWKS)
  - `test_get_current_user_loads_roles`
  - `test_require_role_allows_denies`
- [ ] **Runnable**: `pytest backend/tests/test_auth.py -v` → 3 pass

### Day 3 — Warehouse Migration (RLS + Seed + Test)
- [ ] **Task 1 (M1.4)**: Create `20261113000011_011_warehouse_rls_seed.sql` with **RLS block FIRST, then INSERT** (see Section E for exact SQL)
- [ ] **Task 3**: Create `backend/tests/test_seed.py` with warehouse count test
- [ ] **Runnable**: Apply migration locally → `pytest backend/tests/test_seed.py -v` → pass

---

## I. Risks & Unknowns (Tied to Files Read)

| Risk | File Evidence | Mitigation |
|------|---------------|------------|
| **R1: JWKS endpoint unavailable** | Supabase GoTrue serves JWKS at `/{project}/auth/v1/.well-known/jwks.json` | Cache JWKS with 1h TTL. On fetch failure: fail-closed (reject token). Do NOT fall back to `service_role` for token verification. |
| **R2: `supabase-py` version API changes** (applies **only if D1 = Supabase Auth**) | `requirements.txt` has no supabase dep | Pin `supabase>=2.0,<3.0`; test auth flow early Day 2. |
| **R3: RLS policy for warehouses references `user_roles.store_id`** | 001_core_identity.sql:65 (`store_id UUID` nullable) | Use pattern above with `AND store_id IS NOT NULL` guard. Mirror existing 009_rls_policies.sql pattern. |
| **R4: No test DB configured** | `backend/tests/` FILE NOT FOUND | Day 1: implement per **D5** (Supabase local Docker). |
| **R5: Role `admin` in seed but not in M1.4/Matrix** | 010_seed_data.sql:8 vs MILESTONES.md | See Decision D3 in Section B. |

---

## J1. Could NOT Verify (Needs Running Services / External Docs)

1. **Supabase local JWKS endpoint URL format** — need running `supabase start` to confirm exact path
2. **Whether `supabase.auth` Python client supports OTP/email login flow** — need to test `supabase.auth.sign_in_with_otp({...})` against live GoTrue
3. **Exact `iss` claim value in GoTrue JWT** — blueprint says validate `iss` but doesn't give exact string format; need real token
4. **Exact JWT algorithm (RS256 vs HS256)** — blueprint says "verify signature"; assume RS256/JWKS per GoTrue standard; verify on Day 2

---

## J2. Did NOT Verify But COULD Have (Now Verified → Moved to Section A)

| Item | Previously Unverified | Now Verified (Command + Output) |
|------|----------------------|----------------------------------|
| `config.py` JWT fields | "No JWT config fields" | `cat backend/app/core/config.py` → 59 lines, only Supabase credentials (lines 30-32), no SECRET_KEY/ALGORITHM |
| `requirements.txt` JWT libs | "NO python-jose, pyjwt" | `cat backend/requirements.txt` → 7 deps (fastapi, uvicorn, pydantic, pydantic-settings, sqlalchemy, asyncpg, python-dotenv), confirmed no JWT/supabase libs |
| Auth provider mandate | "Supabase GoTrue mandated" | `grep -n "Supabase Auth" AURA_BELL_PROJECT_BLUEPRINT/08_SECURITY_AND_PRIVACY/AUTHENTICATION_AUTHORIZATION.md` → lines 15-17 |
| `warehouses.store_id` nullability | "NOT NULL" | `grep "store_id" backend/supabase/migrations/20261113000003_003_inventory.sql` → line 7: `store_id UUID NOT NULL REFERENCES public.stores(id)` |
| `user_roles.store_id` nullability | "NOT NULL?" | `grep -A5 "CREATE TABLE.*user_roles" backend/supabase/migrations/20261113000001_001_core_identity.sql` → line 65: `store_id UUID` (nullable) |
| `profiles.store_id` | exists? | `grep -A12 "CREATE TABLE.*profiles" backend/supabase/migrations/20261113000001_001_core_identity.sql` → NO store_id column |
| RLS on `warehouses` | "MISSING" | `grep -E "ALTER TABLE.*warehouses.*ENABLE" backend/supabase/migrations/20261113000009_009_rls_policies.sql` → no output (absent) |
| Role count in matrix | "6 roles?" | `grep -E "^\|.*\|" AURA_BELL_PROJECT_BLUEPRINT/08_SECURITY_AND_PRIVACY/AUTHENTICATION_AUTHORIZATION.md | grep -vE "^\|[-: ]+\|"` → 6 rows (Anonymous/Public, Customer, Support Agent, Inventory Manager, Store Manager, Super Admin/Owner) |
| Role count (7 vs 4 vs 6) | "Seed has 7, M1.4 says 4" | Verified: `grep -c "INSERT.*roles" backend/supabase/migrations/20261113000010_010_seed_data.sql` → 7; `grep "Super Admin\|Store Manager\|Inventory Manager\|Customer" MILESTONES.md` → 4; matrix → 6 |

---

## Known Constraints (No Verification Needed)

- `SUPABASE_SERVICE_ROLE_KEY` CANNOT verify user tokens. It bypasses RLS for admin operations only. Do not use for token verification.
- `user_roles.store_id` is nullable — role can be global (no store) or store-scoped.
- `warehouses.store_id` is NOT NULL — every warehouse must belong to a store.
- `profiles` has no store_id — store association is via `user_roles`.

---

## Plan File
Saved to: `.kilo/plans/1794639579763-m13-m14-implementation-plan.md`