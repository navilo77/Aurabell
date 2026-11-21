import { apiFetch } from "@/lib/api";
import { listPendingMutations, updateMutation, removeMutation, type MutationRecord } from "@/lib/offline/db";

export async function drainQueue() {
  const records = await listPendingMutations();
  const pending = records
    .filter((r) => r.status === "pending" || r.status === "failed")
    .sort((a, b) => a.createdAt - b.createdAt);

  for (const record of pending) {
    record.status = "in-flight";
    await updateMutation(record);
    try {
      await apiFetch(record.endpoint, {
        method: record.method,
        body: record.payload ? JSON.stringify(record.payload) : undefined,
      });
      record.status = "synced";
      await removeMutation(record.id);
    } catch (e: any) {
      record.retries += 1;
      record.lastError = e?.message ?? "unknown";
      record.status = record.retries >= 5 ? "failed" : "pending";
      await updateMutation(record);
    }
  }
}

export function startSyncEngine() {
  if (typeof window === "undefined") return;
  window.addEventListener("online", () => {
    void drainQueue();
  });
  setInterval(() => {
    if (navigator.onLine) void drainQueue();
  }, 30000);
}