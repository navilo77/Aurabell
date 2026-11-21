---
id: DOC-AUR-069
title: Aura Bell — Implementation Roadmap (Hybrid Local-First)
type: technical
status: draft
version: 0.1
language: Bangla with English technical terms
source: AB-SA-001, ADR-011, LOCAL_FIRST_SYNC_SPEC.md, OFFLINE_STRATEGY.md
last_updated: 2026-11-20
---

# Aura Bell — Implementation Roadmap (হাইব্রিড লোকাল-ফার্স্ট ইমপ্লিমেন্টেশন রোডম্যাপ)

> **স্ট্যাটাস**: Draft (প্রস্তাবিত)। এই রোডম্যাপ প্রস্তাবিত ইমপ্লিমেন্টেশন প্ল্যানিং ডকুমেন্ট। ওনার অনুমোদন পাওয়ার আগে কোনো ইমপ্লিমেন্টেশন কাজ শুরু করা যাবে না। সার্ভিস কোডিং, ডাটাবেস মাইগ্রেশন, সিকিউরিটি কনফিগারেশন বা অ্যাপ্লিকেশন logic এখনো শুরু করা **নিষিদ্ধ**।

---

## ১. একচিত্র (Overview)

এই রোডম্যাপ Aura Bell-এর হাইব্রিড লোকাল-ফার্স্ট আর্কিটেকচারের **ইমপ্লিমেন্টেশন প্ল্যানিং** কভার করে। এটি চিহ্নিত করে— কোন ফেজগুলো থাকবে, ফেজের মধ্যে কোন dependency আছে, কোন unresolved architecture decision কোন ফেজে solve করতে হবে, কোন ফাইল/মডিউল প্রভাবিত হতে পারে, migration risk, rollback strategy, testing plan, security check, performance target, এবং offline/low-bandwidth consideration।

**এমনুপাকান(full) ডকুমেন্টেশন-ওনলি। কোড লেখা এখনো যাবে না।**

**শ্রেণিবিন্যাস:**
- **APPROVED ARCHITECTURE** → `PROJECT_BRAIN.md`, `ADR-011` (সার্ভার-অথরিটেটিভ, IndexedDB ক্যাশ নয় ডাটাবেজ, চেকআউট/পেমেন্ট সার্ভার-কেই)
- **APPROVED SPECIFICATION** → `LOCAL_FIRST_SYNC_SPEC.md`, `OFFLINE_STRATEGY.md` (সিঙ্ক কনসেপ্ট, কনফ্লিক্ট নীতিমালা, অফলাইন-রেডি vs সার্ভার-রিকোয়ার্ড মেট্রিক্স)
- **IMPLEMENTATION PLAN** → এই নথি (ফেজ, dependency, risk, decision gate, affected modules)
- **ACTUAL IMPLEMENTATION** → ভবিষ্যত ফেজ (এখনো শুরু হয়নি)

---

## ২. ইমপ্লিমেন্টেশন ফেজসমূহ (Implementation Phases)

### ফেজ ১: Project Setup & Foundations (Setup → Groundwork)

**উদ্দেশ্য**: Project environment setup, infrastructure preparation, foundation layer establish করা।

| Sub-task | Details |
|---|---|
| ১.১ | `package.json`, `requirements.txt` (Python), `next.config.js` (TS) সেটআপ |
| 1.২ | Supabase project creation, PostgreSQL database settings, RLS policies initial configuration |
| 1.৩ | `LOCAL_FIRST_SYNC_SPEC.md` ও `OFFLINE_STRATEGY.md` থেকে প্রযোজ্য configuration values extract করা (retry policy, offline-ready ops matrix, ইত্যাদি) |
| 1.৪ | CI/CD pipeline preliminary setup (GitHub Actions / GitLab CI) |
| 1.৫ | Project structure — `frontend/`, `backend/`, `shared/` module boundaries definitiva confirm করা |
| 1.৬ | **Unresolved decisions to resolve before Fase 2**: retry classification (5xx/4xx), exponential backoff parameters, IndexedDB quota policy, service worker trigger configuration |

### ফেজ ২: Client-Side Local Persistence Infrastructure (IndexedDB & State Management Setup)

**উদ্দেশ্য**: IndexedDB store setup, Zustand/Context integration, mutation queue infrastructure, offline-capable data layers setup।

