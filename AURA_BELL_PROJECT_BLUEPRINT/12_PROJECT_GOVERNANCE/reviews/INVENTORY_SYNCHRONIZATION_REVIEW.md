# Aura Bell — Inventory Synchronization Review

**Review Date:** 2026-11-08  
**Reviewer:** Independent Architecture Reviewer  
**Focus:** Offline/online inventory synchronization, Bangladesh retail realities

---

## Current Inventory Architecture (Verified)

### Documented Coverage

| Document | Coverage |
|----------|----------|
| `INVENTORY_SYSTEM_ARCHITECTURE.md` (DOC-AUR-162) §4.1-4.4 | Stock availability, reservation, release, payment failure |
| `INVENTORY_SYSTEM_ARCHITECTURE.md` §6 | Batch tracking (skincare), Serial/IMEI tracking (gadgets) |
| `INVENTORY_SYSTEM_ARCHITECTURE.md` §7 | COD confirmation workflow (15-min TTL) |
| `INVENTORY_SYSTEM_ARCHITECTURE.md` §9 | Cancellation rules with stock restoration |
| `BUSINESS_RULES.md` (DOC-AUR-031) | RULE-AUR-001, 003, 009, 011 |
| `AB-PV-001` §5.4 | "Offline Sale হলে Admin Panel থেকে Stock Update" |

### Online Inventory Architecture (Strong)

| Component | Status | Coverage |
|-----------|--------|----------|
| **Real-time balances** | ✅ Specified | `inventory_balances` with `quantity_on_hand`, `quantity_reserved`, `quantity_available` |
| **Atomic reservations** | ✅ Specified | `SELECT FOR UPDATE`, TTL-based expiry (15 min) |
| **Immutable ledger** | ✅ Specified | `stock_movements` with movement types |
| **Batch/serial tracking** | ✅ Specified | `product_batches`, `product_serials` |
| **COD confirmation** | ✅ Specified | 15-min TTL, admin confirmation |
| **Cancellation restoration** | ✅ Specified | Stock restore on cancellation |
| **Concurrency control** | ✅ Specified | `SELECT FOR UPDATE`, DB constraints |

---

## Critical Offline Sales Gaps

### 1. No Offline Sales API

**Documented**: `AB-PV-001` §5.4: "Offline Sale হলে Admin Panel থেকে Stock Update"  
**Reality**: Only mentions "Admin Panel" — no API specification, no POS integration

| Missing | Impact |
|---------|--------|
| **Offline sale API endpoint** | No way for POS to record sales |
| **Offline sale stock reservation** | Walk-in sales bypass reservation system |
| **Offline sale COD handling** | Offline COD vs online COD not differentiated |
| **Offline sale staff workflow** | No staff role, no POS UI |

### 2. Race Condition: Online Order + Offline Sale

**Scenario**: Last unit of SKU-X. Online customer adds to cart → reservation created. Simultaneously, walk-in customer buys same SKU-X in store. Staff reduces stock via admin panel.

**Current State**:
- Online: Reservation created (`quantity_reserved++`)
- Offline: Admin directly reduces `quantity_on_hand`
- **Result**: Both succeed, stock goes negative or double-sold

**Root Cause**: No coordination between online reservation system and offline stock updates

### 3. No Offline Sale Conflict Resolution

| Missing | Required |
|---------|----------|
| **Optimistic locking for admin updates** | `SELECT FOR UPDATE` on `inventory_balances` for admin stock changes |
| **Offline sale reservation** | Staff must "reserve" before confirming walk-in sale |
| **Conflict notification** | Alert online customer if stock changed during checkout |
| **Compensation logic** | Timestamp-based priority? Manual review? |

### 4. No Offline Sale Audit Trail Requirements

| Missing | Required |
|---------|----------|
| Staff ID who made sale | `staff_id` on stock movement |
| Sale reference number | Invoice/receipt number |
| Payment method (cash/card/bKash) | Payment type on movement |
| Customer info (optional) | Customer phone/name for returns |
| Reason for manual adjustment | Damage, loss, count correction, sale |

