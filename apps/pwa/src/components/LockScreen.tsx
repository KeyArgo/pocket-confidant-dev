// Optional passphrase gate for encryption-at-rest. Presentational: it owns only
// the passphrase input + busy/error state and derives the AES key via crypto.ts.
// The integrator decides *when* to show it (first run to set a passphrase, or on
// app open when encryption is enabled) and what to do with the derived key.
//
// Modes:
//   - saltB64 === null  -> SETUP: first run. User picks a passphrase (twice).
//     We mint a salt, derive the key, hand BOTH back (onSetup(salt) then
//     onUnlock(key)) so the integrator can persist the salt + hold the key.
//   - saltB64 is a string -> UNLOCK: derive the key from the stored salt and
//     hand it back via onUnlock(key). A wrong passphrase can't be detected here
//     directly (PBKDF2 always derives *a* key); the integrator verifies it by
//     attempting to decrypt a known entry and may show this screen again.

import { useState } from "react";
import { deriveKey, newSaltB64 } from "../lib/data/crypto";

export interface LockScreenProps {
  /** Fired with the derived AES key once the user authenticates. */
  onUnlock: (key: CryptoKey) => void;
  /** Persisted salt (base64), or null on first run to enter setup mode. */
  saltB64: string | null;
  /** Fired during setup with the freshly minted salt, BEFORE onUnlock. */
  onSetup: (saltB64: string) => void;
}

export default function LockScreen({
  onUnlock,
  saltB64,
  onSetup,
}: LockScreenProps) {
  const isSetup = saltB64 === null;
  const [passphrase, setPassphrase] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (!passphrase) {
      setError("Enter a passphrase.");
      return;
    }
    if (isSetup) {
      if (passphrase.length < 8) {
        setError("Use at least 8 characters — longer is stronger.");
        return;
      }
      if (passphrase !== confirm) {
        setError("The two passphrases don't match.");
        return;
      }
    }

    setBusy(true);
    try {
      const salt = isSetup ? newSaltB64() : (saltB64 as string);
      const key = await deriveKey(passphrase, salt);
      if (isSetup) onSetup(salt);
      onUnlock(key);
    } catch {
      setError("Couldn't unlock. Try again.");
    } finally {
      setBusy(false);
      setPassphrase("");
      setConfirm("");
    }
  }

  return (
    <div className="card lockscreen">
      <h2 style={{ fontFamily: "var(--serif)", marginTop: 0 }}>
        {isSetup ? "Set a passphrase" : "Unlock your journal"}
      </h2>
      <p className="hint">
        {isSetup
          ? "Your entries are encrypted on this device. The passphrase is never stored — if you lose it, the journal can't be recovered."
          : "Enter your passphrase to decrypt your journal on this device."}
      </p>
      <form onSubmit={submit}>
        <input
          type="password"
          autoComplete={isSetup ? "new-password" : "current-password"}
          placeholder="Passphrase"
          value={passphrase}
          onChange={(e) => setPassphrase(e.target.value)}
          disabled={busy}
          aria-label="Passphrase"
        />
        {isSetup && (
          <input
            type="password"
            autoComplete="new-password"
            placeholder="Confirm passphrase"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            disabled={busy}
            aria-label="Confirm passphrase"
            style={{ marginTop: "0.5rem" }}
          />
        )}
        {error && <p className="hint error">{error}</p>}
        <button type="submit" className="primary" disabled={busy}>
          {busy ? "Working…" : isSetup ? "Encrypt & continue" : "Unlock"}
        </button>
      </form>
    </div>
  );
}
