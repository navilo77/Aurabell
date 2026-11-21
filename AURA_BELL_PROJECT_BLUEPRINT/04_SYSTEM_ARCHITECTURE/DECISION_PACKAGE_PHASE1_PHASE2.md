---
id: DOC-AUR-070
title: Aura Bell — Decision Package: Phase 1/2 Blocking Architecture Decisions
type: technical
status: draft
version: 0.1
language: Bangla with English technical terms
source: AB-SA-001, ADR-011, LOCAL_FIRST_SYNC_SPEC.md, OFFLINE_STRATEGY.md, IMPLEMENTATION_ROADMAP.md
last_updated: 2026-11-20
---

# Aura Bell — Decision Package: Phase 1/2 Blocking Architecture Decisions (ফেজ ১/২ ব্লকিং সিদ্ধান্ত প্যাকেজ)

> **স্ট্যাটাস**: Draft (প্রস্তাবিত)। এই নথিতে ফেজ ১ ও ২-এ ব্লকিং ৬টি architecture decision-এর detailed analysis রয়েছে। এই সিদ্ধান্তগুলো owner approval ছাড়া finalize করা যাবে না।
>
> **গাইডলাইন**: প্রতিটি সিদ্ধান্তে নিচের পাঁচ স্তর স্পষ্টভাবে পৃথক রাখা হয়েছে:
> 1. **APPROVED CONSTRAINTS** — অনুমোদিত আর্কিটেকচার থেকে আসা বাধ্যবাধকতা (পরিবর্তনযোগ্য নয়)
> 2. **CANDIDATE / RECOMMENDED DESIGN** — প্রস্তাবিত আর্কিটেকচারাল দিকনির্দেশনা (approve করা যেতে পারে direction হিসেবে)
> 3. **PARAMETERS REQUIRING VALIDATION** — যেসব numeric/configuration মান evidence/benchmark দিয়ে ঠিক করতে হবে
> 4. **UNRESOLVED OWNER DECISION** — যা owner-র explicit approval দরকার
> 5. **EVIDENCE/TESTING REQUIRED** — কোন data/testing দিয়ে final parameter ঠিক করা হবে

---

## Overview

IMPLEMENTATION_ROADMAP.md অনুযায়ী, Phase 1 (Project Setup & Foundations) এবং Phase 2 (Client-Side Local Persistence Infrastructure) শুরু করার আগে নিচের ৬টি unresolved decision approve করতে হবে:

| # | Decision | Blocks Phase | Source Document |
|---|---|---|---|
| D1 | **Retry Classification** (which HTTP statuses are retryable) | Fase 1, Fase 3 | LOCAL_FIRST_SYNC_SPEC.md §6.4 |
| D2 | **Retry Backoff Parameters** (base delay, max delay, jitter, max retries) | Fase 1, Fase 3 | LOCAL_FIRST_SYNC_SPEC.md §6.4 |
| D3 | **IndexedDB Quota Policy** (quota thresholds, priority rules, persistence) | Fase 1, Fase 2, Fase 4 | LOCAL_FIRST_SYNC_SPEC.md §5.3, OFFLINE_STRATEGY.md §10 |
| D4 | **Cache Eviction Mechanism** (LRU vs TTL vs priority-based, TTL values) | Fase 2, Fase 4 | LOCAL_FIRST_SYNC_SPEC.md §5.3, OFFLINE_STRATEGY.md §10.3 |
| D5 | **Token/Session Storage Mechanism** (IndexedDB vs memory vs cookies, auth offline) | Fase 2, Fase 5 | AUTHENTICATION_AUTHORIZATION.md §3, LOCAL_FIRST_SYNC_SPEC.md §8 |
| D6 | **Idempotency Key Generation Scheme** (format, client generation, persistence, server deduplication) | Fase 2, Fase 3 | LOCAL_FIRST_SYNC_SPEC.md §6.3 |

---

## Decision D1: Retry Classification

