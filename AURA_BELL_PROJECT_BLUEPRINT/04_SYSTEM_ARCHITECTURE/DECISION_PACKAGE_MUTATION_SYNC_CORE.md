---
id: DOC-AUR-071
title: Aura Bell — Decision Package: Mutation/Sync Architecture Core Decisions
type: technical
status: draft
version: 0.1
language: Bangla with English technical terms
source: AB-SA-001, ADR-011, LOCAL_FIRST_SYNC_SPEC.md, OFFLINE_STRATEGY.md, IMPLEMENTATION_ROADMAP.md, DECISION_PACKAGE_PHASE1_PHASE2.md
last_updated: 2026-11-20
---

# Aura Bell — Decision Package: Mutation/Sync Architecture Core Decisions (মিউটেশন/সিঙ্ক আর্কিটেকচার কোর সিদ্ধান্ত প্যাকেজ)

> **স্ট্যাটাস**: Draft (প্রস্তাবিত)। এই নথিতে mutation/sync আর্কিটেকচারকে সরাসরি unblock করে এমন ৪টি কোর সিদ্ধান্তের detailed analysis রয়েছে। এই সিদ্ধান্তগুলো owner approval ছাড়া finalize করা যাবে না।
>
> **গাইডলাইন**: প্রতিটি সিদ্ধান্তে নিচের পাঁচ স্তর স্পষ্টভাবে পৃথক রাখা হয়েছে:
> 1. **APPROVED CONSTRAINTS** — অনুমোদিত আর্কিটেকচার এবং পূর্বে অনুমোদিত directions (D1–D6) থেকে আসা বাধ্যবাধকতা
> 2. **CANDIDATE ARCHITECTURAL DIRECTION** — প্রস্তাবিত আর্কিটেকচারাল দিকনির্দেশনা (direction হিসেবে approve করা যেতে পারে)
> 3. **VALIDATION REQUIRED** — যেসব numeric/configuration মান evidence/benchmark দিয়ে ঠিক করতে হবে
> 4. **UNRESOLVED IMPLEMENTATION DECISIONS** — যা owner-র explicit approval দরকার implementation phase-এ
> 5. **EVIDENCE/TESTING REQUIRED** — কোন data/testing দিয়ে final parameter ঠিক করা হবে
> 6. **DEPENDENCIES ON D1–D6** — পূর্বে অনুমোদিত সিদ্ধান্তগুলোর সাথে সম্পর্ক

---

## Overview

IMPLEMENTATION_ROADMAP.md অনুযায়ী, mutation/sync architecture-এর core pieces কে unblock করতে নিচের ৪টি decision approve করতে হবে:

| # | Decision | Blocks | Source Document |
|---|---|---|---|
| **D7** | **Conflict Detection & Reconciliation Model** | Fase 3, Fase 6 | LOCAL_FIRST_SYNC_SPEC.md §7, OFFLINE_STRATEGY.md §7 |
| **D8** | **Mutation Queue Data Model** | Fase 2, Fase 3 | LOCAL_FIRST_SYNC_SPEC.md §6, IMPLEMENTATION_ROADMAP.md Fase 2 |
| **D9** | **Sync Protocol Architecture** | Fase 3, Fase 4 | LOCAL_FIRST_SYNC_SPEC.md §6.2, OFFLINE_STRATEGY.md §7 |
| **D10** | **Multi-Device Synchronization Model** | Fase 4, Fase 5, Fase 6 | LOCAL_FIRST_SYNC_SPEC.md §7.3, OFFLINE_STRATEGY.md §5 |

---

## Decision D7: Conflict Detection & Reconciliation Model

