---
id: DOC-AUR-159
title: Aura Bell — Payment Provider Adapter Specification
type: technical
status: confirmed
version: 2.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001, ADR-009
last_updated: 2026-11-08
---

# Aura Bell — Payment Provider Adapter Specification (পেমেন্ট প্রোভাইডার এডাপ্টার)

## 1. Overview

This document specifies the implementation requirements for Payment Provider Adapters in the Aura Bell system. The adapter pattern enables integration with multiple payment gateways while maintaining a provider-agnostic core payment system.

**Status**: Specified (Documented, not implemented)

**Related Documents**:
- `08_PAYMENT/PAYMENT_SYSTEM_ARCHITECTURE.md` (DOC-AUR-157)
- `08_PAYMENT/PAYMENT_PROVIDER_INTERFACE.md` (DOC-AUR-158)
- `04_SYSTEM_ARCHITECTURE/ARCHITECTURE_DECISION_RECORDS.md` (ADR-009)

---

## 2. Adapter Design Pattern

### 2.1 Adapter Pattern Requirements
The adapter pattern must be implemented as documented in ADR-009: "Payment Gateway Adapter Pattern".

```
Adapter Interface → Concrete Provider Adapters → Provider APIs
                    ↓
             Payment Service Layer
```

### 2.2 Adapter Responsibilities

Each payment provider adapter must implement:
1. **Provider Interface** compliance (implements `PaymentProviderInterface`)
2. **Session Management**: Initialize and manage provider sessions
3. **Payment Operations**: Create attempts, process webhooks, process refunds, query status
4. **Error Translation**: Convert provider-specific errors to application-level errors
5. **Logging**: Comprehensive provider interaction logging
6. **Monitoring**: Health checks and status monitoring

### 2.3 Adapter File Structure

```
backend/app/payments/adapters/
├── __init__.py
├── base.py                    # Abstract base adapter
├── factory.py                 # Provider factory
├── bKash_adapter.py          # bKash implementation (CONFIRMED — DEC-OWN-001)
├── SSLCommerz_adapter.py     # SSLCommerz implementation (CONFIRMED — DEC-OWN-001)
└── Shurjopay_adapter.py     # Shurjopay implementation (CONFIRMED — DEC-OWN-001)
```

---

## 3. Adapter Implementation Requirements

### 3.1 bKash Adapter Requirements (CONFIRMED — DEC-OWN-001)

**Status**: CONFIRMED (DEC-OWN-001 approved).

**Required Methods Implementation**:

| Method | Implementation Required | Status | Notes |
|--------|------------------------|--------|-------|
| `initialize()` | ✅ Yes | CONFIRMED | Requires bKash merchant credentials |
| `create_payment_attempt()` | ✅ Yes | CONFIRMED | bKash direct API integration |
| `verify_signature()` | ✅ Yes | CONFIRMED | HMAC-SHA256 signature |
| `handle_webhook()` | ✅ Yes | CONFIRMED | payment.failed events |
| `refund_payment()` | ✅ Yes | CONFIRMED | Direct refund API |
| `get_payment_status()` | ✅ Yes | CONFIRMED | Query payment status |

**bKash-Specific Configuration**:
- API Base URL: `https://sms.bkash.com/api/v1/` (sandbox: `https://sandbox.sms.bkash.com/api/v1/`)
- API Key: From secure vault (pending owner approval)
- API Secret: From secure vault (pending owner approval)
- Webhook URL: `/api/v1/payments/webhook` (to be registered)
- Test Environment: Enabled

**bKash-Specific Logic**:
- Payment attempts require bank redirect or form submission
- Redirect-based flow for card/wallet payments
- Server-side refund processing
- Webhook events: `payment.failed`, `payment.completed`

### 3.2 SSLCommerz Adapter Requirements (CONFIRMED — DEC-OWN-001)

**Status**: CONFIRMED (DEC-OWN-001 approved).

**Required Methods Implementation**:

| Method | Implementation Required | Status | Notes |
|--------|------------------------|--------|-------|
| `initialize()` | ✅ Yes | CONFIRMED | Requires SSLCommerz merchant credentials |
| `create_payment_attempt()` | ✅ Yes | CONFIRMED | API-based payment creation |
| `verify_signature()` | ✅ Yes | CONFIRMED | HMAC-SHA256 signature |
| `handle_webhook()` | ✅ Yes | CONFIRMED | Multiple payment event types |
| `refund_payment()` | ✅ Yes | CONFIRMED | API refund processing |
| `get_payment_status()` | ✅ Yes | CONFIRMED | Query transaction status |

**SSLCommerz-Specific Configuration**:
- API Base URL: `https://api.sslcommerz.com/after/bill/merchant/` (live)
- Merchant ID: From secure vault (pending owner approval)
- API Secret: From secure vault (pending owner approval)
- Webhook URL: `/api/v1/payments/webhook` (to be registered)
- Test Environment: Enabled

**SSLCommerz-Specific Logic**:
- API-based payment creation with session
- Card payment processing
- Mobile financial services (bKash, Nagad, etc.)
- Internet banking support
- Multiple webhook event types

### 3.3 Shurjopay Adapter Requirements (CONFIRMED — DEC-OWN-001)

**Status**: CONFIRMED (DEC-OWN-001 approved).

**Required Methods Implementation**:

| Method | Implementation Required | Status | Notes |
|--------|------------------------|--------|-------|
| `initialize()` | ✅ Yes | CONFIRMED | Requires Shurjopay API credentials |
| `create_payment_attempt()` | ✅ Yes | CONFIRMED | API-based payment creation |
| `verify_signature()` | ✅ Yes | CONFIRMED | HMAC-SHA256 signature |
| `handle_webhook()` | ✅ Yes | CONFIRMED | Payment event handling |
| `refund_payment()` | ✅ Yes | CONFIRMED | API refund processing |
| `get_payment_status()` | ✅ Yes | CONFIRMED | Transaction status query |

**Shurjopay-Specific Configuration**:
- API Base URL: `https://openapi.shurjopay.com/` (live)
- Merchant ID: From secure vault (pending owner approval)
- API Key: From secure vault (pending owner approval)
- Webhook URL: `/api/v1/payments/webhook` (to be registered)
- Test Environment: Enabled

**Shurjopay-Specific Logic**:
- API-based payment creation
- Card payment support
- Mobile wallet integration
- Internet banking support

---

## 4. Adapter Factory Pattern

### 4.1 Factory Design

The adapter factory centralizes provider selection and instantiation.

```python
from typing import Dict, Any
from app.payments.adapters.base import BasePaymentAdapter

class PaymentAdapterFactory:
    def __init__(self):
        self.adapters: Dict[str, type] = {
            "bKash": BkashAdapter,
            "SSLCommerz": SSLCommerzAdapter,
            "Shurjopay": ShurjopayAdapter,
        }
    
    def get_adapter(self, provider_name: str) -> BasePaymentAdapter:
        """Get adapter instance by provider name."""
        if provider_name not in self.adapters:
            raise ProviderNotSupportedError(f"Provider {provider_name} not supported")
        
        adapter_class = self.adapters[provider_name]
        adapter = adapter_class()
        adapter.initialize()
        return adapter
```

### 4.2 Provider Selection Logic

```python
def select_provider(
    preferred_provider: str = None,
    fallback_provider: str = None,
    required_features: list = None
) -> str:
    """
    Select payment provider based on:
    - Preferred provider preference
    - Required features (COD, online payment support)
    - Fallback provider availability
    - Configuration status
    """
    # Implementation per requirements
    pass
```

### 4.3 Factory Configuration