### 1. APPROVED CONSTRAINTS (অপরিবর্তনীয়)
- **Server-authoritative validation**: চেকআউট, পেমেন্ট, মূল্য, স্টক, অর্ডার কনফার্মেশন সবসময় সার্ভারে validate হবে (ADR-008, PROJECT_BRAIN ৩.১)
- **Idempotency required**: সব retryable request অবশ্যই valid idempotency key ধারণ করবে (LOCAL_FIRST_SYNC_SPEC.md §6.3)
- **Replay attack prevention**: Retry mechanism replay attack তৈরি করবে না (SECURITY_ARCHITECTURE.md §3)
- **Business-rule rejection permanent**: Validation failure (400/422), auth failure (401/403), conflict (409) retry করলে business logic violation হবে

### 2. CANDIDATE / RECOMMENDED DESIGN
Retryability is **operation/error-class dependent**, not a blanket HTTP status rule.

| Error Class | Conceptual Retryability | Rationale |
|---|---|---|
| **Transient server failure** (500, 502, 503, 504) | **Retryable** | Server 임시적 문제; time pass করলে solve হতে পারে |
| **Rate limiting / Retry-After** (429 with Retry-After) | **Retryable** | Server explicitly বলে কবে retry করতে হবে |
| **Authentication/session failure** (401, 403) | **Non-retryable** | Credentials/session invalid; retry করলে Same error; user action দরকার |
| **Validation failure** (400, 422) | **Non-retryable** | Client-side bug/bad input; retry করলে same error |
| **Conflict/concurrency** (409) | **Non-retryable** (server resolves) | Server-side conflict resolution; client retry not appropriate |
| **Permanent business-rule rejection** (4xx variants) | **Non-retryable** | Business logic reject; retry করলে semantic violation |

**Direction**: Client retry logic error-class based হবে, hard-coded status list নয়। Server `Retry-After` header precedence পাবে।

### 3. PARAMETERS REQUIRING VALIDATION
- Exact HTTP status → error-class mapping table
- Whether 429 without Retry-After is retryable
- Whether any 5xx should be non-retryable (e.g., 501 Not Implemented)

### 4. UNRESOLVED OWNER DECISION
- Approve the **error-class based retryability model** as architectural direction
- Defer exact status code mapping to implementation phase (configurable)
- Confirm server `Retry-After` takes precedence

### 5. EVIDENCE/TESTING REQUIRED
- Production error distribution analysis (what % of errors are transient vs permanent)
- Load test: retry behavior under thundering herd (synchronized reconnect)
- Security review: retry on auth failures implications

---

## Decision D2: Retry Backoff Parameters

### 1. APPROVED CONSTRAINTS
- **Exponential backoff required**: Linear retry causes thundering herd (LOCAL_FIRST_SYNC_SPEC.md §6.4)
- **Jitter mandatory**: Without jitter, synchronized retries create load spikes (SECURITY_ARCHITECTURE.md §3)
- **Max retry cap**: Infinite retry loop prevented; dead-letter/mutation timeout required
- **Server Retry-After precedence**: Server hint client backoff-től priority পাবে

### 2. CANDIDATE / RECOMMENDED DESIGN
Exponential backoff with jitter, configurable parameters.

| Parameter | Candidate Value (EXAMPLE ONLY) | Why This Range |
|---|---|---|
| **Base delay** | 1s | Fast recovery for transient blips; not so fast to hammer server |
| **Multiplier** | 2x (exponential) | Standard; 1s → 2s → 4s → 8s... |
| **Max delay** | 60s | Cap prevents excessively long waits; reasonable for user perception |
| **Jitter** | ±25% (full jitter or decorrelated) | Spreads synchronized retries; ±25% balances spread vs predictability |
| **Max retries** | 8 | ~3 min total before giving up; mutation then goes to dead-letter queue |

**Direction**: All parameters **configurable via client config/env**, not hardcoded.

