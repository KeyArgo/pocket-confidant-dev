// Local-only persistence (IndexedDB). Everything stays in the browser; no server.
// Journal-sized data fits in memory for cosine search, so we load all entries and
// score in-process (see core/recall.ts) rather than pulling in a vector DB.

import { openDB, type DBSchema, type IDBPDatabase } from "idb";
import type { Entry } from "../core/types";

interface ConfidantDB extends DBSchema {
  entries: {
    key: number;
    value: Entry;
    indexes: { by_day: string; by_ts: number };
  };
  meta: { key: string; value: unknown };
}

let dbPromise: Promise<IDBPDatabase<ConfidantDB>> | null = null;

function getDB(): Promise<IDBPDatabase<ConfidantDB>> {
  if (!dbPromise) {
    dbPromise = openDB<ConfidantDB>("pocket-confidant", 1, {
      upgrade(db) {
        const store = db.createObjectStore("entries", {
          keyPath: "id",
          autoIncrement: true,
        });
        store.createIndex("by_day", "day");
        store.createIndex("by_ts", "ts");
        db.createObjectStore("meta");
      },
    });
  }
  return dbPromise;
}

export async function addEntry(e: Omit<Entry, "id">): Promise<Entry> {
  const db = await getDB();
  const id = await db.add("entries", e as Entry);
  return { ...(e as Entry), id: id as number };
}

export async function updateEntry(e: Entry): Promise<void> {
  const db = await getDB();
  await db.put("entries", e);
}

export async function allEntries(): Promise<Entry[]> {
  const db = await getDB();
  const all = await db.getAll("entries");
  return all.sort((a, b) => a.id - b.id);
}

export async function getMeta<T>(key: string): Promise<T | undefined> {
  const db = await getDB();
  return (await db.get("meta", key)) as T | undefined;
}

export async function setMeta(key: string, value: unknown): Promise<void> {
  const db = await getDB();
  await db.put("meta", value, key);
}

/** Ask the browser to keep our data (resist eviction under storage pressure). */
export async function requestPersistence(): Promise<boolean> {
  if (navigator.storage?.persist) {
    return navigator.storage.persist();
  }
  return false;
}

/** Data ownership: export the whole journal as JSON. */
export async function exportJSON(): Promise<string> {
  const entries = await allEntries();
  return JSON.stringify({ app: "pocket-confidant", version: 1, entries }, null, 2);
}
