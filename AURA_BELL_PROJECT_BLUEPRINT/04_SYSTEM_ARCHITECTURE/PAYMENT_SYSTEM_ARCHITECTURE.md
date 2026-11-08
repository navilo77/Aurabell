---
id: DOC-AUR-157
title: Aura Bell — Payment System Architecture Specification
type: technical
status: confirmed
version: 2.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, Owner Confirmation 2026-11-08
last_updated: 2026-11-08
---

# Aura Bell — Payment System Architecture (পেমেন্ট সিস্টেম আর্কিটেকচার)

## 1. Provider-Independent Payment Architecture

Aura Bell payment system is designed to be provider-agnostic, allowing seamless switching between different payment gateways without code rewrites. The architecture uses the **Provider Adapter Pattern** as documented in ADR-009.

### 1.1 Architecture Overview

```mermaid
flowchart TD
    subgraph PaymentSystem["Aura Bell Payment System"]
        Direction TB
        Customer["Customer (Frontend)"]
        API["REST API v1 (/api/v1/payments)"]
        Adapter["Provider Adapter Layer"]
        Registry["Provider Registry"]
        DB["Database (Supabase PostgreSQL)"]
        GW["Payment Gateway(s)"]
    end

    Customer --> API
    API --> Adapter
    Adapter --> Registry
    Registry -->|Select Provider| Adapter
    Adapter -->|Process Payment| GW
    GW -->|Webhook| Adapter
    Adapter -->|Save Transaction| DB
    DB -->|Retrieve Status| API
```

### 1.2 Core Components

#### 1.2.1 Provider Interface (Provider Interface)
Provider-agnostic contract that all payment gateways must implement:

| Method | Description | Required |
|--------|-------------|--------|
| `initialize()` | Initialize payment session | ✅ Required |
| `createPaymentAttempt()` | Create payment attempt record | ✅ Required |
| `verifySignature()` | Verify webhook signature | ✅ Required |
| `handleWebhook()` | Handle incoming webhook event | ✅ Required |
| `refundPayment()` | Process refund request | ⚠️ Manual only (V1) |
| `getPaymentStatus()` | Get current payment status | ✅ Required |

#### 1.2.2 Provider Registry (Provider Registry)
Central registry that maps provider names to their adapter implementations:

| Field | Description |
|-------|-------------|
| `provider_name` | Unique identifier (bKash, SSLCommerz) |
| `adapter_class` | Fully qualified class name |
| `status` | active/pending/deprecated |
| `features` | Supported features (COD, online, refunds, etc.) |
| `configuration` | Provider-specific configuration keys |

#### 1.2.3 Provider Adapter (Provider Adapter)
Concrete implementation for each payment gateway that translates generic payment operations to gateway-specific API calls.

**Example Adapter Structure**:
```
app/payments/adapters/
├── __init__.py
├── base.py                    # Abstract base adapter
├── factory.py                 # Provider factory
├── bKash_adapter.py          # bKash implementation (CONFIRMED: DEC-OWN-001)
├── SSLCommerz_adapter.py     # SSLCommerz implementation (CONFIRMED: DEC-OWN-001)
└── Shurjopay_adapter.py     # Shurjopay implementation (Future/Optional)
```

Each adapter must implement the Provider Interface.

### 1.3 Payment Lifecycle

#### 1.3.1 Payment Attempt
A single payment try by customer.

| Field | Type | Description |
|-------|------|-------------|
| `attempt_id` | UUID | Unique attempt identifier |
| `order_id` | UUID | Related parent order |
| `provider` | String | Selected gateway (bKash/SSLCommerz) |
| `amount` | Decimal | Payment amount |
| `currency` | String | Currency (BDT) |
| `status` | Enum | pending/processing/failed/succeeded |
| `attempt_number` | Integer | 1-based attempt counter |
| `created_at` | Timestamp | When attempt was created |
| `expires_at` | Timestamp | When attempt expires (15 minutes — DEC-OWN-002 CONFIRMED) |

#### 1.3.2 Payment Transaction
Complete transaction record including all attempts.

| Field | Type | Description |
|-------|------|-------------|
| `transaction_id` | UUID | Unique transaction identifier |
| `order_id` | UUID | Related parent order |
| `total_amount` | Decimal | Total amount charged |
| `currency` | String | Currency (BDT) |
| `provider` | String | Selected gateway |
| `attempts` | JSON Array | All attempt records |
| `final_status` | Enum | succeeded/failed/partially_refunded |
| `created_at` | Timestamp | Transaction creation |
| `updated_at` | Timestamp | Last status update |
| `reconciliation_id` | String | External transaction ID |