### 3. PARAMETERS REQUIRING VALIDATION
| Parameter | Evidence Needed |
|---|---|
| Base delay | Server recovery time distribution (how fast 503 resolves) |
| Multiplier | Load test: 2x vs 1.5x vs 3x under sustained failure |
| Max delay | User tolerance threshold (when do they abandon?) |
| Jitter type | Full jitter vs decorrelated jitter vs equal jitter — which spreads load best |
| Max retries | Mutation timeout SLA: how long is "too long" for user to wait |

### 4. UNRESOLVED OWNER DECISION
- Approve **exponential backoff with jitter** as mandatory architectural pattern
- Defer exact numeric values to implementation phase (configurable)
- Confirm server `Retry-After` header overrides client backoff when present

### 5. EVIDENCE/TESTING REQUIRED
- Load test: simulate 1000 clients reconnecting after 5 min outage; measure server load with different backoff configs
- Chaos engineering: inject 503/504; measure mutation recovery time vs user abandonment
- Battery/network profiling on mobile: retry wake-up cost

---

## Decision D3: IndexedDB Quota Policy

### 1. APPROVED CONSTRAINTS
- **Pending mutations MUST survive eviction**: Any eviction strategy must preserve user-intended mutations (LOCAL_FIRST_SYNC_SPEC.md §5.3, OFFLINE_STRATEGY.md §10)
- **IndexedDB is cache, not business DB**: Data loss in cache acceptable; mutation loss NOT acceptable (PROJECT_BRAIN ৩.১)
- **Browser quota variable**: 50MB–250MB per origin typical; up to 50% disk in some browsers
- **navigator.storage.persist()**: Browser capability/strategy consideration, NOT a guaranteed storage contract; user permission required

### 2. CANDIDATE / RECOMMENDED DESIGN
**Priority-based quota management with mutation protection**

| Priority Tier | Data Type | Preservation Guarantee |
|---|---|---|
| **Critical (100)** | Pending mutations | Never evicted; separate object store |
| **High (50)** | User session/auth cache | Evicted only under extreme pressure |
| **Medium (10)** | Product catalog, categories | LRU + TTL eviction |
| **Low (5)** | Wishlist, recently viewed, analytics | First to evict |

**Conceptual requirement**: Mutations have higher preservation priority than disposable cache data.

**Direction**: Separate IndexedDB object stores for mutations vs cache; priority-based eviction within cache; `navigator.storage.persist()` requested but not relied upon.

### 3. PARAMETERS REQUIRING VALIDATION
| Parameter | Evidence Needed |
|---|---|
| Priority numeric values (100/50/10/5) | Relative sizing: mutation store vs catalog vs wishlist typical sizes |
| Mutation store max size | How many mutations can accumulate offline? (50? 500? 5000?) |
| `persist()` effectiveness | Browser support matrix; user grant rate; fallback when denied |
| Quota monitoring threshold | When to warn (80%? 90%?) and pause non-critical caching |

### 4. UNRESOLVED OWNER DECISION
- Approve **priority-based model with mutation protection** as architectural direction
- Defer exact priority numbers, quota thresholds, `persist()` strategy to implementation
- Confirm mutation store separation is mandatory

### 5. EVIDENCE/TESTING REQUIRED
- Browser quota analysis: typical available space per origin across Chrome/Firefox/Safari/Edge
- Mutation volume study: max pending mutations in realistic offline scenarios (hours/days offline)
- `persist()` grant rate measurement in target user base
- Eviction simulation under memory pressure

---

## Decision D4: Cache Eviction Mechanism

### 1. APPROVED CONSTRAINTS
- **Server is authoritative**: Cache never overrides server validation (ADR-008)
- **Stale price risk**: Cached prices MUST be invalidated before checkout (server re-validates anyway)
- **Mutations never evicted**: Decision D3 enforcement
- **Offline-first**: Cache is primary data source when offline

### 2. CANDIDATE / RECOMMENDED DESIGN
**LRU + TTL hybrid** with data-type-specific TTL

