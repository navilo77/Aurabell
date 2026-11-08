# Aura Bell — COD Fraud & RTO Risk Assessment

**Review Date:** 2026-11-08  
**Reviewer:** Independent Architecture Reviewer  
**Focus:** COD fraud prevention, Return-to-Origin handling, Bangladesh market realities

---

## Bangladesh COD Market Context

| Metric | Bangladesh Reality | Source |
|--------|-------------------|--------|
| COD penetration | 60-70% of e-commerce orders | Industry reports |
| COD fraud rate | 15-25% fake/refused orders | Industry estimates |
| RTO rate | 10-20% of COD orders | Courier reports |
| Average courier cost (Dhaka metro) | 60-120 BDT | Pathao/Steadfast |
| Average courier cost (outside Dhaka) | 100-200 BDT | Pathao/Steadfast |
| RTO cost (round trip) | 2× forward cost | Courier policy |

---

## Current Aura Bell COD Documentation

### Verified Coverage

| Document | Section | Coverage |
|----------|---------|----------|
| `INVENTORY_SYSTEM_ARCHITECTURE.md` §7 | 7-step COD confirmation workflow | ✅ |
| `INVENTORY_SYSTEM_ARCHITECTURE.md` §9.1 | Cancellation rules (COD refusal, partial payment) | ✅ |
| `SHIPPING_SYSTEM_ARCHITECTURE.md` §7.3 | "Courier must confirm collection", "No post-delivery return if COD not confirmed" | ✅ |
| `PAYMENT_SYSTEM_ARCHITECTURE.md` §1.9 | COD listed as V1 feature | ✅ |
| `PAYMENT_TIMEOUT_FAILURE.md` §3.2 | COD failure scenarios in failure handling | ✅ |
| `PAYMENT_SYSTEM_ARCHITECTURE.md` §1.6.2 | 3 attempts max, then release stock | ✅ |

### Documented COD Workflow (from `INVENTORY_SYSTEM_ARCHITECTURE.md` §7.1)

```
1. Customer selects COD at checkout → Order created with payment_status = 'cod_pending'
2. Order created with stock reservation (RULE-AUR-003)
3. Delivery executed (Admin/Delivery person)
4. Customer pays cash on delivery
5. COD confirmation recorded by Admin → payment_status = 'cod_confirmed'
6. Stock reservation finalized → Reservation converted to sale
7. Customer notified
```

---

## Critical Fraud Prevention Gaps

### 1. No Pre-Order Customer Verification

| Gap | Risk | Impact |
|-----|------|--------|
| No phone OTP verification before COD order confirmation | HIGH | Fake orders with invalid numbers |
| No email verification | MEDIUM | Disposable emails for fraud |
| No address validation against courier serviceability | HIGH | Orders to non-serviceable areas |
| No customer COD history check | HIGH | Repeat fraudsters not blocked |

**Missing**: Pre-order OTP/IVR verification step before order confirmation

### 2. No COD Order Value Limits

| Gap | Risk | Impact |
|-----|------|--------|
| No maximum COD order value | HIGH | High-value fraud (electronics, jewelry) |
| No configurable cap per customer tier | MEDIUM | New customers same limit as trusted |
| No daily/weekly COD limit per customer | MEDIUM | Bulk fraud orders |

**Missing**: Configurable COD cap (recommend: 5,000 BDT default, adjustable per customer trust score)

### 3. No Customer Fraud Scoring

| Missing Component | Purpose |
|-------------------|---------|
| Delivery acceptance rate | Identify habitual refusers |
| COD cancellation rate | Identify serial cancellers |
| Return/refund rate | Identify wardrobing/fraud |
| Address mismatch rate | Detect fake addresses |
| Payment failure rate | Detect payment gaming |

**Missing**: Automated fraud scoring engine with configurable thresholds and auto-block rules

### 4. No Courier-Side COD Collection Confirmation

| Gap | Current State | Required |
|-----|---------------|----------|
| Courier COD collection API | Not documented | Real-time confirmation of cash collected |
| Courier cash reconciliation | Not documented | Daily courier cash vs orders report |
| Partial cash collection handling | Not documented | Partial payment workflow |
| Counterfeit detection | Not documented | Fake currency protocol |

**Documented**: `SHIPPING_SYSTEM_ARCHITECTURE.md` §7.3 mentions "Courier must confirm collection" but no API/workflow

---

## Critical RTO (Return to Origin) Gaps

### 1. RTO Cost Allocation Undefined

| Scenario | Forward Cost | Return Cost | Total | Who Pays? |
|----------|-------------|-------------|-------|-----------|
| Customer refuses COD | 1× | 1× | 2× | **UNDEFINED** |
| Address not found | 1× | 1× | 2× | **UNDEFINED** |
| Customer unavailable (3 attempts) | 1× | 1× | 2× | **UNDEFINED** |
| Fake address | 1× | 1× | 2× | **UNDEFINED** |

**Flat fee policy (DEC-OWN-003) collects 1× fee but RTO costs 2×**

### 2. RTO Process Undefined

