---
id: DOC-AUR-165
title: Aura Bell — Shipping System Architecture
type: technical
status: confirmed
version: 2.0
language: Bangla with English technical terms
source: AB-PV-001, AB-SA-001, AB-DS-001, SHIPPING_DELIVERY_PRD, Confirmed Owner Decision (Store-Level Shipment Fulfillment)
last_updated: 2026-11-08
---

# Aura Bell — Shipping System Architecture (শিপিং সিস্টেম আর্কিটেকশন)

## 1. Overview

This document specifies the architecture of the shipping system in the Aura Bell e-commerce platform. The shipping system handles order packaging, courier dispatch, tracking, delivery lifecycle management, and returns/refund workflows.

**Status**: Specified (Documented, not implemented)

**Related Documents**:
- `03_PRODUCT_REQUIREMENTS/SHIPPING_DELIVERY_PRD.md` (DOC-AUR-049) — PRD
- `04_SYSTEM_ARCHITECTURE/SYSTEM_ARCHITECTURE.md` (DOC-AUR-060) — System Architecture
- `02_BUSINESS_REQUIREMENTS/BUSINESS_RULES.md` (RULE-AUR-001, DEC-OWN-004) — Business Rules
- `PAYMENT_REFUND_MANUAL.md` (DOC-AUR-164) — Refund Integration
- Confirmed Owner Decision (Store-Level Shipment Fulfillment V1)

---

## 2. System Requirements

### 2.1 Confirmed Business Rules

| Rule ID | Description | Enforcement | Status |
|---------|-------------|-------------|--------|
| RULE-AUR-001 | DB-Driven Stock Truth | No overselling | ✅ Confirmed |
| DEC-OWN-004 | Courier Partner Selection | Pathao Courier confirmed | ✅ Confirmed |
| BR-AUR-005 | Payment & Financial Audit | Shipping financial adjustments audited | ✅ Confirmed |
| Confirmed Owner Decision | Store-Level Shipment Fulfillment | In V1, each Store Order ships as a complete unit (no item-level splitting within a single store), while Multi-Store Parent Orders generate dedicated shipments per store | ✅ Confirmed |

### 2.2 Functional Requirements

**SR-SHP-001 (Multi-Shipment Architecture)**: A parent order can generate multiple shipments for different stores or warehouses. Each shipment is independent from the payment side but uses the same order as parent.

**SR-SHP-002 (Manual Courier Dispatch - V1)**: Admin panel provides courier name (Steadfast, Pathao, RedX) selection and tracking code input at checkout.

**SR-SHP-003 (Shipment State Lifecycle)**: Shipment goes through PENDING → BOOKED → PICKED_UP → IN_TRANSIT → DELIVERED / RETURNED lifecycle.

**SR-SHP-004 (Tracking Events)**: Each shipment status change has a timestamp recorded in `shipment_events` table.

**SR-SHP-005 (Dispatch Notification)**: Courier dispatch triggers SMS/email notifications to customer.

---

## 3. Architecture Design

### 3.1 Module Overview

The shipping system consists of these modules:

| Module | Responsibility | Boundaries | Dependencies |
|--------|---------------|------------|--------------|
| **Shipment Manager** | Create, track, update shipment records | Manages shipment lifecycle | Inventory (stock release), Notification (dispatch alert) |
| **Courier Interface** | Abstract different courier APIs | Generic interface, provider adapters | Payment (fee calculation), Notification (pickup confirmation) |
| **Tracking Service** | Process tracking events from couriers | Event ingestion, state machine | Logging, Notification (customer update) |
| **Return Handler** | Process returns and refund workflow | Integration with refund module | Payment (refund processing) |
| **Shipping Cost Engine** | Calculate shipping costs | Rate calculation per courier/weight/zone | Courier interfaces |

### 3.2 State Machine

```
┌──────────────┐    ┌──────────────┐
│   SHIPPING   │───→│    BOOKED    │
│  PENDING     │    └──────┬───────┘
└──────────────┘           │
                           │ trigger
                           ↓
                    ┌──────┐ ┌──────────────┐
                    │ PICK │ │ IN_TRANSIT   │
                    │ EDUP│ └──────┬───────┘
                    └──┬───┘       │
                       │          │ trigger event
                       ↓          ↓
              ┌─────────┐    ┌──────────────┐
              │IN_TRANS │───→│ DELIVERED     │
              │ IT      │    │ OR RETURNED   │
              └─────────┘    └──────────────┘
```

### 3.3 Shipment Data Model

