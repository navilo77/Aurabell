# AURA BELL — কোডবেস সামগ্রিক অডিট রিপোর্ট (২০২৬-১১-২০)

**Document ID**: `DOC-AUR-175`  
**তারিখ**: ২০ নভেম্বর ২০২৬  
**সংস্করণ**: 1.0.0  
**স্ট্যাটাস**: চূড়ান্ত অডিট রিপোর্ট (Comprehensive Audit Report)  
**স্কোপ**: সম্পূর্ণ রিপোজিটরি (backend/, frontend/, docs/, AURA_BELL_PROJECT_BLUEPRINT/, scripts/, tests/, migrations)

---

## ১. নির্বাহী সারসংক্ষেপ (Executive Summary)

Aura Bell হলো একটি **Multi-Store E-commerce Platform** (Best Gadget + Aura Skin Care) যা **Modular Monolith** আর্কিটেকচারে তৈরি: **FastAPI (Python 3.11+)** ব্যাকএন্ড, **Supabase PostgreSQL 15+** ডাটাবেজ, **Next.js 14 (App Router) + TypeScript + Tailwind** ফ্রন্টএন্ড।

**বর্তমান অবস্থা**: Milestone 1–3 সম্পন্ন ( Infrastructure, Catalog/Pricing, Inventory/Ledger)। Milestone 4 (Cart, Checkout, Split-Orders, COD) **স্টেজড কোডে বাস্তবায়িত কিন্তু কমিট বা টেস্ট করা হয়নি**। Milestone 5–6 (Payments, Storefronts, Admin, Launch) এখনও পরিকল্পনা ফেজে।

| মেট্রিক | মান |
|---|---|
| **গিট ব্রাঞ্চ** | `main` (up to date with origin) |
| **স্টেজড ফাইল** | ১৫টি (cart, orders, auth, security, main, products, users, MILESTONES.md) |
| **অস্ট্রেড** | ২টি (`.gitignore`, `backend/requirements.txt`) |
| **অনট্র্যাকড** | ১৬+ (নতুন মাইগ্রেশন, টেস্ট ফাইল, ডক্স, ফ্রন্টএন্ড, স্ক্রিপ্টস) |
| **গত ২০ কমিট** | M3 ইনভেন্টরি বাস্তবায়ন পর্যন্ত (নভেম্বর ১৭) |
| **টেস্ট স্যুট** | ১১টি টেস্ট ফাইল (auth, inventory, pricing, stores, seed, users, products, categories — ৩টি নতুন অনট্র্যাকড) |

---

## ২. টেক স্ট্যাক ও আর্কিটেকচার ওভারভিউ

| লেয়ার | প্রযুক্তি | نسخা/নোট |
|---|---|---|
| **Backend Framework** | FastAPI | 0.110+, Pydantic v2, SQLAlchemy 2.0 Async |
| **Database** | Supabase PostgreSQL | 50 relational tables, RLS, enums, check constraints |
| **Auth** | Supabase GoTrue | JWT (RS256), OTP/Email, PKCE flow |
| **File Storage** | Supabase Storage | S3-compatible |
| **Background Jobs** | PostgreSQL Outbox Pattern | In-process worker (`main.py` lifespan) |
| **Frontend Framework** | Next.js 14 | App Router, React 18, TypeScript |
| **Styling** | Tailwind CSS | 3.4.1 |
| **State/Auth** | js-cookie + jwt-decode | Client-side token management |
| **Containerization** | Docker + docker-compose | Dev + Prod configs |
| **Testing** | pytest + pytest-asyncio | Supabase local (Docker) integration tests |

**কোর বিজনেস রুলস (১২টি অলঙ্ঘনীয়)** — `PROJECT_BRAIN.md` অনুযায়ী:
1. DB-Driven Stock Truth  
2. Server-Side Price Authority  
3. Mandatory Stock Reservation (15-min TTL)  
4. Three Independent State Engines (Order/Payment/Shipment)  
5. Webhook Signature & Idempotency  
6. Immutable Order Snapshots  
7. Store-Specific Return Policies  
8. Pre-Checkout Shipping Transparency  
9. Immutable Stock Movement Ledger  
10. Reconciliation & Financial Tracking  
11. Strict Modular Isolation  
12. No AI Autonomy for Financial Actions  

---

## ৩. সম্পন্ন ফিচার লিস্ট (Completed Features)