### 1. APPROVED CONSTRAINTS (অপরিবর্তনীয়)
- **Business-critical → Server authoritative**: পণ্য, মূল্য, ইনভেন্টরি, অর্ডার, পেমেন্ট, অর্ডার স্টেট — সার্ভারের সিদ্ধান্তই চূড়ান্ত (ADR-008, PROJECT_BRAIN ৩.১, LOCAL_FIRST_SYNC_SPEC.md §7.1)
- **Non-critical → Merge/LWW/Custom may be evaluated**: LWW already selected নয় (LOCAL_FIRST_SYNC_SPEC.md §7.2)
- **Cart reconciliation especially unresolved**: একাধিক ডিভাইসে বা অফলাইন-পরবর্তী কার্ট merge-এর exact behavior unresolved (LOCAL_FIRST_SYNC_SPEC.md §7.3)
- **Idempotency required for all mutations**: D6 approved direction — client-generated idempotency identifiers
- **Retry policy applies to conflict resolution sync**: D1/D2 approved directions — retryable errors get exponential backoff

### 2. CANDIDATE ARCHITECTURAL DIRECTION
**Three-tier conceptual conflict resolution model**:

| Tier | Data Classification | Resolution Candidate | Authority |
|---|---|---|---|
| **Tier 1: Business-Critical** | Price, inventory, orders, payments, auth, order state | **Server authoritative** — client mutation rejected or transformed | Server |
| **Tier 2: User State** | Cart, wishlist, recently viewed, user preferences | **Reconciliation/merge candidate** — client proposes, server validates/merges | Server validates |
| **Tier 3: Disposable/Cache** | Catalog, product details, categories, brands | **Refresh/LWW candidate** — no user intent loss | Cache-only |

**Direction**: Three-tier model as architectural direction. Tier 1 = server always wins. Tier 2 = reconciliation/merge (cart = primary use case). Tier 3 = refresh/LWW candidate.

**Do NOT finalize**: LWW as selected; cart merge semantics; conflict detection algorithm; tier assignment for every data type.

### 3. VALIDATION REQUIRED
| Parameter | Evidence Needed |
|---|---|
| Tier assignment criteria | What factors determine tier: business impact, mutability, user intent, volatility, regulatory? |
| Conflict detection algorithm | Vector clocks vs version vectors vs timestamps vs hybrid — scale, clock skew, complexity tradeoffs |
| Tier 2 merge functions (cart) | Additive union vs max qty vs smart merge — UX expectation, conflict frequency, data consistency |
| Server validation latency | Tier 2 merge validation under peak concurrent load |

### 4. UNRESOLVED IMPLEMENTATION DECISIONS
- Exact conflict detection algorithm (vector clocks, version vectors, timestamps, hybrid)
- Exact merge functions for each Tier 2 data type (especially cart)
- Exact tier assignment for every data type in system
- Whether Tier 2 uses client-side vector clocks, server-side version vectors, or hybrid
- Conflict resolution API schema (request/response)

### 5. EVIDENCE/TESTING REQUIRED
- Data classification workshop: enumerate all client-side mutable data, assign tiers with rationale
- Conflict scenario modeling: concurrent cart edits across devices, offline→online merge
- Performance benchmark: vector clock overhead vs timestamp-only at scale
- UX validation: user expectation for cart merge (additive vs replacement vs smart)

### 6. DEPENDENCIES ON D1–D6
- **D1 (Retry Classification)**: Conflict resolution sync requests follow retry policy
- **D2 (Retry Backoff)**: Merge validation retries use exponential backoff
- **D6 (Idempotency)**: Every conflict resolution request carries idempotency key

---

## Decision D8: Mutation Queue Data Model

### 1. APPROVED CONSTRAINTS (অপরিবর্তনীয়)
- **Every mutation carries idempotency key**: D6 approved direction — client-generated identifiers
- **Retry policy applies**: D1/D2 — retryable errors get exponential backoff; non-retryable go to dead-letter
- **Mutations persist offline**: IndexedDB storage required (D3 approved direction — mutation store protected)
- **Server authoritative validation**: All mutations validated server-side before commit (ADR-008)
- **Mutation order matters for some operations**: Cart add/remove sequence affects final state