| Sub-task | Details |
|---|---|
| 2.১ | IndexedDB schema design (object stores: catalog, cart, mutations, wishlist, recently-viewed) — **কনসেপচুয়াল ডিজাইন**; কখনোই finalized স্কিমা হবে না Phase 1-এ |
| 2.২ | Mutation Queue data structure — pending mutation objects with identifiers |
| 2.৩ | Zustand/Context store integration for client state management |
| 2.৪ | Offline-capable data fetching utilities (catalog API with IndexedDB fallback) |
| 2.৫ | `navigator.onLine` monitoring + offline UI indicator components |
| 2.৬ | **Unresolved decisions to resolve before Fase 3**: exact IndexedDB quota policy (LRU/other), cache eviction mechanism details, token storage mechanism (IndexedDB vs memory vs cookies), idempotency key generation scheme |

### ফেজ ৩: Server-Side Sync Infrastructure (Backend Mutation Sync Service)

**উদ্দেশ্য**: Backend mutation sync endpoints (conceptual/routes only), idempotency handling, retry-safe operations, conflict detection logic setup।

| Sub-task | Details |
|---|---|
| 3.১ | FastAPI routes conceptual setup for mutation sync — `/sync`, `/batch-sync` endpoints **documentation only**; কোনো request handling logic করব না |
| 3.২ | Idempotency key storage schema (PostgreSQL table design conceptual) — কোড লিখব না |
| 3.৩ | Retry middleware conceptual design (5xx → retry, 4xx → never retry route conceptual) |
| 3.৪ | Server-side conflict detection logic outline (business-critical = server authoritative, non-critical = merge/LWW conceptual) |
| 3.৫ | Mutation reconciliation service conceptual architecture (how client mutations merge with server state) |
| 3.৬ | **Unresolved decisions to resolve before Fase 4**: exact sync protocol (push/pull/delta), exact endpoints finalization, idempotency implementation details, circuit breaker configuration, failure fallover strategy |

### ফেজ ৪: Offline Strategy Integration (Connectivity Transitions & Caching Strategy)

**উদ্দেশ্য**: Online→Offline→Online transition handling, connectivity-aware UI, offline-ready ops implementation (limited scope)।

| Sub-task | Details |
|---|---|
| 4.১ | Connectivity-aware components (useOnlineStatus hook conceptual, offline indicator UI) |
| 4.২ | Offline-ready data display logic (catalog, product details, wishlist from IndexedDB cache) |
| 4.৩ | Checkout/payment blocking when offline (frontend guard logic) |
| 4.৪ | Session management offline handling conceptual (token retention/refresh rules) |
| 4.৫ | **Unresolved decisions to resolve before Fase 5**: Service Worker registration strategy, Background Sync API usage, exact offline mutation sync timing/frequency, multi-device sync strategy |
| 4.৬ | IndexedDB cache eviction policy finalization (must preserve pending mutations) |

### ফেজ ৫: Authentication & Session Management (Offline Auth Considerations)

**উদ্দেশ্য**: Auth state management, session expiry/refresh, offline user state handling (limited to read-only display)।

| Sub-task | Details |
|---|---|
| 5.১ | JWT token storage mechanism design conceptual (NOT finalized — IndexedDB/memory/cookie comparison, owner approval needed) |
| 5.২ | Session expiry/refresh logic conceptual (offline scenario rules undefined) |
| 5.৩ | Guest cart vs authenticated cart merge logic conceptual |
| 5.৪ | Multi-device auth state sync conceptual (how auth state syncs across devices) |
| 5.৫ | **Unresolved decisions**: final token storage mechanism decision, offline session retention policy, refresh token strategy in offline scenario |

### ফেজ ৬: Full Integration Testing (System-Level Integration)

**উদ্দেশ্য**: Integrated system testing, mutation sync end-to-end testing, offline scenario validation।

| Sub-task | Details |
|---|---|
| 6.১ | E2E test scenarios: online→offline→online mutation flow |
| 6.২ | Mutation lifecycle testing: create offline → sync → server validate → success/failure |
| 6.৩ | Conflict scenario testing: concurrent modifications across sessions |
| 6.৪ | Retry policy testing: 5xx retry behavior, 4xx no-retry behavior |
| 6.৫ | Offline-ready vs server-required ops validation matrix |
| 6.৬ | **Unresolved decisions**: exact sync protocol behavior, exact conflict resolution algorithms, token storage finalization |

### ফেজ ৭: Performance & Security Hardening (Production Readiness)