| Data Type | Candidate TTL (EXAMPLE) | Volatility | Freshness Requirement |
|---|---|---|---|
| Product catalog (list) | 24h | Low (daily updates) | Medium |
| Product details | 12h | Medium (price/stock changes) | High |
| Categories/brands | 48h | Very low | Low |
| Wishlist/recently viewed | Session-based | User-specific | N/A |

**Direction**: LRU for within-TTL eviction; expired TTL evicted first. TTL configurable per data type.

### 3. PARAMETERS REQUIRING VALIDATION
| Parameter | Evidence Needed |
|---|---|
| TTL values (24h/12h/48h) | Price change frequency analysis; stock change frequency; user tolerance for stale data |
| LRU vs LFU vs FIFO | Cache hit rate simulation with realistic access patterns |
| Background cleanup frequency | CPU/battery impact vs stale data window |
| Stale-while-revalidate pattern | Should expired cache serve stale data while fetching fresh? |

### 4. UNRESOLVED OWNER DECISION
- Approve **LRU + TTL hybrid** as architectural direction
- Defer exact TTL values to implementation (configurable per data type)
- Confirm stale-while-revalidate for offline UX

### 5. EVIDENCE/TESTING REQUIRED
- Catalog volatility measurement: how often do prices/stock change per day?
- Cache hit rate simulation: LRU vs LFU vs TTL-only with real access logs
- Offline UX test: user reaction to stale product details (wrong price shown briefly)
- Bandwidth savings: cache hit vs network fetch ratio

---

## Decision D5: Token Storage / Authentication

### 1. APPROVED CONSTRAINTS (CRITICAL — HIGHEST RISK)
- **Server-side authorization remains authoritative**: JWT validation always on server; client storage NEVER bypasses authz (AUTHENTICATION_AUTHORIZATION.md §3, SECURITY_ARCHITECTURE.md §3)
- **Offline cached data ≠ offline authorization**: Read-only cached user data may display; write/modify operations require server (LOCAL_FIRST_SYNC_SPEC.md §8)
- **Token/session storage must be secure**: XSS/CSRF/session theft resistant
- **Existing auth stack**: Supabase Auth (GoTrue) + FastAPI JWT validation + Next.js App Router/SSR

### 2. CANDIDATE / RECOMMENDED DESIGN
**Split storage: Short-lived access token in memory; refresh token in httpOnly cookie (SameSite=Strict, Secure)**

| Component | Storage | Lifetime | Offline Capability |
|---|---|---|---|
| **Access token (JWT)** | Memory (JS variable) | Short (15-30 min) | No — lost on tab close/refresh |
| **Refresh token** | httpOnly cookie (SameSite=Strict, Secure) | Long (7-30 days) | No — requires network for refresh |
| **Offline user data** | IndexedDB (cached profile, order history) | Per cache TTL | Read-only display only |

**Direction**: No offline authenticated API calls. Offline = read-only cached data. Full auth requires network.

### 3. COMPATIBILITY ANALYSIS (Must Be Validated Before Approval)

| Component | Compatibility Concern | Validation Needed |
|---|---|---|
| **Supabase Auth / GoTrue** | Issues access+refresh tokens; refresh rotation; session handling | Does GoTrue support httpOnly cookie for refresh? Custom claims? |
| **FastAPI JWT validation** | Validates access token signature, exp, iss; expects Bearer header | Works with memory-stored access token sent in Authorization header |
| **Next.js App Router / SSR** | Server components need access token; client components use memory | Token passing from server to client on hydration; cookie handling in middleware |
| **Browser refresh lifecycle** | Tab reload → memory cleared → access token lost → need refresh | Silent refresh via httpOnly cookie on app init; UX during refresh |
| **CSRF protection** | httpOnly cookie + SameSite=Strict mitigates CSRF; but need defense-in-depth | Double-submit cookie? Custom header? SameSite=Strict sufficient? |
| **Session expiration** | Access token 15-30 min; refresh token 7-30 days | Silent refresh before access token expiry; logout handling |
| **Logout/revocation** | Server must revoke refresh token; client clears memory + cookie | Supabase Admin API for revocation; client logout flow |
| **Multi-tab behavior** | Tab A gets new access token via refresh; Tab B has stale token | BroadcastChannel or storage event to sync access token across tabs |
| **Offline cached user data** | IndexedDB cached profile/order history | Read-only; no token needed; invalidated on logout |

