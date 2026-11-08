# Aura Bell — Critical Architecture Review

**Review Date:** 2026-11-08  
**Reviewer:** Independent Architecture Reviewer  
**Scope:** Complete documentation review against Bangladesh e-commerce operational realities

---

## Executive Summary

| Review Area | Overall Assessment | Risk Level |
|-------------|-------------------|------------|
| COD Fraud & RTO | **PARTIALLY ADDRESSED** — Core workflows documented, critical gaps in fraud prevention | HIGH |
| Flat Delivery Fee Economics | **PARTIALLY ADDRESSED** — Policy confirmed, operational cost allocation unspecified | MEDIUM |
| Payment Reliability | **WELL DOCUMENTED** — Solid architecture, gaps in edge-case handling | MEDIUM |
| Offline/Online Inventory | **PARTIALLY ADDRESSED** — Architecture exists, operational procedures incomplete | HIGH |
| Implementation Complexity | **HIGH** — 43 tables, 11 modules, single-developer ambitious | HIGH |

**Overall Architecture Assessment: PRODUCTION-READY WITH CRITICAL OPERATIONAL GAPS**

---

## 1. COD Fraud & RTO — Detailed Analysis

### What's Documented (Verified)

| Document | Coverage |
|----------|----------|
| `INVENTORY_SYSTEM_ARCHITECTURE.md` (DOC-AUR-162) §7 | COD confirmation workflow (7 steps), COD pending → confirmed within 15-min TTL |
| `INVENTORY_SYSTEM_ARCHITECTURE.md` §9.1 | Cancellation rules for COD (customer refuses, partial payment) |
| `SHIPPING_SYSTEM_ARCHITECTURE.md` (DOC-AUR-165) §7.3 | COD return handling: "Courier must confirm collection", "No post-delivery return if COD not confirmed" |
| `PAYMENT_SYSTEM_ARCHITECTURE.md` (DOC-AUR-157) §1.9 | COD listed as V1 feature |
| `PAYMENT_TIMEOUT_FAILURE.md` (DOC-AUR-163) §3.2 | COD failure scenarios in failure handling |

### Critical Gaps Identified

| Gap | Risk | Evidence |
|-----|------|----------|
| **No customer verification before COD order** | HIGH — Fake orders, wasted courier costs | No OTP/phone verification documented for COD orders |
| **No COD amount limit** | HIGH — High-value fraud exposure | No maximum COD order value specified |
| **No customer delivery history tracking for fraud scoring** | MEDIUM — Repeat offenders undetected | `CUSTOMER_PRD.md` only has order history, no fraud flags |
| **No courier-side COD collection confirmation workflow** | HIGH — Disputes unresolvable | `SHIPPING_SYSTEM_ARCHITECTURE.md` §7.3 mentions "Courier must confirm collection" but no API/workflow |
| **RTO (Return to Origin) cost allocation undefined** | HIGH — Financial exposure | Flat fee policy (DEC-OWN-003) doesn't address who pays return shipping on RTO |
| **No COD reconciliation with courier cash collection** | HIGH — Cash leakage | `PAYMENT_RECONCILIATION.md` only covers gateway payments |
| **No COD order confirmation before dispatch** | MEDIUM — Wasted courier trips | No documented "confirm with customer before dispatch" step |

### Missing Requirements

1. **Pre-COD order verification**: Phone OTP or IVR confirmation before order confirmation
2. **COD order value cap**: Configurable maximum (e.g., 5,000 BDT default)
3. **Customer COD fraud score**: Based on delivery acceptance rate, return rate, cancellation rate
4. **Courier COD collection API**: Real-time confirmation of cash collected
5. **RTO cost policy**: Who bears return shipping — customer, store, or platform?
6. **COD cash reconciliation**: Daily reconciliation of courier-collected cash vs orders
7. **Blacklist management**: Auto-block customers with >X failed COD deliveries

### Verdict: **PARTIALLY ADDRESSED — HIGH RISK**
Core workflows exist but fraud prevention and RTO economics are significantly under-specified for Bangladesh market realities.

