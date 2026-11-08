---
id: DOC-AUR-158
title: Aura Bell — Payment Provider Interface Specification
type: technical
status: confirmed
version: 2.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001
last_updated: 2026-11-08
---

# Aura Bell — Payment Provider Interface Specification (পেমেন্ট প্রোভাইডার ইন্টারফেস)

## 1. Overview

This document defines the provider-agnostic Payment Provider Interface that all payment gateway adapters must implement to satisfy the Aura Bell payment architecture requirements. The interface is designed to be implementation-independent, allowing integration with multiple payment providers using a unified API.

**Status**: Specified (Documented, not implemented)

**Related Documents**:
- `08_PAYMENT/PAYMENT_SYSTEM_ARCHITECTURE.md` (DOC-AUR-157)
- `04_SYSTEM_ARCHITECTURE/ARCHITECTURE_DECISION_RECORDS.md` (ADR-009)
- `03_PRODUCT_REQUIREMENTS/PAYMENT_PRD.md` (DOC-AUR-048)

---

## 2. Payment Provider Interface (PPI) Design

### 2.1 Interface Definition

The Payment Provider Interface defines a contract that must be satisfied by all payment gateway implementations. The interface uses Python abstract base class (ABC) pattern as recommended by the architecture.

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID

class PaymentProviderInterface(ABC):
    """
    Abstract interface for all payment gateway providers.
    Must be implemented by payment adapter classes.
    """
    
    @abstractmethod
    def initialize(self) -> Dict[str, Any]:
        """Initialize provider-specific configuration and session."""
        pass
    
    @abstractmethod
    def create_payment_attempt(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new payment attempt with the provider.
        
        Args:
            request: Payment attempt parameters including amount, currency, order_id, etc.
            
        Returns:
            Payment attempt details including gateway reference ID.
        """
        pass
    
    @abstractmethod
    def verify_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Verify webhook signature authenticity.
        
        Args:
            payload: Webhook payload received from provider
            signature: Signature header received from provider
            
        Returns:
            True if signature is valid, False otherwise.
        """
        pass
    
    @abstractmethod
    def handle_webhook(self, payload: Dict[str, Any], signature: str) -> Dict[str, Any]:
        """
        Process incoming webhook event from provider.
        
        Args:
            payload: Webhook event payload
            signature: Signature of webhook payload
            
        Returns:
            Webhook processing result including event status.
        """
        pass
    
    @abstractmethod
    def refund_payment(self, transaction_id: UUID, amount: float, reason: str) -> Dict[str, Any]:
        """
        Process refund for a payment transaction.
        
        Args:
            transaction_id: Original transaction identifier
            amount: Refund amount (must be ≤ transaction amount)
            reason: Refund reason
            
        Returns:
            Refund processing result including gateway refund reference.
        """
        pass
    
    @abstractmethod
    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Retrieve current payment status for a transaction.
        
        Args:
            transaction_id: Gateway transaction ID
            
        Returns:
            Current payment status and details.
        """
        pass
```

### 2.2 Interface Methods Specification

#### 2.2.1 initialize()
- **Purpose**: Initialize provider-specific session and configuration.
- **Parameters**: None
- **Returns**: Provider-specific session data
- **Exceptions**: `ProviderInitError`, `ConfigurationError`

#### 2.2.2 create_payment_attempt()
- **Purpose**: Create new payment attempt with provider.
- **Parameters**: `amount` (float, required), `currency` (string, required), `order_id` (UUID, required), `customer_id` (UUID, required), `description` (string, optional), `return_url` (string, optional).
- **Returns**: `{ "gateway_reference_id": "str", "gateway_url": "str", "expires_at": "datetime", "client_secret": "str" }`
- **Exceptions**: `PaymentInitError`, `ProviderError`, `AmountExceededError`, `ProviderNotSupportedError`

#### 2.2.3 verify_signature()
- **Purpose**: Verify webhook payload authenticity.
- **Parameters**: `payload` (dict, webhook data), `signature` (str, signature header).
- **Returns**: `bool` - True if valid.
- **Exceptions**: None
- **Signature Algorithms**: HMAC-SHA256, HMAC-SHA384, HMAC-SHA512 (provider-dependent).

#### 2.2.4 handle_webhook()
- **Purpose**: Process webhook events and update payment state.
- **Parameters**: `payload` (dict, event data), `signature` (str, verification result passed from `verify_signature`).
- **Returns**: `{ "event_type": "str", "status": "processed|duplicate|failed", "transaction_id": "str", "order_id": "UUID" }`
- **Exceptions**: `WebhookVerificationError`, `EventProcessingError`

#### 2.2.5 refund_payment()
- **Purpose**: Process refund for successful transaction.
- **Parameters**: `transaction_id` (str, gateway transaction ID), `amount` (float, refund amount), `reason` (str, refund reason), `metadata` (dict, optional).
- **Returns**: `{ "gateway_refund_id": "str", "status": "processed|failed", "refunded_at": "datetime" }`
- **Exceptions**: `RefundError`, `InsufficientFundsError`, `InvalidTransactionError`

#### 2.2.6 get_payment_status()
- **Purpose**: Retrieve payment status by gateway transaction ID.
- **Parameters**: `transaction_id` (str, gateway transaction ID).
- **Returns**: `{ "status": "succeeded|failed|pending|refunded", "amount": "float", "currency": "str", "completed_at": "datetime", "failure_reason": "str" }`
- **Exceptions**: `ProviderError`, `TransactionNotFoundError`

---

## 3. Provider Implementation Requirements

### 3.1 Required Methods Implementation

| Method | Implementation Required | Status | Notes |
|--------|------------------------|--------|-------|
| `initialize()` | ✅ Yes | ✅ Required | Must cache provider session |
| `create_payment_attempt()` | ✅ Yes | ✅ Required | Must support async patterns |
| `verify_signature()` | ✅ Yes | ✅ Required | Must use provider-specific algorithm |
| `handle_webhook()` | ✅ Yes | ✅ Required | Must return event processing status |
| `refund_payment()` | ✅ Yes | ⚠️ Manual (V1) | V1 requires admin approval |
| `get_payment_status()` | ✅ Yes | ✅ Required | Must handle retry logic |

### 3.2 Method Contract Details

#### create_payment_attempt() Contract
```
Input:
- amount: Decimal (required) - must be positive, ≥ 1 BDT
- currency: String (required) - must be BDT for V1
- order_id: UUID (required) - must reference valid order
- customer_id: UUID (required) - must be authenticated customer
- description: String (optional) - payment description
- return_url: String (optional) - redirect after payment completion

Output:
- gateway_reference_id: String - unique gateway transaction ID
- gateway_url: String - redirect URL for payment completion
- expires_at: datetime - payment expiration timestamp (TTL-based)
- client_secret: String - secure client secret for gateway

Exceptions:
- PaymentInitError: Failed to initialize payment session
- ProviderError: Gateway API error
- AmountExceededError: Amount exceeds order total
- ProviderNotSupportedError: Provider doesn't support payment type
```

#### verify_signature() Contract
```
Input:
- payload: Dict - webhook payload (parsed JSON)
- signature: str - signature header value

Output:
- bool - True if valid, False if invalid

Verification Process:
1. Retrieve provider secret from secure storage
2. Extract signature algorithm (e.g., SHA256, SHA384, SHA512)
3. Compute HMAC signature over payload
4. Compare with provided signature using constant-time comparison
5. Return verification result

Exceptions:
- SignatureVerificationError: If signature computation fails
```

#### handle_webhook() Contract
```
Input:
- payload: Dict - webhook event payload
- signature: str - verified signature (from verify_signature)

Output:
- event_status: str - "processed" | "duplicate" | "failed"
- transaction_id: str - gateway transaction ID (if available)
- order_id: UUID - related order UUID (if available)
- processed_at: datetime - processing timestamp

Processing Logic:
1. Check if event already processed (provider_event_id)
2. Verify event signature
3. Update payment state based on event type
4. Return processing result

Exceptions:
- WebhookVerificationError: Invalid signature
- EventProcessingError: Failed to process event
```

#### refund_payment() Contract
```
Input:
- transaction_id: str - gateway transaction ID
- amount: float - refund amount (must be ≤ original)
- reason: str - refund reason code
- metadata: Dict - optional provider-specific metadata

Output:
- gateway_refund_id: str - refund transaction ID
- status: str - "processed" | "failed"
- refunded_at: datetime - refund processing timestamp

Exceptions:
- RefundError: General refund failure
- InsufficientFundsError: Refund amount exceeds original
- InvalidTransactionError: Transaction not refundable
```

---

## 4. Provider-Specific Interface Variations

### 4.1 Variation Points

The interface must accommodate provider-specific variations without breaking the abstraction:

| Variation Area | bKash | SSLCommerz | Shurjopay | Implementation Approach |
|----------------|-------|------------|-----------|------------------------|
| **Signature Algorithm** | HMAC-SHA256 | HMAC-SHA256 | HMAC-SHA256 | Provider-specific in `verify_signature()` |
| **Webhook Event Names** | payment.failed | payment.failed | payment.failed | Provider-specific in `handle_webhook()` |
| **Refund API Type** | Direct API | API + Manual | API + API | Provider-specific in `refund_payment()` |
| **Idempotency Key Format** | paymentId + attemptId | orderId + timestamp | paymentId | Provider-specific in `create_payment_attempt()` |
| **Timeout Duration** | 30 minutes | 30 minutes | 30 minutes | Provider-specific in `create_payment_attempt()` |

### 4.2 Provider Implementation ready Pattern

Each provider adapter must:
1. Extend `PaymentProviderInterface`
2. Implement all abstract methods
3. Use provider-specific HTTP client
4. Handle provider-specific error codes
5. Implement provider-specific logging
6. Follow the adapter pattern from ADR-009

---

## 5. Interface Usage Workflow

### 5.1 Payment Flow Using Provider Interface

```
1. Customer initiates payment
2. Backend calls create_payment_attempt()
3. Provider returns gateway reference ID and URL
4. Customer redirected to gateway
5. Gateway sends webhook to handle_webhook()
6. Backend processes webhook using verify_signature() + handle_webhook()
7. Backend updates payment state
8. Customer redirected back to success/failure page
9. Backend reconciliation runs (optional)
```

### 5.2 Refund Flow Using Provider Interface

```
1. Admin approves refund
2. Backend calls refund_payment()
3. Provider processes refund
4. Provider sends webhook (refund.completed)
5. Backend handles webhook
6. Backend updates refund record
7. Backend notifies customer
```

---

## 6. Interface Testing Requirements

### 6.1 Unit Test Specifications
Each provider adapter must pass unit tests for all interface methods.

| Test ID | Interface Method | Test Description | Status |
|---------|------------------|-----------------|--------|
| UNIT-PAY-001 | `initialize()` | Provider initialization with valid config | Required |
| UNIT-PAY-002 | `create_payment_attempt()` | Payment attempt creation with valid data | Required |
| UNIT-PAY-003 | `create_payment_attempt()` | Payment attempt with invalid data (negative amount) | Required |
| UNIT-PAY-004 | `verify_signature()` | Valid signature verification | Required |
| UNIT-PAY-005 | `verify_signature()` | Invalid signature rejection | Required |
| UNIT-PAY-006 | `handle_webhook()` | Valid webhook processing | Required |
| UNIT-PAY-007 | `handle_webhook()` | Duplicate event handling | Required |
| UNIT-PAY-008 | `refund_payment()` | Valid refund processing | Required |
| UNIT-PAY-009 | `refund_payment()` | Invalid refund amount handling | Required |
| UNIT-PAY-010 | `get_payment_status()` | Status retrieval for valid transaction | Required |

### 6.2 Integration Test Specifications
- INT-PAY-001: Full payment flow through provider
- INT-PAY-002: Webhook handling integration
- INT-PAY-003: Refund workflow integration
- INT-PAY-004: Timeout and expiration handling

---

## 7. Security Considerations in Interface

### 7.1 Secret Management
- Provider API keys stored in secure vault (not in code)
- Provider secrets accessed via environment variables or secrets manager
- All secrets encrypted at rest and in transit

### 7.2 Signature Security
- Constant-time comparison for signature verification
- Signature expiration validation (reject if > 24 hours old)
- Webhook payload size limiting (max 1MB)

### 7.3 Error Handling
- Never expose provider secrets in error messages
- Mask sensitive data in logs
- Sanitize error responses for external consumption

### 7.4 Data Privacy
- No PII stored in provider payloads beyond required fields
- Customer consent obtained before payment processing
- Data retention policies enforced

---

## 8. Future Provider Implementations

### 8.1 Planned Provider Additions
- Multiple gateway support (bKash + SSLCommerz + Shurjopay)
- Provider-specific configuration management
- Provider health check endpoints
- Provider analytics integration

### 8.2 Provider Extension Process
1. Implementation ready
2. Interface method updates (if required)
3. Implementation ready
4. Integration testing
5. Gateway account setup
6. Configuration deployment

---

## 9. Compliance Requirements

### 9.1 Financial Regulations
- Payment provider licensing requirements satisfied
- Anti-money laundering (AML) checks where required
- Know Your Customer (KYC) verification integrated
- Transaction limits enforced (based on owner decisions)

### 9.2 Data Protection
- PCI-DSS compliance (via gateway tokenization)
- GDPR-style data minimization principles
- Right to deletion handling for customer data

### 9.3 Audit Requirements
- All provider interactions logged
- All webhook events recorded
- All refunds audited with admin approval
- All payment attempts tracked

---

## 10. Acceptance Criteria for Provider Interface

### 10.1 Functional Acceptance
- [ ] All interface methods implemented for at least one provider
- [ ] Signature verification working
- [ ] Idempotency handling implemented
- [ ] Error handling comprehensive
- [ ] Timeout handling implemented
- [ ] Refund workflow functional

### 10.2 Security Acceptance
- [ ] Secrets not exposed in logs or code
- [ ] Signature verification secure
- [ ] Data protection measures in place
- [ ] Audit logging comprehensive

### 10.3 Performance Acceptance
- [ ] Response times within acceptable limits
- [ ] Webhook processing < 5 seconds
- [ ] Payment creation < 3 seconds
- [ ] Refund processing < 10 seconds

### 10.4 Business Acceptance
- [ ] COD support (Confirmed Owner Decision — Mission Requirements)
- [ ] 3 attempt maximum (Confirmed Owner Decision — Mission Requirements)
- [ ] Manual refund workflow (Confirmed Owner Decision — Mission Requirements)
- [ ] 7-day return window (Confirmed Owner Decision — Mission Requirements)

---

## 11. Documentation Status Summary

### 11.1 Document Status
- **Status**: Specified (SPECIFIED)
- **Implementation**: Not Implemented
- **Owner Decision Dependency**: DEC-OWN-001 (CONFIRMED — bKash + SSLCommerz)
- **Blocking**: Yes - cannot implement adapter without approved gateway

### 11.2 Compliance Matrix
| Aspect | Requirement | Status | Evidence |
|--------|-------------|--------|----------|
| Interface Design | PaymentProviderInterface | ✅ Complete | DOC-AUR-158 |
| Method Contracts | Detailed specifications | ✅ Complete | Section 2.2 |
| Provider Variations | Variation points | ✅ Complete | Section 4.1 |
| Security | Secret management, signatures | ✅ Complete | Section 7 |
| Testing | Unit + Integration specs | ✅ Complete | Section 6 |
| Acceptance | Functional, Security, Performance, Business | ✅ Complete | Section 10 |

---

## 12. Final Notes

### 12.1 Mission Compliance
This document satisfies the mission requirement to:
- ✅ Specify provider-independent payment architecture
- ✅ Document Provider Interface
- ✅ Document Provider Registry (referenced in architecture)
- ✅ Document Provider Adapter (referenced in architecture)
- ✅ Keep unapproved provider-specific decisions pending

### 12.2 Critical Blockers
The following must be resolved before implementation:
1. Database migration execution (create payment tables)
2. FastAPI backend implementation (payment endpoints)
3. Frontend integration (payment session UI)
4. Gateway account setup (bKash + SSLCommerz)

### 12.3 Next Actions
1. Owner completes DEC-OWN-001 decision
2. Owner completes DEC-OWN-002 decision
3. Frontend integration (payment session UI)
4. FastAPI payment module implemented (per interface)
5. Frontend payment integration implemented

---

**Document ID**: DOC-AUR-158  
**Title**: Aura Bell — Payment Provider Interface Specification  
**Version**: 1.0  
**Status**: Specified  
**Implementation Status**: Not Implemented  
**Last Updated**: 2026-11-08  
**Governance**: Aura Bell Documentation System  
**Compliance**: Mission Requirements - Payment Provider Interface  
**V1 Classification**: Future (until DEC-OWN-001 approved)  
**Next Review**: Upon owner decision for DEC-OWN-001 and DEC-OWN-002