### Milestone 1: Infrastructure, Database & Auth ✅ (৪/৪ সাব-মাইলস্টোন)
| সাব-মাইলস্টোন | স্ট্যাটাস | ভেরিফিকেশন |
|---|---|---|
| M1.1: Backend Scaffold (FastAPI, Pydantic v2, SQLAlchemy 2.0 Async, Docker, `/api/v1/health`) | ✅ COMPLETED | `backend/app/main.py`, `backend/app/core/`, `Dockerfile`, `docker-compose.yml` |
| M1.2: Supabase DDL Migrations (50 tables, enums, triggers, 12 RLS policies) | ✅ COMPLETED | `backend/supabase/migrations/001-010` + 2 new secure RLS migrations (uncommitted) |
| M1.3: Core Identity & Auth (JWT middleware, RBAC `require_role`, Profile/Address CRUD) | ✅ COMPLETED | `backend/app/core/auth.py`, `backend/app/modules/auth/`, `backend/app/modules/users/` |
| M1.4: Base Seed Data (7 Roles, Central Warehouse, 2 Flagship Stores) | ✅ COMPLETED | `seed_dummy_data.py`, `verify_seed.py` |

### Milestone 2: Multi-Store Catalog & Pricing Engine ✅ (৪/৪)
| সাব-মাইলস্টোন | স্ট্যাটাস | ভেরিফিকেশন |
|---|---|---|
| M2.1: Store Management & Policy Engine | ✅ COMPLETED | `stores/router.py`, `stores/service.py`, `store_policies` table, 20/20 tests pass |
| M2.2: Category Hierarchy & Dynamic Attributes | ✅ COMPLETED | `categories/` module, parent-child tree, skincare/gadget attributes |
| M2.3: Product Catalog & Variant Generator | ✅ COMPLETED | `products/` module, SKU gen, Supabase Storage image upload |
| M2.4: Server-Side Pricing Engine | ✅ COMPLETED | `pricing/` module, BDT pricing, coupon validation, tamper-proof |

### Milestone 3: Concurrency-Safe Inventory & Warehouse Ledger ✅ (৫/৫)
| সাব-মাইলস্টোন | স্ট্যাটাস | ভেরিফিকেশন |
|---|---|---|
| M3.1: Warehouse Stock Balances | ✅ COMPLETED | `inventory_balances` table, zero negative stock constraint |
| M3.2: Atomic Stock Reservation (SELECT FOR UPDATE, 15-min TTL) | ✅ COMPLETED | `inventory_reservations` table, `create_reservation`/`consume_reservation` |
| M3.3: Automatic Cleanup Worker (1-min cron) | ✅ COMPLETED | `cleanup_expired_reservations()` in `main.py` lifespan |
| M3.4: Immutable Stock Movement Ledger | ✅ COMPLETED | `stock_movements` append-only audit trail |
| M3.5: Batch & Serial Tracking | ✅ COMPLETED | `product_batches` (skincare), `product_serials` (gadgets) |

### Milestone 4: Cart, Checkout & Split-Orders 🟡 **স্টেজড (Implementated in Staged Code, Not Committed/Tested)**
| সাব-মাইলস্টোন | স্ট্যাটাস | ফাইল |
|---|---|---|
| M4.1: Multi-Store Shared Cart | 🟡 STAGED | `backend/app/modules/cart/` (service, schema, router, `__init__`) |
| M4.2: Server-Side Checkout Calculation | 🟡 STAGED | `CartService.checkout_preview()`, flat delivery fee (70/120 BDT) |
| M4.3: Split Order Transaction Engine | 🟡 STAGED | `OrdersService.place_order()` atomic txn: parent order → store orders → item snapshots → stock reservations |
| M4.4: COD Fraud Prevention (4-digit SMS OTP) | 🟡 STAGED | `OrdersService.verify_cod_otp()`, in-memory OTP store (dev) |

> **নোট**: রুট `MILESTONES.md`-এ M4 ১০০% চেকবক্সে আছে, কিন্তু ব্লুপ্রিন্টের `MASTER_MILESTONES.md`-এ এখনও `PLANNED/PENDING`। কোড বাস্তবায়ন সম্পন্ন (স্টেজড), কিন্তু কমিট, টেস্ট বা প্রোডাকশন-রেডি হয়নি।

---

## ৪. বাকি/অসম্পূর্ণ টাস্ক লিস্ট (Pending / Incomplete Tasks)

### ৪.১ ক্রিটিক্যাল বাগ — ইতিমধ্যে ফিক্সড (স্টেজড কোডে)
| সমস্যা | ফাইল | ফিক্সড স্ট্যাটাস |
|---|---|---|
| UsersService: ভুল SQLAlchemy সিনট্যাক্স (String table names) → ১০০% রানটাইম ক্র্যাশ | `users/service.py` | ✅ `text()` SQL ব্যবহার করে ফিক্সড |
| ProductsService: `_generate_unique_slug` অসীম লুপ + NameError | `products/service.py` | ✅ লজিক ও ইনডেন্টেশন ফিক্সড |
| Security: `SUPABASE_URL` নাল চেক না থাকা → AttributeError | `core/security.py` | ✅ `_get_supabase_base_url()`-এ JWKSFetchError রেইজ করে ফিক্সড |
| Auth: `AuthService.logout` ব্রোকেন (সিঙ্গলটন ক্লায়েন্ট সেশন রিভোক করতে পারে না) | `auth/service.py` | ❌ **এখনও বাকি** (স্টেজড ডিফে নেই) |