### 4. PARAMETERS REQUIRING VALIDATION
| Parameter | Evidence Needed |
|---|---|
| Access token lifetime (15-30 min) | Security vs UX tradeoff; Supabase default; token rotation impact |
| Refresh token lifetime (7-30 days) | Security vs convenience; Supabase config; revocation granularity |
| httpOnly cookie settings | SameSite=Strict vs Lax; Secure; Domain; Path; Partitioned (CHIPS) |
| CSRF defense | SameSite=Strict enough? Need custom header? Double-submit pattern? |
| Silent refresh timing | When to proactively refresh (5 min before expiry? on 401?) |

### 5. UNRESOLVED OWNER DECISION
- Approve **split storage direction** (memory access + httpOnly refresh) as architectural approach
- **Defer exact implementation** until Supabase/Next.js/FastAPI compatibility validated
- **Explicitly do NOT approve** offline authenticated API capability (remains UNRESOLVED per LOCAL_FIRST_SYNC_SPEC.md §8)
- Confirm no new auth mechanism introduced without demonstrating compatibility with approved stack

### 6. EVIDENCE/TESTING REQUIRED
- Prototype: Supabase + FastAPI + Next.js with proposed storage; test login, refresh, logout, multi-tab, SSR
- Security audit: XSS scenario → token theft? CSRF scenario → forged request?
- Load test: concurrent sessions, refresh token rotation, revocation propagation
- Offline test: cached user data display without token; blocked write operations

---

## Decision D6: Idempotency Key Generation

### 1. APPROVED CONSTRAINTS
- **Every mutation sync request must carry idempotency key** (LOCAL_FIRST_SYNC_SPEC.md §6.3, SECURITY_ARCHITECTURE.md §3)
- **Client-generated, server-validated**: Server stores key + request hash for deduplication
- **Must survive offline→online, tab close, app restart**: Persisted with mutation in IndexedDB
- **Deduplication window**: Server retains keys for configurable TTL (24-72h typical)

### 2. CANDIDATE / RECOMMENDED DESIGN
**UUID v7 (RFC 9562) — Time-Ordered UUID**

| Aspect | Candidate Approach |
|---|---|
| **Format** | 128-bit: 48-bit timestamp (ms since epoch) + 74-bit random + version/variant |
| **Generation** | Client-side via `crypto.randomUUID()` with timestamp or small library |
| **Mutation persistence** | Stored with mutation in IndexedDB `mutations` object store |
| **Server deduplication** | Key + request body hash → if exists, return original response |
| **Retention/Expiry** | Server TTL: 24-72h (configurable); cleanup job |
| **Replay handling** | Same key + same body = return cached response; same key + different body = error |

**Direction**: UUID v7 as key format; client-generated; server TTL configurable.

### 3. PARAMETERS REQUIRING VALIDATION
| Parameter | Evidence Needed |
|---|---|
| UUID v7 library availability | Browser support for `crypto.randomUUID()` with timestamp; polyfill size |
| Server deduplication TTL (24-72h) | Mutation retry window vs storage cost; GDPR/data retention policy |
| Key collision probability | 2^74 random bits → negligible; but verify with birthday paradox at scale |
| Request body hash algorithm | SHA-256 vs Blake3 vs xxHash — performance vs collision resistance |

### 4. UNRESOLVED OWNER DECISION
- Approve **UUID v7 as idempotency key format** as architectural direction
- Defer client generation method, server TTL, storage implementation to implementation phase
- **Do not add UUID library dependency yet** — use native `crypto.randomUUID()` if sufficient