#### `shipments` Table

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `shipment_id` | UUID | PRIMARY KEY | PRIMARY KEY |
| `order_id` | UUID | FK to parent order | FK, NOT NULL |
| `store_order_id` | UUID | FK to store order | FK, NOT NULL |
| `courier_name` | Enum | Steadfast, Pathao, RedX | NOT NULL |
| `courier_tracking_code` | String | Provider-specific tracking ID | NOT NULL |
| `status` | Enum | pending, booked, picked_up, in_transit, delivered, returned | DEFAULT pending |
| `shipping_cost` | Decimal | Total cost charged | CHECK > 0 |
| `weight_kg` | Decimal | Ordered weight estimate | CHECK >= 0 |
| `destination` | JSONB | Delivery address and details | NOT NULL |
| `notes` | Text | Dispatch notes | NULLABLE |
| `created_at` | Timestamp | Creation timestamp | NOT NULL |
| `updated_at` | Timestamp | Last update timestamp | NOT NULL |
| `created_by` | UUID | Admin who created shipment | FK, NOT NULL |

#### `shipment_events` Table

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `event_id` | UUID | PRIMARY KEY | PRIMARY KEY |
| `shipment_id` | UUID | FK to shipments | FK, NOT NULL |
| `event_type` | Enum | picked_up, in_transit, delivered, returned, exception | NOT NULL |
| `event_data` | JSONB | Event payload from courier | NOT NULL |
| `courier_ref` | String | Courier reference code | NOT NULL |
| `occurred_at` | Timestamp | Event time | NOT NULL |
| `processed_at` | Timestamp | System processed timestamp | NOT NULL |
| `created_at` | Timestamp | Record creation | NOT NULL |

---

## 4. Courier Provider Architecture

### 4.1 Courier Strategy Pattern

The system implements a strategy pattern for courier providers:

```
Courier Provider Registry:
├── SteadfastProvider
├── PathaoProvider
├── RedXProvider
└── FutureProviders...

Provider Interface:
def create_shipment(payload: ShipmentPayload) -> CourierShipmentResponse
def track_shipment(tracking_code: str) -> TrackingEvent[]
def cancel_shipment(tracking_code: str) -> bool
```

### 4.2 V1 Couriers

| Courier | Courier Name | V1 Support | Tracking Events | API Available |
|--------|-------------|-------------|-----------------|---------------|
| Steadfast | Steadfast | Manual selection + integration pending | Basic events | CONFIRMED (Pathao) |
| Pathao | Pathao | Manual selection + integration pending | Basic events | CONFIRMED (Pathao) |
| RedX | RedX | Manual selection + integration pending | Basic events | CONFIRMED (Pathao) |

### 4.3 Future Providers (Phase 2+)

| Provider | Phase | Notes |
|----------|-------|-------|
| Dialog Courier | Phase 2 | Bangladesh network |
| BD Blue | Phase 2 | Regional delivery |
| Simpler Mail | Phase 3 | Premium logistics |
| Local Pickup | Phase 3 | Self-service pickup |

---

## 5. Shipping Cost Calculation

### 5.1 Cost Formula

```
Shipping Cost = Base Fee + Weight Fee + Service Fee

Where:
- Base Fee = Fixed fee per carrier
- Weight Fee = Rate per kg × weight_kg (rounded up)
- Service Fee = Service charge based on destination zone

Example:
Steadfast:
  Base Fee = TBD (CONFIRMED)
  Weight Rate = TBD (Pending owner)
  Service Zone Charges = TBD
```

### 5.2 Cost Estimation Flow

```
1. Customer selects items → calculate total weight
2. Admin selects courier type at checkout
3. System calls CourierInterface.estimate_cost(weight, destination)
4. Courier calculates applicable fees
5. System displays estimated shipping cost
6. Customer confirms order → shipping cost becomes part of order total
7. Courier dispatched → actual charges recorded in `shipments.shipping_cost`
```

---

## 6. Shipment Flow at Checkout

### 6.1 Checkout Workflow

```
Checkout Flow:
1. Customer adds items to cart
2. Customer reviews cart → clicks "Place Order"
3. System validates stock availability (critical!)
4. Admin or system creates shipment record:
   a. Select courier (Steadfast/Pathao/RedX)
   b. Enter tracking code placeholder
   c. Calculate estimated shipping cost
5. Shipment created with status = 'pending'
6. Order placed with `total_cost` including shipping
7. Payment initiated
8. On successful payment:
   a. Shipment status = 'booked'
   b. Customer notified (SMS + email via notification engine)
```

### 6.2 Multi-Shipment Handling

For orders from multiple stores:

```
Multi-Shipment Scenario:
Parent Order {order_id=parent123}
├── Shipment #1 (from Store A) → stores[0]
├── Shipment #2 (from Store B) → stores[1]
└── Shipment #3 (from Warehouse) → warehouse

Each shipment is independent but shares:
- Same parent order reference
- Same customer reference
- Shared payment transaction
```

---

## 7. Return Process

### 7.1 Return Trigger Conditions

| Condition | Return Process | Requires Courier? |
|-----------|---------------|-------------------|
| Customer initiates return request | Follow standard return flow | Yes (for pickup) |
| Shipment status = 'delivered' AND within return window | Enable return button | Optional (self-service) |
| Admin initiates return for inspection | Admin process | Yes (for return pick-up) |

### 7.2 Return Process Flow