**উদ্দেশ্য**: Performance optimization, security hardening, production deployment preparation।

| Sub-task | Details |
|---|---|
| 7.১ | Performance benchmarking: IndexedDB read/write latency, sync operation timing |
| 7.২ | Security audit: IndexedDB data sensitivity, client-side state tampering prevention |
| 7.৩ | Rate limiting, input validation, CSP (Content Security Policy) setup |
| 7.৪ | Rollback strategy finalization for sync operations |
| 7.৫ | **Unresolved decisions**: Service Worker/BG Sync finalization, quota/eviction policy hardening, token storage mechanism finalization |

### ফেজ ৮: Production Deployment (Optional — depends on owner)

| Sub-task | Details |
|---|---|
| 8.১ | Production deployment checklist |
| 8.২ | Monitoring & logging setup for sync operations |
| 8.৩ | Disaster recovery plan for mutation data loss scenarios |

---

## ৩. ফেজগুলোর মধ্যে Dependency (Dependencies Between Phases)

```
Fase 1 → Fase 2 → Fase 3 → Fase 4 → Fase 5 → Fase 6 → Fase 7 → Fase 8 (Optional)
```

### Chained Dependencies:

| Dependencies | Reason |
|---|---|
| **Fase 1 complete → Fase 2 start** | Project setup must finish before client-side IndexedDB infrastructure can be configured |
| **Fase 2 complete → Fase 3 start** | Client-side mutation queue and state management must exist before backend sync infrastructure can integrate |
| **Fase 3 complete → Fase 4 start** | Backend sync service conceptual routes must be outlined before offline transition logic can reference them |
| **Fase 4 complete → Fase 5 start** | Offline transition handling must have defined connectivity-aware components before auth considerations can be layered on |
| **Fase 5 complete → Fase 6 start** | Auth state management conceptual foundation must exist before full integration testing can properly validate auth-aware sync flows |
| **Fase 6 complete → Fase 7 start** | Integrated system testing must pass before performance/security hardening can be meaningfully measured |
| **Fase 7 complete → Fase 8 optional** | Production readiness must be established before optional deployment considerations |

### Critical Path:

```
Fase 1 → Fase 2 → Fase 3 → Fase 6 → Fase 7
```

(Fase 3, 4, 5 are parallel-ish but must complete before Fase 6)

---

## ৪. সম্ভাব্যভাবে প্রভাবিত ফাইল/Module (Files/Modules Likely Affected)

| Module/File | Expected Changes | Risk Level |
|---|---|---|
| `frontend/lib/api.ts` / `frontend/lib/indexeddb.ts` | IndexedDB wrapper utilities, mutation queue client functions (conceptual design only) | Medium — structure changes possible |
| `frontend/store/` (Zustand/Context) | Client state management integration with local persistence | Medium — API surface changes |
| `backend/app/modules/**/` (11 modules) | Sync request handlers conceptual routes only (no logic) | Medium — route definitions |
| `backend/app/workers/` (outbox_worker.py) | Mutation sync worker conceptual architecture (no code) | Low — mostly config |
| `shared/types.ts` / `shared/constants.ts` | Offline-ready / server-required ops type definitions (constants only) | Low — type definitions |
| `frontend/components/**` | Offline-aware UI components, connectivity indicators (UI-only) | Low — component library |
| `DOCUMENTATION/` (all .md files in 04_SYSTEM_ARCHITECTURE/) | Version bumps, content updates, classification legend updates | Low — docs only |

---

## ৫. মাইগ্রেশন রিস্ক (Migration Risks)

| Risk | Description | Mitigation (Conceptual / TBD) |
|---|---|---|
| **Risk-1**: Data loss during sync transition | If mutations are lost during offline→online sync, pending user intent (cart additions, wishlist edits) may be permanently lost | Implement retry policy with exponential backoff (**proposed default**); ensure every sync attempt logged; maintain local retry queue until server acknowledgment |
| **Risk-2**: IndexedDB quota overflow | If cache eviction policy not properly designed, important mutation data may be evicted before sync | **Unresolved**: quota policy must be designed to preserve pending mutations; any eviction strategy must have safeguard for mutation priority |
| **Risk-3**: Stale data serving from cache | If offline-ready data serves stale catalog/product details, user experience degrades; potentially incorrect pricing display | Offline-ready ops clearly delimited from server-required ops; catalog data has explicit expiry/invalidation strategy (**proposed/TBD**) |
| **Risk-4**: Conflict resolution incorrectness | If merge/LWW strategy chosen incorrectly, data inconsistencies appear (especially cart state across devices) | **Unresolved**: conflict detection/merge algorithms not finalized; business-critical → server authoritative rule must be strictly enforced |
| **Risk-5**: Auth token tampering/Stale session | If offline token storage mechanism chosen incorrectly, sessions may be hijacked or users locked out | **Unresolved**: token storage mechanism (IndexedDB/memory/cookie) not finalized; server-side authz always authoritative |
| **Risk-6**: Sync endpoint incompatibility | If sync endpoints change between versions, client mutations may fail to sync | Versioning strategy (API versioning `/api/v1`, mutation version stamps) must be designed from Fase 3 |

