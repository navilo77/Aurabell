import { openDB, type IDBPDatabase } from "idb";

const DB_NAME = "aurabel-offline";
const DB_VERSION = 2;

export const MAX_RETRIES = 5;

export interface MutationRecord {
  id: string;
  user_id: string;             // owner of the mutation (account scoping)
  type: string;
  endpoint: string;
  method: string;
  payload: unknown;
  idempotency_key: string;     // = id, sent as Idempotency-Key header
  createdAt: number;
  retries: number;
  next_retry_at: number;       // backoff scheduling
  lastError: string | null;
  retryable: boolean;          // whether the mutation can be retried
  status:
    | "pending"
    | "in-flight"
    | "failed"
    | "dead-letter"
    | "synced";
}

let dbPromise: Promise<IDBPDatabase> | null = null;

export function getDb() {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db, _oldVersion, _newVersion, transaction) {
        if (!db.objectStoreNames.contains("mutations")) {
          db.createObjectStore("mutations", { keyPath: "id" });
        }
        if (!db.objectStoreNames.contains("entities")) {
          db.createObjectStore("entities", { keyPath: "key" });
        }
        const mutationsStore = transaction.objectStore("mutations");
        if (!mutationsStore.indexNames.contains("user_id")) {
          mutationsStore.createIndex("user_id", "user_id");
        }
        if (!mutationsStore.indexNames.contains("status")) {
          mutationsStore.createIndex("status", "status");
        }
      },
    }).catch(() => null as unknown as IDBPDatabase);
  }
  return dbPromise;
}

type MutationInput = Omit<
  MutationRecord,
  | "id"
  | "createdAt"
  | "retries"
  | "lastError"
  | "idempotency_key"
  | "next_retry_at"
  | "retryable"
  | "status"
> & { user_id: string };

export async function enqueueMutation(m: MutationInput) {
  const db = await getDb();
  if (!db) return null;
  const id = crypto.randomUUID();
  const now = Date.now();
  const record: MutationRecord = {
    ...m,
    id,
    user_id: m.user_id,
    idempotency_key: id,
    createdAt: now,
    retries: 0,
    next_retry_at: now,
    retryable: true,
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

export async function listMutationsByUser(userId: string): Promise<MutationRecord[]> {
  const db = await getDb();
  if (!db) return [];
  return db.getAllFromIndex("mutations", "user_id", userId);
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

export async function purgeUserMutations(userId: string): Promise<void> {
  const db = await getDb();
  if (!db) return;
  const records = await db.getAllFromIndex("mutations", "user_id", userId);
  for (const record of records) {
    await db.delete("mutations", record.id);
  }
}
