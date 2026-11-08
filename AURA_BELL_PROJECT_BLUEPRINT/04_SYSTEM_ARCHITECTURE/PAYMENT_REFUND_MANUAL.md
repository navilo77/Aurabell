---
id: DOC-AUR-164
title: Aura Bell — Payment Refund and Manual Refund Specification
type: technical
status: confirmed
version: 2.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001, BR-AUR-005, RULE-AUR-012
last_updated: 2026-11-08
---

# Aura Bell — Payment Refund and Manual Refund Specification (পেমেন্ট রিফান্ড ও ম্যানুয়াল রিফান্ড)

## 1. Overview

This document specifies the payment refund process for the Aura Bell system. All refunds in V1 require admin manual approval per the confirmed owner decision #2 (Refund Policy: Admin Manual Refund).

**Status**: Specified (Documented, not implemented)

**Related Documents**:
- `08_PAYMENT/PAYMENT_SYSTEM_ARCHITECTURE.md` (DOC-AUR-157)
- `03_PRODUCT_REQUIREMENTS/PAYMENT_PRD.md` (DOC-AUR-048)
- `02_BUSINESS_REQUIREMENTS/BUSINESS_RULES.md` (RULE-AUR-012)
- `03_PRODUCT_REQUIREMENTS/ORDER_MANAGEMENT_PRD.md` (DOC-AUR-047)

---

## 2. Refund Policy and Governance

### 2.1 Confirmed Owner Decision

**Refund Policy: Admin Manual Refund** (Confirmed Owner Decision — Mission Requirements)

This means:
- All refunds require explicit admin approval
- No automated refund processing in V1
- Admin must verify eligibility before processing
- Refund must be recorded in audit trail

### 2.2 Refund Policy Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| Admin approval required | Every refund needs admin sign-off | ✅ Required |
| 7-day return window | Refund only within 7 days of delivery | ✅ Required (Confirmed Owner Decision — Mission Requirements) |
| Product inspection | Returned product must be inspected | ✅ Required |
| Stock restoration | Returned items must restore stock | ✅ Required |
| Manual refund processing | Admin initiates refund via gateway | ✅ Required |

---

## 3. Refund Eligibility Criteria

### 3.1 Eligibility Conditions

A refund is eligible if ALL of the following conditions are met:

| Condition | Required | Description |
|-----------|----------|-------------|
| Order delivered | ✅ Yes | Order status must be 'delivered' |
| Within 7-day window | ✅ Yes | Return request within 7 days of delivery |
| Product condition | ✅ Yes | Product must pass inspection |
| Admin approval | ✅ Yes | Admin must explicitly approve |
| Payment completed | ✅ Yes | Original payment must have succeeded |

### 3.2 Ineligible Conditions

| Condition | Ineligible | Description |
|-----------|------------|-------------|
| Beyond 7-day window | ❌ No | Return request > 7 days after delivery |
| Damaged product | ❌ No | Product damaged by customer |
| Non-returnable items | ❌ No | Items marked non-returnable |
| Partial return not allowed | ❌ No | V1: Partial shipments not allowed (Confirmed Business Decision — Mission Requirements) |
| COD unconfirmed | ❌ No | Cash on Delivery not confirmed |

---

## 4. Refund Process Workflow

### 4.1 Refund Request Flow

```
Refund Request Process:
1. Customer submits return request in account portal
   - Selects order and items to return
   - Provides reason and photos
   - Submits request

2. System validates:
   - Order status = 'delivered'
   - Delivery date within 7 days [Confirmed Owner Decision — Mission Requirements]
   - Items not already returned
   - Creates return_request record

3. Admin reviews return request:
   - Reviews customer photos/reason
   - Checks order history
   - Verifies 7-day window [Confirmed Owner Decision — Mission Requirements]
   - Approves or rejects

4. If approved:
   a. Customer ships return (or scheduled pickup)
   b. Admin receives return
   c. Product inspection performed
   d. If inspection passes:
      i. Stock restoration initiated
      ii. Refund processing started
   e. If inspection fails:
      i. Reject refund
      ii. Notify customer

5. Refund Processing:
   a. Admin initiates refund via gateway
   b. Gateway processes refund
   c. Refund recorded in `refunds` table
   d. Order status updated
   f. Customer notified
```

### 4.2 Refund State Machine

```
Refund States:
pending_inspection → approved → processing → processed
                   ↓
                   rejected → cancelled
```

### 4.3 Refund Processing Steps

| Step | Action | Responsible | Database Impact |
|------|--------|-------------|-----------------|
| 1 | Return request submitted | Customer | `return_requests` created |
| 2 | Admin approves request | Admin | `return_requests` status updated |
| 3 | Product received and inspected | Admin/Warehouse | `return_items` inspection status |
| 4 | Stock restoration | Admin/System | `inventory_balances` + `stock_movements` |
| 5 | Refund initiated | Admin | `refunds` record created |
| 6 | Gateway processes refund | Payment Gateway | `payment_transactions` updated |
| 7 | Refund completed | System | `refunds` status = 'processed' |
| 8 | Order status updated | System | `orders` status = 'refunded' |

