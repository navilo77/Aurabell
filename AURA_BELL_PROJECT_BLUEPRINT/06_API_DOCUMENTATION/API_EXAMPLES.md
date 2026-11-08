---
id: DOC-AUR-082
title: Aura Bell — API Request & Response Payload Examples
type: technical
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001 (Section 5, 6)
last_updated: 2026-11-04
---

# Aura Bell — API Request & Response Examples (পেলোড উদাহরণ)

## ১. চেকআউট রিকোয়েস্ট ও রেসপন্স (`POST /api/v1/checkout`)

### Request Headers
```http
POST /api/v1/checkout HTTP/1.1
Host: api.aurabell.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Idempotency-Key: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d
Content-Type: application/json
```

### Request Payload
```json
{
  "shipping_address_id": "8fa85f64-5717-4562-b3fc-2c963f66afa6",
  "billing_address_id": "8fa85f64-5717-4562-b3fc-2c963f66afa6",
  "payment_method": "cod",
  "customer_notes": "দয়া করে বিকাল ৫টার পর ডেলিভারি করবেন।"
}
```

### Success Response (201 Created)
```json
{
  "success": true,
  "data": {
    "order_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "order_number": "AB-20261104-0012",
    "total_amount": 3450.00,
    "currency": "BDT",
    "status": "PENDING",
    "payment_status": "PENDING",
    "store_orders": [
      {
        "store_order_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "store_slug": "best-gadget",
        "store_name": "Best Gadget",
        "subtotal": 2500.00,
        "shipping_fee": 70.00,
        "items_count": 1
      },
      {
        "store_order_id": "c9a646d3-9c61-4cd7-9f59-5fd6dd7d29c2",
        "store_slug": "aura-skin-care",
        "store_name": "Aura Skin Care",
        "subtotal": 850.00,
        "shipping_fee": 30.00,
        "items_count": 1
      }
    ],
    "created_at": "2026-11-04T12:00:00Z"
  },
  "message": "অর্ডারটি সফলভাবে তৈরি হয়েছে।"
}
```