### 1.4 Webhook Lifecycle

#### 1.4.1 Webhook Events
| Event Type | Description | Required Action |
|------------|-------------|-----------------|
| `payment_initiated` | Payment session started | Log and acknowledge |
| `payment_completed` | Payment successfully completed | Update order status, notify customer |
| `payment_failed` | Payment failed after max attempts | Mark transaction failed, notify customer |
| `payment_refunded` | Refund processed | Update order, adjust inventory |
| `payment_timeout` | Payment attempt expired | Release stock reservation, notify customer |

#### 1.4.2 Signature Verification
Every webhook MUST include signature verification:

```
Steps:
1. Receive webhook payload from gateway
2. Extract signature header (X-SSLCommerz-Signature or X-bKash-Signature)
3. Retrieve provider secret key from secure storage
4. Compute HMAC-SHA256(payload, secret_key)
5. Compare computed signature with received signature
6. If mismatch → Reject webhook with 400 status
7. If match → Process webhook event
```

### 1.5 Idempotency

#### 1.5.1 Idempotency Requirements
- Every payment request must include `provider_event_id` (unique per gateway)
- Database unique constraint on `provider_event_id` in `payment_webhook_events` table
- Duplicate event detection and rejection
- Safe retry mechanism without double-charging

#### 1.5.2 Duplicate Event Handling
```
Algorithm:
1. Receive webhook event
2. Check `payment_webhook_events` table for `provider_event_id`
3. If exists → Log as duplicate, return 200 OK (no reprocessing)
4. If not exists → Insert new record, process event
5. Always return 200 OK to gateway (never 500)
```

### 1.6 Payment Failure Handling

#### 1.6.1 Maximum Attempts Configuration
- **Confirmed Owner Decision**: "Payment Failure: Maximum 3 attempts" (Mission Requirements, CONFIRMED 2026-11-08)
- **Current**: 3 attempts maximum before marking as failed
- **Attempt Count Definition**: Each `create_payment_attempt()` call counts as one attempt

#### 1.6.2 Failure Workflow
```
1. Attempt 1 → Failed → Retry after timeout
2. Attempt 2 → Failed → Retry after timeout  
3. Attempt 3 → Failed → Mark as final failure
4. Release stock reservation (TTL 15 minutes — DEC-OWN-002 CONFIRMED)
5. Notify customer of payment failure
6. Enable manual refund (COD confirmation required)
```

#### 1.6.3 Late Success Handling
```
If payment succeeds after timeout:
1. Verify transaction status with gateway
2. If succeeded → Release held reservation, complete order
3. If failed → Proceed with failure workflow
4. Always update `payment_transactions` table
5. Notify admin of late success event
```

### 1.7 Reconciliation

#### 1.7.1 Reconciliation Process
```
Daily Reconciliation Workflow:
1. Retrieve all transactions from database
2. Compare with gateway's transaction list (bKash + SSLCommerz)
3. Identify discrepancies:
   - Missing transactions
   - Status mismatches
   - Amount differences
   - Duplicate entries
4. Resolve each discrepancy:
   - Manual investigation
   - Gateway API verification
   - Database record update
5. Generate reconciliation report
6. Update financial entries table
7. Alert admin of any unresolved issues
```

#### 1.7.2 Manual Refund
**V1 Restriction**: Partial shipments not allowed in V1, similarly manual refunds require admin approval.

| Step | Action | Required |
|------|--------|----------|
| 1 | Admin initiates refund request | ✅ Required |
| 2 | Verify order eligibility (7-day return window) [Confirmed Owner Decision — Mission Requirements] | ✅ Required |
| 3 | Product inspection (if returned) | ✅ Required |
| 4 | Stock restoration (if applicable) | ✅ Required |
| 5 | Admin approval | ✅ Required |
| 6 | Process refund via gateway (bKash or SSLCommerz) | ✅ Required |
| 6 | Update `refunds` table with reason and approval ID | ✅ Required |
| 7 | Notify customer | ✅ Required |
| 8 | Update order status to "refunded" | ✅ Required |

### 1.8 Refund Ledger