---

## 5. Refund Data Model

### 5.1 `refunds` Table

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `refund_id` | UUID | PRIMARY KEY | PRIMARY KEY |
| `return_request_id` | UUID | FK to return_requests | FK, NOT NULL |
| `order_id` | UUID | FK to orders | FK, NOT NULL |
| `store_order_id` | UUID | FK to store_orders | FK, NOT NULL |
| `amount` | Decimal | Refund amount | CHECK > 0 |
| `reason` | Text | Refund reason | NOT NULL |
| `approved_by` | UUID | Admin who approved | FK, NOT NULL |
| `approved_at` | Timestamp | Approval timestamp | NOT NULL |
| `processed_at` | Timestamp | Processing timestamp | NULL = pending |
| `gateway_refund_id` | String | Gateway refund ID | NULL = pending |
| `status` | Enum | pending/processing/processed/failed | NOT NULL |
| `created_at` | Timestamp | Request timestamp | NOT NULL |

### 5.2 `return_requests` Table

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `request_id` | UUID | PRIMARY KEY | PRIMARY KEY |
| `order_id` | UUID | FK to orders | FK, NOT NULL |
| `customer_id` | UUID | FK to profiles | FK, NOT NULL |
| `reason` | Text | Return reason | NOT NULL |
| `photos` | JSONB | Array of photo URLs | NULLable |
| `status` | Enum | pending_inspection/approved/rejected | NOT NULL |
| `created_at` | Timestamp | Request timestamp | NOT NULL |
| `approved_at` | Timestamp | Approval timestamp | NULLable |
| `approved_by` | UUID | Admin who approved | FK, NULLable |

### 5.3 `return_items` Table

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `return_item_id` | UUID | PRIMARY KEY | PRIMARY KEY |
| `return_request_id` | UUID | FK to return_requests | FK, NOT NULL |
| `order_item_id` | UUID | FK to order_items | FK, NOT NULL |
| `quantity` | Integer | Quantity to return | CHECK > 0 |
| `inspection_status` | Enum | pending/passed/failed | DEFAULT pending |
| `inspection_notes` | Text | Inspection notes | NULLable |
| `inspected_at` | Timestamp | Inspection timestamp | NULLable |
| `inspected_by` | UUID | Admin who inspected | FK, NULLable |

---

## 6. Refund Ledger

### 6.1 Refund Ledger Requirements

The refund ledger provides complete audit trail for all refunds:

| Requirement | Description | Status |
|-------------|-------------|--------|
| Immutable records | Refund records cannot be modified | ✅ Required |
| Complete audit trail | All actions logged with timestamps | ✅ Required |
| Approval trail | Who approved and when | ✅ Required |
| Gateway reference | Gateway refund transaction ID | ✅ Required |
| Financial reconciliation | Linked to financial entries | ✅ Required |

### 6.2 Refund ledger integration

```
Refund ledger integration:
1. Refund created → Create refund_ledger entry
2. Admin approves → Log approval in ledger
3. Gateway processes → Log gateway response
4. Refund completed → Mark ledger entry complete
5. Reconciliation → Use ledger for financial reconciliation
```

### 6.3 Refund Ledger Data Points

| Data Point | Source | Purpose |
|------------|--------|---------|
| Refund ID | refunds.refund_id | Unique identifier |
| Order ID | refunds.order_id | Order reference |
| Amount | refunds.amount | Financial amount |
| Reason | refunds.reason | Business reason |
| Approved By | refunds.approved_by | Accountability |
| Approved At | refunds.approved_at | Timestamp |
| Processed At | refunds.processed_at | Completion timestamp |
| Gateway Refund ID | refunds.gateway_refund_id | Gateway reference |
| Status | refunds.status | Current state |
| Created At | refunds.created_at | Request timestamp |

---

## 7. Stock Restoration Process

### 7.1 Stock Restoration Rules

Stock restoration happens ONLY after:
1. Return request approved
2. Product received and inspected
3. Inspection passes
4. Admin confirms restoration

### 7.2 Stock Restoration Process

```
Stock restoration workflow:
1. Admin confirms inspection passed
2. System identifies product variant and warehouse
3. Increment inventory_balances.quantity_on_hand
3. Create stock_movement record:
   - movement_type = RETURN
   - quantity = returned quantity
   - related_order_id = order_id
   - notes = "Return inspection passed - stock restored"
4. Update order status to reflect return
5. Create audit log entry
```

### 7.3 Stock Restoration Validation