### 2. CANDIDATE ARCHITECTURAL DIRECTION
**Structured mutation queue with explicit type, tier, dependencies, lifecycle, and idempotency identifier**

Conceptual mutation record structure (fields are CANDIDATE, not final):

```typescript
interface Mutation {
  // Identity
  id: string;                    // Client-generated unique identifier
  idempotencyKey: string;        // D6: client-generated idempotency identifier
  
  // Classification
  type: MutationType;            // Domain-specific operation type
  tier: DataTier;                // D7: Tier 1/2/3 — affects retry, conflict, priority
  
  // Payload
  payload: MutationPayload;      // Operation-specific data
  dependencies?: string[];       // IDs of mutations this depends on (ordering hint)
  
  // Lifecycle
  status: MutationStatus;        // 'pending' | 'syncing' | 'synced' | 'failed' | 'dead' | 'conflict'
  retryCount: number;            // D2: tracks backoff attempts
  lastAttempt?: timestamp;       // For backoff calculation
  createdAt: timestamp;          // For ordering, TTL
  updatedAt: timestamp;
  
  // Conflict/Resolution
  conflictResolution?: ConflictResolution;  // D7: how server resolved
  serverVersion?: number;        // For optimistic locking (Tier 1)
  
  // Metadata
  clientInfo: ClientInfo;        // Device ID, app version
  correlationId?: string;        // For tracing related mutations
}
```

**Queue behavior candidates**:
- **Priority**: Tier 1 > Tier 2 > Tier 3 (D3 priority model)
- **Ordering**: Must preserve business dependencies where required; exact scheduling algorithm TBD
- **Batching**: Group by tier/type for sync efficiency (D9 sync protocol)
- **Dead-letter**: After max retries (D2) → move to dead-letter queue, notify user

**Direction**: Structured queue with explicit type, tier, dependencies, lifecycle, idempotency identifier. Priority by tier. Ordering must preserve business dependencies where required; exact scheduling algorithm TBD.

**Do NOT finalize**: Exact IndexedDB object stores; exact fields; exact queue schema; FIFO as mandatory guarantee; dependency graph implementation; batch size; dead-letter TTL; maximum queue size.

### 3. VALIDATION REQUIRED
| Parameter | Evidence Needed |
|---|---|
| Max queue size per tier | Offline duration study: mutations accumulated in 24h/72h/week |
| Dependency graph complexity | Cart operations: dependent mutations in typical session |
| Dead-letter retention TTL | User resolution timeframe; GDPR/data retention policy |
| Batch size per sync | D9 sync protocol; network payload limits; server capacity |

### 4. UNRESOLVED IMPLEMENTATION DECISIONS
- Exact IndexedDB object store schema
- Exact field definitions and types
- Exact queue schema (single store vs per-tier stores)
- FIFO vs priority scheduling algorithm
- Dependency graph representation and traversal
- Batch size per sync operation
- Dead-letter TTL and user notification mechanism
- Maximum queue size per tier

### 5. EVIDENCE/TESTING REQUIRED
- Mutation volume study: real-world offline session data or simulation
- Queue processing simulation: 1000 mutations, various failure modes, measure latency
- Schema migration test: add/remove fields, version upgrade path

### 6. DEPENDENCIES ON D1–D6
- **D1/D2 (Retry)**: Queue status transitions driven by retry policy
- **D3 (Quota)**: Mutation store protected; queue size affects quota budget
- **D6 (Idempotency)**: idempotencyKey field required; client generation
- **D7 (Conflict)**: Tier field from D7 classification; conflictResolution field from D7 resolution

---

## Decision D9: Sync Protocol Architecture

### 1. APPROVED CONSTRAINTS (অপরিবর্তনীয়)
- **Push/Pull/Delta not finalized**: LOCAL_FIRST_SYNC_SPEC.md §6.2 — exact protocol unresolved
- **Endpoints TBD**: `/sync`, `/batch-sync`, `/reconcile` conceptual only
- **Idempotency mandatory**: D6 — every sync request carries idempotency key
- **Retry policy applies**: D1/D2 — sync requests follow exponential backoff
- **Conflict resolution integrated**: D7 — sync includes conflict detection/resolution
- **Mutation queue drives sync**: D8 — queue status determines what syncs

