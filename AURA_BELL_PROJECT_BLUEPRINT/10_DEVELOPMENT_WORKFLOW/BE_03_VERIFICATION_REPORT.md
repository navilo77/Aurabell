# BE-03 Verification Report

**Date:** 2026-11-25  
**Milestone:** BE-03 — Checkout Address Reconciliation  
**Verdict:** `BE-03 COMPLETE — READY FOR APPROVAL`

---

## Changed Files

| File | Change |
|---|---|
| `backend/app/modules/orders/schema.py` | Added `address: OrderAddressCreate \| None` to `OrderCreate`; added `OrderAddressRead` schema; added `delivery_address` field to `OrderRead` |
| `backend/app/modules/orders/service.py` | Implemented address resolution (saved/inline/both/neither); replaced placeholder snapshot with actual resolved address; added delivery address fetch in `get_order` |
| `backend/tests/test_be03_checkout_address.py` | Created — 16 unit tests (schema validation, address resolution rules, snapshot immutability) |

---

## Database Changes

None. The `order_addresses` table already existed in migration `004_cart_orders.sql` with all required fields (recipient_name, phone, division, district, upazila, area, address_line, postal_code, address_type). No new migration needed. The snapshot mechanism reuses the existing table.

---

## API Contract

### Saved Address Request
```json
POST /api/v1/orders/checkout
{
  "cart_id": "uuid",
  "delivery_address_id": "address-uuid",
  "payment_method": "cod",
  "district": "Dhaka"
}
```
→ Service verifies address exists and belongs to user. Snapshots address fields into `order_addresses`.

### Inline Address Request
```json
POST /api/v1/orders/checkout
{
  "cart_id": "uuid",
  "address": {
    "recipient_name": "John Doe",
    "phone": "01700000000",
    "division": "Dhaka",
    "district": "Dhaka",
    "address_line": "123 Main St"
  },
  "payment_method": "cod"
}
```
→ Service validates inline address. Snapshots into `order_addresses`. No saved address required.

### Both Supplied
```json
{ "delivery_address_id": "addr-1", "address": {...} }
```
→ 400 `AMBIGUOUS_ADDRESS`: "Provide either delivery_address_id or address, not both"

### Neither Supplied
```json
{ "cart_id": "uuid", "payment_method": "cod" }
```
→ 400 `ADDRESS_REQUIRED`: "Delivery address is required (delivery_address_id or address)"

### Authorization Behavior
- Own saved address → 201 Created
- Another user's address ID → 404 `ADDRESS_NOT_FOUND` (no info leak)
- Nonexistent address ID → 404 `ADDRESS_NOT_FOUND`
- Unauthenticated request → 401 (handled by auth middleware)

### Order Response (includes delivery_address snapshot)
```json
{
  "id": "order-uuid",
  "order_number": "AB-20261125-XXXX",
  "order_status": "pending",
  "delivery_address": {
    "recipient_name": "John Doe",
    "phone": "01700000000",
    "division": "Dhaka",
    "district": "Dhaka",
    "address_line": "123 Main St",
    "address_type": "delivery"
  },
  "store_orders": [...],
  "order_items": [...]
}
```

---

## Snapshot Behavior

The delivery address is copied into the `order_addresses` table at order creation time. This is an **immutable snapshot**:

1. `order_addresses` has NO foreign key to `addresses` table — it's a standalone snapshot
2. If the saved address is later edited → existing order's `order_addresses` row is unchanged
3. If the saved address is later deleted → existing order's `order_addresses` row is unchanged
4. `get_order` reads from `order_addresses`, NOT from `addresses` — historical data is always preserved
5. The `OrderRead.delivery_address` field returns the snapshot, not a live reference

---

## Tests

| Category | Tests Added | Tests Executed | Passed | Failed | Blocked |
|---|---|---|---|---|---|
| BE-03 (checkout address) | 16 | 16 | 16 | 0 | 0 |
| BE-02 (catalog) | 10 | 10 | 10 | 0 | 0 |
| BE-01 (pagination) | 15 | 15 | 15 | 0 | 0 |
| Integration (DB) | 0 | 0 | 0 | 0 | 144 backend + 4 E2E (Supabase/Docker unavailable) |

**Test command:** `python -m pytest tests/test_be03_checkout_address.py tests/test_be02_catalog.py tests/test_be01_pagination.py -q` → 41 passed in 0.07s

---

## Security

- **Ownership validation:** `delivery_address_id` lookup includes `AND user_id = :user_id` — prevents using another user's address
- **No info leak:** Foreign/nonexistent address returns 404 `ADDRESS_NOT_FOUND` (same error for both cases)
- **Inline validation:** Pydantic `OrderAddressCreate` validates all fields (length constraints, required fields)
- **Ambiguity rejection:** Both address forms supplied → 400 `AMBIGUOUS_ADDRESS`
- **Missing address rejection:** Neither supplied → 400 `ADDRESS_REQUIRED`

---

## Scope

- **BE-04 through BE-08:** NOT implemented. Only BE-03 changes were made.
- **Auth, cart, offline sync:** Unchanged.

---

## BE-03 Status

`BE-03 COMPLETE — READY FOR APPROVAL`