// Encryption-at-rest for Pocket Confidant.
//
// THREAT MODEL
// ------------
// What this protects: the *confidentiality of journal text at rest* if the
// physical device (or a raw copy of the IndexedDB / OS storage) is stolen or
// imaged by someone who does NOT know the user's passphrase. Entry text and
// reflections are wrapped with AES-GCM before they touch the database, so a
// dump of the on-disk store yields only ciphertext.
//
// What this does NOT protect against:
//   - A live, unlocked session. Once the user types the passphrase the derived
//     key lives in memory (a non-extractable CryptoKey) and plaintext is visible
//     in the running app — this is unavoidable for a usable journal.
//   - Malware / a compromised browser / a malicious extension with DOM access.
//   - A weak passphrase. PBKDF2 raises the cost of brute force but cannot rescue
//     a trivial passphrase. Security scales with passphrase entropy.
//
// Key handling: the passphrase is NEVER stored anywhere — not in IndexedDB, not
// in localStorage, not in meta. Only a random per-user salt is persisted (it is
// not secret). The AES key is re-derived from passphrase+salt on every unlock
// and kept only in volatile memory as a non-extractable key. Lose the
// passphrase => the data is unrecoverable by design.
//
// Crypto choices: AES-GCM (256-bit) for authenticated encryption (tamper
// detection via the GCM tag); PBKDF2-HMAC-SHA-256 with a high iteration count
// for key stretching. A fresh 12-byte IV is generated per encryption and
// prepended to the ciphertext. Dependency-free: only globalThis.crypto.subtle.

const subtle = globalThis.crypto.subtle;

// PBKDF2 work factor. Higher = slower brute force but slower unlock. 210k is in
// line with current OWASP guidance for PBKDF2-HMAC-SHA256.
const PBKDF2_ITERATIONS = 210_000;
const SALT_BYTES = 16;
const IV_BYTES = 12; // 96-bit nonce — the recommended size for AES-GCM
const KEY_BITS = 256;

const encoder = new TextEncoder();
const decoder = new TextDecoder();

function bytesToB64(bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

// Note the explicit Uint8Array<ArrayBuffer>: under TS's stricter typed-array
// generics, WebCrypto's BufferSource requires an ArrayBuffer-backed view (not a
// possibly-SharedArrayBuffer one), so we pin the backing buffer type here.
function b64ToBytes(b64: string): Uint8Array<ArrayBuffer> {
  const binary = atob(b64);
  const bytes = new Uint8Array(new ArrayBuffer(binary.length));
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

/** Generate a fresh random salt (base64). Not secret; persist alongside data. */
export function newSaltB64(): string {
  const salt = new Uint8Array(SALT_BYTES);
  globalThis.crypto.getRandomValues(salt);
  return bytesToB64(salt);
}

/**
 * Derive a non-extractable AES-GCM key from a passphrase + persisted salt.
 * The same passphrase + salt always yields the same key, so unlocking a stored
 * journal just means re-deriving. A wrong passphrase derives a *different* key,
 * which then fails GCM authentication on decrypt (see decryptString).
 */
export async function deriveKey(
  passphrase: string,
  saltB64: string,
): Promise<CryptoKey> {
  const baseKey = await subtle.importKey(
    "raw",
    encoder.encode(passphrase),
    "PBKDF2",
    false,
    ["deriveKey"],
  );
  return subtle.deriveKey(
    {
      name: "PBKDF2",
      salt: b64ToBytes(saltB64),
      iterations: PBKDF2_ITERATIONS,
      hash: "SHA-256",
    },
    baseKey,
    { name: "AES-GCM", length: KEY_BITS },
    false, // non-extractable: the raw key bytes never leave WebCrypto
    ["encrypt", "decrypt"],
  );
}

/**
 * Encrypt a UTF-8 string. Returns base64 of (iv || ciphertext+tag), so the
 * single string is self-contained for storage. A fresh random IV is used every
 * call — never reuse an IV with the same key under GCM.
 */
export async function encryptString(
  key: CryptoKey,
  plaintext: string,
): Promise<string> {
  const iv = new Uint8Array(IV_BYTES);
  globalThis.crypto.getRandomValues(iv);
  const ciphertext = new Uint8Array(
    await subtle.encrypt(
      { name: "AES-GCM", iv },
      key,
      encoder.encode(plaintext),
    ),
  );
  const payload = new Uint8Array(iv.length + ciphertext.length);
  payload.set(iv, 0);
  payload.set(ciphertext, iv.length);
  return bytesToB64(payload);
}

/**
 * Decrypt a payload produced by encryptString. Throws if the key is wrong or
 * the data was tampered with (GCM authentication failure) — callers can treat a
 * thrown error as "wrong passphrase / corrupt data".
 */
export async function decryptString(
  key: CryptoKey,
  payload: string,
): Promise<string> {
  const bytes = b64ToBytes(payload);
  const iv = bytes.slice(0, IV_BYTES);
  const ciphertext = bytes.slice(IV_BYTES);
  const plaintext = await subtle.decrypt(
    { name: "AES-GCM", iv },
    key,
    ciphertext,
  );
  return decoder.decode(plaintext);
}