| Missing | Description |
|---------|-------------|
| RTO detection workflow | How system knows package returned |
| RTO notification to customer | Auto-notify with reason |
| RTO stock restoration | Auto-restock on RTO receipt |
| RTO cost recovery | Invoice customer? Absorb? |
| RTO dispute resolution | Customer claims delivered, courier says returned |

### 3. Courier Cash Reconciliation Missing

| Missing | Impact |
|---------|--------|
| Daily courier cash collection report | Cash leakage undetected |
| COD amount vs order amount validation | Short collection undetected |
| Counterfeit currency protocol | Fake notes accepted |
| Partial cash collection handling | Partial payment not specified |

---

## Bangladesh-Specific Fraud Vectors (Unaddressed)

| Fraud Vector | Description | Mitigation Needed |
|--------------|-------------|-------------------|
| **Fake orders** | Competitors/order bots place fake COD orders | Pre-order OTP verification |
| **Serial refusers** | Customers habitually refuse COD | Fraud score + auto-block |
| **Address fraud** | Fake addresses in non-serviceable areas | Address validation API |
| **Courier collusion** | Courier marks "delivered" without delivery | OTP on delivery, photo proof |
| **Partial payment** | Customer pays less than order amount | Courier must collect exact amount |
| **Counterfeit cash** | Fake notes given to courier | Courier training, detection pens |
| **Wardrobing** | Buy, use, return | Return inspection, restocking fee |
| **Address hopping** | Same customer, multiple fake addresses | Address fingerprinting |

---

## Required COD Fraud Prevention Architecture

### Missing Components

| Component | Specification Needed |
|-----------|---------------------|
| **Pre-order verification service** | OTP/IVR before order confirmation |
| **Fraud scoring engine** | Real-time scoring, configurable thresholds |
| **COD order value limits** | Configurable per customer tier |
| **Customer fraud profile** | Delivery history, refusal rate, return rate |
| **Courier COD confirmation API** | Real-time cash collection confirmation |
| **COD cash reconciliation** | Daily courier cash vs orders |
| **RTO cost policy** | Who pays return shipping on refusal |
| **Fraud blacklist management** | Auto-block, manual review, appeal process |
| **Courier cash reconciliation** | Daily cash collected vs orders |

### Required Owner Decisions

| Decision | Options | Recommendation |
|----------|---------|----------------|
| COD order value cap | 3,000 / 5,000 / 10,000 / No limit BDT | 5,000 BDT default |
| Pre-order verification | OTP / IVR / None | OTP mandatory |
| RTO cost on refusal | Customer / Store / Platform | Customer (with grace) |
| Return shipping on RTO | Customer / Platform | Platform (with limit) |
| Auto-block threshold | 3/5/10 failed COD | 3 failed deliveries |
| COD verification method | OTP / IVR / Manual call | OTP + fallback IVR |

---

## COD/RTO Risk Matrix

| Risk | Likelihood | Impact | Current Mitigation | Residual Risk |
|------|------------|--------|-------------------|---------------|
| Fake COD orders | HIGH | HIGH | None | HIGH |
| COD refusal after dispatch | HIGH | HIGH | 15-min TTL stock release | HIGH |
| RTO cost absorption | HIGH | HIGH | None | HIGH |
| Courier cash theft | MEDIUM | HIGH | None | HIGH |
| Fake address orders | MEDIUM | MEDIUM | None | MEDIUM |
| Courier collusion | LOW | HIGH | None | MEDIUM |
| Counterfeit cash | LOW | MEDIUM | None | LOW |

---

## Recommendations Priority

| Priority | Action | Effort | Owner Decision |
|----------|--------|--------|----------------|
| **CRITICAL** | Add pre-COD OTP verification | Medium | Verification method |
| **CRITICAL** | Define COD order value cap | Low | Cap amount |
| **CRITICAL** | Define RTO cost allocation policy | Low | Cost bearer |
| **HIGH** | Implement fraud scoring engine | Medium | Thresholds |
| **HIGH** | Courier COD confirmation API | Medium | API spec |
| **HIGH** | Daily COD cash reconciliation | Low | Process doc |
| **MEDIUM** | Customer fraud profile & auto-block | Medium | Thresholds |
| **MEDIUM** | RTO workflow & cost recovery | Medium | Process doc |

---

## Verdict

**COD Fraud & RTO Risk: HIGH**

The current documentation covers the *happy path* COD workflow but completely lacks:
1. **Pre-order fraud prevention** (verification, limits, scoring)
2. **RTO cost allocation** (who pays 2× courier cost)
3. **Courier cash accountability** (collection confirmation, reconciliation)
4. **Fraudster management** (scoring, blocking, appeal)

**These are not edge cases — they are daily operational realities in Bangladesh e-commerce.** Without addressing these, the platform will suffer significant financial losses from fake orders, refused deliveries, and courier cash leakage.

**Recommendation**: Do not proceed to COD implementation without Owner decisions on the 6 critical policies above and implementation of the fraud prevention architecture.

---

**Document ID:** COD_RTO_RISK_ASSESSMENT  
**Version:** 1.0  
**Status:** FINAL  
**Date:** 2026-11-08