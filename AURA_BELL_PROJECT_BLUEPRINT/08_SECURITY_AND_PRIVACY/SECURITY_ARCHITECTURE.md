---
id: DOC-AUR-100
title: Aura Bell — Security Architecture & Threat Model
type: security
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001 (Section 10, 13, 14)
last_updated: 2026-11-04
---

# Aura Bell — Security Architecture (সিকিউরিটি আর্কিটেকচার)

## ১. সিকিউরিটি ওভারভিউ
Aura Bell প্ল্যাটফর্মটি **Defense-in-Depth** নীতিমালার ওপর প্রতিষ্ঠিত। 

```text
ক্লায়েন্ট রিকোয়েস্ট (HTTPS / TLS 1.3)
      ⬇️
WAF / CDN (DDoS Mitigation & Rate Limiting)
      ⬇️
FastAPI Security Middleware (CORS, JWT Signature, RBAC)
      ⬇️
SQLAlchemy Parameterized Queries (No SQL Injection)
      ⬇️
PostgreSQL Row Level Security (RLS) & DB Constraints
```

---

## ২. মূল নিরাপত্তা স্তম্ভ
* **জিরো ট্রাস্ট ক্লায়েন্ট ইনপুট**: ক্লায়েন্ট থেকে আসা কোনো ডেটা সরাসরি কার্যকর করা যাবে না। Pydantic স্কিমা দিয়ে টাইপ ও রেঞ্জ ভ্যালিডেশন বাধ্যতামূলক।
* **ক্রিপ্টোগ্রাফিক ওয়েবহুক ভ্যালিডেশন**: গেটওয়ে প্রেরিত সিক্রেট টোকেন ও এইচএমএসি সিগনেচার যাচাই ব্যতীত পেমেন্ট আপডেট গ্রহণ করা সম্পূর্ণ নিষিদ্ধ।
* **সিক্রেট কি বিচ্ছিন্নকরণ**: Supabase `service_role` সিক্রেট কি কখনোই ফ্রন্টএন্ডে বা ক্লায়েন্ট বান্ডেলে যুক্ত করা যাবে না; এটি কেবল সুরক্ষিত ব্যাকএন্ড এনভায়রনমেন্ট ভ্যারিয়েবলে থাকবে।
