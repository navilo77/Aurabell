---
id: DOC-AUR-063
title: Aura Bell — Backend Architecture (FastAPI & SQLAlchemy)
type: technical
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001 (Section 2, 4, 12)
last_updated: 2026-11-04
---

# Aura Bell — Backend Architecture (ব্যাকএন্ড আর্কিটেকচার)

## ১. ব্যাকএন্ড ডিজাইন প্যাটার্ন
FastAPI অ্যাপ্লিকেশনটি পরিষ্কার লেয়ার্ড আর্কিটেকচার (Layered Architecture) অনুসরণ করবে:

```text
HTTP Request
     ⬇️
API Router (/api/v1/...) [Pydantic Input Validation]
     ⬇️
Service Layer [Business Rules & Domain Logic]
     ⬇️
Repository Layer [SQLAlchemy / Database Queries]
     ⬇️
PostgreSQL Database (ACID Commit)
```

---

## ২. কোড ডিরেক্টরি কাঠামো
```text
backend/
├── app/
│   ├── core/                  # কনফিগ, ডাটাবেজ সেশন, সিকিউরিটি ও এরর হ্যান্ডলার
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── modules/               # ১১টি বিজনেস মডিউল
│   │   ├── identity/
│   │   ├── store/
│   │   ├── catalog/
│   │   ├── pricing/
│   │   ├── inventory/
│   │   ├── cart/
│   │   ├── order/
│   │   ├── payment/
│   │   ├── fulfillment/
│   │   ├── support/
│   │   └── reporting/
│   ├── workers/               # পোস্টগ্রেস আউটবক্স ব্যাকগ্রাউন্ড জবস
│   │   └── outbox_worker.py
│   └── main.py                # FastAPI অ্যাপ্লিকেশন এন্ট্রি পয়েন্ট
```
