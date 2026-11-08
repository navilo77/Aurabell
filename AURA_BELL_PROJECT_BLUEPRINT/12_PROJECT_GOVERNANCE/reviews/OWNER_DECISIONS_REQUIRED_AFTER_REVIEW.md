# Aura Bell — Owner Decisions Required After Critical Review

**Review Date:** 2026-11-08  
**Reviewer:** Independent Architecture Reviewer  
**Context**: Post-critical-architecture-review — additional owner decisions needed before implementation

---

## Context

The critical architecture review identified **6 critical operational gaps** that require explicit Owner decisions before implementation can safely proceed. The 4 original DEC-OWN decisions (payment gateway, TTL, delivery fee, courier) are **CONFIRMED** but insufficient for Bangladesh operational realities.

---

## New Owner Decisions Required

### DEC-REVIEW-001: COD Order Verification Method
**Area**: COD Fraud Prevention  
**Risk**: HIGH — Fake orders, wasted courier costs  
**Current Gap**: No pre-order verification documented

| Option | Description | Pros | Cons | Recommendation |
|--------|-------------|------|------|----------------|
| **A: SMS OTP** | Send OTP to customer phone before order confirmation | Standard, automated, auditable | Requires SMS gateway, delivery delays | **RECOMMENDED** |
| **B: IVR Call** | Automated voice call with confirmation code | Works on feature phones | Higher cost, call drops | Fallback |
| **C: Manual Call** | Staff calls customer to confirm | Personal touch, no tech | Not scalable, staff cost | No |
| **D: None** | No verification | Simple, fast | Maximum fraud exposure | No |

**Required Configuration**:
- OTP length (4/6 digits)
- OTP expiry (5/10/15 minutes)
- Max retry attempts (3/5)
- Resend cooldown (30/60 seconds)
- Fallback to IVR on SMS failure

**Owner Decision Required**: Select verification method(s) and configure parameters.

---

### DEC-REVIEW-002: COD Order Value Cap
**Area**: COD Fraud Prevention  
**Risk**: HIGH — High-value fraud exposure (electronics)  
**Current Gap**: No maximum COD order value

| Option | Description | Pros | Cons | Recommendation |
|--------|-------------|------|------|----------------|
| **A: 3,000 BDT** | Conservative cap | Low fraud exposure | Limits high-value sales | Conservative |
| **B: 5,000 BDT** | Balanced cap | Covers most legitimate orders | Some fraud exposure | **RECOMMENDED** |
| **C: 10,000 BDT** | Higher cap | Covers premium electronics | Higher fraud exposure | Aggressive |
| **D: Tiered by trust score** | New: 3,000 / Trusted: 10,000 / VIP: No limit | Dynamic, rewards good customers | Complex implementation | Future |
| **E: No limit** | Unlimited COD | Maximum sales | Maximum fraud | No |

**Required Configuration**:
- Default cap for new customers
- Trust score thresholds for tier upgrades
- Override process for exceptional orders
- Admin override capability

**Owner Decision Required**: Set COD order value cap and tier configuration.

---

### DEC-REVIEW-003: RTO (Return to Origin) Cost Allocation
**Area**: Delivery Fee Economics  
**Risk**: HIGH — Unbounded loss on refused deliveries  
**Current Gap**: Flat fee covers 1× courier, RTO costs 2×

| Option | Description | Pros | Cons | Recommendation |
|--------|-------------|------|------|----------------|
| **A: Customer pays** | Charge customer return shipping on refusal | Full cost recovery | Customer hostility, cart abandonment | No |
| **B: Platform absorbs** | Platform pays all RTO costs | Best customer experience | Unbounded loss (est. 270K BDT/yr) | No |
| **C: Hybrid — First free** | First RTO free, subsequent charged to customer | Balanced | Complex tracking | **RECOMMENDED** |
| **D: Courier insurance** | Insure against RTO losses | Predictable cost | Premium cost, claims process | Evaluate |
| **E: Courier bears** | Negotiate courier absorbs RTO | Zero platform cost | Unlikely, higher base rates | Negotiate |

**Required Configuration**:
- Free RTO allowance per customer (1/3/5 per year)
- Charge amount for subsequent RTOs
- Dispute process for customer claims
- Courier contract RTO clauses

**Owner Decision Required**: Select RTO cost allocation model and configure parameters.

---

### DEC-REVIEW-004: Return Shipping Cost Policy
**Area**: Delivery Fee Economics  
**Risk**: MEDIUM-HIGH — Platform absorbs all return shipping  
**Current Gap**: Flat fee doesn't cover return shipping

