---
id: DOC-AUR-161
title: Aura Bell — Payment Reconciliation Specification
type: technical
status: confirmed
version: 2.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001, BR-AUR-005
last_updated: 2026-11-08
---

# Aura Bell — Payment Reconciliation Specification (পেমেন্ট রিকনসিলিয়েশন)

## 1. Overview

This document specifies the payment reconciliation process for the Aura Bell system. Reconciliation involves comparing payment transaction records in the database with actual payment gateway records to ensure financial accuracy and integrity.

**Status**: Specified (Documented, not implemented)

**Related Documents**:
- `08_PAYMENT/PAYMENT_SYSTEM_ARCHITECTURE.md` (DOC-AUR-157)
- `05_DATABASE/DATABASE_SCHEMA.md` (DOC-AUR-070)
- `05_DATABASE/DATA_VALIDATION_RULES.md` (DOC-AUR-073)
- `02_BUSINESS_REQUIREMENTS/BUSINESS_REQUIREMENTS.md` (BR-AUR-005)

---

## 2. Reconciliation Objectives

### 2.1 Purpose

The payment reconciliation process aims to:
1. Ensure all payment transactions are accurately recorded
2. Detect discrepancies between database and gateway
3. Resolve financial discrepancies
4. Maintain audit trail of all financial activities
5. Provide operational visibility into payment flows

### 2.2 Scope

- Daily reconciliation of all payment transactions
- Manual reconciliation for specific transactions
- Gateway vs database discrepancy resolution
- Financial reporting accuracy verification
- Fraud detection and investigation support

---

## 3. Reconciliation Workflow

### 3.1 Daily Reconciliation Process

```
Daily Reconciliation Workflow:
1. Trigger Time: Daily at 02:00 AM (BDT)
2. Retrieve all payment transactions from database for the previous day
3. Fetch corresponding transactions from selected payment gateway
4. Compare transaction records:
   a. Transaction existence (database vs gateway)
   b. Transaction status (database vs gateway)
   c. Transaction amounts (database vs gateway)
   d. Transaction timestamps (database vs gateway)
   e. Transaction identifiers (gateway reference IDs)
5. Analyze discrepancies
6. Resolve each discrepancy appropriately
7. Generate reconciliation report
8. Update financial entries
9. Alert admin for unresolved issues
```

### 3.2 Reconciliation Data Sources

| Data Source | Description | Fields |
|-------------|-------------|--------|
| Database | `payments` table, `payment_transactions` table, `payment_attempts` table | All transaction fields |
| Gateway | Provider-specific transaction API | Gateway reference IDs, statuses, amounts |
| Bank Statements | External financial records | Settlement information |

---

## 4. Reconciliation Rules and Policies

### 4.1 Reconciliation Criteria

| Criteria | Description | Tolerance |
|----------|-------------|-----------|
| Amount Accuracy | Database amount = Gateway amount | 0 BDT (exact) |
| Status Consistency | Database status = Gateway status | 0 (exact) |
| Timestamp Alignment | Processing times within 5 minutes | ≤ 5 minutes |
| Identifier Match | Gateway transaction ID in database | 100% required |

### 4.2 Reconciliation Frequency

| Level | Frequency | Scope | Owner |
|-------|-----------|-------|-------|
| Daily | Daily at 02:00 AM | All transactions | Automated |
| Real-time | Per transaction | Pending transactions | Automated |
| Manual | As needed | Specific transactions | Admin |

### 4.3 Reconciliation Thresholds

| Discrepancy Type | Severity | Action |
|-----------------|----------|--------|
| Amount difference | High | Immediate alert, manual investigation |
| Status mismatch | High | Immediate alert, manual reconciliation |
| Missing transaction | High | Alert, create missing record |
| Duplicate transaction | Medium | Investigate, correct records |
| Timestamp mismatch | Low | Log, monitor |

---

## 5. Reconciliation Process Flow

### 5.1 Automated Reconciliation Process

```
1. Trigger: Scheduled job (cron) or manual admin request
2. Retrieve daily transactions from database:
   SELECT * FROM payments 
   WHERE created_at >= '2026-11-07 00:00:00' 
     AND created_at < '2026-11-08 00:00:00'
3. For each transaction, query gateway for status
4. Compare and reconcile
5. Update database if needed
6. Generate report
7. Store reconciliation log
8. Alert if discrepancies found
```

### 5.2 Reconciliation Logic

```
Reconciliation Algorithm:
for each transaction in database_today:
    gateway_tx = gateway.getTransaction(transaction.gateway_ref_id)
    
    # Check existence
    if gateway_tx is None:
        # Transaction not found at gateway - mark as potentially failed
        transaction.status = 'gateway_not_found'
        continue
    
    # Check status
    if transaction.status != gateway_tx.status:
        transaction.status = gateway_tx.status
        update_transaction()
    
    # Check amount
    if transaction.amount != gateway_tx.amount:
        discrepancy_found = True
        # Flag for manual review
        transaction.reconciliation_flag = True
    
    # Check timestamp
    if abs(transaction.created_at - gateway_tx.created_at) > 300:
        # Within 5 minutes tolerance
        log_warning()
```

---

## 6. Reconciliation Data Model

### 6.1 reconciliation_records Table