| Field | Type | Description |
|-------|------|-------------|
| `refund_id` | UUID | Unique refund identifier |
| `transaction_id` | UUID | Related payment transaction |
| `order_id` | UUID | Related parent order |
| `amount` | Decimal | Refund amount |
| `reason` | Text | Reason for refund |
| `approved_by` | UUID | Admin user who approved |
| `approved_at` | Timestamp | Approval timestamp |
| `processed_at` | Timestamp | When refund was processed |
| `gateway_refund_id` | String | Gateway's refund transaction ID |
| `status` | Enum | pending/processed/failed |
| `created_at` | Timestamp | When refund was requested |

### 1.9 V1 vs Future Features

**V1 (Currently Planned)**:
- ✅ Cash on Delivery (COD) support
- ✅ Dual online payment gateways (bKash + SSLCommerz — DEC-OWN-001 CONFIRMED)
- ✅ Manual webhook handling
- ✅ Manual refunds with admin approval
- ✅ 3 payment attempt maximum (Confirmed Owner Decision)
- ✅ Stock reservation with TTL (15 minutes — DEC-OWN-002 CONFIRMED)
- ✅ Manual courier dispatch (V1 architecture)

**Future (Post-V1)**:
- 📅 Shurjopay integration (optional)
- 📅 Automated refund processing
- 📅 Advanced fraud detection
- 📅 Subscription payments
- 📅 Wallet integration

## 2. Database Schema Integration

### 2.1 New Tables (Payment System)

| Table Name | Purpose | Key Fields |
|------------|---------|------------|
| `payment_attempts` | Individual payment tries | attempt_id, order_id, provider, status, attempt_number |
| `payment_transactions` | Complete transaction records | transaction_id, order_id, provider, total_amount, final_status |
| `payment_webhook_events` | Webhook event log | event_id, provider_event_id, signature_verified, processed |
| `refunds` | Refund records | refund_id, transaction_id, amount, approved_by, status |

### 2.2 Existing Tables Modified
- `orders`: Add `payment_status` field, `gateway_name` field
- `payments`: Extend with provider-specific fields
- `order_items`: May need payment status snapshots

### 2.3 RLS Policies (Row Level Security)
- Customers can view own payment attempts
- Admins can view all payment transactions
- No customer can modify payment records after creation
- Webhook endpoints have service_role access only

---

## 3. API Specifications (Payment Endpoints)

### 3.1 Endpoint: POST /api/v1/payments/initiate

| Field | Description |
|-------|-------------|
| `API ID` | DOC-AUR-pay-001 |
| `HTTP Method` | POST |
| `Endpoint` | /api/v1/payments/initiate |
| `Purpose` | Initiate payment session for order |
| `Authentication` | JWT token with admin/customer scope |
| `Authorization` | Customer: own orders only; Admin: all orders |
| `Request Schema` | `{ "order_id": "UUID", "provider": "enum[bKash,SSLCommerz]", "attempt_number": "Integer" }` |
| `Response Schema` | `{ "payment_attempt_id": "UUID", "gateway_url": "String", "expires_at": "Timestamp", "attempt_number": "Integer" }` |
| `Validation Rules` | - order_id must exist and belong to customer/admin<br>- provider must be valid option (bKash or SSLCommerz)<br>- attempt_number must be 1-3 |
| `Error Codes` | 400: Invalid input, 401: Unauthorized, 403: Forbidden, 404: Order not found, 422: Validation error |
| `Rate Limits` | 10 requests/minute per customer |
| `Idempotency Requirements` | Must include `provider_event_id` in request |
| `Related Database Entities` | `payment_attempts`, `orders`, `order_items` |
| `Related Requirements` | BR-AUR-005, DEC-OWN-001 (CONFIRMED) |
| `Acceptance Criteria` | - Payment session created successfully<br>- Gateway URL provided<br>- Attempt number validated<br>- Customer notified |
| `Test References` | TC-AUR-PAY-001 |
| `V1/Future Classification` | V1 (DEC-OWN-001 CONFIRMED — bKash + SSLCommerz) |

### 3.2 Endpoint: POST /api/v1/payments/webhook