---

## 2. Flat Delivery Fee Economics — Detailed Analysis

### Owner Decision (CONFIRMED)
- **DEC-OWN-003**: Flat delivery fee per order (single fee regardless of stores/shipments)

### What's Documented

| Document | Coverage |
|----------|----------|
| `CART_CHECKOUT_PRD.md` (DOC-AUR-046) PRD-CHK-004 | "Flat delivery fee (single shipping fee per order) calculated, displayed transparently" |
| `SHIPPING_SYSTEM_ARCHITECTURE.md` §5.1 | Cost formula: Base Fee + Weight Fee + Service Fee (all TBD) |
| `SHIPPING_SYSTEM_ARCHITECTURE.md` §6.1 | Shipping cost calculated at checkout, displayed before payment |

### Economic Analysis

| Scenario | Fee Collected | Actual Cost | Exposure |
|----------|---------------|-------------|----------|
| Single store, single shipment | 1× flat fee | 1× courier charge | Break-even if fee ≥ cost |
| Multi-store, single shipment (consolidated) | 1× flat fee | 1× courier charge | **Profit if fee > cost** |
| Multi-store, multi-shipment (split) | 1× flat fee | N× courier charges | **LOSS if N×cost > fee** |
| Failed delivery → RTO | 1× flat fee | 2× courier (out + return) | **LOSS** |
| Return shipment | 1× flat fee | 1× return courier | **LOSS** |
| Partial return | 1× flat fee | Return courier cost | **LOSS** |

### Critical Gaps

| Gap | Financial Impact |
|-----|------------------|
| **No courier rate card integration** | Cannot calculate if flat fee covers actual costs |
| **No weight/dimension-based fee tiers** | Heavy items subsidized by light items |
| **No zone-based pricing** | Remote areas subsidized by metro |
| **RTO cost recovery mechanism undefined** | 100% platform loss on RTO |
| **Return shipping cost allocation** | Platform absorbs return shipping |
| **Multi-shipment loss scenario** | No policy for when N×courier > flat fee |

### Missing Financial Policies Required

1. **Courier rate card**: Base fee, per-kg rate, zone surcharges per courier (Pathao)
2. **Fee adequacy threshold**: Minimum flat fee = max expected courier charge + buffer
3. **RTO cost recovery**: Customer pays return shipping on refusal, or platform absorbs with limit
4. **Return shipping policy**: Free returns vs customer-paid, max return shipping per order
5. **Multi-shipment surcharge**: Additional fee when split shipments required
6. **Monthly fee adequacy review**: Automated report comparing collected vs actual courier costs

### Verdict: **PARTIALLY ADDRESSED — MEDIUM RISK**
Policy confirmed but operational cost model incomplete. Without courier rate integration and RTO/return cost policies, platform faces unbounded shipping loss exposure.

---

## 3. Payment Reliability — Detailed Analysis

### What's Well Documented (Strengths)

| Area | Coverage | Document |
|------|----------|----------|
| Provider Adapter Pattern | Complete with interface, registry, factory | `PAYMENT_SYSTEM_ARCHITECTURE.md` §1.2 |
| Webhook Security | HMAC-SHA256, constant-time compare, timestamp validation | `PAYMENT_WEBHOOK_LIFECYCLE.md` §6 |
| Idempotency | `provider_event_id` unique constraint, duplicate handling | `PAYMENT_WEBHOOK_LIFECYCLE.md` §5, `PAYMENT_SYSTEM_ARCHITECTURE.md` §1.5 |
| Signature Verification | HMAC-SHA256, constant-time compare, 24hr timestamp tolerance | `PAYMENT_WEBHOOK_LIFECYCLE.md` §6 |
| Payment Failure | 3 attempts max, 15-min TTL, backoff, late success | `PAYMENT_TIMEOUT_FAILURE.md` §2-4 |
| Reconciliation | Daily 02:00 AM, discrepancy types, resolution workflow | `PAYMENT_RECONCILIATION.md` §3-7 |
| Refund Workflow | Admin-only, 7-day window, inspection, gateway refund | `PAYMENT_REFUND_MANUAL.md` (DOC-AUR-164) |