| Option | Description | Pros | Cons | Recommendation |
|--------|-------------|------|------|----------------|
| **A: Free returns** | Platform pays all return shipping | Best customer experience | High cost (est. 288K BDT/yr) | Customer acquisition |
| **B: Customer pays** | Customer pays return shipping | Zero platform cost | High cart abandonment | No |
| **C: Hybrid — Defective free** | Defective/incorrect: free; Change of mind: customer pays | Fair, industry standard | Requires inspection | **RECOMMENDED** |
| **D: Capped platform** | Platform pays up to X BDT per return | Predictable cost | Complex | Alternative |
| **E: Free for loyal** | Free returns for high-trust customers | Rewards loyalty | Complex tiers | Future |

**Required Configuration**:
- Return shipping cap per order (e.g., 100 BDT)
- Defective vs change-of-mind classification process
- Return shipping carrier (same courier? cheaper option?)
- Return pickup scheduling

**Owner Decision Required**: Select return shipping cost model and configure parameters.

---

### DEC-REVIEW-005: Multi-Shipment Surcharge Policy
**Area**: Delivery Fee Economics  
**Risk**: MEDIUM — Split orders lose money (1 fee vs N×courier)  
**Current Gap**: Flat fee per order, but multi-store = multi-shipment

| Option | Description | Pros | Cons | Recommendation |
|--------|-------------|------|------|----------------|
| **A: No surcharge** | Platform absorbs (current DEC-OWN-003) | Simple, customer-friendly | Loss per extra shipment (est. 168K BDT/yr) | No |
| **B: Per-shipment surcharge** | Flat fee per additional shipment (e.g., 50 BDT) | Recovers marginal cost | Customer may abandon | **RECOMMENDED** |
| **C: Weight-based surcharge** | Surcharge proportional to additional weight | Fair | Complex calculation | Alternative |
| **D: Dynamic** | Surcharge = actual additional courier cost | Exact recovery | Complex, unpredictable | No |
| **E: Threshold-based** | Free up to X kg, then surcharge | Simple | May not cover cost | Alternative |

**Required Configuration**:
- Surcharge amount per additional shipment (e.g., 50 BDT)
- Weight threshold for surcharge
- Cap on total surcharge per order
- Display at checkout (RULE-AUR-008)

**Owner Decision Required**: Select multi-shipment surcharge model and configure amount.

---

### DEC-REVIEW-006: Offline Sales Staff Role & Workflow
**Area**: Inventory Synchronization  
**Risk**: HIGH — Offline sales treated as afterthought  
**Current Gap**: Only "Admin Panel" mentioned, no staff role, no POS workflow

| Option | Description | Pros | Cons | Recommendation |
|--------|-------------|------|------|----------------|
| **A: Admin panel only** | Staff use admin panel for offline sales | No new UI, uses existing | Poor UX, no POS features | Minimum viable |
| **B: Staff role + Admin panel workflow** | New `store_staff` role, dedicated offline sale flow | Proper permissions, audit trail | New role, UI work | **RECOMMENDED** |
| **C: POS API + Mobile app** | REST API + staff mobile app for offline sales | Real POS experience | Significant development | Phase 2 |
| **D: Barcode scanner integration** | USB/Bluetooth scanner for stock lookup/sale | Fast, accurate | Hardware dependency | Phase 2 |

**Required Configuration**:
- Staff role permissions (own store only)
- Offline sale workflow steps (reserve → confirm → payment → receipt)
- Offline sale TTL (5 min reservation → confirm)
- Offline COD handling (same 15-min TTL?)
- Receipt printing (thermal printer)
- Shift handover stock count

**Owner Decision Required**: Select offline sales approach and configure staff role permissions.

---

### DEC-REVIEW-007: COD Verification Method (Refinement)
**Area**: COD Fraud Prevention  
**Risk**: HIGH — Fake orders  
**Current Gap**: DEC-REVIEW-001 covers method, but needs refinement

| Option | Description | Pros | Cons | Recommendation |
|--------|-------------|------|------|----------------|
| **A: Mandatory OTP for all COD** | Every COD order requires OTP | Maximum fraud prevention | Friction for legitimate customers | **RECOMMENDED** |
| **B: OTP for new customers only** | Trusted customers skip OTP | Better UX for repeat buyers | Fraudsters can build trust | Alternative |
| **C: OTP for orders > 2,000 BDT** | Risk-based verification | Less friction for small orders | Fraudsters stay under threshold | Alternative |
| **D: IVR fallback** | If SMS fails, auto-call with code | Reliability | Cost | Include as backup |

