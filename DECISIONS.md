# AURA BELL — Implementation Decisions (Day 0)

Generated: 2026-11-14

## D1: Auth Provider — CLOSED
**Decision**: Supabase GoTrue (mandated by blueprint)
**JWT Validation**: RS256 via JWKS endpoint at `SUPABASE_URL + "/auth/v1/.well-known/jwks.json"`
**Verify on Day 2**: Exact algorithm from real token

---

## D2: Warehouse Ownership — RESOLVED
**Decision**: Option (i) — Link central warehouse to **Best Gadget** (slug `best-gadget`)
**Rationale**: Primary revenue store, simpler, matches migration 010 seed order (first store inserted)
**Implementation**: Migration 011 INSERT uses `WHERE slug = 'best-gadget'`

---

## D3: Role Count Resolution — RESOLVED
**Decision**: Option (A) — Keep all 7 seeded roles; update MILESTONES.md M1.4 to list 7
**Roles from seed (010)**:
1. `owner` — Platform owner
2. `admin` — Platform administrator
3. `store_manager` — Store management
4. `inventory_manager` — Inventory management
5. `order_manager` — Order management
6. `support_agent` — Customer support
7. `customer` — Customer account
**Matrix alignment**: Auth spec matrix has 6 (includes Anonymous); Anonymous handled in auth logic, not DB role

---

## D4: aud/iss Strict Validation — RESOLVED
**Decision**: Validate both strictly
- `iss` must equal `settings.SUPABASE_URL + "/auth/v1"`
- `aud` must equal `"authenticated"`
**Implementation**: In `security.py:verify_token()` using `jose.jwt.decode` with `options={"verify_iss": True, "verify_aud": True}`

---

## D5: Test Database Strategy — CLOSED
**Decision**: Supabase local Docker (`supabase start`)
**Configuration**: `backend/tests/conftest.py` starts Supabase local, provides async DB fixture