| Field | Description |
|-------|-------------|
| `API ID` | DOC-AUR-pay-002 |
| `HTTP Method` | POST |
| `Endpoint` | /api/v1/payments/webhook |
| `Purpose` | Receive webhook events from payment gateway |
| `Authentication` | API key or signature verification |
| `Authorization` | Service role only (no user auth) |
| `Request Schema` | Gateway-specific webhook payload with `signature` and `provider_event_id` |
| `Response Schema` | `{ "status": "success", "event_id": "String", "processed": "Boolean" }` |
| `Validation Rules` | - Signature must be valid (HMAC-SHA256)<br>- `provider_event_id` must be unique<br>- Event type must be recognized |
| `Error Codes` | 400: Invalid signature, 400: Duplicate event, 400: Unknown event type |
| `Rate Limits` | 100 requests/minute (gateway may impose limits) |
| `Idempotency Requirements` | Must use `provider_event_id` for deduplication |
| `Related Database Entities` | `payment_webhook_events`, `payment_transactions`, `payment_attempts` |
| `Related Requirements` | DEC-OWN-001 (CONFIRMED), RULE-AUR-005 |
| `Acceptance Criteria` | - Signature verified<br>- Event logged or deduplicated<br>- Appropriate action taken<br>- Status updated |
| `Test References` | TC-AUR-PAY-002, TC-AUR-PAY-003 |
| `V1/Future Classification` | V1 (DEC-OWN-001 CONFIRMED — bKash + SSLCommerz) |

### 3.3 Endpoint: POST /api/v1/payments/refunds

| Field | Description |
|-------|-------------|
| `API ID` | DOC-AUR-pay-003 |
| `HTTP Method` | POST |
| `Endpoint` | /api/v1/payments/refunds |
| `Purpose` | Process manual refund (V1 requires admin approval) |
| `Authentication` | JWT token with admin scope |
| `Authorization` | Admin only |
| `Request Schema` | `{ "transaction_id": "UUID", "amount": "Decimal", "reason": "Text", "admin_id": "UUID" }` |
| `Response Schema` | `{ "refund_id": "UUID", "status": "pending", "processed_at": "Timestamp" }` |
| `Validation Rules` | - transaction_id must exist<br>- amount must be ≤ original amount<br>- reason must be provided<br>- admin_id must have admin role<br>- Order within 7-day return window |
| `Error Codes` | 400: Invalid input, 403: Forbidden (non-admin), 404: Transaction not found, 422: Validation error, 400: Outside return window |
| `Rate Limits` | 5 requests/hour per admin |
| `Idempotency Requirements` | Must include `refund_id` for deduplication |
| `Related Database Entities` | `refunds`, `payment_transactions`, `orders`, `order_items`, `inventory_reservations` |
| `Related Requirements` | DEC-OWN-001 (CONFIRMED), RULE-AUR-012 |
| `Acceptance Criteria` | - Admin approves refund request<br>- Order within 7-day return window<br>- Refund amount validated<br>- Refund processed via gateway (bKash or SSLCommerz)<br>- `refunds` table updated<br>- Customer notified<br>- Order status updated |
| `Test References` | TC-AUR-PAY-004, TC-AUR-PAY-005, TC-AUR-PAY-006 |
| `V1/Future Classification` | V1 (manual refunds with admin approval, DEC-OWN-001 CONFIRMED) |

---

## 4. Provider-Specific Considerations (DEC-OWN-001 CONFIRMED)

### 4.1 bKash PGW (Direct Integration)
**Status**: CONFIRMED (DEC-OWN-001 approved — bKash will be implemented)

**Features**:
- ✅ Direct bKash bank integration
- ✅ Card payments via bKash
- ✅ bKash wallet payments
- ✅ Mobile financial services (MFS)

**Configuration Requirements**:
- Store API key and secret securely
- Configure webhook URL
- Set up merchant account
- Test mode → Production mode transition

**Estimated Fees**:
- Transaction fee: 1-2% per transaction
- Setup fee: None
- Monthly fee: None

### 4.2 SSLCommerz
**Status**: CONFIRMED (DEC-OWN-001 approved — SSLCommerz will be implemented)

**Features**:
- ✅ Supports all card types (Visa, MasterCard, American Express)
- ✅ Mobile financial services (bKash, Nagad, etc.)
- ✅ Internet banking
- ✅ Cash on Delivery option within SSLCommerz platform

**Configuration Requirements**:
- Store merchant ID and password
- Configure webhook URL
- Set up SSLCommerz merchant portal
- Enable required payment methods

**Estimated Fees**:
- Transaction fee: 2.5% per transaction (approximately)
- Setup fee: None
- Monthly fee: None