**Required Configuration**:
- OTP length (4 vs 6 digits)
- OTP expiry (5 vs 10 minutes)
- Max retries (3 vs 5)
- Resend cooldown (30 vs 60 seconds)
- Rate limiting per phone/IP

**Owner Decision Required**: Confirm mandatory OTP for all COD and configure parameters.

---

### DEC-REVIEW-008: Customer Fraud Scoring & Auto-Block
**Area**: COD Fraud Prevention  
**Risk**: HIGH — Serial fraudsters  
**Current Gap**: No fraud scoring, no auto-block

| Option | Description | Pros | Cons | Recommendation |
|--------|-------------|------|------|----------------|
| **A: Auto-block at 3 failed COD** | Hard block after 3 refused deliveries | Simple, strong deterrent | False positives possible | **RECOMMENDED** |
| **B: Auto-block at 5 failed COD** | More lenient | Fewer false positives | More fraud exposure | Alternative |
| **C: Soft flag at 3, block at 5** | Warning then block | Balanced | More complex | Alternative |
| **D: Manual review only** | Flag for admin, no auto-block | No false blocks | Slow, manual effort | No |

**Required Configuration**:
- Failed COD threshold (3/5)
- Failed delivery types counted (refusal, unavailable, fake address)
- Auto-block duration (30/90/365 days / permanent)
- Appeal process for customers
- Admin override capability

**Owner Decision Required**: Set fraud thresholds and block policy.

---

## Decision Summary Matrix

| Decision ID | Area | Risk | Urgency | Owner Input |
|-------------|------|------|---------|-------------|
| DEC-REVIEW-001 | COD Verification | HIGH | Before implementation | Required |
| DEC-REVIEW-002 | COD Value Cap | HIGH | Before implementation | Required |
| DEC-REVIEW-003 | RTO Cost Allocation | HIGH | Before implementation | Required |
| DEC-REVIEW-004 | Return Shipping Cost | MEDIUM-HIGH | Before launch | Required |
| DEC-REVIEW-005 | Multi-Shipment Surcharge | MEDIUM | Before launch | Required |
| DEC-REVIEW-006 | Offline Staff Role | HIGH | Before implementation | Required |
| DEC-REVIEW-007 | COD Verification Refinement | HIGH | Before implementation | Required |
| DEC-REVIEW-008 | Fraud Auto-Block | HIGH | Before launch | Required |

---

## Implementation Dependency

| Decision | Blocks Implementation Of |
|----------|--------------------------|
| DEC-REVIEW-001, 002, 007, 008 | COD workflow, fraud prevention, customer onboarding |
| DEC-REVIEW-003, 004, 005 | Shipping cost engine, checkout display, courier integration |
| DEC-REVIEW-006 | Inventory admin panel, offline sales, staff workflow |

---

## Recommendation

**All 8 decisions should be resolved before Phase 2 (System Foundation) begins**, as they affect:
- Database schema (fraud scores, staff roles, surcharge fields)
- API specifications (COD verification, surcharge calculation)
- Business logic (RTO handling, return shipping, fraud blocking)
- UI/UX (COD verification flow, surcharge display, staff panel)

**Estimated Owner Review Time**: 2-3 hours for all 8 decisions  
**Recommended**: Single review session with all stakeholders

---

## Documentation Updates Required Post-Decision

| Document | Updates Needed |
|----------|----------------|
| `OWNER_DECISIONS_REQUIRED.md` | Add 8 new DEC-REVIEW entries |
| `OPEN_OWNER_DECISIONS.md` | Track 8 new decisions |
| `INVENTORY_SYSTEM_ARCHITECTURE.md` | Add staff role, offline sale API, fraud scoring |
| `SHIPPING_SYSTEM_ARCHITECTURE.md` | Add RTO/return cost policies, surcharge logic |
| `PAYMENT_SYSTEM_ARCHITECTURE.md` | Add COD verification flow, value cap |
| `CART_CHECKOUT_PRD.md` | Add surcharge display, COD verification step |
| `DOCUMENT_INDEX.md` | Version bump |
| `CHANGELOG.md` | New entries for each decision |

---

**Document ID:** OWNER_DECISIONS_REQUIRED_AFTER_REVIEW  
**Version:** 1.0  
**Status:** FINAL  
**Date:** 2026-11-08