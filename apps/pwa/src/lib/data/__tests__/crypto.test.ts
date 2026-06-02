import { describe, it, expect } from "vitest";
import {
  deriveKey,
  encryptString,
  decryptString,
  newSaltB64,
} from "../crypto";

describe("crypto (AES-GCM + PBKDF2)", () => {
  it("round-trips a string with the right passphrase", async () => {
    const salt = newSaltB64();
    const key = await deriveKey("correct horse battery staple", salt);
    const plaintext = "A private thought I'd never put on a server.";

    const payload = await encryptString(key, plaintext);
    expect(payload).not.toContain(plaintext); // stored value is ciphertext

    const recovered = await decryptString(key, payload);
    expect(recovered).toBe(plaintext);
  });

  it("round-trips unicode and empty strings", async () => {
    const salt = newSaltB64();
    const key = await deriveKey("pass", salt);

    for (const text of ["", "emoji 🎙 and accents é ü ñ", "line1\nline2"]) {
      const payload = await encryptString(key, text);
      expect(await decryptString(key, payload)).toBe(text);
    }
  });

  it("fails to decrypt with the wrong passphrase", async () => {
    const salt = newSaltB64();
    const right = await deriveKey("right-passphrase", salt);
    const wrong = await deriveKey("wrong-passphrase", salt);

    const payload = await encryptString(right, "secret");

    // GCM authentication should reject the wrong key.
    await expect(decryptString(wrong, payload)).rejects.toBeDefined();
  });

  it("fails to decrypt tampered ciphertext", async () => {
    const salt = newSaltB64();
    const key = await deriveKey("pass", salt);
    const payload = await encryptString(key, "integrity matters");

    // Flip the last base64 char to corrupt the GCM tag / ciphertext.
    const tampered =
      payload.slice(0, -2) + (payload.slice(-2, -1) === "A" ? "B" : "A") + payload.slice(-1);

    await expect(decryptString(key, tampered)).rejects.toBeDefined();
  });

  it("produces a different IV (and thus payload) each call", async () => {
    const salt = newSaltB64();
    const key = await deriveKey("pass", salt);
    const a = await encryptString(key, "same text");
    const b = await encryptString(key, "same text");
    expect(a).not.toBe(b); // random IV per encryption
    expect(await decryptString(key, a)).toBe("same text");
    expect(await decryptString(key, b)).toBe("same text");
  });

  it("newSaltB64 yields distinct salts", () => {
    expect(newSaltB64()).not.toBe(newSaltB64());
  });
});