### ৪.২ হাই প্রায়োরিটি (P1) — অবিলম্বে সমাধান প্রয়োজন
| # | ঝুঁকি / টাস্ক | ফাইল | প্রভাব |
|---|---|---|---|
| 1 | **ক্রস-স্টোর আইসোলেশন নেই**: User মডেলে `store_ids` নেই, `require_role` স্টোর স্কোপ যাচাই করে না | `core/auth.py`, `products/router.py`, `stores/router.py` | Store Manager অন্য স্টোরের ডেটা অ্যাক্সেস/ডিলিট করতে পারে (CRITICAL) |
| 2 | **ইনভেন্টরি রিলিজে FOR UPDATE লক অনুপস্থিত** | `inventory/service.py:424-452` | রেস কন্ডিশন / ডেডলক ঝুঁকি (HIGH) |
| 3 | **ব্যাকগ্রাউন্ড ক্লিনিং নীরব এক্সেপশন + N+1 কোয়েরি** | `main.py:48-51`, `inventory/service.py:473-526` | সাইলেন্ট ফেইলার, পিক আওয়ারে ডিবি চোক (HIGH) |
| 4 | **প্রোডাক্ট লিস্টিং N+1 কোয়েরি** (প্রতি প্রোডাক্টের জন্য আলাদা variants/images কোয়েরি) | `products/service.py:420-425` | ২০ প্রোডাক্টের পেজে ৪১টি রাউন্ডট্রিপ, ধীর লোড (HIGH) |
| 5 | **ডাটাবেজ কানেকশন পুল ডিফল্ট (pool_size=5)** | `core/database.py:20-24` | ১৫+ কনকারেন্ট রিকোয়েস্টে টাইমআউট (MEDIUM) |
| 6 | **অ্যাসিন্ক লুপে সিনক্রোনাস Supabase ক্লায়েন্ট** (`create_client` ব্লকিং) | `auth/service.py:30-31` | ইভেন্ট লুপ ব্লক, থ্রুপুট কমে যায় (MEDIUM) |
| 7 | **হার্ডকোডেড হোস্ট/CORS/সেশন সিক্রেট** (প্রোডাকশন-রেডি নন) | `main.py:85-116` | ডকার/প্রোডাকশনে রিকোয়েস্ট রিজেক্ট (MEDIUM) |

### ৪.৩ মিডিয়াম প্রায়োরিটি (P2)
| # | টাস্ক | ফাইল/এলাকা |
|---|---|---|
| 1 | `datetime.utcnow()` → `datetime.now(timezone.utc)` রূপান্তর | সার্ভিস ফাইলগুলো (`products`, `categories`, `stores`, `users`) |
| 2 | টেস্ট কভারেজ চালানো (নতুন `test_users.py`, `test_products.py`, `test_categories.py` অনট্র্যাকড) | `backend/tests/` |
| 3 | `AuthService.logout` ঠিক করা (টোকেন রিভোকেশন) | `auth/service.py` |
| 4 | ইন-মেমোরি OTP স্টোর → Redis বা DB-backed (প্রোডাকশনের জন্য) | `orders/service.py:_cod_otp_store` |

### ৪.৪ Milestone 5: Payment Adapters & Webhooks (০/৫) — **Not Started**
| সাব-মাইলস্টোন | স্ট্যাটাস |
|---|---|
| M5.1: Provider-Agnostic Payment Adapter Layer | 📋 Planned |
| M5.2: bKash Direct PGW Integration | 📋 Planned |
| M5.3: SSLCommerz Gateway Integration | 📋 Planned |
| M5.4: Cryptographic Webhook Receiver & Idempotency | 📋 Planned |
| M5.5: Refund & Financial Reconciliation | 📋 Planned |

### ৪.৫ Milestone 6: Storefronts, Admin & Launch (০/৫) — **Partial UI Only**
| সাব-মাইলস্টোন | স্ট্যাটাস | বর্তমান অবস্থা |
|---|---|---|
| M6.1: Next.js Multi-Storefront (Customer Web) | 🟡 Partial | Shop page, product grid, cart UI বাস্তবায়িত; থিমিং (tech/beauty) বাকি |
| M6.2: Customer Portal & Unified Checkout | 📋 Planned | Cart modal, checkout modal আংশিক; অর্ডার হিস্ট্রি, রিটার্ন ফর্ম নেই |
| M6.3: Admin Backoffice Operations Portal | 🟡 Partial | Store-admin (Products/Orders placeholder), Super-admin (Stores/Catalog UI) বাস্তবায়িত; ফুলফিলমেন্ট, Pathao ট্র্যাকিং, স্টক অ্যাডজাস্টমেন্ট নেই |
| M6.4: Transactional Outbox Worker (SMS/Email) | 📋 Planned | `outbox_events` টেবিল আছে, ওয়ার্কার বাস্তবায়িত নেই |
| M6.5: E2E Testing & Production Deployment | 📋 Planned | Vercel/Render/Supabase ডেপ্লয়মেন্ট কনফিগ নেই |