### 5. No Offline Sale Stock Reservation

**Current**: Offline sale directly reduces `quantity_on_hand`  
**Required**: Offline sale should create `inventory_reservations` with short TTL (e.g., 5 min) or immediate `SALE` movement

### 6. No Staff Role for Offline Sales

**Current RBAC** (`AUTHENTICATION_AUTHORIZATION.md`): Anonymous, Customer, Support, Inventory Manager, Store Manager, Super Admin  
**Missing**: "Store Staff" role with permissions:
- Create offline sale (reduce stock)
- View own store inventory
- Process offline returns
- No access to online orders, payments, other stores

### 7. No Offline Sale Reconciliation

**Current**: Daily reconciliation only covers payments (`PAYMENT_RECONCILIATION.md`)  
**Missing**: Daily offline sales reconciliation:
- Physical count vs system
- Offline sales vs stock movements
- Cash collected vs offline sales
- Discrepancy investigation

---

## Bangladesh Retail Reality

| Factor | Bangladesh Reality | Architecture Gap |
|--------|-------------------|------------------|
| **Offline retail dominance** | 85%+ retail is offline | No POS integration |
| **Walk-in customers** | Significant for electronics/skincare | No walk-in workflow |
| **Staff-operated stores** | Staff manage inventory | No staff role |
| **Cash-heavy** | Cash payments common | Offline COD not differentiated |
| **Manual stock counts** | Daily/weekly physical counts | No count workflow |
| **Return to store** | Customers return to physical store | Offline return workflow missing |

---

## Race Condition Deep Dive

### Current Flow (Problematic)

```
Online Customer                          Walk-in Customer + Staff
─────────────────                          ───────────────────────
1. Add to cart (checks available)          
2. Checkout → SELECT FOR UPDATE            
3. quantity_available--, reserved++        
4. Order created, reservation created      
                                                    1. Staff checks stock (sees available)
                                                    2. Admin panel: reduce quantity_on_hand
                                                    3. Stock movement OUT created
5. Order complete, reservation → SALE      
                                                    (stock now negative or double-sold)
```

### Required Flow (Solution)

```
Online Customer                          Walk-in Customer + Staff
─────────────────                          ───────────────────────
1. Add to cart (checks available)          
2. Checkout → SELECT FOR UPDATE            
3. quantity_available--, reserved++        
4. Order created, reservation created      
                                                    1. Staff checks stock (sees reserved)
                                                    2. Staff creates OFFLINE RESERVATION
                                                    3. SELECT FOR UPDATE on balances
                                                    4. If available: reserved++ → SALE
                                                    5. If not: "Out of stock" shown
5. Order complete, reservation → SALE      
                                                    (stock consistent)
```

---

## Required Architecture Additions

### 1. Offline Sales API

```yaml
POST /api/v1/inventory/offline-sale
Authorization: Staff role + Store scope
Request:
  {
    "store_id": "uuid",
    "staff_id": "uuid",
    "items": [
      {"product_variant_id": "uuid", "quantity": 1, "serial_number": "IMEI123"}
    ],
    "payment_method": "cash|card|bkash",
    "reference_number": "INV-20261108-001",
    "customer_phone": "01XXXXXXXXX" (optional)
  }
Response:
  {
    "sale_id": "uuid",
    "movements": [...],
    "reservations_created": [...]
  }
```

### 2. Staff Role Addition

```yaml
Role: store_staff
Permissions:
  - inventory:read (own store)
  - inventory:offline_sale:create (own store)
  - inventory:offline_return:create (own store)
  - inventory:stock_count:create (own store)
  - NO: online orders, payments, other stores, admin
```

### 3. Optimistic Locking for Admin Stock Updates