| Validation | Requirement |
|------------|-------------|
| Product variant exists | Required |
| Warehouse exists | Required |
| Quantity > 0 | Required |
| Inspection passed | Required |
| Admin confirmation | Required |

---

## 8. V1 vs Future Classification

### 8.1 V1 Refund Features

**V1 Refund Features Included**:
1. Manual refund process with admin approval
2. 7-day return window enforcement
3. Product inspection workflow
4. Stock restoration on successful return
5. Complete refund ledger audit trail
6. COD refund handling
7. Partial refund support (per item)

**V1 Refund Features Excluded**:
1. Automated refund processing
2. Self-service refund initiation (customer must request)
3. Instant refund (requires admin approval)
4. Refund to original payment method only (gateway dependent)

### 8.2 Future (Post-V1) Refund Features

**Planned Refund Enhancements**:
1. Automated refund for eligible returns
2. Self-service return portal
3. Instant refund for verified returns
4. Multiple refund methods (wallet, store credit)
5. AI-assisted inspection
6. Refund analytics and optimization
7. Automated reconciliation

---

## 9. Integration with Order Management

### 9.1 Order State Machine Integration

```
Order State → Refund State Mapping:
Order: delivered → return_requested → returned → refunded
Refund: pending → processing → processed

V1 Rules:
- No partial shipments = no partial returns
- 7-day window from delivery
- Manual admin approval at each step
```

### 9.2 Integration Points

| Integration Point | Description |
|-------------------|-------------|
| `orders` table | Update order status to 'refunded' |
| `order_items` table | Track returned items |
| `inventory_balances` | Restore stock on return |
| `stock_movements` | Log stock restoration |
| `payment_transactions` | Update payment status |
| `refunds` table | Record refund details |
| `return_requests` | Track return workflow |

---

## 10. Acceptance Criteria

### 10.1 Refund Acceptance

- [ ] Admin can approve/reject refund requests
- [ ] 7-day window enforced
- [ ] Product inspection workflow functional
- [ ] Stock restored on successful return
- [ ] Refund ledger immutable and complete
- [ ] Customer notified at each step
- [ ] Order status updated correctly

### 10.2 Process Acceptance

- [ ] Refund request → Admin review workflow
- [ ] Inspection → Admin confirmation workflow
- [ ] Refund initiation → Gateway processing
- [ ] Completion → Status updates and notifications
- [ ] Audit trail complete for all actions

### 10.3 Non-Functional Acceptance

- [ ] All refund actions require admin authentication
- [ ] No refund processed without admin approval
- [ ] Refund ledger immutable
- [ ] Financial reconciliation possible
- [ ] Performance: refund initiation < 5 seconds

---

## 11. Implementation Status

### 11.1 Current Status

- **Status**: Specified (SPECIFIED)
- **Implementation**: Not Implemented
- **Related Owner Decision**: DEC-OWN-001 (Payment Gateway)
- **Blocking**: Yes - Refund processing ready with bKash + SSLCommerz

### 11.2 Readiness

| Component | Status | Ready? |
|-----------|--------|--------|
| Refund Policy | ✅ Specified | Yes |
| Eligibility Criteria | ✅ Specified | Yes |
| Workflow Design | ✅ Specified | Yes |
| Data Model | ✅ Specified | Yes |
| Ledger Specification | ✅ Specified | Yes |
| Stock Restoration | ✅ Specified | Yes |
| Implementation | ❌ Not Implemented | No |

---

## 12. Final Notes

### 12.1 Mission Compliance
This document satisfies the mission requirement to:
- ✅ Document Manual Refund
- ✅ Document Refund Ledger
- ✅ Integrate with 7-day Return Window (Confirmed Owner Decision — Mission Requirements)
- ✅ Integrate with Admin Manual Refund (Confirmed Owner Decision — Mission Requirements)

### 12.2 Critical Blockers
- Refund implementation blocked by DEC-OWN-001 (Payment Gateway)
- Gateway refund API required for implementation

### 12.3 Next Actions
1. Gateway refund APIs accessible (bKash + SSLCommerz)
2. Database migration executed with refund tables
3. Refund service implemented
4. Admin refund approval UI implemented
5. Gateway refund integration (bKash + SSLCommerz)
6. Refund ledger integration
7. Stock restoration workflow

---

**Document ID**: DOC-AUR-164  
**Title**: Aura Bell — Payment Refund and Manual Refund Specification  
**Version**: 1.0  
**Status**: Specified  
**Implementation Status**: Not Implemented  
**Last Updated**: 2026-11-08  
**Governance**: Aura Bell Documentation System  
**Compliance**: Mission Requirements - Payment Refund and Manual Refund  
**V1 Classification**: Future (until DEC-OWN-001 approved)  
**Blocking**: DEC-OWN-001 (Payment Gateway Selection)