### Critical Edge-Case Gaps

| Gap | Severity | Missing Specification |
|-----|----------|----------------------|
| **Browser closure during payment redirect** | HIGH | No specification for abandoned checkout recovery |
| **Network disconnection during payment** | HIGH | Client-side timeout handling, retry UX |
| **Payment success after order timeout (late success)** | MEDIUM | Documented in `PAYMENT_TIMEOUT_FAILURE.md` §10 but no frontend UX |
| **Duplicate callback from gateway** | MEDIUM | Covered by idempotency but no retry-after guidance |
| **Gateway maintenance window handling** | MEDIUM | No scheduled downtime handling |
| **Partial payment scenarios** | LOW | Not supported in V1 (COD only full amount) |
| **Currency mismatch** | LOW | BDT only in V1 |
| **Gateway API version changes** | MEDIUM | No adapter versioning strategy |

### Browser Closure / Network Disconnection — Specific Analysis

**Current Gap**: No specification for:
- Customer closes browser after clicking "Pay" but before gateway redirect completes
- Network fails during gateway redirect
- Customer closes gateway payment page
- Gateway redirects back but browser crashed

**Required but Missing**:
1. **Abandoned payment recovery**: Polling mechanism or webhook-only reliance
2. **Client-side payment state persistence**: LocalStorage/sessionStorage for payment attempt ID
3. **Return URL handling**: Deep link / universal link for app, query params for web
4. **Timeout UX**: Countdown timer, "Payment in progress" page, manual retry button

### Verdict: **WELL DOCUMENTED ARCHITECTURE — MEDIUM RISK ON EDGE CASES**
Core architecture is solid. Critical gap: client-side payment flow resilience (browser closure, network issues) not specified. This is a common production failure mode in Bangladesh where network reliability is variable.

---

## 4. Offline/Online Inventory Synchronization — Detailed Analysis

### What's Documented

| Document | Coverage |
|----------|----------|
| `INVENTORY_SYSTEM_ARCHITECTURE.md` (DOC-AUR-162) §4.1-4.4 | Stock availability, reservation, release, payment failure release |
| `INVENTORY_SYSTEM_ARCHITECTURE.md` §7 | COD confirmation workflow (15-min TTL) |
| `INVENTORY_SYSTEM_ARCHITECTURE.md` §6 | Batch tracking (skincare), Serial/IMEI tracking (gadgets) |
| `INVENTORY_SYSTEM_ARCHITECTURE.md` §9 | Cancellation rules with stock restoration |
| `BUSINESS_RULES.md` (DOC-AUR-031) | RULE-AUR-001 (DB-Driven Stock Truth), RULE-AUR-003 (Mandatory Reservation), RULE-AUR-009 (Immutable Ledger) |
| `AB-PV-001` §5.4 | "Offline Sale হলে Admin Panel থেকে Stock Update" |

### Critical Gaps

| Gap | Risk | Missing Specification |
|-----|------|----------------------|
| **No offline sale API** | HIGH | Only "Admin Panel" mentioned, no API for POS integration |
| **No concurrent offline/online conflict resolution** | HIGH | Race condition: online order + offline sale same SKU |
| **No offline sale audit trail requirements** | MEDIUM | Who, when, why, reference number not specified |
| **No offline stock sync frequency** | HIGH | Real-time? Batch? Manual trigger? |
| **No offline sale stock reservation** | HIGH | Offline sale bypasses reservation system |
| **No offline sale COD handling** | HIGH | Offline COD vs online COD differentiation |
| **No staff role for offline sales** | MEDIUM | No "Store Staff" role in RBAC (`AUTHENTICATION_AUTHORIZATION.md`) |
| **No offline sale reconciliation** | HIGH | Daily reconciliation only covers payments |

### Race Condition Analysis

**Scenario**: Online customer adds last unit to cart → reservation created. Simultaneously, walk-in customer buys same item in physical store. Staff updates stock via admin panel.