### 5. EVIDENCE/TESTING REQUIRED
- Prototype: client generates UUID v7, server stores/validates, deduplication works
- Load test: 10k concurrent mutations with duplicate keys → correct deduplication
- Offline test: mutations created offline, keys persisted, synced online, deduplication verified
- Library size impact: UUID v7 polyfill vs native crypto API

---

## Decision Dependencies

| Decision | Depends On | Affects |
|---|---|---|
| **D1 (Retry Classification)** | — | D2 (backoff applies to retryable errors), D6 (idempotency required for retryable) |
| **D2 (Retry Backoff)** | D1 (which errors retryable) | Mutation retry behavior, queue processing time |
| **D3 (IndexedDB Quota)** | — | D4 (cache eviction operates within quota), D5 (token storage if in IndexedDB), D6 (mutation store) |
| **D4 (Cache Eviction)** | D3 (quota budget) | Offline data freshness, bandwidth usage |
| **D5 (Token Storage)** | — | D1 (auth failures non-retryable), D4 (cached user data), D6 (authenticated mutations) |
| **D6 (Idempotency Key)** | D1 (retry needs idempotency), D3 (mutation store), D5 (auth context in mutation) | Sync protocol, server deduplication, mutation queue |

**Critical Path**: D3 → D4 (quota enables eviction), D1 → D2 → D6 (retry chain), D5 somewhat independent but affects offline auth behavior.

---

## Approval Model Summary

| Decision | What Can Be Approved Now (Direction) | What Must Remain TBD | Evidence Required Before Final Params | Finalization Phase |
|---|---|---|---|---|
| **D1: Retry Classification** | Error-class based model (not blanket status list) | Exact HTTP status → error-class mapping | Production error distribution; security review | Fase 3 (server-side retry middleware) |
| **D2: Retry Backoff** | Exponential backoff + jitter mandatory; configurable | Base delay, multiplier, max delay, jitter %, max retries | Load test under thundering herd; user tolerance | Fase 3 (retry middleware config) |
| **D3: IndexedDB Quota** | Priority-based with mutation protection; separate stores | Priority numbers, quota thresholds, `persist()` strategy | Browser quota analysis; mutation volume study | Fase 2 (IndexedDB schema) |
| **D4: Cache Eviction** | LRU + TTL hybrid; per-data-type TTL | TTL values (24h/12h/48h), stale-while-revalidate | Price volatility data; cache hit rate simulation | Fase 2 (cache layer) |
| **D5: Token Storage** | Split storage (memory access + httpOnly refresh); no offline auth | Exact cookie settings, CSRF defense, Supabase/Next.js compatibility | Prototype integration test; security audit | Fase 5 (auth management) |
| **D6: Idempotency Key** | UUID v7 format; client-generated; server TTL configurable | Generation method, server TTL, dedup storage | Prototype deduplication; library size impact | Fase 2 (mutation queue) |

---

## Next Steps

1. **Owner reviews** each D1–D6 decision package
2. **Owner provides** explicit approval/modification for **architectural direction only** (not numeric parameters)
3. **Document approved directions** as design notes (NOT ADRs yet — ADRs created when parameters finalized)
4. **Update** `LOCAL_FIRST_SYNC_SPEC.md`, `OFFLINE_STRATEGY.md`, `IMPLEMENTATION_ROADMAP.md` with approved directions
5. **Only then** proceed to Phase 1 detailed task breakdown

---

**STOP — WAITING FOR OWNER APPROVAL ON ARCHITECTURAL DIRECTIONS FOR D1–D6**

*Decision Package version: 0.1 | Status: DRAFT | Last updated: 2026-11-20*

---

**Scope Validation:**
- ✅ No source code modified
- ✅ No dependencies added
- ✅ No migrations created
- ✅ No API endpoints created
- ✅ No IndexedDB implemented
- ✅ No sync implemented
- ✅ No Service Worker created
- ✅ No ADRs created yet
- ✅ All numeric parameters marked TBD with validation path
- ✅ APPROVED CONSTRAINTS → CANDIDATE DESIGN → PARAMETERS TBD → UNRESOLVED DECISION separation maintained