### 2. CANDIDATE ARCHITECTURAL DIRECTION
**Hybrid push-based mutation synchronization with periodic pull reconciliation**

**Why this candidate**:
- Push-based: Client controls when to send pending mutations; natural for offline-first
- Periodic pull: Ensures Tier 1 authoritative state converges even if push missed
- Batch mutations: Reduces round-trips, improves efficiency
- Per-mutation results: Enables fine-grained retry/dead-letter per D1/D2

**Alternative architectures evaluated**:
| Architecture | Pros | Cons |
|---|---|---|
| **Push-only** | Simple, client-controlled | Missed pushes = stale Tier 1 state |
| **Pull-only** | Server controls, guaranteed convergence | Latency; client passive; wasted polls |
| **Push + Pull (candidate)** | Best of both; client pushes mutations, server pushes authoritative state | More complex; two sync paths |
| **Delta-based** | Bandwidth efficient | Complex; partial update semantics; conflict detection harder |
| **Event/version-based** | Real-time convergence | WebSocket/SSE complexity; connection management |

**Sync flow candidate (not finalized)**:
```
1. Client online → detects pending mutations (status='pending')
2. Sort by: tier priority → createdAt → dependencies
3. Batch up to N mutations (configurable, D8)
4. POST /sync with { mutations: [...], clientVersion, clientClock }
5. Server: validate each, detect conflicts (D7), apply/resolve, return { results: [{ id, status, serverVersion, conflictResolution }] }
6. Client: update mutation statuses, apply conflict resolutions, retry failed per D1/D2
7. Periodic: GET /reconcile?since=clientVersion → receive authoritative Tier 1 state
```

**Error handling candidates**:
- 4xx per mutation → mark failed, don't retry (D1), move to dead-letter
- 5xx / network error → retry per D2 backoff
- 409 conflict → apply D7 resolution, update local state
- 429 rate limit → respect Retry-After, backoff per D2

**Direction**: Push-based primary + periodic pull reconciliation as candidate sync architecture. Batch mutations. Per-mutation results with conflict resolutions.

**Do NOT finalize**: `/sync`, `/batch-sync`, `/reconcile` endpoints; batch size; sync frequency; polling interval; delta protocol; partial-failure semantics; server response schema; WebSocket/SSE/background sync mechanism.

### 3. VALIDATION REQUIRED
| Parameter | Evidence Needed |
|---|---|
| Batch size (N) | Network payload limits; server processing latency per mutation; partial failure handling |
| Sync frequency (push) | Immediate on online? Debounced? Periodic? Battery/network tradeoff |
| Reconciliation interval (pull) | Tier 1 volatility; user perception of staleness; server load |
| Delta vs full payload | Bandwidth savings vs complexity; partial update semantics |
| Partial failure handling | Fail entire batch? Fail individual? Retry failed subset? |

### 4. UNRESOLVED IMPLEMENTATION DECISIONS
- Exact sync endpoints and request/response schemas
- Batch size per sync operation
- Push sync frequency and trigger conditions (immediate, debounced, periodic)
- Pull reconciliation interval and trigger
- Delta synchronization support and protocol
- Partial failure semantics (batch fail vs individual fail vs retry subset)
- Server response schema for sync and reconcile
- WebSocket/SSE/Background Sync mechanism (if any)
- Connection quality adaptation (2G/3G/4G/WiFi)

### 5. EVIDENCE/TESTING REQUIRED
- Network simulation: 2G/3G/4G/WiFi sync latency, battery, success rate
- Load test: 10k concurrent clients syncing; server throughput, latency
- Failure injection: 503, 429, 409, network drop — verify retry, backoff, dead-letter
- Conflict scenario: concurrent mutations from multiple devices → verify D7 resolution
- Bandwidth measurement: push vs pull vs delta payload sizes

