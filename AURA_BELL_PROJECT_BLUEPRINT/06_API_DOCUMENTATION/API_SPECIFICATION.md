---
id: DOC-AUR-080
title: Aura Bell — API Specification & Global Conventions
type: technical
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001 (Section 5)
last_updated: 2026-11-04
---

# Aura Bell — RESTful API Specification (এপিআই স্পেসিফিকেশন)

## ১. ওভারভিউ ও স্ট্যান্ডার্ড কনভেনশন
Aura Bell ব্যাকএন্ড সমস্ত ক্লায়েন্ট ও অ্যাপ্লিকেশনের সাথে যোগাযোগের জন্য একটি সুরক্ষিত, দ্রুত ও স্ট্যান্ডার্ড RESTful JSON API সরবরাহ করে।

* **Base URL**: `https://api.aurabell.com/api/v1` (Production) বা `http://localhost:8000/api/v1` (Development)
* **OpenAPI Documentation**: `/docs` (Swagger UI) এবং `/redoc` (ReDoc UI)
* **Headers**:
  - `Content-Type: application/json`
  - `Accept: application/json`
  - `Authorization: Bearer <JWT_TOKEN>` (প্রটেক্টেড এন্ডপয়েন্টের জন্য)
  - `Idempotency-Key: <UUID>` (পোস্ট মিউটেশন ও চেকআউটের জন্য)

---

## ২. স্ট্যান্ডার্ড রেসপন্স স্ট্রাকচার (Standard Response Envelopes)

### সফল রেসপন্স (Success Response)
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful",
  "meta": {
    "timestamp": "2026-11-04T12:00:00Z"
  }
}
```

### ত্রুটি রেসপন্স (Error Response)
```json
{
  "success": false,
  "error": {
    "code": "STOCK_RESERVATION_FAILED",
    "message": "নির্বাচিত পণ্যের পর্যাপ্ত স্টক অবশিষ্ট নেই।",
    "details": [
      {
        "field": "items[0].variant_id",
        "issue": "Requested quantity 2 exceeds available 1"
      }
    ]
  }
}
```
