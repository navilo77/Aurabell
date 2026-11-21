import { apiFetch } from "@/lib/api";
import {
  listMutationsByUser,
  updateMutation,
  removeMutation,
  purgeUserMutations,
  type MutationRecord,
  MAX_RETRIES,
} from "@/lib/offline/db";

const BASE_DELAY_MS = 1000;
const JITTER_RATIO = 0.1;

// ─── Concurrency lock ─────────────────────────────────────────────
// Only one queue drain may execute at a time. All triggers (online
// event, interval, manual sync) share the same lock.

let drainPromise: Promise<void> | null = null;

export async function drainQueue(userId: string): Promise<void> {
  if (drainPromise) {
    await drainPromise;
    return;
  }
  drainPromise = (async () => {
    try {
      await drainQueueLocked(userId);
    } finally {
      drainPromise = null;
    }
  })();
  await drainPromise;
}

async function drainQueueLocked(userId: string): Promise<void> {
  const records = await listMutationsByUser(userId);
  const now = Date.now();

  const pending = records
    .filter(
      (r) =>
        (r.status === "pending" || r.status === "failed") &&
        (!r.next_retry_at || r.next_retry_at <= now)
    )
    .sort((a, b) => a.createdAt - b.createdAt);

  for (const record of pending) {
    record.status = "in-flight";
    await updateMutation(record);
    try {
      await replayMutation(record);
      await removeMutation(record.id);
    } catch (e: any) {
      await handleMutationFailure(record, e);
    }
  }
}

// ─── Mutation replay ──────────────────────────────────────────────

async function replayMutation(record: MutationRecord): Promise<void> {
  const init: RequestInit = {
    method: record.method,
    credentials: "include",
    headers: {
      "Idempotency-Key": record.idempotency_key,
    },
  };

  if (
    record.payload &&
    record.method !== "GET" &&
    record.method !== "DELETE" &&
    record.method !== "HEAD"
  ) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(record.payload);
  }

  const res = await fetch(`/api/v1${record.endpoint}`, init);

  if (res.ok) return;

  const error = new Error(`API error: ${res.status}`);
  (error as { status?: number }).status = res.status;
  throw error;
}

// ─── Error policy ─────────────────────────────────────────────────

function isPermanentFailure(status: number): boolean {
  return status === 403 || status === 409 || status === 422;
}

function isRetryable(status: number | null): boolean {
  if (status === null) return true; // network error / timeout
  if (status === 429 || status >= 500) return true;
  return false;
}

function computeBackoff(retries: number): number {
  const delay = BASE_DELAY_MS * Math.pow(2, retries - 1);
  const jitter = delay * JITTER_RATIO * (Math.random() * 2 - 1);
  return delay + jitter;
}

async function handleMutationFailure(record: MutationRecord, error: any): Promise<void> {
  const status = error?.status ?? null;
  record.retries += 1;
  record.lastError = error?.message ?? "unknown";

  // Unrecoverable 401: refresh was already attempted by apiFetch
  if (status === 401) {
    record.status = "dead-letter";
    await updateMutation(record);
    return;
  }

  // Permanent failures: do not retry
  if (status !== null && isPermanentFailure(status)) {
    record.status = "dead-letter";
    await updateMutation(record);
    return;
  }

  // Non-retryable, non-permanent → dead-letter
  if (status !== null && !isRetryable(status)) {
    record.status = "dead-letter";
    await updateMutation(record);
    return;
  }

  // Retryable: schedule backoff or dead-letter if max retries reached
  if (record.retries >= MAX_RETRIES) {
    record.status = "dead-letter";
  } else {
    record.status = "pending";
    record.next_retry_at = Date.now() + computeBackoff(record.retries);
  }
  await updateMutation(record);
}

// ─── Account isolation ────────────────────────────────────────────

export async function purgeQueueForUser(userId: string): Promise<void> {
  await purgeUserMutations(userId);
}
