---
id: DOC-AUR-160
title: Aura Bell — Payment Webhook Lifecycle Specification
type: technical
status: confirmed
version: 2.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001
last_updated: 2026-11-08
---

# Aura Bell — Payment Webhook Lifecycle Specification (পেমেন্ট ওয়েবহুক লাইফসাইকেল)

## 1. Overview

This document specifies the webhook lifecycle for payment gateway events in the Aura Bell system. Webhook handling is critical for payment processing as it provides asynchronous notifications from payment gateways about payment state changes.

**Status**: Specified (Documented, not implemented)

**Related Documents**:
- `08_PAYMENT/PAYMENT_SYSTEM_ARCHITECTURE.md` (DOC-AUR-157)
- `08_PAYMENT/PAYMENT_PROVIDER_INTERFACE.md` (DOC-AUR-158)
- `08_PAYMENT/PAYMENT_PROVIDER_ADAPTER.md` (DOC-AUR-159)

---

## 2. Webhook Architecture

### 2.1 Webhook Lifecycle Overview

```mermaid
flowchart TD
    subgraph Provider["Payment Gateway Provider"]
        Provider["Provider sends webhook"]
    end

    subgraph Webhook["Webhook Handler Layer"]
        Receiver["Webhook Receiver Endpoint"]
        Validator["Signature Validator"]
        Processor["Webhook Processor"]
        Duplicate["Duplicate Event Checker"]
    end

    subgraph Business["Business Logic Layer"]
        Order["Order State Manager"]
        Inventory["Inventory Manager"]
        Notification["Notification Service"]
    end

    subgraph Database["Database Layer"]
        WebhookTable["payment_webhook_events table"]
        TransactionTable["payment_transactions table"]
        AttemptTable["payment_attempts table"]
    end

    Provider --> Receiver
    Receiver --> Validator
    Validator -->|Valid| Duplicate
    Validator -->|Invalid| Reject["Reject with 400"]
    Duplicate -->|New| Processor
    Duplicate -->|Duplicate| Return200["Return 200 OK"]
    Processor -->|Processed| Order
    Processor -->|Processed| Inventory
    Processor -->|Processed| Notification
    Order --> TransactionTable
    Inventory --> WebhookTable
    Notification --> Return200
```

### 2.2 Webhook Endpoint Specification

| Field | Specification |
|-------|---------------|
| **Endpoint** | POST /api/v1/payments/webhook |
| **Authentication** | API Key or Signature header verification |
| **Authorization** | Service role only (no user auth) |
| **Content-Type** | application/json |
| **Rate Limit** | 100 requests/minute (gateway-specific limits may apply) |
| **Timeout** | 10 seconds max processing time |
| **Response** | 200 OK always (never 500 to avoid retry storms) |

---

## 3. Webhook Event Types

### 3.1 Supported Event Types

| Event Type | Description | Action Required | V1 Status |
|------------|-------------|-----------------|-----------|
| `payment.initiated` | Payment session started with gateway | Log and acknowledge | Required |
| `payment.processing` | Payment currently being processed by gateway | Log and track | Required |
| `payment.completed` | Payment successfully completed | Update order, notify customer | Required |
| `payment.failed` | Payment failed after max attempts | Release stock, mark order failed | Required |
| `payment.refunded` | Refund processed for transaction | Update refund record, adjust inventory | Required |
| `payment.expired` | Payment attempt expired | Release reservation, notify customer | Required |
| `payment.refund.failed` | Refund failed via gateway | Alert admin for manual intervention | Required |

### 3.2 Event Payload Structure

```json
{
  "event_id": "string",
  "event_type": "string",
  "provider": "string",
  "provider_event_id": "string",
  "transaction_id": "string",
  "order_id": "string",
  "amount": "number",
  "currency": "string",
  "status": "string",
  "timestamp": "datetime",
  "signature": "string",
  "metadata": "object"
}
```

---

## 4. Webhook Processing Pipeline

### 4.1 Step-by-Step Processing Flow