```python
# Required for ALL admin stock mutations
async def update_stock(admin_user, variant_id, warehouse_id, delta, reason):
    async with db.transaction():
        # Lock the row
        balance = await db.fetchrow(
            "SELECT * FROM inventory_balances WHERE product_variant_id=$1 AND warehouse_id=$2 FOR UPDATE",
            variant_id, warehouse_id
        )
        # Check availability
        if balance['quantity_on_hand'] + delta < 0:
            raise InsufficientStockError()
        # Update
        await db.execute(
            "UPDATE inventory_balances SET quantity_on_hand = quantity_on_hand + $1 WHERE balance_id = $2",
            delta, balance['balance_id']
        )
        # Create movement
        await create_stock_movement(...)
```

### 4. Offline Sale Reservation Protocol

```python
async def create_offline_reservation(staff, variant_id, quantity, ttl_minutes=5):
    """Staff must reserve before confirming walk-in sale"""
    async with db.transaction():
        balance = await db.fetchrow(
            "SELECT * FROM inventory_balances WHERE product_variant_id=$1 FOR UPDATE",
            variant_id
        )
        if balance['quantity_available'] < quantity:
            raise InsufficientStockError()
        # Create reservation with short TTL
        reservation = await db.fetchrow("""
            INSERT INTO inventory_reservations (order_id, product_variant_id, quantity_reserved, expires_at, released_at, release_reason)
            VALUES (NULL, $1, $2, NOW() + INTERVAL '$3 minutes', NULL, 'OFFLINE_SALE_PENDING')
            RETURNING reservation_id
        """, variant_id, quantity, ttl_minutes)
        # Update balances
        await db.execute("UPDATE inventory_balances SET quantity_reserved = quantity_reserved + $1, quantity_available = quantity_available - $1 WHERE balance_id = $2", quantity, balance['balance_id'])
        # Log movement
        await create_stock_movement(movement_type='RESERVATION', ...)
        return reservation
```

---

## Required Owner Decisions

| Decision | Options | Recommendation |
|----------|---------|----------------|
| **Offline sales API scope** | V1: Admin panel only / V2: POS API | V1: Admin panel with staff workflow |
| **Staff role creation** | Yes/No | Yes — add `store_staff` role |
| **Offline sale reservation TTL** | 5 min / 10 min / Immediate sale | 5 min reservation → confirm |
| **Conflict resolution priority** | Online first / Offline first / Timestamp | Timestamp (first come) |
| **Offline sale reconciliation frequency** | Daily / Per shift / Real-time | Per shift |
| **Offline COD handling** | Same as online / Separate | Same (15-min TTL) |
| **Physical stock count workflow** | Manual entry / Barcode scanner | Barcode scanner (future) |

---

## Bangladesh-Specific Requirements

| Requirement | Description |
|-------------|-------------|
| **Bangla receipt printing** | Thermal printer integration for offline sales |
| **Cash drawer management** | Open/close tracking for staff |
| **Shift handover** | Stock count at shift change |
| **Damaged goods workflow** | Staff marks damaged → auto stock adjustment |
| **Expired batch handling** | Auto-alert for skincare near expiry |
| **IMEI verification** | Scan IMEI at sale, verify not duplicated |

---

## Verdict

**Inventory Synchronization: PARTIALLY ADDRESSED — HIGH RISK**

**What's Production-Ready**:
- Online inventory core (balances, reservations, ledger, batches/serials)
- Atomic reservations with TTL
- Immutable ledger with movement types
- Batch/serial tracking for skincare/gadgets
- COD confirmation, cancellation workflows

**What's NOT Production-Ready**:
1. **No offline sales API** — only "admin panel" mention
2. **No race condition handling** for online + offline concurrent sales
3. **No staff role** for offline operations
4. **No offline sale audit trail** requirements
4. **No offline sale reconciliation** process
5. **No staff workflow** for walk-in sales

**For Bangladesh where offline retail is 85%+ of market**, treating offline sales as an afterthought is a critical operational gap. The platform cannot launch with only online inventory management.

**Recommendation**: Add offline sales API, staff role, conflict resolution, and audit trail to V1 scope. At minimum, implement the admin panel offline sale workflow with proper locking and audit trail before launch.

---

**Document ID:** INVENTORY_SYNCHRONIZATION_REVIEW  
**Version:** 1.0  
**Status:** FINAL  
**Date:** 2026-11-08