---

## ৬. রোলব্যাক কনসিডারেশন (Rollback Strategy)

| Scenario | Rollback Approach |
|---|---|
| **Mutation sync failure** | If server sync fails, keep mutation in local retry queue; do NOT remove from local queue until server acknowledgment; UI shows "retrying" status |
| **IndexedDB corruption** | If IndexedDB data appears corrupted, fallback to server data only; UI disables offline features temporarily; restore from server backup |
| **Sync endpoint change** | If API version changes, maintain backward-compatible old endpoints temporarily; migration script to re-process pending local mutations |
| **Auth token mechanism change** | If token storage mechanism changes (e.g., IndexedDB → cookies), migrate stored tokens; old tokens valid until expiry; new login forces fresh token storage update |
| **Conflict resolution strategy change** | If merge strategy changes, re-concile all pending mutations using new strategy; maintain old resolution data temporarily for rollback |
| **Quota policy change** | If IndexedDB quota/eviction policy changes, run migration to adjust existing stored data; ensure pending mutations preserved during migration |

---

## ৭. টেস্টিং স্ট্র্যাটেজি (Testing Strategy)

### 7.1 Unit Testing
- Mock IndexedDB operations; test mutation queue enqueue/dequeue logic
- Test retry policy logic (5xx → retry decision, 4xx → never retry)
- Test idempotency key generation and deduplication

### 7.2 Integration Testing
- **Online→Offline→Online mutation flow**: create mutation offline, go online, verify sync to server, verify server validation, verify local queue state
- **Conflict scenarios**: simulate concurrent modifications, verify conflict detection and resolution behavior
- **Retry behavior**: intentionally trigger 5xx/4xx from server, verify client retry/non-retry behavior per policy
- **Offline-ready vs server-required validation**: verify that checkout/payment blocked when offline; verify catalog browse works offline

### 7.3 E2E Testing (Playwright/Cypress)
- Full user journey: browse catalog → add to cart offline → go to checkout (blocked offline) → go online → checkout succeeds after server validation
- Multi-device cart sync: add item on device A, go offline on device B, verify state
- Session management: login, logout, token refresh scenarios
- Service Worker / Background Sync scenarios (if/when implemented)

### 7.4 Security Testing
- IndexedDB data sensitivity verification
- Client-side state tampering attempt verification
- Auth token storage mechanism verification (whatever is chosen)
- CSP, rate limiting, input validation verification

### 7.5 Performance Testing
- IndexedDB read/write latency measurement
- Sync operation timing measurement (**proposed default retry/backoff** as reference)
- Offline mode switch performance impact measurement

---

## ৮. নিরাপত্তা কনসিডারেশন (Security Considerations)

### 8.1 Client-Side Security
- **IndexedDB data never authoritative**: always treat as untrusted; never store sensitive data (payment details, auth tokens as final storage)
- **Client-side state tampering prevention**: all mutations validated server-side before commit
- **XSS prevention**: ensure IndexedDB data not injected into DOM without sanitization
- **CSP (Content Security Policy)**: proper CSP headers to prevent malicious JS execution

### 8.2 Server-Side Security
- **All mutations validated server-side**: no exception, even when client claims "offline-ready"
- **Idempotency key validation**: every sync request must have valid idempotency key; reject duplicates
- **Retry policy enforcement**: server must respect 4xx → never retry rule; 5xx retry with appropriate limits
- **Rate limiting on sync endpoints**: prevent sync storm from overwhelmed clients
- **Input validation on all sync requests**: prevent malicious mutation data injection