### 6. DEPENDENCIES ON D1–D6
- **D1 (Retry Classification)**: Sync request retryability per error class
- **D2 (Retry Backoff)**: Backoff applied to failed sync requests
- **D3 (Quota)**: Sync batch size affects mutation queue memory
- **D6 (Idempotency)**: Every sync request + every mutation in batch carries idempotency key
- **D7 (Conflict)**: Sync response includes conflict resolution per mutation
- **D8 (Queue)**: Queue provides mutations to sync; status updated from sync response

---

## Decision D10: Multi-Device Synchronization Model

### 1. APPROVED CONSTRAINTS (অপরিবর্তনীয়)
- **Auth state sync unresolved**: D5 approved direction — token storage TBD; offline auth behavior NOT approved
- **Cart reconciliation especially unresolved**: D7 — Tier 2 (cart) merge with server reconciliation
- **Server authoritative for business data**: Tier 1 always server-wins
- **Offline cached data read-only**: D5 — no offline authenticated API calls

### 2. CANDIDATE ARCHITECTURAL DIRECTION
**Server-as-convergence-point for business state; authentication/session synchronization separate from business-data synchronization**

**Critical distinction — do NOT conflate**:
1. **Authentication/session synchronization** — Who is logged in, token validity, session expiry
2. **Business-data synchronization** — Cart, wishlist, orders, user preferences
3. **Client cache refresh** — Catalog, product details, categories (Tier 3)
4. **Mutation synchronization** — Pending operations sync to server (D9)

**Candidate model**:

| Concern | Candidate Approach |
|---|---|
| **Auth/session sync** | **Per-device authentication**; each device independently authenticates with Supabase; no cross-device session sync (per D5 direction). Refresh tokens per-device. |
| **Business state (Tier 2: cart)** | **Server reconciliation** (D7). Each device pushes cart mutations; server merges additive operations, resolves conflicts via merge function. |
| **User preferences (Tier 2: wishlist)** | **Merge candidate** — set-union or LWW; server accepts all, client merges locally. |
| **Cache (Tier 3)** | **Independent per device**; no cross-device sync needed. Server invalidation on catalog update (optional). |
| **Convergence** | **Server as convergence point**. No direct device-to-device sync. Each device independently syncs with server. |

**Direction**: Server-as-convergence-point for business state. Authentication/session synchronization separate from business-data synchronization. Per-device auth. Tier 2 merge via server reconciliation.

**Do NOT finalize**: 
- "Per-device auth" without Supabase Auth compatibility analysis
- "No cross-device session sync" as approved security decision (requires analysis)
- Cart convergence strategy (merge function TBD)
- Push/poll/WebSocket for convergence
- Reconciliation frequency
- Whether session revocation propagates across devices

### 3. VALIDATION REQUIRED
| Parameter | Evidence Needed |
|---|---|
| Supabase Auth compatibility | Does GoTrue support per-device refresh tokens? Session revocation propagation? |
| Auth/session sync security | Threat model: session hijacking, token theft, revocation latency |
| Cart merge function | Additive union vs max qty vs smart merge — UX test required |
| Convergence frequency | Polling interval vs WebSocket/SSE — battery, latency, server load |
| Session revocation | Logout on one device → other devices behavior |

### 4. UNRESOLVED IMPLEMENTATION DECISIONS
- Authentication/session synchronization strategy (per-device vs shared vs hybrid)
- Cross-device session revocation behavior
- Cart merge function (additive, max qty, smart)
- Reconciliation frequency and mechanism (poll vs push vs WebSocket/SSE)
- Whether catalog invalidation uses push or pull
- Offline device behavior when other device modifies shared state

### 5. EVIDENCE/TESTING REQUIRED
- Multi-device UX test: user adds on phone, views on desktop — latency, consistency expectation
- Conflict scenario: same cart item qty changed on two devices offline → merge result
- Auth test: logout on one device; other device session behavior; token refresh
- Network test: high-latency device sync vs low-latency device
- Supabase Auth integration test: per-device tokens, revocation, rotation