---

## ৫. গিট স্ট্যাটাস সারসংক্ষেপ (Git Status Summary)

```text
Current Branch: main (up to date with origin/main)
Remote: origin/main

Staged Changes (15 files - ready to commit):
  M MILESTONES.md                           (M4 চেকবক্স আপডেট)
  M backend/app/core/auth.py                (LEFT JOIN fix, User roles fetch)
  M backend/app/core/security.py            (SUPABASE_URL null guard)
  M backend/app/main.py                     (Cart/Orders router imports)
  A backend/app/modules/cart/__init__.py    (New M4.1 module)
  A backend/app/modules/cart/router.py      (Cart endpoints)
  A backend/app/modules/cart/schema.py      (Cart Pydantic schemas)
  A backend/app/modules/cart/service.py     (CartService: M4.1-M4.2)
  A backend/app/modules/orders/router.py    (Orders endpoints)
  A backend/app/modules/orders/schema.py    (Orders Pydantic schemas)
  A backend/app/modules/orders/service.py   (OrdersService: M4.3-M4.4)
  M backend/app/modules/products/service.py (Slug infinite-loop fix)
  M backend/app/modules/users/service.py    (text() SQL rewrite)

Unstaged Changes (2 files):
  M .gitignore                              (/lib/ line added)
  M backend/requirements.txt                (itsdangerous + pydantic[email])

Untracked Files (16+):
  backend/supabase/migrations/20261117174530_secure_catalog_rls.sql
  backend/supabase/migrations/20261117180011_secure_remaining_unrestricted_tables.sql
  backend/tests/test_categories.py          (New - comprehensive CRUD tests)
  backend/tests/test_products.py            (New - CRUD + slug regression)
  backend/tests/test_users.py               (New - Profile/Address CRUD)
  docs/DEVELOPMENT_LAUNCHER.md              (PowerShell dev launcher docs)
  frontend/                                 (Complete Next.js app)
  package-lock.json                         (Root lockfile)
  scripts/                                  (dev-start/stop/status.ps1 + tasks.json)
  seed_dummy_data.py / verify_seed.py       (Seed scripts)
  AURA_BELL_PROJECT_BLUEPRINT/09_AI_AGENT_SYSTEM/frontend/
  AURA_BELL_PROJECT_BLUEPRINT/10_DEVELOPMENT_WORKFLOW/MILESTONE_4_MASTER_EXECUTION_PLAN.md
  AURA_BELL_PROJECT_BLUEPRINT/11_QUALITY_ASSURANCE/CODEBASE_COMPREHENSIVE_AUDIT_REPORT.md
```

---

## ৬. মাইলস্টোন প্রগ্রেস রিপোর্ট (Milestone Progress Report)

| মাইলস্টোন | শিরোনাম | মোট সাব | সমাপ্ত | অগ্রগতি | স্ট্যাটাস |
|---|---|---|---|---|---|
| **M1** | Infrastructure, DB & Auth | ৪ | ৪ | ১০০% | ✅ **COMPLETED** |
| **M2** | Catalog & Pricing Engine | ৪ | ৪ | ১০০% | ✅ **COMPLETED** |
| **M3** | Inventory & Ledger | ৫ | ৫ | ১০০% | ✅ **COMPLETED** |
| **M4** | Cart, Checkout & Split-Orders | ৪ | ৪* | ১০০%* | 🟡 **STAGED (Uncommitted)** |
| **M5** | Payments & Webhooks | ৫ | ০ | ০% | 📋 **PLANNED** |
| **M6** | Storefronts, Admin & Launch | ৫ | ০ | ০% | 📋 **PLANNED (Partial UI)** |
| **Total** | **Full Platform** | **27** | **17** | **~63%** | — |

> \* M4 কোড বাস্তবায়িত (স্টেজড) কিন্তু কমিট, টেস্ট, ডকুমেন্টেশন বা প্রোডাকশন-রেডি **নয়**। ব্লুপ্রিন্ট `MASTER_MILESTONES.md` এখনও M4 কে `PLANNED` দেখাচ্ছে। দুটি ডকুমেন্টের মধ্যে অসঙ্গতি রয়েছে।

**সমগ্র প্রজেক্ট কমপ্লিশন অনুমান**: **~63%** (Backend core logic ~80%, Frontend ~40%, Payments 0%, DevOps/Launch 0%)

---

## ৭. কৌশলগত সুপারিশ (Strategic Recommendations)