**Current State**: 
- Online: Reservation created (quantity_reserved++)
- Offline: Admin reduces quantity_on_hand directly
- **Race condition**: Both succeed, stock goes negative or double-sold

**Missing**: 
1. **Optimistic locking** on `inventory_balances` for admin updates
2. **Offline sale reservation**: Staff must "reserve" before confirming sale
3. **Conflict notification**: Alert online customer if stock changed during checkout
4. **Compensation logic**: If conflict, which sale wins? (timestamp-based?)

### Verdict: **PARTIALLY ADDRESSED — HIGH RISK**
Architecture supports online inventory well. Offline sales treated as afterthought — no API, no conflict resolution, no staff workflow, no reconciliation. For Bangladesh where offline retail is significant, this is a critical operational gap.

---

## 5. Implementation Complexity — Detailed Assessment

### Architecture Metrics

| Metric | Value | Assessment |
|--------|-------|------------|
| **Database Tables** | 43 | High for modular monolith |
| **Backend Modules** | 11 | Well-bounded |
| **API Endpoints** | 33+ | Reasonable |
| **Payment Adapters** | 2 (bKash, SSLCommerz) + 1 future | Standard |
| **Courier Adapters** | 1 (Pathao) + 2 future | Standard |
| **State Machines** | 3 (Order, Payment, Shipment) | Complex |
| **RLS Policies** | 43 tables × 6 roles | Very High |
| **Background Workers** | 4+ (outbox, TTL, reconciliation, notifications) | Moderate |

### Module Boundaries Assessment

| Module | Dependencies | Coupling | Risk |
|--------|--------------|----------|------|
| Identity | — | Low | ✅ |
| Store | Identity | Low | ✅ |
| Catalog | Store, Identity | Medium | ⚠️ |
| Pricing | Catalog | Low | ✅ |
| Inventory | Catalog, Store | Medium | ⚠️ |
| Cart | Inventory, Pricing, Identity | High | 🔴 |
| Order | Cart, Inventory, Payment | High | 🔴 |
| Payment | Order, Inventory | High | 🔴 |
| Fulfillment | Order, Payment, Inventory | High | 🔴 |
| Returns | Order, Payment, Inventory | High | 🔴 |
| Reporting | All | Read-only | ✅ |

**Critical Coupling**: Cart → Checkout → Order → Payment → Fulfillment → Returns form a tight chain. Any change ripples through 6 modules.

### Single-Developer Feasibility

| Factor | Assessment |
|--------|------------|
| **Database migrations (43 tables, 10 migrations)** | 2-3 weeks solo |
| **11 backend modules** | 8-12 weeks solo |
| **Frontend (2 storefronts + admin)** | 6-8 weeks solo |
| **Payment adapters (2 gateways)** | 3-4 weeks solo |
| **Courier adapter (Pathao)** | 2-3 weeks solo |
| **Testing (unit + integration + E2E)** | 4-6 weeks solo |
| **DevOps/Deployment** | 2-3 weeks solo |
| **Total estimate** | **27-39 weeks (7-10 months) solo** |

**Verdict**: Ambitious but feasible for experienced full-stack developer. Risk: payment gateway sandbox access delays, courier API access delays.

### Operational Complexity

| Operational Task | Complexity | Frequency |
|------------------|------------|-----------|
| Daily payment reconciliation | Medium | Daily |
| Stock reservation TTL monitoring | Low | Continuous (automated) |
| Courier dispatch (manual V1) | Medium | Per order |
| Return processing | Medium | Per return |
| Payment reconciliation discrepancies | High | As needed |
| RLS policy debugging | High | As needed |
| Database migration rollback | High | Rare |
| Secret rotation | Low | Quarterly |

---

## 6. External Critique Validation

### Critique 1: "COD Fraud & RTO handling is insufficient"
**Verdict: VALID**
- Confirmed: No pre-COD verification, no COD amount limit, no fraud scoring, no RTO cost policy, no courier COD confirmation API
- Evidence: `INVENTORY_SYSTEM_ARCHITECTURE.md` §7, `SHIPPING_SYSTEM_ARCHITECTURE.md` §7.3