```
Step 1: Webhook Receipt
├── Gateway sends HTTP POST to /api/v1/payments/webhook
├── System receives payload with signature header
└── Returns immediate ACK if possible

Step 2: Signature Validation
├── Extract signature from header
├── Retrieve provider secret from secure vault
├── Compute HMAC-SHA256(payload, secret)
├── Compare computed signature with provided signature
├── If mismatch → Return 400 Bad Request (do not process)
└── If match → Proceed to step 3

Step 3: Duplicate Event Check
├── Query payment_webhook_events table for provider_event_id
├── If exists → Log as duplicate, return 200 OK (no reprocessing)
├── If new → Insert new record, proceed to step 4
└── Always return 200 OK (avoid gateway retries)

Step 4: Event Processing
├── Parse webhook payload
├── Extract transaction_id, order_id, event_type, status
├── Update payment_transactions table with new status
├── Update payment_attempts table if applicable
├── Process order state change (if event type requires)
└── Commit database transaction

Step 5: Business Logic Execution
├── If payment.completed → Order confirmed → Notify customer
├── If payment.failed → Order cancelled → Release stock → Notify customer
├── If payment.refunded → Refund processed → Adjust inventory → Notify admin
└── If payment.expired → Release reservation → Notify customer

Step 6: Response Generation
├── Return 200 OK to gateway
├── Log all processing steps in audit log
└── Trigger downstream notifications if applicable
```

### 4.2 Webhook Processing States

| State | Description | Next State | Trigger |
|-------|-------------|------------|---------|
| received | Webhook received but not validated | validated | Successful signature validation |
| validated | Signature validated and event new | processing | Duplicate check passed |
| processing | Event being processed by business logic | completed | Successful processing |
| completed | Event processing complete | - | - |
| failed | Processing failed at any step | retry or alert | Depends on failure type |
| duplicate | Duplicate event detected | - | Provider_event_id already exists |
| rejected | Invalid signature or malformed payload | - | Signature validation failed |

---

## 5. Idempotency Requirements

### 5.1 Idempotency Key

Every webhook event must include a unique `provider_event_id` from the payment gateway. This ID must be:

- Generated by the payment gateway (not the system)
- Unique per event per provider
- Stored in `payment_webhook_events` table with unique constraint
- Used for duplicate detection

### 5.2 Idempotency Handling

```
Algorithm:
1. Receive webhook event with provider_event_id
2. Query database: SELECT * FROM payment_webhook_events WHERE provider_event_id = ?
3. If record exists:
   - Log as duplicate
   - Return 200 OK to gateway (do not reprocess)
   - Include original processing result if available
4. If no record exists:
   - Insert new record with provider_event_id
   - Process event normally
   - Return 200 OK to gateway
5. Handle race conditions:
   - Use database transaction with row lock (SELECT FOR UPDATE)
   - Ensure atomic check-and-insert operation
```

### 5.3 Duplicate Event Scenarios

| Scenario | Description | Handling |
|----------|-------------|----------|
| Gateway retry | Gateway retries webhook due to timeout | Return 200 OK, do not reprocess |
| Network issue | Network delay causes duplicate delivery | Return 200 OK, do not reprocess |
| System restart | System restarts during processing | Return 200 OK for already-processed events |
| Concurrent processing | Two instances process same event | Database locking ensures single processing |

---

## 6. Signature Verification

### 6.1 Signature Verification Process

```
Signature Verification Steps:
1. Extract signature from webhook header (X-SSLCommerz-Signature or equivalent)
2. Retrieve provider secret key from secure vault
3. Extract timestamp from webhook payload if available
4. Compute HMAC-SHA256(payload_string, secret_key)
5. Compare computed signature with provided signature using constant-time comparison
6. Return True if match, False if mismatch
7. Reject if timestamp is older than 24 hours
```

### 6.2 Signature Verification Requirements

| Requirement | Description | Status |
|-------------|-------------|--------|
| HMAC-SHA256 | Minimum signature algorithm | Required |
| Constant-time comparison | Prevent timing attacks | Required |
| Secret key storage | Secure vault, never in code | Required |
| Timestamp validation | Reject if > 24 hours old | Required |
| Header name per provider | X-SSLCommerz-Signature, X-bKash-Signature, etc. | Required |

### 6.3 Signature Verification Failure Handling

| Failure Type | Response Code | Action |
|--------------|---------------|--------|
| Invalid signature | 400 Bad Request | Log as security event |
| Missing signature header | 400 Bad Request | Log as security event |
| Expired timestamp | 400 Bad Request | Log as security event |
| Unknown provider | 400 Bad Request | Log as configuration error |

---

## 7. Webhook Event Processing Rules

### 7.1 Event Processing Rules Table