### 8.3 Authentication/Session Security (Conceptual Only)
- **Server-authoritative auth**: JWT validation always on server; client-side token storage mechanism decision does not reduce server auth requirement
- **Token storage mechanism**: whatever chosen (IndexedDB/memory/cookie) must not bypass server authorization
- **Offline session handling**: offline session/token retention policy undefined; server always re-authenticates on online return

### 8.4 Data Privacy
- **No sensitive data in IndexedDB**: catalog, product details, wishlist OK; payment, order state, auth tokens NOT in IndexedDB as authoritative store
- **Mutation data privacy**: sync requests contain only mutation identifiers and delta data; no personal identifiers beyond what's necessary

---

## ৯. পারফরম্যান্স কনসিডারেশন (Performance Considerations)

### 9.1 IndexedDB Performance
- **Read latency**: typical IndexedDB read operations ~1-5ms (local); ~10-50ms (persisted across sessions)
- **Write latency**: typical IndexedDB write operations ~1-3ms; batch writes more efficient
- **Quota management**: browser-dependent; must design eviction policy that works within common browser quotas (usually 50MB-250MB per origin)
- **Eviction performance**: LRU or other policy should have O(1) or O(log n) performance; must not block main thread during sync

### 9.2 Sync Performance
- **Proposed default retry**: exponential backoff (**proposed example**: starts at ~1s, doubles, max ~60s; jitter example ±25%) — **UNRESOLVED**, subject to owner approval
- **Batch sync**: preferred over individual mutations; **batch size example**: 10-20 mutations per batch (**proposed example**, TBD)
- **Delta sync**: if implemented, should minimize data transfer; exact algorithm unresolved

### 9.3 Offline Mode Performance
- **Online→Offline switch**: instantaneous (navigator.onLine change detection)
- **Offline data serving**: IndexedDB cache read ~1-5ms; negligible UI impact
- **Recon sync**: initial sync may be batch-heavy; subsequent syncs incremental; server validation adds latency but is required

### 9.4 Low-Bandwidth / Offline Considerations
- **Minimal data transfer**: sync payloads should only include essential mutation data (mutation ID, type, delta fields); avoid full object transfer
- **Compression**: sync endpoint responses should be compressed (gzip/deflate) when feasible (**implementation consideration**, not final protocol selection)
- **Cache-first strategy**: offline-ready data served from IndexedDB before any network attempt
- **Graceful degradation**: when offline, UI should gracefully degrade — show cached data, disable server-required ops, display appropriate offline indicators
- **Connection quality awareness**: consider `navigator.connection.effectiveType` to adapt sync behavior (2G/3G/4G WiFi differ in acceptable sync timing) — **implementation consideration**

---

## ১০. কম-ব্যান্ডউেধ/অফলাইন কনসিডারেশন (Low-Bandwidth/Offline)

### 10.1 Offline-First Data Prioritization
- **Critical path offline**: catalog browsing, product details, wishlist, recently viewed — all IndexedDB-cacheable
- **Never offline**: checkout, payment, price validation, stock validation, order confirmation — always require server
- **Graceful degradation**: when network fails mid-checkout, show clear error; do NOT silently proceed with stale data

### 10.2 Sync Optimization for Low-Bandwidth
- **Incremental sync**: only sync mutations since last successful sync (track by timestamp or mutation version) — **implementation consideration**
- **Batch instead of individual**: group multiple mutations into single HTTP request to reduce overhead — **implementation consideration**
- **Compression**: enable HTTP compression on sync endpoints — **implementation consideration**
- **Priority-based sync**: if bandwidth limited, sync critical mutations first (checkout-related > cart edits > wishlist edits) — **implementation consideration**

### 10.3 Offline Data Expiry
- **Catalog data expiry**: IndexedDB cached catalog data should have TTL (time-to-live); **proposed consideration**: ~24 hours maximum freshness (**TBD**, not finalized)
- **Mutation stale detection**: mutations older than last successful sync should be re-evaluated for sync priority
- **Automatic invalidation**: when back online, automatically invalidate stale cached data and refetch from server

### 10.4 User Experience in Low-Bandwidth/Offline
- **Offline indicator**: always visible when `navigator.onLine = false`
- **Feature availability**: clearly show which features work offline (catalog browse) and which don't (checkout)
- **Reconnect strategy**: when network restores, auto-sync pending mutations or show "pending sync" indicator with manual retry option
- **No silent data loss**: always show user when data may be lost or pending operations incomplete

---

## ১১. ডিসিশন গেটস (Decision Gates)

