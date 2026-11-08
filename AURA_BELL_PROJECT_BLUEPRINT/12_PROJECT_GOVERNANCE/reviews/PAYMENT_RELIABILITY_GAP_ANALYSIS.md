# Aura Bell — Payment Reliability Gap Analysis

**Review Date:** 2026-11-08  
**Reviewer:** Independent Architecture Reviewer  
**Focus:** Payment system reliability, edge cases, Bangladesh network realities

---

## Current Payment Architecture Assessment

### Well-Documented Strengths

| Area | Coverage | Document |
|------|----------|----------|
| **Provider Adapter Pattern** | Complete interface, registry, factory | `PAYMENT_SYSTEM_ARCHITECTURE.md` §1.2 |
| **Webhook Security** | HMAC-SHA256, constant-time compare, 24hr timestamp | `PAYMENT_WEBHOOK_LIFECYCLE.md` §6 |
| **Idempotency** | `provider_event_id` unique constraint, duplicate handling | `PAYMENT_WEBHOOK_LIFECYCLE.md` §5 |
| **Signature Verification** | HMAC-SHA256, constant-time, 24hr tolerance | `PAYMENT_WEBHOOK_LIFECYCLE.md` §6 |
| **Payment Failure** | 3 attempts max, 15-min TTL, backoff, late success | `PAYMENT_TIMEOUT_FAILURE.md` §2-4 |
| **Reconciliation** | Daily 02:00 AM, discrepancy types, resolution | `PAYMENT_RECONCILIATION.md` §3-7 |
| **Refund Workflow** | Admin-only, 7-day window, inspection, gateway refund | `PAYMENT_REFUND_MANUAL.md` |

---

## Critical Edge-Case Gaps

### 1. Browser Closure During Payment Redirect (HIGH)

**Scenario**: Customer clicks "Pay", gateway redirect initiates, customer closes browser/tab before gateway loads.

**Current Gap**: No specification for:
- Payment attempt state when redirect initiated but not completed
- Customer return flow (how do they resume?)
- Abandoned payment detection and recovery
- Stock reservation status during abandonment

**Required but Missing**:
| Component | Specification Needed |
|-----------|---------------------|
| **Abandoned payment detection** | Background job scanning `payment_attempts` with `created_at > 30 min` and no webhook |
| **Client-side payment state** | LocalStorage/sessionStorage: `payment_attempt_id`, `order_id`, `provider` |
| **Return URL handling** | Deep link / universal link for app, query params for web |
| **Recovery UX** | "Payment in progress" page with "Resume" / "Cancel" buttons |
| **Reservation during abandonment** | Keep reservation until TTL expiry (15 min) or explicit cancel |

### 2. Network Disconnection During Payment (HIGH)

**Scenario**: Customer on gateway payment page, network drops (common in Bangladesh mobile networks).

**Current Gap**: No specification for:
- Client-side offline detection and queue
- Gateway callback handling when client offline
- Payment status polling fallback
- User notification of pending payment

**Required but Missing**:
| Component | Specification Needed |
|-----------|---------------------|
| **Offline payment queue** | Service Worker + IndexedDB for payment callbacks |
| **Payment status polling** | Client polls `/api/v1/payments/{id}/status` every 10s |
| **Network recovery UX** | "Reconnecting..." overlay, auto-retry webhook processing |
| **Gateway timeout handling** | Gateway-specific timeout configs (bKash: 120s, SSLCommerz: 180s) |

### 3. Payment Success After Order Timeout (Late Success) - MEDIUM

**Documented**: `PAYMENT_TIMEOUT_FAILURE.md` §10 and `PAYMENT_WEBHOOK_LIFECYCLE.md` §10

**Gap**: Late success handling documented server-side but **no frontend UX specification**:
- Customer sees "Payment failed" but later payment succeeds
- No "Payment completed after timeout" notification flow
- No automatic order recovery UX
- Stock restoration race condition if customer re-orders

### 4. Duplicate Callback Handling - MEDIUM

**Documented**: Idempotency via `provider_event_id` unique constraint

**Gap**: No guidance for:
- Gateway retry-after headers (how long to wait before retry)
- Exponential backoff for gateway retries
- Maximum retry attempts from gateway side
- Circuit breaker for repeated failures

### 5. Gateway Maintenance Windows - MEDIUM

**Missing**: No specification for:
- Scheduled gateway downtime handling
- Graceful degradation (COD-only mode during gateway outage)
- Customer notification during maintenance
- Webhook queue during downtime

### 6. Gateway API Version Changes - MEDIUM

**Missing**: No adapter versioning strategy:
- Adapter interface versioning
- Backward compatibility requirements
- Migration path for gateway API v1 → v2
- Deprecation timeline

---

## Bangladesh Network Reality Impact