| Event Type | Required Action | Database Tables Affected | Related Business Rules |
|------------|-----------------|-------------------------|------------------------|
| payment.initiated | Log event, acknowledge | payment_webhook_events | RULE-AUR-005 |
| payment.processing | Log event, update attempt status | payment_attempts, payment_webhook_events | RULE-AUR-005 |
| payment.completed | Confirm order, update inventory, notify customer | orders, order_items, inventory_reservations, stock_movements | RULE-AUR-005, RULE-AUR-006 |
| payment.failed | Mark order failed, release stock reservation | orders, inventory_reservations | RULE-AUR-005, Confirmed Business Decision (3 attempts max) |
| payment.refunded | Process refund, adjust inventory | refunds, inventory_reservations, stock_movements | RULE-AUR-005, RULE-AUR-012 |
| payment.expired | Release reservation, mark attempt expired | inventory_reservations | DEC-OWN-002, RULE-AUR-003 |
| payment.refund.failed | Alert admin, log for manual intervention | refunds | RULE-AUR-012 |

### 7.2 Processing Priority

All webhook events must be processed in order of arrival within a short window (5 seconds). Events must be processed atomically with database transactions.

### 7.3 Error Handling Rules

| Error Type | Webhook Response | System Action |
|------------|-----------------|---------------|
| Invalid signature | 400 Bad Request | Log security event |
| Duplicate event | 200 OK | Do not reprocess |
| Database error | 200 OK (for gateway) | Log error, retry later |
| Processing error | 200 OK (for gateway) | Alert admin for manual intervention |
| Timeout | 200 OK (for gateway) | Gateway may retry |

---

## 8. Idempotency Keys Specification

### 8.1 Idempotency Key Format

| Format | Example | Description |
|--------|---------|-------------|
| Provider Event ID | `payment_evt_abc123` | Unique per gateway event |
| Attempt ID | `attempt_abc123_3` | Unique per attempt |
| Refund ID | `refund_abc123` | Unique per refund |

### 8.2 Idempotency Storage

| Table | Column | Constraint | Purpose |
|-------|--------|------------|---------|
| payment_webhook_events | provider_event_id | UNIQUE | Duplicate event detection |
| payment_attempts | attempt_id | PRIMARY KEY | Attempt uniqueness |
| refunds | refund_id | PRIMARY KEY | Refund uniqueness |

### 8.3 Idempotency Enforcement

```
Enforcement Logic:
1. Before processing webhook, check payment_webhook_events for provider_event_id
2. Before creating payment attempt, check if attempt_id already exists
3. Before processing refund, check if refund_id already exists
4. All checks performed within database transaction
5. If duplicate detected → Return immediately without side effects
```

---

## 9. Webhook Timeout Configuration

### 9.1 Timeout Settings

| Setting | Value | Purpose |
|---------|-------|---------|
| Webhook processing timeout | 10 seconds | Maximum time to process single event |
| Gateway retry timeout | 30 seconds | Time before gateway retries failed webhook |
| Signature timestamp tolerance | 24 hours | Reject old webhook events |
| Duplicate event TTL | 30 days | Keep webhook event records for dedup |

### 9.2 Timeout Handling

```
Timeout Handling:
1. If processing exceeds 10 seconds → Log warning, continue processing
2. If database lock timeout → Retry once, then alert admin
3. If external API call timeout → Log error, mark event as failed
4. Gateway retry → System must be idempotent (no side effects)
```

---

## 10. Late Success Handling

### 10.1 Late Success Definition

A late success occurs when a payment completes after the reservation TTL has expired (DEC-OWN-002 dependent) or after the system has already marked the payment as failed.

### 10.2 Late Success Workflow

```
Late Success Processing:
1. Receive payment.completed webhook for expired order
2. Verify transaction status with gateway
3. If gateway confirms success:
   - Restore stock reservation if still available
   - Complete order processing
   - Notify customer of successful late payment
   - Alert admin for review
4. If gateway does not confirm:
   - Process as payment failure
   - Mark order as failed
   - Notify customer
5. Always log late success event in audit log
```

### 10.3 Late Success Database Impact

| Table | Action |
|-------|--------|
| `payment_transactions` | Update status to succeeded |
| `payment_attempts` | Mark relevant attempt as succeeded |
| `inventory_reservations` | Restore if still available |
| `orders` | Update status if inventory available |
| `stock_movements` | Log stock restoration |

---

## 11. Webhook Processing Failure Recovery

### 11.1 Recovery Process

```
Recovery Process for Failed Webhook Processing:
1. Identify failed webhook events in payment_webhook_events
2. Determine failure reason (signature, database, processing)
3. For signature failures → Alert security team
4. For database failures → Retry processing
5. For processing failures → Alert admin for manual intervention
6. After recovery → Verify transaction state consistency
```

### 11.2 Manual Intervention Triggers

