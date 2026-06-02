// Thin encryption glue between the app and the entry store. Lives in the
// integrator/db layer (not in crypto.ts, not in db.ts) so the pure crypto and the
// raw IndexedDB store both stay untouched.
//
// When a CryptoKey is held, `text` and `reflection` on an Entry are wrapped with
// AES-GCM before they're written, and unwrapped after they're read. `encrypted`
// is the at-rest marker: true => the stored text/reflection are ciphertext.
//
// Meta keys used (all via the existing getMeta/setMeta — no new DB store):
//   enc.enabled  : boolean  — has the user turned encryption on
//   enc.salt     : string   — base64 PBKDF2 salt (not secret)
//   enc.canary   : string   — encryptString(key, CANARY_PLAINTEXT), used to
//                              verify a passphrase on unlock
//
// Why a canary: PBKDF2 always derives *a* key, so a wrong passphrase can only be
// detected by attempting an authenticated decrypt. We decrypt the canary on
// unlock; a thrown error means "wrong passphrase".

import type { Entry } from "../core/types";
import { encryptString, decryptString } from "./crypto";
import { getMeta, setMeta } from "./db";

export const ENC_ENABLED_KEY = "enc.enabled";
export const ENC_SALT_KEY = "enc.salt";
export const ENC_CANARY_KEY = "enc.canary";

const CANARY_PLAINTEXT = "pocket-confidant-canary-v1";

/** Is at-rest encryption turned on for this device? */
export async function encEnabled(): Promise<boolean> {
  return (await getMeta<boolean>(ENC_ENABLED_KEY)) === true;
}

/** Persisted salt (base64), or null if encryption has never been set up. */
export async function encSalt(): Promise<string | null> {
  return (await getMeta<string>(ENC_SALT_KEY)) ?? null;
}

/** Persist the salt minted during LockScreen setup. */
export async function setEncSalt(saltB64: string): Promise<void> {
  await setMeta(ENC_SALT_KEY, saltB64);
}

/**
 * Finish enabling encryption once we hold a key: write a canary so future
 * unlocks can verify the passphrase, and flip the enabled flag on.
 */
export async function enableEncryption(key: CryptoKey): Promise<void> {
  await setMeta(ENC_CANARY_KEY, await encryptString(key, CANARY_PLAINTEXT));
  await setMeta(ENC_ENABLED_KEY, true);
}

/**
 * Verify a freshly derived key against the stored canary. Returns true if the
 * passphrase was correct. If no canary exists yet (older setup), we accept the
 * key — it's the first one in and there's nothing to contradict it.
 */
export async function verifyKey(key: CryptoKey): Promise<boolean> {
  const canary = await getMeta<string>(ENC_CANARY_KEY);
  if (!canary) return true;
  try {
    return (await decryptString(key, canary)) === CANARY_PLAINTEXT;
  } catch {
    return false;
  }
}

/** Wrap an entry's text/reflection for storage. No-op (returns input) if no key. */
export async function encryptEntry<T extends Pick<Entry, "text" | "reflection" | "encrypted">>(
  entry: T,
  key: CryptoKey | null,
): Promise<T> {
  if (!key) return { ...entry, encrypted: false };
  return {
    ...entry,
    text: await encryptString(key, entry.text),
    reflection: entry.reflection ? await encryptString(key, entry.reflection) : entry.reflection,
    encrypted: true,
  };
}

/**
 * Unwrap a stored entry for display/recall. Only touches entries flagged
 * `encrypted`. If decryption fails (wrong key), the entry is returned as-is so the
 * UI never crashes — the caller is expected to have verified the key first.
 */
export async function decryptEntry(entry: Entry, key: CryptoKey | null): Promise<Entry> {
  if (!entry.encrypted || !key) return entry;
  try {
    return {
      ...entry,
      text: await decryptString(key, entry.text),
      reflection: entry.reflection ? await decryptString(key, entry.reflection) : entry.reflection,
      encrypted: false, // in-memory copy is now plaintext
    };
  } catch {
    return entry;
  }
}

/** Decrypt a whole list (used right after allEntries()). */
export async function decryptAll(entries: Entry[], key: CryptoKey | null): Promise<Entry[]> {
  if (!key) return entries;
  return Promise.all(entries.map((e) => decryptEntry(e, key)));
}
