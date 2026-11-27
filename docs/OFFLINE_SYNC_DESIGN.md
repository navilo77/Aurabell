# Offline Sync Design (Phase 4)

## Stores
- entities: cached catalog/products/stores
- mutations: pending API mutations
- metadata: lastSync, version

## Mutation Record
{id, type, endpoint, method, payload, createdAt, retries, lastError, status}

## Sync Triggers
online event, interval 30s, app focus, manual

## Conflict Policy
server-authoritative

## Retry/Backoff
exponential backoff, max 5 retries, dead-letter after

## Fallback
if IndexedDB unavailable, in-memory queue only
EOF