### ৭.১ তাত্ক্ষণিক (This Week - P0/P1)
1. **স্টেজড M4 কোড কমিট ও টেস্ট চালান**: `git commit` স্টেজড ফাইলগুলো দিয়ে, তারপর `pytest backend/tests/` রান করুন (Supabase local দরকার)। M4 চেকবক্স আপডেট করুন।
2. **ক্রস-স্টোর আইসোলেশন বাস্তবায়ন**: `User` ডেটাক্লাসে `store_ids: list[str]` যুক্ত করুন; `get_current_user`-এ `user_roles.store_id` ফেচ করুন; সব অ্যাডমিন রাউটারে (`products`, `categories`, `stores`) `store_id` ভ্যালিডেশন এনফোর্স করুন। এটি **সিকিউরিটি ব্লকার**।
3. **ইনভেন্টরি রিলিজ/ক্লিনিং কনকারেন্সি ফিক্স**: `release_reservation`-এ `FOR UPDATE` লক; `cleanup_expired_reservations`-এ ব্যাচ CTE আপডেট + লগিং (`logger.exception`)।
4. **প্রোডাক্ট লিস্টিং N+1 অপটিমাইজ**: `LEFT JOIN` বা `IN` কোয়েরি দিয়ে variants/images ব্যাচ ফেচ করুন।

### ৭.২ ছোটমাধ্যমিক (Next 2 Weeks - P1/P2)
5. **কনফিগারেশন হার্ডকোডিং মুক্ত করুন**: `main.py`-এ `ALLOWED_HOSTS`, `CORS_ORIGINS`, `SESSION_SECRET_KEY`, `HTTPS_ONLY`_env থেকে লোড করুন (`core/config.py`-এ ফিল্ড যোগ করুন)।
6. **ডিবি কানেকশন পুল টিউন**: `core/database.py`-এ `pool_size=20, max_overflow=10, pool_timeout=30, pool_recycle=1800`।
7. **সিন্ক Supabase ক্লায়েন্ট অ্যাসিন্ক র‍্যাপার**: `auth/service.py`-এ `asyncio.to_thread` বা `httpx.AsyncClient` দিয়ে GoTrue REST API কল করুন।
8. **নতুন টেস্ট ফাইলগুলো কমিট ও CI-এ যোগ করুন**: `test_users.py`, `test_products.py`, `test_categories.py` রান ভেরিফাই করুন।

### ৭.৩ Milestone 5 এন্ট্রি ক্রাইটেরিয়া (M5 শুরু করার পূর্বে)
- উপরের P1 আইটেম ১–৪ সমাধান ও টেস্টেড থাকা।
- M4 কমিটেড, স্ট্রেস-টেস্টেড (রেস কন্ডিশন, ডুপ্লিকেট রিজার্ভেশন, প্রাইস টেম্পারিং)।
- ডকুমেন্টেশন সিঙ্ক করা (OpenAPI/Swagger, MILESTONES.md, MASTER_MILESTONES.md ইন-সিঙ্ক)।

### ৭.৪ আর্কিটেকচারাল গার্ডরেইলস
- **কোনো মাইক্রোসার্ভিস, Kafka, Redis, Kubernetes যুক্ত করা যাবে না** (SSOT নিষেধাজ্ঞা)।
- **ফ্রন্টএন্ডে `service_role` কী ব্যবহার নিষিদ্ধ**।
- **এআই এজেন্ট Фин্যানসিয়াল অ্যাকশন (রিফান্ড, ডিসকাউন্ট) নিতে পারবে না** মালিকের অনুমোদন ব্যতীত।

---

## ৮. পরবর্তী অ্যাকশন প্ল্যান (Next Action Plan for Junior Agents)

নিচে জুনিয়ার কোডিং এজেন্টদের জন্য **রেডি-টু-ইউজ প্রম্পট/ইনস্ট্রাকশন** দেয়া হলো। প্রতিটি টাস্ক স্বতন্ত্র ও পর্যায়ক্রমে এক্সিকিউট করা উচিত।

---

### 📋 TASK-01: Commit Staged M4 Code & Run Test Suite
**Objective**: স্টেজড ১৫টি ফাইল কমিট করুন, Supabase local চালু করে পুরো টেস্ট স্যুট পাস করান, MILESTONES.md আপডেট করুন।
```markdown
## Agent Prompt (Copy-Paste Ready)

You are a Junior Backend Engineer. Your task:

1. **Commit staged changes**:
   ```bash
   git add -A
   git commit -m "feat(M4): implement shared cart, split-order checkout & COD verification

   - Add cart module (M4.1): guest/user cart, merge, add/update/remove items, checkout preview
   - Add orders module (M4.2-M4.4): atomic split-order txn, server-side pricing, flat delivery fee, 4-digit COD OTP
   - Fix ProductsService slug infinite-loop (P0)
   - Fix UsersService SQLAlchemy text() queries (P0)
   - Fix Security SUPABASE_URL null guard (P0)
   - Fix Auth LEFT JOIN for new users (P1)
   "
   ```

2. **Start Supabase local & run tests**:
   ```bash
   cd backend
   supabase start
   pytest tests/ -v --tb=short
   ```

3. **Verify all 78+ tests pass** (including new test_users.py, test_products.py, test_categories.py).

4. **Update MILESTONES.md**: Mark M4 sub-milestones as `[x] COMPLETED` with today's date and `Verified By: <your-id>`.

5. **Sync MASTER_MILESTONES.md** in blueprint to match root MILESTONES.md.

**Acceptance Criteria**:
- `git status` clean (no staged/unstaged except .env)
- `pytest backend/tests/` → all pass (exit code 0)
- M4 checkboxes ticked in both milestone files
```

