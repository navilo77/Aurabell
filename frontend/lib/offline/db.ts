import { openDB, type IDBPDatabase } from "idb";

const DB_NAME = "aurabel-offline";
const DB_VERSION = 1;

export interface MutationRecord {
  id: string;
  type: string;
  endpoint: string;
  method: string;
  payload: unknown;
  createdAt: number;
  retries: number;
  lastError: string | null;
  status: "pending" | "in-flight" | "failed" | "synced";
}

let dbPromise: Promise<IDBPDatabase> | null = null;

export function getDb() {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains("mutations")) {
          db.createObjectStore("mutations", { keyPath: "id" });
        }
        if (!db.objectStoreNames.contains("entities")) {
          db.createObjectStore("entities", { keyPath: "key" });
        }
      },
    }).catch(() => null as unknown as IDBPDatabase);
  }
  return dbPromise;
}

export async function enqueueMutation(m: Omit<MutationRecord, "id" | "createdAt" | "retries" | "lastError" | "status">) {
  const db = await getDb();
  if (!db) return null;
  const record: MutationRecord = {
    ...m,
    id: crypto.randomUUID(),
    createdAt: Date.now(),
    retries: 0,
    lastError: null,
    status: "pending",
  };
  await db.put("mutations", record);
  return record;
}

export async function listPendingMutations(): Promise<MutationRecord[]> {
  const db = await getDb();
  if (!db) return [];
  return db.getAll("mutations");
}

export async function updateMutation(record: MutationRecord) {
  const db = await getDb();
  if (!db) return;
  await db.put("mutations", record);
}

export async function removeMutation(id: string) {
  const db = await getDb();
  if (!db) return;
  await db.delete("mutations", id);
}