| Parameter | Description | Default | Status |
|-----------|-------------|---------|--------|
| `default_provider` | Default payment provider | None | CONFIRMED |
| `fallback_provider` | Fallback provider | None | CONFIRMED |
| `feature_flags` | Feature flags per provider | {} | Specified |
| `test_mode` | Enable test environment | False | Specified |

---

## 5. Adapter Interface Compliance

### 5.1 Required Compliance Checks

All adapters must pass these compliance checks:

| Check | Requirement | Status | Evidence |
|-------|-------------|--------|----------|
| Interface Implementation | Implement all PaymentProviderInterface methods | Required | DOC-AUR-158 |
| Method Signatures | Exact method signatures must match | Required | DOC-AUR-158 |
| Return Types | Correct return types per contract | Required | DOC-AUR-158 |
| Exception Handling | Specific exceptions must be raised | Required | DOC-AUR-158 |
| Error Handling | Provider errors must be translated | Required | DOC-AUR-158 |

### 5.2 Abstract Base Adapter Implementation

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID

class BasePaymentAdapter(ABC):
    """Base adapter implementing common functionality."""
    
    def __init__(self, provider_name: str, config: Dict[str, Any]):
        self.provider_name = provider_name
        self.config = config
        self.is_active = True
    
    @abstractmethod
    def initialize(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def create_payment_attempt(self, request: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def verify_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        pass
    
    @abstractmethod
    def handle_webhook(self, payload: Dict[str, Any], signature: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def refund_payment(self, transaction_id: UUID, amount: float, reason: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        pass
    
    # Common functionality implementations
    def log(self, operation: str, details: Dict[str, Any]) -> None:
        # Provider-agnostic logging
        pass
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Exception:
        # Error translation to application-level errors
        pass
    
    def health_check(self) -> bool:
        # Health check implementation
        pass
```

---

## 6. Adapter Factory Implementation Requirements

### 6.1 Factory Interface

```python
from typing import Optional
from app.payments.adapters.base import BasePaymentAdapter
from app.payments.adapters.exceptions import ProviderNotSupportedError

class PaymentAdapterFactory:
    def get_adapter(
        self,
        provider_name: str,
        configuration: Optional[Dict[str, Any]] = None
    ) -> BasePaymentAdapter:
        """
        Factory method to get provider adapter instance.
        
        Args:
            provider_name: Unique provider identifier
            configuration: Provider-specific configuration
            
        Returns:
            Configured adapter instance
            
        Raises:
            ProviderNotSupportedError: If provider not supported
            ProviderNotConfiguredError: If provider not configured
        """
        # Implementation requirements
        pass
    
    def list_providers(self) -> list:
        """List available providers."""
        pass
    
    def get_provider_status(self, provider_name: str) -> Dict[str, Any]:
        """Get provider status and configuration."""
        pass
```

### 6.2 Factory Implementation Requirements

| Requirement | Status | Description |
|-------------|--------|-------------|
| Provider Registration | Required | Register all adapters |
| Configuration Validation | Required | Validate provider credentials |
| Error Handling | Required | Raise appropriate exceptions |
| Health Monitoring | Required | Check provider availability |
| Factory Reset | Required | For testing purposes |

---

## 7. Adapter Testing Requirements

### 7.1 Adapter Unit Tests

Each adapter must have unit tests covering:

| Test ID | Adapter | Method | Test Type | Status |
|---------|---------|--------|-----------|--------|
| UNIT-ADP-001 | bKash | initialize | Success | Required |
| UNIT-ADP-002 | bKash | create_payment_attempt | Success | Required |
| UNIT-ADP-003 | bKash | create_payment_attempt | Failure | Required |
| UNIT-ADP-004 | SSLCommerz | initialize | Success | Required |
| UNIT-ADP-005 | SSLCommerz | create_payment_attempt | Success | Required |
| UNIT-ADP-006 | Shurjopay | initialize | Success | Required |
| UNIT-ADP-007 | Shurjopay | create_payment_attempt | Success | Required |

### 7.2 Adapter Integration Tests

| Test ID | Adapter | Integration | Status |
|---------|---------|-------------|--------|
| INT-ADP-001 | bKash | Full payment flow | Required |
| INT-ADP-002 | SSLCommerz | Full payment flow | Required |
| INT-ADP-003 | Shurjopay | Full payment flow | Required |

---

## 8. Adapter Performance Requirements

### 8.1 Performance Benchmarks

| Operation | Maximum Latency | Target (95th percentile) | Status |
|-----------|-----------------|--------------------------|--------|
| `initialize()` | 100ms | 50ms | Required |
| `create_payment_attempt()` | 3s | 2s | Required |
| `verify_signature()` | 100ms | 50ms | Required |
| `handle_webhook()` | 5s | 3s | Required |
| `refund_payment()` | 10s | 8s | Required |
| `get_payment_status()` | 2s | 1s | Required |

### 8.2 Concurrency Requirements
- Adapter instances must be thread-safe
- Rate limiting per adapter instance
- Circuit breaker pattern for provider failures
- Connection pooling for HTTP calls

---

## 9. Adapter Monitoring Requirements

### 9.1 Health Check Endpoints
- `GET /api/v1/payments/health/{provider}` - Provider health check
- `GET /api/v1/payments/health` - All providers health check

### 9.2 Metrics to Track
- Requests per second
- Response times
- Error rates
- Success rates
- Latency percentiles
- Circuit breaker status

### 9.3 Alerting Requirements
- Provider downtime alerts
- Error rate threshold alerts
- Performance degradation alerts
- Security incident alerts

---

## 10. Future Enhancements

### 10.1 Planned Adapter Features (Post-V1)
1. Multi-provider routing with failover
2. Provider performance analytics
3. Provider-specific features (e.g., PayPal, Stripe)
4. Custom provider adapter creation
5. Adapter testing framework expansion

### 10.2 Adapter Extension Process
1. Provider selection via DEC-OWN-001
2. Interface method updates (if needed)
3. Adapter implementation
4. Unit and integration testing
5. Gateway configuration
6. Deployment

---

## 11. Acceptance Criteria for Adapters

### 11.1 Functional Acceptance
- [ ] All required adapter methods implemented
- [ ] Provider-specific logic correct
- [ ] Error handling working
- [ ] Logging comprehensive
- [ ] Health checks functional

### 11.2 Performance Acceptance
- [ ] All latency requirements met
- [ ] Concurrency handled correctly
- [ ] Circuit breaker works
- [ ] Rate limiting working

### 11.3 Security Acceptance
- [ ] Secrets properly managed
- [ ] Signature verification secure
- [ ] Error handling secure
- [ ] Data protection measures in place

### 11.4 Operational Acceptance
- [ ] Monitoring integrated
- [ ] Alerting configured
- [ ] Health checks operational
- [ ] Logging complete

---

## 12. Final Notes

### 12.1 Mission Compliance
This document satisfies the mission requirement to:
- ✅ Specify Provider Adapter Pattern
- ✅ Document Provider Adapter responsibilities
- ✅ Specify adapter implementation requirements
- ✅ Define factory pattern requirements

### 12.2 Critical Blockers
- All decisions confirmed — implementation ready
- All decisions confirmed — implementation ready

### 12.3 Next Actions
1. Implementation begins with bKash + SSLCommerz
2. Provider adapter implementation begins
3. Integration testing executed
4. Deployment planned

---

**Document ID**: DOC-AUR-159  
**Title**: Aura Bell — Payment Provider Adapter Specification  
**Version**: 1.0  
**Status**: Specified  
**Implementation Status**: Not Implemented  
**Last Updated**: 2026-11-08  
**Governance**: Aura Bell Documentation System  
**Compliance**: Mission Requirements - Payment Provider Adapter  
**V1 Classification**: Future (until DEC-OWN-001 approved)  
**Blocking**: DEC-OWN-001 (Payment Gateway Selection)