---

### 📋 TASK-02: Cross-Store Security Isolation (CRITICAL)
**Objective**: Store Manager যেন অন্য স্টোরের ডেটা অ্যাক্সেস/ম্যানিপুলেট করতে না পারে।
```markdown
## Agent Prompt (Copy-Paste Ready)

You are a Security Engineer. Implement multi-tenant store isolation:

**Files to modify**:
1. `backend/app/core/auth.py`:
   - Update `User` dataclass: add `store_ids: list[str]` field
   - In `get_current_user`: fetch `ur.store_id` from `user_roles` (can be NULL for global roles)
   - Populate `user.store_ids = [str(r.store_id) for r in rows if r.store_id is not None]`

2. `backend/app/core/auth.py` (require_role factory):
   - Add optional `store_id: str | None` parameter
   - If `store_id` provided, verify `store_id in user.store_ids` OR `super_admin` in roles
   - Raise 403 if not authorized for that store

3. All admin routers (`products/router.py`, `categories/router.py`, `stores/router.py`, `inventory/router.py`):
   - Change `require_role("store_manager", "super_admin")` to capture `store_id` from request (path/body/query)
   - Pass `store_id` to dependency: `Depends(require_role("store_manager", "super_admin", store_id=...))`

4. `backend/app/modules/products/router.py`:
   - In `create_product`, `update_product`, `delete_product`: validate `data.store_id` against user's store_ids

**Testing**:
- Write integration test: two stores, two managers, verify cross-store access denied (403)
- Verify super_admin can access all stores

**Acceptance Criteria**:
- Store Manager of Store A cannot CRUD products/categories of Store B (403)
- Super Admin can access all stores
- Customer role unaffected
```

---

### 📋 TASK-03: Inventory Concurrency Fixes (release_reservation + cleanup)
**Objective**: রেস কন্ডিশন ও সাইলেন্ট ফেইলার ঠিক করুন।
```markdown
## Agent Prompt (Copy-Paste Ready)

You are a Backend Engineer. Fix inventory concurrency bugs:

**1. `backend/app/modules/inventory/service.py` — `release_reservation` (lines 424-471)**:
   - Before UPDATE `inventory_balances`, lock the row:
     ```sql
     SELECT * FROM inventory_balances WHERE warehouse_id = :wid AND variant_id = :vid FOR UPDATE
     ```
   - Then perform the UPDATE and INSERT stock_movements in same transaction.

**2. `backend/app/modules/inventory/service.py` — `cleanup_expired_reservations` (lines 473-526)**:
   - Replace per-row loop with single CTE batch update:
     ```sql
     WITH expired AS (
       SELECT id, warehouse_id, variant_id, quantity
       FROM inventory_reservations
       WHERE status = 'active' AND expires_at <= NOW()
       FOR UPDATE SKIP LOCKED
     ),
     upd_bal AS (
       UPDATE inventory_balances b
       SET quantity_reserved = b.quantity_reserved - e.quantity, updated_at = NOW()
       FROM expired e
       WHERE b.warehouse_id = e.warehouse_id AND b.variant_id = e.variant_id
     ),
     upd_res AS (
       UPDATE inventory_reservations SET status = 'expired' FROM expired WHERE inventory_reservations.id = expired.id
     ),
     ins_mov AS (
       INSERT INTO stock_movements (warehouse_id, variant_id, movement_type, quantity_delta, reference_type, reference_id, note, created_by)
       SELECT warehouse_id, variant_id, 'released', quantity, 'inventory_reservations', id, 'Reservation expired (TTL)', NULL FROM expired
     )
     SELECT count(*) FROM expired;
     ```
   - Add `logger.exception("cleanup failed", exc_info=e)` in except block (import `logging`).

**3. `backend/app/main.py` — lifespan cleanup loop (lines 48-51)**:
   - Replace bare `except Exception: pass` with:
     ```python
     except asyncio.CancelledError:
         raise
     except Exception as e:
         logger.exception("Inventory cleanup worker error", exc_info=e)
     ```

**Testing**:
- Write concurrency test: simulate 2 parallel `release_reservation` + 1 `consume_reservation` on same variant
- Verify no negative `quantity_reserved`, no deadlock
- Trigger cleanup with 100 expired reservations → verify single query, <500ms

**Acceptance Criteria**:
- No race condition on balance release
- Cleanup uses single batched query
- All errors logged with traceback
```

---

