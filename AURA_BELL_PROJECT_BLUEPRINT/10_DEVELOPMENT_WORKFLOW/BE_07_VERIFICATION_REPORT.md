# BE-07 Verification Report

**Date:** 2026-11-25  
**Milestone:** BE-07 — Payment Gateway (AmarPay)  
**Verdict:** `BE-07 IMPLEMENTED / BLOCKED FOR LIVE VERIFICATION`

---

## Audit Findings

### Existing (Reused)
- `payments`, `payment_transactions`, `payment_webhook_events`, `refunds` tables (migration 005)
- Order model and BE-04 order state machine
- BE-01 pagination
- Auth system (HttpOnly cookies, ES256 JWT) — unchanged
- Idempotency middleware (BE-01)

### Missing (Implemented)
- `payments` module (adapter, schema, service, router)
- AmarPay gateway adapter (sandbox + live)
- Payment initiation, verification, callback, IPN endpoints
- AmarPay contract documentation

### Needs Change
- None — all new module, no existing code modified except main.py registration

---

## AmarPay Contract (Verified)

### Environment
- **Sandbox:** `https://sandbox.aamarpay.com`
- **Live:** `https://secure.aamarpay.com`

### Initiation
- **Endpoint:** POST `{base_url}/jsonpost.php`
- **Content-Type:** application/json
- **Parameters:** store_id, signature_key, cus_name, cus_email, cus_phone, cus_add1, cus_add2, cus_city, cus_country, amount, tran_id, currency, success_url, fail_url, cancel_url, desc, opt_a/b/c, type="json"
- **Response:** `{ result: "true", payment_url: "..." }`

### Verification (Search Transaction)
- **Endpoint:** GET `{base_url}/api/v1/trxcheck/request.php?request_id=...&store_id=...&signature_key=...&type=json`
- **Response:** includes pay_status ("Successful"), status_code ("2" = success), amount, mer_txnid, pg_txnid

### IPN / Callback
- **Method:** HTTP POST to merchant's designated URL
- **Payload:** Transaction details (pg_txnid, mer_txnid, amount, pay_status, status_code, etc.)
- **Only successful transactions notified**
- Server-side verification via Search Transaction API is authoritative

### Status Mapping
| AmarPay | Internal |
|---|---|
| status_code "2" | paid |
| pay_status "Successful" | paid |
| pay_status "Failed"/"Cancelled" | failed |
| otherwise | pending |

---

## Changed Files

| File | Change |
|---|---|
| `backend/app/modules/payments/adapter.py` | Created — AmarPayGateway adapter |
| `backend/app/modules/payments/schema.py` | Created — payment schemas |
| `backend/app/modules/payments/service.py` | Created — PaymentService |
| `backend/app/modules/payments/router.py` | Created — payment router (8 endpoints) |
| `backend/app/main.py` | Registered payments_router |
| `backend/tests/test_be07_payment.py` | Created — 14 unit tests |

---

## API Endpoints

| Method | Path | Purpose | Auth |
|---|---|---|---|
| `POST` | `/api/v1/payments/initiate` | Initiate payment for order | Customer |
| `GET` | `/api/v1/payments/{payment_id}` | Get payment details | Owner |
| `POST` | `/api/v1/payments/{payment_id}/verify` | Verify payment server-side | Owner |
| `POST` | `/api/v1/payments/callback/success` | AmarPay success callback | Public |
| `POST` | `/api/v1/payments/callback/fail` | AmarPay fail callback | Public |
| `POST` | `/api/v1/payments/callback/cancel` | AmarPay cancel callback | Public |
| `POST` | `/api/v1/payments/ipn` | AmarPay IPN webhook | Public |

---

## Payment State Machine

```
pending → paid (via verified gateway confirmation)
pending → failed (via verified gateway failure)
paid → (immutable, no revert)
```

---

## Order Integration

- Payment success updates order status `pending → confirmed` via direct update (respecting BE-04 state machine)
- Failed/cancelled payment does NOT mark order as paid
- Amount derived from server-side order total, never from client

---

## Security

- No hardcoded credentials (verified by test)
- Config via env vars: AMARPAY_STORE_ID, AMARPAY_SIGNATURE_KEY, AMARPAY_BASE_URL, AMARPAY_ENVIRONMENT, APP_BASE_URL
- Customer can only access own payments (ownership via order.user_id)
- Amount manipulation rejected (server-side amount check)
- No secrets logged

---

## Idempotency / Replay Protection

- Existing pending payment reused on repeated initiation
- Already-paid payment not reverted on repeated verification
- Database UNIQUE constraint on (provider, provider_event_id) for webhook events

---

## Database

- Reused existing `payments`, `payment_transactions`, `payment_webhook_events`, `refunds` tables (migration 005)
- No new migrations required

---

## Tests

| Category | Tests | Passed |
|---|---|---|
| BE-07 | 14 | 14 |
| BE-01–BE-07 (combined) | 116 | 116 |

**Live AmarPay:** BLOCKED — merchant credentials unavailable

---

## Regression

- Auth: unchanged
- Cart: unchanged
- Checkout: unchanged
- Catalog: unchanged
- Orders: unchanged
- Admin: unchanged
- Community/Chat: unchanged

---

## Blockers

- **AmarPay live/sandbox integration test — BLOCKED** (merchant credentials unavailable)

---

## Scope

- BE-08: not implemented

---

## Final Decision

BE-07 IMPLEMENTED / BLOCKED FOR LIVE VERIFICATION