| Scenario | Admin Action Required |
|----------|----------------------|
| Multiple consecutive webhook failures | Yes - investigate gateway connectivity |
| Inconsistent transaction state | Yes - reconcile with gateway |
| Payment failed but inventory not released | Yes - manual stock adjustment |
| Refund failed after admin approval | Yes - process refund manually |
| Duplicate events causing inconsistency | Yes - investigate and resolve |

---

## 12. Security Considerations

### 12.1 Webhook Security Requirements

| Requirement | Description | Status |
|-------------|-------------|--------|
| Signature verification | Mandatory for all webhooks | Required |
| Source IP validation | Whitelist provider IP addresses | Specified |
| Rate limiting | 100 requests/minute per gateway | Required |
| Payload size limit | Maximum 1MB | Required |
| Header validation | Check required headers present | Required |

### 12.2 Audit Logging

All webhook processing must be logged:

| Log Field | Description |
|-----------|-------------|
| event_id | Gateway event ID |
| provider_event_id | Unique event identifier |
| event_type | Type of event |
| signature_valid | Whether signature validated |
| processing_result | Success or failure |
| processing_time_ms | Time taken to process |
| order_id | Related order (if applicable) |
| admin_action | Any manual admin intervention |

### 12.3 Data Protection

- No sensitive card data stored
- Webhook payloads masked in logs
- Provider secrets never logged
- Webhook events retained per data retention policy

---

## 13. Acceptance Criteria

### 13.1 Functional Acceptance

- [ ] Webhook endpoint accepts POST requests
- [ ] Signature verification implemented
- [ ] Duplicate event detection working
- [ ] All event types handled
- [ ] Always returns 200 OK (never 500)
- [ ] Late success handling implemented

### 13.2 Security Acceptance

- [ ] Signatures verified before processing
- [ ] Invalid signatures rejected with 400
- [ ] Rate limiting implemented
- [ ] Audit logging comprehensive
- [ ] No sensitive data in logs

### 13.3 Performance Acceptance

- [ ] Processing time < 10 seconds per event
- [ ] Duplicate detection < 1 second
- [ ] Concurrent processing supported
- [ ] Database transactions atomic

### 13.4 Business Acceptance

- [ ] Payment completed triggers order confirmation
- [ ] Payment failed triggers stock release
- [ ] Payment expired triggers reservation release
- [ ] Refund processed triggers inventory adjustment
- [ ] Late success handled appropriately

---

## 14. Implementation Dependencies

### 14.1 Blocking Dependencies

| Dependency | Status | Impact |
|------------|--------|--------|
| DEC-OWN-001 (Payment Gateway) | CONFIRMED (bKash + SSLCommerz) | Gateway-specific webhooks configured for bKash + SSLCommerz |
| DEC-OWN-002 (Stock Reservation TTL) | CONFIRMED (15 minutes) | TTL expiration handling configured (15 minutes) |
| Database migration for payment_webhook_events | Not executed | Cannot store webhook events |
| Webhook URL registration with gateway | CONFIRMED | Cannot receive webhooks |

### 14.2 Implementation Prerequisites

1. Gateway accounts configured (bKash + SSLCommerz)
2. Database schema created with payment_webhook_events table
3. Webhook endpoint implemented (FastAPI)
4. Signature verification implemented
5. Duplicate detection implemented
6. Business logic handlers implemented
7. Webhook URL registered with gateway (bKash + SSLCommerz)

---

## 15. Final Notes

### 15.1 Mission Compliance
This document satisfies the mission requirement to:
- ✅ Document Webhook Lifecycle
- ✅ Document Signature Verification
- ✅ Document Idempotency
- ✅ Document Duplicate Event Handling
- ✅ Document Timeout
- ✅ Document Late Success
- ✅ Document Payment Failure

### 15.2 Critical Blockers
- Webhook implementation blocked by DEC-OWN-001 (Payment Gateway Selection)
- Cannot register webhook URL without approved gateway

### 15.3 Next Actions
1. Gateway accounts configured
2. Webhook endpoint implemented
3. Signature verification tested
4. Duplicate detection verified
5. Business logic handlers validated

---

**Document ID**: DOC-AUR-160  
**Title**: Aura Bell — Payment Webhook Lifecycle Specification  
**Version**: 1.0  
**Status**: Specified  
**Implementation Status**: Not Implemented  
**Last Updated**: 2026-11-08  
**Governance**: Aura Bell Documentation System  
**Compliance**: Mission Requirements - Payment Webhook Lifecycle  
**V1 Classification**: Future (until DEC-OWN-001 approved)  
**Blocking**: DEC-OWN-001 (Payment Gateway Selection)