### Critique 2: "Flat delivery fee economics are undefined"
**Verdict: PARTIALLY VALID**
- Policy confirmed (DEC-OWN-003) but cost model, RTO/return cost allocation, multi-shipment loss scenarios undefined
- Evidence: `CART_CHECKOUT_PRD.md` PRD-CHK-004, `SHIPPING_SYSTEM_ARCHITECTURE.md` §5

### Critique 3: "Payment reliability edge cases unaddressed"
**Verdict: PARTIALLY VALID**
- Core architecture solid, but browser closure/network disconnection edge cases not specified
- Evidence: `PAYMENT_WEBHOOK_LIFECYCLE.md`, `PAYMENT_TIMEOUT_FAILURE.md` — strong on server side, weak on client-side resilience

### Critique 4: "Offline/online inventory sync is an afterthought"
**Verdict: VALID**
- Architecture supports online well, offline sales have no API, no conflict resolution, no staff workflow
- Evidence: `INVENTORY_SYSTEM_ARCHITECTURE.md`, `AB-PV-001` §5.4 mentions offline but no spec

### Critique 5: "Implementation complexity is underestimated for single developer"
**Verdict: PARTIALLY VALID**
- 43 tables, 11 modules, tight coupling in checkout chain, complex RLS — 7-10 months solo is ambitious
- Evidence: 43 tables, 11 modules, 33+ endpoints, 3 state machines, RLS on 43 tables × 6 roles

---

## Overall Assessment Summary

| Category | Status | Production Ready? |
|----------|--------|-------------------|
| **Core Architecture** | Solid, well-documented | ✅ YES |
| **Business Rules** | 12 inviolable rules, well-enforced | ✅ YES |
| **Owner Decisions** | All 4 confirmed, blocking removed | ✅ YES |
| **Payment Architecture** | Solid, gaps in client-edge cases | ⚠️ MOSTLY |
| **COD/RTO Operations** | Significant gaps | ❌ NO |
| **Delivery Fee Economics** | Policy set, cost model incomplete | ⚠️ PARTIAL |
| **Offline Inventory** | Architecture gap | ❌ NO |
| **Implementation Plan** | Ambitious but feasible | ⚠️ AMBITIOUS |

### What Can Safely Proceed to Implementation
1. Database schema & migrations (43 tables) — **READY**
2. Identity, Store, Catalog modules — **READY**
3. Inventory core (balances, reservations, movements) — **READY** (with TTL=15min)
4. Cart module — **READY**
5. Payment provider interface & adapters (bKash, SSLCommerz) — **READY**
6. API foundation, auth, RLS — **READY**

### What Needs Additional Documentation Before Implementation
1. **COD fraud prevention workflow** (pre-order verification, amount limits, fraud scoring)
2. **RTO/Return cost allocation policy** (who pays what)
3. **Offline sales API & conflict resolution** (staff workflow, race conditions)
4. **Client-side payment resilience** (browser closure, network disconnect UX)
5. **Courier rate card integration** (for fee adequacy monitoring)
6. **Staff/offline sales role & workflow** (POS integration)

### What Requires Owner Decisions
1. **COD order value cap** (default 5,000 BDT?)
2. **RTO cost allocation** (customer / store / platform?)
3. **Return shipping cost** (free returns? customer-paid? capped?)
4. **Multi-shipment surcharge** (when N×courier > flat fee)
4. **Offline sales staff role permissions** (new RBAC role?)
5. **COD verification method** (OTP / IVR / none?)

---

**Review Conclusion**: The Aura Bell architecture is **technically sound and well-documented** for core e-commerce flows. However, **Bangladesh-specific operational realities (COD fraud, RTO economics, offline sales, network reliability) expose critical gaps** that must be addressed before production deployment. The architecture can proceed to implementation for core modules, but COD, shipping economics, and offline inventory require additional specification.

---

**Document ID:** CRITICAL_ARCHITECTURE_REVIEW  
**Version:** 1.0  
**Status:** FINAL  
**Date:** 2026-11-08