প্রতিটি unresolved architecture decision-এর জন্য নিচে decision gate স্পষ্ট করা হলো। এই decision-গুলো owner approval ছাড়া finalize করা যাবে না।

| # | Decision | Why Needed | Dependent Phase | Blocks Phase? | What Must Be Approved Before Implementation |
|---|---|---|---|---|---|
| 1 | **Retry classification** (which HTTP statuses retryable) | Determines client retry behavior | Fase 3 (server-side retry middleware), Fase 6 (retry testing) | Yes — Fase 3 cannot complete | Exact list of retryable vs non-retryable status codes |
| 2 | **Retry backoff parameters** (base delay, max delay, jitter) | Controls sync retry timing & aggressiveness | Fase 3 (retry middleware), Fase 6 (timing tests) | Yes — Fase 3 cannot complete | Base delay, max delay, jitter formula, max retry count |
| 3 | **Retry lifecycle** (circuit breaker, failover, max retry count) | Defines failure handling after retries exhausted | Fase 3 (failover strategy), Fase 7 (production hardening) | Yes — Fase 3 cannot complete | Circuit breaker threshold, failover behavior, dead letter handling |
| 4 | **Token/session storage mechanism** (IndexedDB vs memory vs cookies) | Determines where auth tokens persist | Fase 2 (client storage), Fase 5 (auth management) | Yes — Fase 2/5 cannot complete | Final storage choice with security audit |
| 5 | **Offline authenticated API behavior** | Defines what API calls work offline vs require server | Fase 4 (offline strategy), Fase 5 (auth) | Yes — Fase 4/5 cannot complete | List of offline-allowed auth operations, token refresh rules |
| 6 | **Conflict detection algorithm** | Determines how conflicts identified | Fase 3 (server detection), Fase 6 (conflict testing) | Yes — Fase 3 cannot complete | Exact detection method (version vectors, timestamps, etc.) |
| 7 | **Conflict merge algorithm** (LWW vs custom merge) | Determines how non-critical conflicts resolved | Fase 3 (reconciliation), Fase 6 (cart reconciliation) | Yes — Fase 3 cannot complete | LWW / custom merge / other — with cart-specific rules |
| 8 | **IndexedDB quota/eviction policy** | Controls cache size & mutation preservation | Fase 2 (cache design), Fase 4 (eviction), Fase 7 (hardening) | Yes — Fase 2/4 cannot complete | Specific policy (LRU/TTL/priority), quota thresholds, mutation safeguard |
| 9 | **Exact sync protocol** (push vs pull vs delta) | Defines sync message flow & data transfer | Fase 3 (endpoints), Fase 4 (timing), Fase 6 (protocol tests) | Yes — Fase 3 cannot complete | Push/pull/delta selection, frequency, batch size |
| 10 | **Exact sync endpoints** (`/sync`, `/batch-sync`, `/reconcile`) | Defines API surface for sync | Fase 3 (route design), Fase 6 (endpoint tests) | Yes — Fase 3 cannot complete | Final endpoint URLs, request/response schemas |
| 11 | **Idempotency implementation details** (key format, storage, validation) | Prevents duplicate mutation processing | Fase 3 (server validation), Fase 2 (client generation) | Yes — Fase 2/3 cannot complete | Key format, client storage, server verification logic |
| 12 | **Service Worker / Background Sync strategy** | Controls offline→online auto-sync triggering | Fase 4 (offline strategy), Fase 7 (production) | Yes — Fase 4 cannot complete | Registration trigger, periodic sync, connectivity change handling |
| 13 | **Multi-device synchronization strategy** | Defines cross-device state convergence | Fase 5 (auth sync), Fase 6 (multi-device tests) | Partial — can defer to post-launch | Auth state sync, cart merge rules, conflict resolution across devices |

---

## ১২. বাকি অনিশ্চিত সিদ্ধান্তগুলো (Remaining Unresolved Decisions)

১. Retry classification (which HTTP status codes are retryable)
২. Retry backoff parameters (base delay, max delay, jitter)
৩. Retry lifecycle (max retry count, circuit breaker, failover behavior)
৪. Token/session storage mechanism (IndexedDB / memory / cookies / other)
৫. Offline authenticated API behavior (whether/how offline auth works)
৬. Conflict detection algorithm (exact method, especially for cart)
৭. Conflict merge algorithm (LWW / custom / merge — esp. cart reconciliation)
৮. IndexedDB quota management & cache eviction policy (LRU or other)
৯. Exact sync protocol (push/pull/delta, frequency, batch size)
১০. Exact sync endpoints (`/sync`, `/batch-sync`, `/reconcile`)
১১. Idempotency mechanism (key generation, storage, server-side verification)
১২. Service Worker / Background Sync strategy (registration, periodic sync, triggers)
১৩. Multi-device synchronization strategy (auth state, cart state, cross-device conflict)