| Field | Type | Description |
|-------|------|-------------|
| reconciliation_id | UUID | Unique reconciliation run ID |
| reconciliation_date | Date | Date being reconciled |
| status | Enum | completed/pending_failed/in_progress |
| total_transactions | Integer | Total transactions checked |
| reconciled_count | Integer | Successfully reconciled |
| discrepancy_count | Integer | Found discrepancies |
| error_count | Integer | Errors during reconciliation |
| started_at | Timestamp | Start time |
| completed_at | Timestamp | Completion time |
| completed_by | UUID | Admin who initiated/completed |
| notes | Text | Reconciliation notes |

### 6.2 reconciliation_discrepancies Table

| Field | Type | Description |
|-------|------|-------------|
| discrepancy_id | UUID | Unique discrepancy ID |
| reconciliation_id | UUID | Related reconciliation run |
| transaction_id | UUID | Related payment transaction |
| type | Enum | amount/status/missing/duplicate/other |
| severity | Enum | low/medium/high/critical |
| description | Text | Discrepancy description |
| gateway_data | JSONB | Gateway-side data |
| database_data | JSONB | Database-side data |
| resolution | Text | Resolution status/action |
| resolved_at | Timestamp | When resolved |
| resolved_by | UUID | Who resolved |

---

## 7. Reconciliation Rules

### 7.1 Reconciliation Rules Registry

| Rule ID | Description | Source |
|---------|-------------|--------|
| REC-AUR-001 | Daily reconciliation must run at 02:00 AM | Operational |
| REC-AUR-002 | Amount must match exactly between DB and gateway | Financial |
| REC-AUR-003 | Status must match between DB and gateway | Financial |
| REC-AUR-004 | Reconciliation logs must be immutable | Governance |
| REC-AUR-005 | Discrepancies must be resolved within 48 hours | Operational |

### 7.2 Reconciliation Exception Handling

| Exception | Response | Escalation |
|-----------|----------|-----------|
| Transaction not found at gateway | Flag for investigation | Admin alert |
| Amount mismatch | Flag for manual review | Admin alert, finance review |
| Status mismatch | Flag for manual review | Admin alert, finance review |
| Gateway API error | Retry, then alert | Admin alert |
| Database error | Retry, then alert | Admin alert |
| Duplicate transaction | Detect, resolve | Finance review |

---

## 8. Financial Reporting Integration

### 8.1 Reconciliation vs Financial Reporting

```
Reconciliation Process → Financial Reports:
1. Reconciliation identifies discrepancies
2. Resolved discrepancies update transaction records
3. Financial reports query reconciled data
4. Reports generate from reconciled data
5. Financial statements verified against reconciliation
```

### 8.2 Financial Report Requirements

- Reports must use reconciled data
- Discrepancies must be flagged in reports
- Audit trail of all reconciliations
- Financial statements must balance

---

## 9. Acceptance Criteria

### 9.1 Reconciliation Acceptance

- [ ] Daily reconciliation runs at 02:00 AM
- [ ] All transactions reconciled
- [ ] Discrepancies identified and resolved
- [ ] Reconciliation logs stored
- [ ] Financial reports use reconciled data

### 9.2 Accuracy Acceptance

- [ ] No amount discrepancies remain after reconciliation
- [ ] No status mismatches remain after reconciliation
- [ ] All transaction identifiers match
- [ ] Reconciliation reports generated

---

## 10. Implementation Status

### 10.1 Current Status

- **Status**: Specified (SPECIFIED)
- **Implementation**: Not Implemented
- **Related Owner Decision**: DEC-OWN-001 (Payment Gateway)
- **Blocking**: Yes - Cannot complete reconciliation without gateway access

### 10.2 Readiness

| Component | Status | Ready? |
|-----------|--------|--------|
| Reconciliation Rules | ✅ Specified | Yes |
| Reconciliation Workflow | ✅ Specified | Yes |
| Database Schema | ✅ Documented | Yes |
| Financial Reports Integration | ✅ Specified | Yes |
| Implementation | ❌ Not Implemented | No |

---

## 11. Final Notes

### 11.1 Mission Compliance
This document satisfies the mission requirement to:
- ✅ Document Reconciliation
- ✅ Specify reconciliation process
- ✅ Define reconciliation rules
- ✅ Integrate with financial reporting

### 11.2 Critical Blockers
- Reconciliation implementation blocked by DEC-OWN-001 (Payment Gateway Selection)
- Reconciliation can run with bKash + SSLCommerz APIs

### 11.3 Next Actions
1. Gateway APIs accessible (bKash + SSLCommerz)
2. Database schema updated with reconciliation tables
3. Reconciliation service implemented
4. Reconciliation scheduler implemented
5. Financial reporting integrated

---

**Document ID**: DOC-AUR-161  
**Title**: Aura Bell — Payment Reconciliation Specification  
**Version**: 1.0  
**Status**: Specified  
**Implementation Status**: Not Implemented  
**Last Updated**: 2026-11-08  
**Governance**: Aura Bell Documentation System  
**Compliance**: Mission Requirements - Payment Reconciliation  
**V1 Classification**: Future (until DEC-OWN-001 approved)  
**Blocking**: DEC-OWN-001 (Payment Gateway Selection)