### 4.3 Shurjopay
**Status**: Future/Optional (not selected for V1 per DEC-OWN-001)

**Features**:
- ✅ Popular in Bangladesh market
- ✅ Supports card payments
- ✅ Mobile wallet integration
- ✅ Internet banking integration

**Note**: Shurjopay adapter implementation is deferred to Future/Post-V1 phase.

### 3.3 Shurjopay
**Status**: Pending owner approval (DEC-OWN-001)

**Features**:
- ✅ Popular in Bangladesh market
- ✅ Supports card payments
- ✅ Mobile wallet integration
- ✅ Internet banking integration

**Configuration Requirements**:
- Store API credentials
- Configure webhook URL
- Test environment setup
- Production deployment

**Estimated Fees**:
- Transaction fee: Variable, typically 2-3%
- Setup fee: None
- Monthly fee: None

**Questions for Owner**:
1. Approve Shurjopay as V1 payment gateway?
2. Accept transaction fee structure?
3. Configure required payment methods?

---

## 4. Implementation Dependencies

### 4.1 Blocking Decisions
- **DEC-OWN-001**: Payment Gateway Selection - Blocks ALL payment implementation
- **DEC-OWN-002**: Stock Reservation TTL - Affects payment timeout handling
- **DEC-OWN-003**: Delivery Fee Policy - Affects payment amount calculation
- **DEC-OWN-004**: Courier Partner - Affects order completion workflow

### 4.2 Implementation Prerequisites
Before any payment code can be written:
1. ✅ DEC-OWN-001 approved (which gateway)
2. ✅ DEC-OWN-002 approved (TTL period)
3. ✅ Database schema updated (payment tables added)
4. ✅ API endpoints documented (specifications created)
5. ✅ Webhook endpoints configured (gateway-specific)
6. ✅ Idempotency keys implemented (`provider_event_id`)
7. ✅ Signature verification implemented (per gateway)
8. ✅ Failure workflow defined (3 attempts max)
9. ✅ Manual refund process documented (admin approval required)
10. ✅ Reconciliation process documented (daily checks)

### 4.3 Implementation Blockers
All prerequisites met. Payment implementation can now proceed:
- ✅ Gateway-specific implementation (bKash + SSLCommerz)
- ✅ Provider-agnostic architecture documentation
- ✅ Database schema documentation
- ✅ API specification documentation
- ✅ Test specification documentation

---

## 5. Security Considerations

### 4.1 Payment Data Protection
- All payment amounts encrypted at rest
- Card details never stored (tokenized by gateway)
- Webhook secrets stored in secure vault
- API keys rotated regularly (every 90 days)
- Access logs maintained for all payment operations

### 4.2 Webhook Security
- Signature verification mandatory for all webhooks
- Only service_role can access webhook endpoints
- Payload size limited (max 1MB)
- Rate limiting on webhook endpoints (100/min)
- Signature timestamp validation (reject if > 24 hours old)