```
Return Process:
1. Customer requests return (account portal)
   - Select order and items
   - Reason and photos
   - Submits return request

2. Admin reviews:
   - Verifies order delivered
   - Verifies 7-day return window (Confirmed Business Decision)
   - Approves/rejects request

3. If approved:
   a. Admin dispatches courier for return
   b. Customer ships back (or scheduled pickup)
   c. Admin receives package
   d. Product inspected
   e. If passes: → Stock restoration + Refund
   f. If fails: → Reject refund, notify customer

4. Courier tracking activated for return
```

### 7.3 COD Return Handling

When COD is used:
- Courier must confirm collection
- No post-delivery return if COD not confirmed
- Cash handling requires admin attention

---

## 8. Notification Integration

### 8.1 Shipping Notification Events

| Event | Recipient | Channel | Content |
|-------|-----------|---------|---------|
| Shipment booked | Customer | SMS + Email | "Your order has been shipped via [Courier]" |
| Pick-up scheduled | Customer | SMS | "Your package is being collected by [Courier]" |
| In transit | Customer | SMS + App | "Your package is in transit, tracking available" |
| Delivered | Customer | SMS + Email + App | "Your package has been delivered" |
| Exception | Customer | Email + App | "Delivery issue, follow-up needed" |
| Return initiated | Admin | Internal | "Return request received" |
| Return accepted | Customer | SMS | "Return confirmed, shipping instructions sent" |
| Return complete | Admin | Internal | "Return received and processing" |

---

## 9. Integration Points

| Integration Point | Description |
|-------------------|-------------|
| `orders` table | Update order status based on shipment events |
| `store_orders` table | Track store-level shipping context |
| `shipments` table | Shipments CRUD operations |
| `shipment_events` table | Tracking event ingestion and processing |
| `inventory_balances` | Stock release when shipping confirmed |
| `notifications` table | Dispatch and tracking notifications |
| `payment_transactions` | Track shipping cost in payment |
| `refunds` table | Handle return refunds |
| Courier APIs | Real-time tracking and dispatch |
| SMS Gateway | Delivery status SMS |
| Email Provider | Delivery confirmation emails |

---

## 10. Acceptance Criteria

### 10.1 Functional Acceptance

- [ ] Multiple shipments per parent order supported
- [ ] Coucher selection (Steadfast/Pathao/RedX) functional
- [ ] Shipment state transitions correct
- [ ] Tracking events recorded in `shipment_events`
- [ ] Shipping cost calculated and displayed
- [ ] Return workflow integrated with refund process

### 10.2 Non-Functional Acceptance

- [ ] Courier integrations can be added without code changes (strategy pattern)
- [ ] Notification system works across all channels
- [ ] Performance: shipment creation < 2 seconds
- [ ] Database queries optimized for large volume
- [ ] All tracking events are immutable in audit log

---

## 11. Implementation Status

### 11.1 Current Status

- **Status**: Specified (SPECIFIED)
- **Implementation**: Not Implemented
- **Blocking**: Owner decisions (DEC-OWN-001, DEC-OWN-002, DEC-OWN-003, DEC-OWN-004)

### 11.2 Readiness

| Component | Status | Ready? |
|-----------|--------|--------|
| Architecture Design | ✅ Specified | Yes |
| Data Model | ✅ Specified | Yes |
| State Machine | ✅ Specified | Yes |
| Courier Strategy | ✅ Specified | Yes |
| Cost Calculation | ✅ Specified | Yes |
| Checkout Flow | ✅ Specified | Yes |
| Return Process | ✅ Specified | Yes |
| Courier Integrations | ❓ CONFIRMED (bKash + SSLCommerz) | No |
| Implementation | ❌ Not Implemented | No |

---

## 12. Final Notes

### 12.1 Mission Compliance
This document satisfies the mission requirement to:
- ✅ Document Shipping System Architecture
- ✅ Document Courier Integration Strategy
- ✅ Document Return and Refund Flow
- ✅ Document Shipment State Machine

### 12.2 Critical Blockers
- Courier API integration ready for Pathao
- Delivery fee calculation ready (flat fee per order)
- Implementation ready with Pathao and flat fee policy

### 12.3 Next Actions
1. Flat delivery fee policy configured
2. Pathao Courier integration configured
3. Database migration for shipment tables
4. Courier adapter implementations (Pathao)
5. Shipment service implementation
6. Courier dispatch UI in checkout
7. Tracking integration
8. Return workflow implementation

---

**Document ID**: DOC-AUR-165  
**Title**: Aura Bell — Shipping System Architecture  
**Version**: 1.0  
**Status**: Specified  
**Implementation Status**: Not Implemented  
**Last Updated**: 2026-11-08  
**Governance**: Aura Bell Documentation System  
**Compliance**: Mission Requirements - Shipping System  
**V1 Classification**: Future (until DEC-OWN-001 approved)  
**Blocking**: DEC-OWN-003 (Delivery Fee Policy), DEC-OWN-004 (Courier Partner Selection)

