# AI_MAP.md — Aura Bell Project Map for AI Assistants

> এই ফাইলটা AI (Kilo Code / ChatGPT) প্রথমে পড়বে।
> কাজ শুরুর আগে এই ফাইলের সাথে মিলিয়ে দেখো — নতুন কিছু বানানোর আগে এখানে খোঁজো।

---

## 1. Project Snapshot

- **Name:** Aura Bell — Multi-Store E-commerce Platform
- **Stores (V1):** Best Gadget (electronics), Aura Skin Care (skincare)
- **Stack:** FastAPI (Python) + Supabase (PostgreSQL) + Next.js
- **Architecture:** Modular Monolith
- **Region:** Bangladesh (BDT, bKash/Nagad later)
- **Current Milestone:** M1 — Infrastructure, Database & Auth (Ready to Start)

---

## 2. Folder Map

| Path | Purpose | Notes |
|---|---|---|
| `AURA_BELL_PROJECT_BLUEPRINT/` | Complete project documentation & blueprint | Source of truth for all specs |
| `AURA_BELL_PROJECT_BLUEPRINT/00_FOUNDATION/` | Vision, scope, principles, glossary | |
| `AURA_BELL_PROJECT_BLUEPRINT/02_BUSINESS_REQUIREMENTS/` | Business rules, customer/store requirements | |
| `AURA_BELL_PROJECT_BLUEPRINT/03_PRODUCT_REQUIREMENTS/` | PRDs for all domains | |
| `AURA_BELL_PROJECT_BLUEPRINT/04_SYSTEM_ARCHITECTURE/` | Architecture decisions, ADRs, DB/API architecture | |
| `AURA_BELL_PROJECT_BLUEPRINT/05_DATABASE/` | Schema, migrations strategy, relationships, validation | |
| `AURA_BELL_PROJECT_BLUEPRINT/06_API_DOCUMENTATION/` | API endpoints, specs, examples, error codes | |
| `AURA_BELL_PROJECT_BLUEPRINT/07_UI_UX_DESIGN/` | Design system, user flows, admin workflows | |
| `AURA_BELL_PROJECT_BLUEPRINT/08_SECURITY_AND_PRIVACY/` | Security architecture, auth, privacy, checklists | |
| `AURA_BELL_PROJECT_BLUEPRINT/09_AI_AGENT_SYSTEM/` | Agent roles, workflows, coding standards, Kilocode instructions | |
| `AURA_BELL_PROJECT_BLUEPRINT/10_DEVELOPMENT_WORKFLOW/` | Git workflow, milestones, roadmap, deployment, testing | |
| `AURA_BELL_PROJECT_BLUEPRINT/11_QUALITY_ASSURANCE/` | QA strategy, test cases, acceptance criteria | |
| `AURA_BELL_PROJECT_BLUEPRINT/12_PROJECT_GOVERNANCE/` | Risk register, decisions, reviews, change management | |
| `AURA_BELL_PROJECT_BLUEPRINT/13_REFERENCE/` | Technical refs, external deps, future features | |
| `backend/` | FastAPI app (to be created in M1.1) | main entry: `backend/app/main.py` |
| `backend/app/core/` | config, security, settings | `config.py`, `security.py` |
| `backend/app/modules/` | feature modules (modular monolith) | এক module = এক business area |
| `backend/app/modules/auth/` | login, register, JWT, password | router.py, service.py, schema.py |
| `backend/app/modules/users/` | user profile, addresses | |
| `backend/app/modules/products/` | product CRUD, categories | |
| `backend/app/modules/cart/` | shared cart logic | cross-store cart |
| `backend/app/modules/orders/` | Parent Order + Store Order logic | core business rule |
| `backend/app/modules/stores/` | store registry (Best Gadget, Aura Skin) | |
| `backend/app/modules/payments/` | payment gateway (later) | M3+ |
| `supabase/migrations/` | SQL migrations (43 tables) | never edit old file, always new |
| `supabase/rls/` | Row Level Security policies | security critical |
| `frontend/` | Next.js app (to be created in M6) | |
| `tests/` | pytest (backend), vitest (frontend) | |
| `docs/` | additional docs (if needed) | |

> ⚠️ উপরের path গুলো আপনার আসল repo অনুযায়ী ঠিক করে নিন। না মিললে এই ফাইল আপডেট করবেন।
> **Note:** `backend/`, `frontend/`, `supabase/` folders will be created during implementation (M1.1, M6.1).

---

## 3. Milestone Status

| # | Milestone | Status |
|---|---|---|
| M1 | Infrastructure, DB & Auth | ⏳ Ready to Start |
| M2 | Catalog & Pricing Engine | 📋 Planned |
| M3 | Inventory & Ledger | 📋 Planned |
| M4 | Cart, Checkout & Orders | 📋 Planned |
| M5 | Payments & Webhooks | 📋 Planned |
| M6 | Storefront, Admin & Launch | 📋 Planned |

**Rule:** কোনো কাজ শুরু করার আগে চেক করো সেটা কোন milestone-এর। বর্তমান milestone-এর বাইরে কোড লিখবে না।

---

## 4. Key Files (Read First)

কাজ শুরুর আগে এই ফাইলগুলো পড়ো:

1. `README.md` (if exists, else `AURA_BELL_PROJECT_BLUEPRINT/README.md`)
2. `MILESTONES.md` (deliverables + acceptance criteria)
3. `AI_MAP.md` (এই ফাইল)
4. যেই module-এ কাজ হবে, তার `router.py` + `service.py` + `schema.py` (M1.1+, not yet created)
5. `backend/app/core/config.py` (settings structure বুঝতে) (M1.1+, not yet created)
6. `supabase/migrations/` — সবচেয়ে শেষের migration (schema বোঝতে) (M1.2+, not yet created)
7. `AURA_BELL_PROJECT_BLUEPRINT/10_DEVELOPMENT_WORKFLOW/MASTER_MILESTONES.md` — detailed milestones
8. `AURA_BELL_PROJECT_BLUEPRINT/09_AI_AGENT_SYSTEM/KILO_CODE_INSTRUCTIONS.md` — AI agent rules
9. `AURA_BELL_PROJECT_BLUEPRINT/09_AI_AGENT_SYSTEM/PROJECT_WORKING_RULES.md` — working rules

---

## 5. Conventions (Follow Existing Pattern)

- **File naming:** snake_case (Python), PascalCase (React components)
- **Router pattern:** `router.py` → `service.py` → `schema.py` (একই module-এ)
- **Schema:** সব request/response Pydantic model দিয়ে, raw dict নয়
- **DB access:** Supabase client দিয়ে, string SQL concat কখনো না
- **Error handling:** custom exception → centralized handler (আলাদা `core/exceptions.py` থাকলে সেটাই)
- **Logging:** `logger.info` / `logger.error` — token/password কখনো log করবে না
- **Env:** সব config `.env` থেকে, `core/config.py`-তে Pydantic Settings দিয়ে লোড

---

## 6. Rules for AI (Non-Negotiable)

### ❌ করবে না
- `.env`, `.env.*`, `secrets/`, `*.key`, `*.pem` পড়া বা দেখা
- পুরোনো migration ফাইল edit করা — নতুন ফাইল বানাবে
- একবারে ৩+ ফাইল বদলানো (ছোট ছোট step-এ করবে)
- নতুন library যোগ করা — আগে জিজ্ঞেস করবে
- ফাইল delete/rename — আগে জিজ্ঞেস করবে
- `print()` দিয়ে debug — `logger` ব্যবহার করবে
- Hardcoded secret/token/password কোডে লেখা
- `user.role` বা permission চেক ছাড়া admin route বানানো

### ✅ করবে
- কাজ শুরুর আগে: AI_MAP + MILESTONES + relevant module পড়া
- Change-এর পর ২–৩ লাইনে বলা: কী করলে, কেন করলে
- Security impact ১ লাইনে বলা (rate limit? auth? input validation?)
- নতুন endpoint-এ auth + input validation যোগ করা বাধ্যতামূলক
- অস্পষ্ট হলে থামা + ১টা নির্দিষ্ট প্রশ্ন করা

---

## 7. Security Boundaries (সবসময় মনে রাখবে)

| Area | Rule |
|---|---|
| Password | bcrypt বা argon2 দিয়ে hash, plaintext নয় |
| JWT | secret `.env`-এ, short expiry (15m access + 7d refresh) |
| Supabase RLS | প্রতিটা user-facing table-এ RLS চালু, policy ছাড়া query নয় |
| SQL | parameterized only (Supabase client / ORM) |
| Input | সব Pydantic model দিয়ে validate |
| CORS | শুধু allowlist domain, `*` নয় production-এ |
| Rate limit | `/auth/login`, `/auth/register`-এ বাধ্যতামূলক |
| Logging | PII, token, password log করবে না |
| File upload | type + size validate (M2+) |

---

## 8. Common Tasks — Where to Look

| আমি চাই... | শুরু করব এখানে |
|---|---|
| Login/register ঠিক করা | `backend/app/modules/auth/` (M1.3+) |
| নতুন DB table | `supabase/migrations/` (নতুন ফাইল) (M1.2+) |
| Multi-store order logic | `backend/app/modules/orders/` (M4+) |
| RLS policy লিখতে | `supabase/rls/` (M1.2+) |
| Frontend page | `frontend/app/` (M6+) |
| Test লিখতে | `tests/` (backend), component-এর পাশে (frontend) |
| Business requirements | `AURA_BELL_PROJECT_BLUEPRINT/02_BUSINESS_REQUIREMENTS/` |
| Product requirements | `AURA_BELL_PROJECT_BLUEPRINT/03_PRODUCT_REQUIREMENTS/` |
| Architecture decisions | `AURA_BELL_PROJECT_BLUEPRINT/04_SYSTEM_ARCHITECTURE/` |
| Database schema | `AURA_BELL_PROJECT_BLUEPRINT/05_DATABASE/` |
| API specification | `AURA_BELL_PROJECT_BLUEPRINT/06_API_DOCUMENTATION/` |

---

## 9. Quando Confused → Ask

অনুমান করবে না। এই ৩টা প্রশ্নের যেকোনোটা হলে থামো ও জিজ্ঞেস করো:
1. এই কাজটা কোন milestone-এর?
2. এই change কি existing schema/API ভাঙবে?
3. এখানে security impact কী?

---

_Last updated: 2026-11-12_
_Maintained by: Navilo_