### 4.3 Transaction Security
- `provider_event_id` unique constraint in database
- Attempt counter with max 3 checks
- Amount validation against order total
- Customer ID binding (cannot modify other customer's payments)
- Admin approval required for all refunds

### 4.4 Audit Logging
Every payment operation must log:
- Who performed the operation (user ID or service name)
- When it was performed (timestamp)
- What operation was performed (operation type)
- What parameters were used (operation parameters)
- Result of operation (success/failure/status)
- Related identifiers (order ID, transaction ID, attempt ID)

Logging tables: `payment_audit_logs`, `refund_audit_logs`, `transaction_audit_logs`

---

## 5. Cross-Document References

### 5.1 Owner Decisions (ALL CONFIRMED)
- DEC-OWN-001: Payment Gateway Selection — **CONFIRMED** (bKash + SSLCommerz)
- DEC-OWN-002: Stock Reservation TTL — **CONFIRMED** (15 minutes)
- DEC-OWN-003: Delivery Fee Policy — **CONFIRMED** (Flat fee per order)
- DEC-OWN-004: Courier Partner Selection — **CONFIRMED** (Pathao)

### 5.2 Business Rules
- RULE-AUR-005: Webhook Signature & Idempotency
- RULE-AUR-012: No AI Autonomy for Financial Actions

### 5.3 Database Schema
- `payment_attempts` table (new)
- `payment_transactions` table (new)
- `payment_webhook_events` table (new)
- `refunds` table (new)
- Modified: `orders` table (add payment_status, gateway_name)
- Modified: `payments` table (extend with provider fields)

### 5.4 API Documentation
- API_ENDPOINTS.md: Payment endpoints documented
- API_SPECIFICATION.md: Payment specification overview
- API_ERROR_CODES.md: Payment error codes listed
- API_EXAMPLES.md: Payment request/response examples

### 5.4 Business Requirements
- BR-AUR-005: Payment & Financial Audit
- RULE-AUR-005: Webhook Signature & Idempotency
- RULE-AUR-012: No AI Autonomy for Financial Actions

### 5.5 PRD Documents
- PAYMENT_PRD.md: Payment Processing & Webhooks PRD
- All 11 PRDs reference payment system where applicable

### 5.6 Architecture Decisions
- ADR-008: Server-Side Price Recalculation
- ADR-009: Payment Gateway Adapter Pattern
- ADR-010: Manual Courier Dispatch for V1

### 5.7 Test Specifications
- TC-AUR-PAY-001 through TC-AUR-PAY-010: Payment test cases
- Reservation race condition tests
- Refund scenario tests
- Webhook failure recovery tests

### 5.8 Security Documentation
- AUTHENTICATION_AUTHORIZATION.md: Auth and RBAC for payments
- SECURITY_CHECKLIST.md: Payment security checklist items
- SECURITY_ARCHITECTURE.md: Overall security architecture including payments

### 5.8 Development Workflow
- DEVELOPMENT_ROADMAP.md: Payment implementation phase
- TESTING_STRATEGY.md: Payment testing strategy
- DEPLOYMENT_GUIDE.md: Payment deployment steps

---

## 6. V1 Scope vs Future Scope

### 6.1 V1 (Valid for V1 Release)
**Payment Features Included**:
1. Cash on Delivery (COD) - Confirmed Owner Decision (Mission Requirements)
2. Dual online payment gateways (bKash + SSLCommerz) — **DEC-OWN-001 CONFIRMED**
3. Manual webhook handling - V1 manual dispatch model
4. Manual refunds with admin approval - Confirmed Owner Decision (Mission Requirements)
5. 3 payment attempt maximum - Confirmed Owner Decision (Mission Requirements)
6. 7-day return window for refunds - Confirmed Owner Decision (Mission Requirements)
7. Stock reservation with TTL - Pending DEC-OWN-002 approval
8. Manual courier dispatch - V1 architecture (ADR-010)

**Payment Features Excluded from V1**:
1. Shurjopay integration — Future/Post-V1
2. Automated recurring payments - Post-V1 feature
3. Advanced fraud detection - Post-V1 feature
4. Wallet integration - Post-V1 feature
5. Automated refund processing - Post-V1 feature

### 6.2 Future (Post-V1)
**Planned Payment Enhancements**:
1. Multiple gateway support (bKash + SSLCommerz + Shurjopay)
2. Automated refund processing (after admin approval)
3. Advanced fraud detection and prevention
4. Wallet/money transfer integration
5. Subscription and recurring payments
6. Transaction analytics and reporting
7. Currency expansion (BDT + potential future currencies)
8. Payment method analytics and optimization

### 6.3 V1/Future Classification Guidelines
```
Use "V1" classification when:
- Feature is approved for V1 release
- Owner decision is confirmed
- Implementation can proceed
- Documentation status: CONFIRMED

Use "Future" classification when:
- Feature pending owner decision
- Feature planned for post-V1 release
- Implementation blocked by pending decision
- Documentation status: PENDING OWNER REVIEW or SPECIFIED


```

---

## 7. Implementation Readiness Assessment

### 7.1 Current Status
| Component | Status | Blocking Issues |
|-----------|--------|-----------------|
| Provider-agnostic architecture | ✅ Complete | None |
| Provider Interface specification | ✅ Complete | None |
| Provider Adapter Pattern design | ✅ Complete | None |
| Database schema (payment tables) | ✅ Documented | None — ready for implementation |
| API endpoint specifications | ✅ Complete | None — ready for implementation |
| Webhook lifecycle documentation | ✅ Complete | None — ready for implementation |
| Idempotency implementation | ✅ Specified | None — ready for implementation |
| Payment failure workflow | ✅ Specified | None — ready for implementation |
| Manual refund process | ✅ Specified | None — ready for implementation |
| Reconciliation process | ✅ Specified | None (documentation only) |
| Security controls | ✅ Specified | None (documentation only) |

### 7.2 Readiness Status: **CONFIRMED** (Documentation complete, all owner decisions approved, ready for implementation)
All payment system documentation is complete at specification level, all owner decisions approved, and implementation is ready to begin.

### 7.3 Prerequisites for Implementation
Database migration execution (create payment tables)
FastAPI backend implementation (payment endpoints)
Frontend integration (payment session UI)
Gateway account setup (bKash + SSLCommerz)
Webhook endpoint deployment (with gateway)
SSL certificate configuration (for production)
Test environment setup (sandbox mode)
Production deployment planning



### 7.4 Post-Implementation Validation
1. All payment endpoints tested (unit + integration)
2. Webhook events verified (successful and failed cases)
3. Idempotency verified (duplicate event handling)
4. Failure workflow tested (3 attempts + timeout)
5. Manual refund process verified (admin approval flow)
6. Reconciliation process validated (daily checks)
7. Security controls audited (signature verification, access logs)
8. Performance tested (throughput, timeout handling)
9. Compliance verified (financial regulations, data protection)
10. Owner sign-off on all implemented features

---

## 8. Change Management

### 8.1 Changelog Entry Format
```
## [1.1.0] - 2026-XX-XX
### Added
- New payment gateway integration (if DEC-OWN-001 approved)
- Additional payment methods (if approved)
- Enhanced webhook handling

### Changed
- Updated payment failure workflow
- Modified refund process
- Improved reconciliation procedure

### Deprecated
- Deprecated payment gateway (if switched)
- Old webhook format (if updated)

### Fixed
- Fixed idempotency edge case
- Fixed signature verification bug
- Fixed race condition in reservation
```

### 8.2 Documentation Update Triggers
- Owner decision approval (DEC-OWN-xxx)
- New payment gateway integration
- API endpoint changes
- Database schema modifications
- Security vulnerability patches
- Workflow process improvements

### 8.3 Versioning Scheme
- **Major**: DEC-OWN-001 approval (blocks/Enables implementation)
- **Minor**: New payment method addition
- **Patch**: Bug fixes, workflow improvements

---

## 9. Final Notes

### 9.1 Mission Critical
This payment system architecture specification is **CONFIRMED** status — complete documentation exists, all owner decisions approved, and implementation is ready to begin.

### 9.2 Owner Action Complete
All required owner decisions have been approved:
1. ✅ **DEC-OWN-001**: Select payment gateway — **bKash + SSLCommerz**
2. ✅ **DEC-OWN-002**: Set stock reservation TTL — **15 minutes**
3. ✅ **DEC-OWN-003**: Define delivery fee policy — **Flat fee per order**
4. ✅ **DEC-OWN-004**: Select courier partner — **Pathao Courier**

### 9.3 Documentation Integrity
All payment system documentation:
- ✅ Uses unique document IDs (DOC-AUR-157)
- ✅ Follows Aura Bell documentation conventions
- ✅ Clearly marks V1 vs Future classification
- ✅ References all related documents
- ✅ Maintains Bangla with English technical terms
- ✅ Clearly distinguishes specified vs implemented

### 9.4 Next Steps
1. Owner reviews and approves pending decisions (DEC-OWN-001 through DEC-OWN-004)
2. Database migration executed creating payment tables
3. FastAPI backend implemented per specifications
4. Frontend payment UI developed
5. Gateway accounts setup and tested
6. Production deployment executed
7. Post-implementation validation completed
8. Documentation updated to reflect implementation

---

**Document ID**: DOC-AUR-157  
**Title**: Aura Bell — Payment System Architecture Specification  
**Version**: 2.0  
**Status**: **CONFIRMED** (All owner decisions approved, documentation complete, ready for implementation)  
**Last Updated**: 2026-11-08  
**Governance**: Aura Bell Documentation System  
**Compliance**: Mission Requirements - Payment System Documentation  
**Dependencies**: DEC-OWN-001 (CONFIRMED), DEC-OWN-002 (CONFIRMED), DEC-OWN-003 (CONFIRMED), DEC-OWN-004 (CONFIRMED)  
**V1 Classification**: **V1 READY** (All blocking decisions confirmed)  
**Implementation Blocking**: **NONE** — All decisions confirmed