### 📋 TASK-04: Product Listing N+1 Optimization
**Objective**: লিস্টিং এন্ডপয়েন্টে ১টি কোয়েরি + ব্যাচ ফেচ।
```markdown
## Agent Prompt (Copy-Paste Ready)

You are a Performance Engineer. Optimize `ProductsService.list_products` (lines 395-425):

**Current Problem**: Loop per product → `_get_variants` + `_get_images` = N×2 queries.

**Solution**:
1. Fetch all product IDs from main query.
2. Single query for variants: `WHERE product_id IN (...)` → map by `product_id`.
3. Single query for images: `WHERE product_id IN (...)` → map by `product_id`.
4. Build `ProductRead` objects in memory using maps.

**Code Sketch**:
```python
product_ids = [str(row["id"]) for row in rows]
# Batch fetch variants
variants_map = defaultdict(list)
if product_ids:
    v_result = await self.db.execute(text("""
        SELECT id, product_id, sku, variant_name, attributes, barcode, is_active
        FROM product_variants WHERE product_id = ANY(:ids)
    """), {"ids": product_ids})
    for v in v_result.mappings().all():
        variants_map[v["product_id"]].append(v)

# Batch fetch images
images_map = defaultdict(list)
if product_ids:
    i_result = await self.db.execute(text("""
        SELECT id, product_id, image_url, alt_text, sort_order, is_primary
        FROM product_images WHERE product_id = ANY(:ids) ORDER BY sort_order
    """), {"ids": product_ids})
    for img in i_result.mappings().all():
        images_map[img["product_id"]].append(img)

# Build response
products = []
for row in rows:
    pid = str(row["id"])
    products.append(self._row_to_read(row, variants_map.get(pid, []), images_map.get(pid, [])))
```

**Testing**:
- Add test: create 20 products with variants/images → call list_products → assert query count = 3 (via `caplog` or mock)
- Verify response shape unchanged

**Acceptance Criteria**:
- list_products executes exactly 3 queries (main + variants + images) regardless of page size
- Response time <100ms for 50 products (local DB)
- All existing product tests pass
```

---

### 📋 TASK-05: Configuration Externalization (Hardcoded → Env)
**Objective**: প্রোডাকশন-রেডি কনফিগারেশন।
```markdown
## Agent Prompt (Copy-Paste Ready)

You are a DevOps/Backend Engineer. Move all hardcoded values in `main.py` to `core/config.py`:

**1. `backend/app/core/config.py`** — Add fields:
```python
class Settings(BaseSettings):
    # ... existing ...
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1", "*.localhost", "testserver"]
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    SESSION_SECRET_KEY: str = "dev-secret-change-in-production"
    SESSION_HTTPS_ONLY: bool = False
    HSTS_ENABLED: bool = True
```

**2. `backend/app/main.py`** — Use settings:
```python
# TrustedHost
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# CORS
app.add_middleware(CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS, ...)

# Session
app.add_middleware(SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    https_only=settings.SESSION_HTTPS_ONLY, ...)

# HSTS middleware - conditional
if settings.HSTS_ENABLED:
    @app.middleware("http")
    async def add_hsts_header(...): ...
```

**3. Create `.env.example`** with all new vars documented.

**Testing**:
- Run with `.env` overrides → verify middleware config picks up values
- Test with `ALLOWED_HOSTS=["example.com"]` → request to other host rejected

**Acceptance Criteria**:
- No hardcoded hosts/origins/secrets in main.py
- All configurable via environment variables
- `.env.example` updated
```

---

### 📋 TASK-06: Database Connection Pool Tuning
**Objective**: প্রোডাকশন লোড হ্যান্ডলিং।
```markdown
## Agent Prompt (Copy-Paste Ready)

You are a Backend Engineer. Tune SQLAlchemy connection pool in `backend/app/core/database.py`:

**Modify `create_async_engine` call**:
```python
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,           # Base connections
    max_overflow=10,        # Extra under load
    pool_timeout=30,        # Seconds to wait for connection
    pool_recycle=1800,      # Recycle after 30 min (prevent stale)
    future=True,
)
```

**Testing**:
- Load test: 50 concurrent requests to `/api/v1/health` → no pool timeout
- Verify `pool_recycle` works (connections refreshed after 30 min)

**Acceptance Criteria**:
- Pool config explicit in code
- No `QueuePool limit exceeded` under 30 concurrent requests
```

---

### 📋 TASK-07: Async Supabase Client Wrapper
**Objective**: ইভেন্ট লুপ ব্লকিং রোধ।
```markdown
## Agent Prompt (Copy-Paste Ready)

You are a Backend Engineer. Wrap synchronous Supabase client calls in `auth/service.py` with `asyncio.to_thread`:

**Current (blocking)**:
```python
self._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
# ...
await self._client.auth.sign_in_with_password(...)
```

**Refactor**:
```python
import asyncio
from supabase import create_client