### 6. DEPENDENCIES ON D1–D6
- **D5 (Token Storage)**: Per-device auth tokens; no cross-device session sync
- **D7 (Conflict)**: Tier 2 cart merge function defined here
- **D8 (Queue)**: Mutations from all devices go through same queue/sync pipeline
- **D9 (Sync)**: Reconciliation pull delivers multi-device converged state

---

## Dependency Graph (Updated)

```
D1 (Retry Classification) ──► D2 (Retry Backoff)
     │                            │
     ▼                            ▼
D7 (Conflict) ◄──────────────────┤
     │                            │
     ▼                            ▼
D8 (Mutation Queue) ◄────────────┤
     │                            │
     ▼                            ▼
D9 (Sync Protocol) ◄─────────────┘
     │
     ▼
D10 (Multi-Device) ◄─── D5 (Token Storage)
     │
     ▼
D3/D4 (Quota/Cache) ──► D8, D9 (indirect)

No circular dependencies identified.
```

**Dependency Legend**:
- **D1/D2** → Retry behavior for all sync/conflict operations
- **D3/D4** → Local persistence/cache budget for queue and cache
- **D5** → Authenticated synchronization scope and mechanism
- **D6** → Mutation idempotency for sync and conflict resolution
- **D7** → Conflict/reconciliation rules for Tier 1/2/3
- **D8** → Mutation queue structure and ordering
- **D9** → Sync protocol for mutation delivery and state reconciliation
- **D10** → Multi-device convergence built on D5, D7, D8, D9

---

## Approval Model Summary

| Decision | What Can Be Approved Now (Direction) | Candidate Direction | What Must Remain Unresolved | Validation Required | Finalization Phase |
|---|---|---|---|---|---|
| **D7: Conflict** | Three-tier conceptual model | Tier 1=server, Tier 2=reconcile, Tier 3=refresh/LWW | Exact detection algo, merge functions, tier assignment | Data classification; scenario modeling; perf benchmark | Fase 3 |
| **D8: Mutation Queue** | Structured model with type, tier, deps, lifecycle, idempotencyKey | Priority by tier; ordering preserves deps | Exact fields, IndexedDB schema, batch size, dead-letter TTL | Volume study; queue sim; migration test | Fase 2 |
| **D9: Sync Protocol** | Push-based primary + periodic pull as candidate architecture | Batch mutations; per-mutation results | Endpoints, batch size, frequency, delta, failure handling | Network sim; load test; failure injection | Fase 3 |
| **D10: Multi-Device** | Server-as-convergence-point; auth separate from business data | Per-device auth; Tier 2 merge via server | Auth sync strategy, cart merge, frequency, push/poll | Supabase compat; UX test; auth test | Fase 4/5 |

---

## Next Steps

1. **Owner reviews** each D7–D10 decision package
2. **Owner provides** explicit approval/modification for **architectural direction only**
3. **Document approved directions** as design notes (NOT ADRs yet)
4. **Update** `LOCAL_FIRST_SYNC_SPEC.md`, `OFFLINE_STRATEGY.md`, `IMPLEMENTATION_ROADMAP.md` with approved directions
5. **Only then** proceed to Fase 1/2 detailed task breakdown

---

**STOP — WAITING FOR OWNER APPROVAL ON ARCHITECTURAL DIRECTIONS FOR D7–D10**

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
- ✅ No ADRs created
- ✅ All numeric parameters marked TBD with validation path
- ✅ APPROVED CONSTRAINTS → CANDIDATE DIRECTION → VALIDATION REQUIRED → UNRESOLVED IMPLEMENTATION DECISIONS separation maintained
- ✅ Dependencies on D1–D6 explicitly documented
- ✅ Critical distinction: auth/session sync ≠ business-data sync ≠ cache refresh ≠ mutation sync