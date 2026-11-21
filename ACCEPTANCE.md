# ACCEPTANCE.md

## Phase 1 — no-img-element
- lint: no-img-element warnings = 0 ✅

## Phase 2 — auth cookie
- backend sets HttpOnly cookies ✅
- frontend sends credentials ✅
- localStorage still present (backward compat) ✅

## Phase 3 — route guards
- middleware protects routes ✅
- /login redirect for authenticated ✅

## Phase 4 — offline sync
- IndexedDB wrapper + queue + sync engine ✅

## Phase 5 — tests
- frontend test framework: pending approval
- backend pytest: timeout (env issue)
EOF