class AuthService:
    def __init__(self):
        self._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        self._admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

    async def _run_sync(self, func, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    async def login(self, credentials: UserLogin) -> Token:
        resp = await self._run_sync(
            lambda: self._client.auth.sign_in_with_password({
                "email": credentials.email, "password": credentials.password
            })
        )
        # ... rest unchanged
```

Apply to all methods: `register`, `request_otp`, `verify_otp`, `refresh_token`, `logout`, `admin_get_user`, `admin_delete_user`, `admin_update_user`.

**Testing**:
- Verify all auth endpoints still work
- Run 20 concurrent login requests → no event loop lag (monitor with `asyncio.get_event_loop().slow_callback_duration`)

**Acceptance Criteria**:
- No synchronous blocking calls in async methods
- All auth tests pass
- No performance regression
```

---

### 📋 TASK-08: New Test Files Commit & CI Integration
**Objective**: অনট্র্যাকড টেস্ট ফাইলগুলো কমিট ও যাচাই।
```markdown
## Agent Prompt (Copy-Paste Ready)

You are a QA Engineer. Commit and verify new test files:

**Files to commit**:
- `backend/tests/test_users.py`
- `backend/tests/test_products.py`
- `backend/tests/test_categories.py`

**Steps**:
1. `git add backend/tests/test_users.py backend/tests/test_products.py backend/tests/test_categories.py`
2. `git commit -m "test: add Users, Products, Categories test suites

   - test_users.py: Profile CRUD, Address CRUD (M1.3)
   - test_products.py: Product CRUD, SKU/slug, variants, images, slug regression
   - test_categories.py: Category CRUD, tree hierarchy, duplicate slug conflict
   "
3. Run full suite: `pytest backend/tests/ -v --tb=short`
3. Verify coverage: `pytest backend/tests/ --cov=app.modules --cov-report=term-missing`

**Acceptance Criteria**:
- All 3 new test files committed
- Full test suite passes (target: 78+ tests)
- Coverage for users/products/categories modules >80%
```

---

## ৯. nächস্টে ভাবতে হবে (What Comes After M4)

| ফেজ | মূল কাজ | এক্সপেক্টেড টাইমলাইন |
|---|---|---|
| **M5.1–M5.3** | Payment Adapter Layer + bKash + SSLCommerz Integration | ২-৩ সপ্তাহ |
| **M5.4** | HMAC Webhook Receiver, Idempotency, Reservation Finalization | ১ সপ্তাহ |
| **M5.5** | Refund Ledger + Expense Tracking | ১ সপ্তাহ |
| **M6.1** | Next.js Storefront Themes (Best Gadget tech / Aura Skin Care beauty) | ২ সপ্তাহ |
| **M6.2** | Customer Portal (Order Timeline, Invoice, 7-day Return) | ১-২ সপ্তাহ |
| **M6.3** | Admin Backoffice (Order Review, Pathao Tracking, Stock Adjust) | ২ সপ্তাহ |
| **M6.4** | Outbox Worker (SMS/Email via Greenweb/Elitbuzz) | ১ সপ্তাহ |
| **M6.5** | E2E Tests + Vercel/Render/Supabase Deploy + Release Sign-off | ১ সপ্তাহ |

**মোট আনুমানিক**: ১১-১৪ সপ্তাহ (M5–M6 সম্পূর্ণ করার জন্য) বর্তমান গতিতে।

---

## ১০. উপসংহার

Aura Bell প্রজেক্টের **ব্যাকএন্ড কোর (M1–M3) সুদৃঢ় ও প্রোডাকশন-রেডি আসল**। M4 বাস্তবায়ন সম্পন্ন কিন্তু **কমিট/টেস্ট বাকি**। principales ব্লকার বাগগুলো (P0) ইতিমধ্যে স্টেজড কোডে ফিক্সড। এখন **সবচেয়ে জরুরি ৩টি কাজ**:

1. **স্টেজড M4 কমিট + ফুল টেস্ট স্যুট পাস** (এই সপ্তাহে)
2. **ক্রস-স্টোর সিকিউরিটি আইসোলেশন বাস্তবায়ন** (ক্রিটিক্যাল — এই সপ্তাহে)
3. **ইনভেন্টরি কনকারেন্সি / N+1 / কনফিগারেশন / পুল টিউনিং** (পরবর্তী সপ্তাহে)

এগুলো完了 হলে M5 (Payments) এ ঢুকা নিরাপদ। ফ্রন্টএন্ডে Super/Store Admin UI স্কাফলড আছে, কিন্তু ফুলফিলমেন্ট ও কাস্টমার পোর্টাল বাকি।

---

**রিপোর্ট প্রস্তুতকর্তা**: Kilo Code (Principal Software Architect & Project Manager Persona)  
**তिथি**: ২০২৬-১১-২০  
**পরবর্তী পর্যালোচনা**: M4 কমিট ও টেস্ট সম্পন্ন হওয়ার পর