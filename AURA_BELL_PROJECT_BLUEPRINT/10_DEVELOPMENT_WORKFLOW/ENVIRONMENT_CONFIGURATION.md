---
id: DOC-AUR-126
title: Aura Bell — Environment Variables & Configuration
type: workflow
status: confirmed
version: 1.0
language: Bangla with English technical terms
source: AB-SA-001 (Section 12, 13)
last_updated: 2026-11-04
---

# Environment Configuration (পরিবেশ ভ্যারিয়েবল নির্দেশিকা)

## ১. ব্যাকএন্ড পরিবেশ ভ্যারিয়েবল (`backend/.env`)
```bash
# Environment
ENVIRONMENT=development # development | staging | production
DEBUG=True

# Database & Supabase
DATABASE_URL=postgresql+asyncpg://postgres:password@db.supabase.co:5432/postgres
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOi...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi... # STRICTLY BACKEND ONLY

# Security & JWT
JWT_SECRET_KEY=super-secret-hex-token
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Payment Gateway
PAYMENT_GATEWAY_PROVIDER=bkash # bkash | sslcommerz
PAYMENT_GATEWAY_APP_KEY=...
PAYMENT_GATEWAY_APP_SECRET=...
PAYMENT_WEBHOOK_SECRET=...
```

## ২. ফ্রন্টএন্ড পরিবেশ ভ্যারিয়েবল (`frontend/.env.local`)
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_SUPABASE_URL=https://xyz.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOi...
# কখনোই ফ্রন্টএন্ডে SERVICE_ROLE_KEY যোগ করবেন না!
```