---

## ১৩. রিস্ক/রোলব্যাক সারসংক্ষেপ (Risk/Rollback Summary)

**Top Risks:**
1. **Data loss** during sync (mitigated by retry queue + server ack)
2. **IndexedDB quota overflow** evicting mutations (unresolved: quota policy TBD)
3. **Stale cache serving** incorrect data (offline-ready vs server-required boundary enforced)
4. **Conflict resolution bugs** (unresolved: algorithms TBD; business-critical → server authority)
5. **Auth token security** (unresolved: storage mechanism TBD; server auth always authoritative)
6. **Sync endpoint versioning** (API versioning strategy required from Fase 3)

**Rollback Strategy:** All scenarios maintain local mutation queue until server ack; fallback to server data on corruption; backward-compatible endpoints during migration.

---

## ১৪. কন্ট্রাডিকশন চেক (Contradiction Check)

| Document | Check | Result |
|---|---|---|
| **P0: PROJECT_BRAIN.md** | Server-authoritative business data; IndexedDB not business DB; checkout/payment server-side | ✅ Consistent — roadmap enforces these as approved constraints |
| **P1: BACKEND/API/SYSTEM/SECURITY/AUTH** | Server-side validation, idempotency, retry-safe, offline security boundary | ✅ Consistent — roadmap references these as conceptual dependencies |
| **ADR-011** | Hybrid Local-First (Approved/Documented) | ✅ Consistent — roadmap implements ADR-011 principles in phased approach |
| **LOCAL_FIRST_SYNC_SPEC.md** | Retry proposed only, conflict LWW not selected, auth conceptual, quota unresolved | ✅ Consistent — all proposed values marked TBD, no finalization |
| **OFFLINE_STRATEGY.md** | Offline-ready vs server-required matrix, connectivity transitions | ✅ Consistent — roadmap phases implement these in order |

**No contradictions found.**

---

## ১৫. স্কোপ ভ্যালিডেশন (Scope Validation)

| Check | Result |
|---|---|
| Source code modified? | ❌ No (documentation only) |
| Dependencies added? | ❌ No |
| IndexedDB implemented? | ❌ No |
| Sync implemented? | ❌ No |
| API endpoints created? | ❌ No (conceptual routes only) |
| Database migration? | ❌ No |
| Token storage finalized? | ❌ No (explicitly UNRESOLVED) |
| Conflict algorithms finalized? | ❌ No (explicitly UNRESOLVED) |
| Service Worker / Background Sync finalized? | ❌ No (explicitly UNRESOLVED) |
| Retry parameters finalized? | ❌ No (marked as proposed examples/TBD) |
| Cache TTL/eviction finalized? | ❌ No (marked as proposed consideration/TBD) |
| Sync batch size/protocol finalized? | ❌ No (marked as proposed examples/TBD) |
| APPROVED → APPROVED SPEC → IMPLEMENTATION PLAN → ACTUAL IMPLEMENTATION separation? | ✅ Yes |

---

## 🛑 **STOP — WAITING FOR OWNER APPROVAL**

This implementation roadmap is a **draft/proposed planning document**. No implementation work may proceed until:

1. Owner reviews and approves this roadmap, OR
2. Owner specifies required revisions to the roadmap

**Critical constraints to remember:**
- **DO NOT** create migrations, dependencies, API endpoints
- **DO NOT** implement IndexedDB stores, sync code, Service Workers
- **DO NOT** create application code, business logic
- **DO NOT** finalize any of the 13 unresolved decisions listed above
- **MAINTAIN** strict separation: APPROVED ARCHITECTURE → APPROVED SPECIFICATION → IMPLEMENTATION PLAN → ACTUAL IMPLEMENTATION

After owner approval of this roadmap, the next phase would be detailed implementation planning with task breakdowns — but ONLY after explicit owner approval.

*Roadmap version: 0.1 | Status: DRAFT (proposed implementation roadmap, awaiting owner approval) | Last updated: 2026-11-20*

**Ready for owner review and approval.**