| Factor | Bangladesh Reality | Architecture Impact |
|--------|-------------------|---------------------|
| **Mobile network reliability** | Frequent drops, high latency | Client-side resilience critical |
| **2G/3G fallback** | Common in rural areas | Long timeouts, large payloads fail |
| **Gateway uptime** | bKash/SSLCommerz ~99.5% | 43 hours downtime/year expected |
| **Peak load (Eid, sales)** | 10-50x normal traffic | Auto-scaling, queue management |
| **Customer device diversity** | Low-end Android dominant | Lightweight JS, minimal payloads |

---

## Missing Technical Specifications

### 1. Client-Side Payment State Machine

```typescript
// Required but not specified
interface PaymentSessionState {
  paymentAttemptId: string;
  orderId: string;
  provider: 'bKash' | 'SSLCommerz';
  status: 'initiated' | 'redirecting' | 'awaiting_webhook' | 'completed' | 'failed' | 'expired';
  redirectUrl: string;
  expiresAt: number; // timestamp
  attemptNumber: number;
  createdAt: number;
}
```

### 2. Abandoned Payment Recovery Job

```sql
-- Required but not specified
SELECT * FROM payment_attempts 
WHERE status IN ('initiated', 'redirecting', 'awaiting_webhook')
  AND created_at < NOW() - INTERVAL '30 minutes'
  AND attempt_number < 3;
```

### 3. Gateway-Specific Timeout Configuration

| Gateway | Redirect Timeout | Webhook Timeout | Polling Interval |
|---------|------------------|-----------------|------------------|
| bKash | 120s | 30s | 10s |
| SSLCommerz | 180s | 30s | 10s |

### 4. Client-Side Payment Recovery UX

| State | UI Component | Actions |
|-------|-------------|---------|
| `redirecting` | Full-screen loader with "Please wait..." | Cancel button (cancels reservation) |
| `awaiting_webhook` | "Payment processing..." with spinner | "Check status" button (polls API) |
| `failed` | Error message + retry button | Retry (new attempt) / Cancel |
| `expired` | "Payment timed out" + "Try again" | New payment attempt |
| `late_success` | "Payment completed!" + order details | Auto-navigate to order |

---

## Payment Failure Edge Cases (Documented but Incomplete)

| Scenario | Documented | Missing |
|----------|------------|---------|
| 3 attempts exhausted | `PAYMENT_TIMEOUT_FAILURE.md` §3.3 | Stock release confirmation UX |
| Gateway timeout | `PAYMENT_TIMEOUT_FAILURE.md` §2.3 | Retry with different gateway? |
| Insufficient funds | `PAYMENT_TIMEOUT_FAILURE.md` §3.2 | No retry, clear user message |
| Validation failure | `PAYMENT_TIMEOUT_FAILURE.md` §3.2 | Field-level error mapping |
| Late success | `PAYMENT_TIMEOUT_FAILURE.md` §10 | Frontend UX, stock race condition |

---

## Reconciliation Gaps

| Gap | Impact |
|-----|--------|
| **Gateway API rate limits during reconciliation** | Daily job may hit rate limits |
| **Partial settlement handling** | Gateway settles batch, not per-transaction |
| **Currency conversion** | BDT only in V1, but gateway may settle in USD |
| **Chargeback handling** | Not documented (future) |
| **Settlement timing mismatch** | Gateway settles T+1 or T+2 |

---

## Required Technical Specifications (Before Implementation)

| Specification | Priority | Effort |
|---------------|----------|--------|
| Client-side payment state machine | CRITICAL | Medium |
| Abandoned payment recovery job | CRITICAL | Low |
| Gateway-specific timeout config | HIGH | Low |
| Client-side offline queue (Service Worker) | HIGH | Medium |
| Payment status polling fallback | HIGH | Low |
| Late success frontend UX | HIGH | Medium |
| Gateway maintenance window handling | MEDIUM | Low |
| Adapter versioning strategy | MEDIUM | Low |
| Reconciliation rate limit handling | MEDIUM | Low |

---

## Verdict

**Payment Reliability: WELL-ARCHITECTED CORE — CRITICAL GAPS IN CLIENT-SIDE RESILIENCE**

**What's Production-Ready**:
- Server-side webhook processing, idempotency, signature verification
- Payment failure workflow (3 attempts, 15-min TTL, late success)
- Reconciliation, refund workflow
- Security (signatures, idempotency, audit logging)

**What's NOT Production-Ready**:
1. **Client-side payment flow resilience** (browser closure, network drops) — **CRITICAL**
2. **Abandoned payment recovery** — **CRITICAL**
3. **Gateway maintenance/degradation handling** — HIGH
4. **Late success frontend UX** — HIGH
4. **Gateway API versioning strategy** — MEDIUM

**Recommendation**: Do not deploy payment system without implementing client-side resilience specifications (abandoned payment recovery, network disconnect handling, payment status polling). These are not edge cases — they are daily occurrences in Bangladesh mobile networks.

---

**Document ID:** PAYMENT_RELIABILITY_GAP_ANALYSIS  
**Version:** 1.0  
**Status:** FINAL  
**Date:** 2026-11-08