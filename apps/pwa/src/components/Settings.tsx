// Settings — model/diagnostics, data ownership, privacy, and a tasteful Pro
// section. Presentational only: all state + side effects (export, persistence,
// upgrade flow) are owned by App and passed in as callbacks. Matches the warm
// journal aesthetic (reuses .card/.chip/.hint/.primary/.quiet from styles.css).

import { useState } from "react";
import type { Entry } from "../lib/core/types";
import { requestPersistence } from "../lib/data/db";
import { FEATURES_BY_TIER, type Tier } from "../lib/features/entitlements";

export interface SettingsProps {
  entries: Entry[];
  onExport: () => void; // App performs the actual JSON export/download
  tier: Tier;
  onUpgrade: () => void; // open the Pro / paywall flow
  modelInfo: string; // human-readable current model (or "not loaded")
  webgpu: boolean; // hasWebGPU() result, passed from App
}

export default function Settings({
  entries,
  onExport,
  tier,
  onUpgrade,
  modelInfo,
  webgpu,
}: SettingsProps) {
  const [persisted, setPersisted] = useState<boolean | null>(null);
  const isPro = tier === "pro";

  async function onRequestPersistence() {
    const ok = await requestPersistence();
    setPersisted(ok);
  }

  return (
    <div className="settings">
      {/* Model & diagnostics */}
      <section className="card">
        <h2 className="settings-h">On-device engine</h2>
        <div className="settings-row">
          <span className="settings-label">WebGPU</span>
          <span className="chip">
            {webgpu ? "available" : "not available"}
          </span>
        </div>
        <div className="settings-row">
          <span className="settings-label">Reflection model</span>
          <span className="chip">{modelInfo}</span>
        </div>
        {!webgpu && (
          <p className="hint">
            This browser has no WebGPU, so on-device reflections aren't
            available here. Journaling and asking your journal still work.
          </p>
        )}
      </section>

      {/* Data ownership */}
      <section className="card">
        <h2 className="settings-h">Your data</h2>
        <p className="hint">
          {entries.length} {entries.length === 1 ? "entry" : "entries"} stored
          on this device. Nothing ever leaves it.
        </p>
        <div className="settings-actions">
          <button className="quiet" onClick={onExport}>
            Export as JSON
          </button>
          <button className="quiet" onClick={onRequestPersistence}>
            Keep data on this device
          </button>
        </div>
        {persisted !== null && (
          <p className="hint">
            {persisted
              ? "This browser will try to keep your journal even under storage pressure."
              : "The browser declined persistent storage. Your data is still here, but consider exporting a backup."}
          </p>
        )}
      </section>

      {/* Privacy */}
      <section className="card">
        <h2 className="settings-h">Privacy</h2>
        <div className="settings-row">
          <span className="settings-label">At-rest encryption</span>
          <span className="chip">{isPro ? "available" : "Pro"}</span>
        </div>
        <p className="hint">
          Everything already stays on your device. Encryption adds a passphrase
          so entries are unreadable even if someone gets to this browser's
          storage.
        </p>
        <button
          className="quiet"
          disabled
          aria-disabled="true"
          title="Coming soon"
        >
          Set up encryption (coming soon)
        </button>
      </section>

      {/* Pro — tasteful, non-aggressive */}
      <section className="card pro-card">
        <div className="settings-row">
          <h2 className="settings-h" style={{ margin: 0 }}>
            Pocket Confidant Pro
          </h2>
          <span className="chip">{isPro ? "active" : "free plan"}</span>
        </div>

        {isPro ? (
          <p className="hint">
            Thank you for supporting Pocket Confidant. You have everything.
          </p>
        ) : (
          <>
            <p className="hint">
              You're on the free plan — journaling, reflections, and asking your
              journal are yours to keep, always. Pro adds a little more depth
              whenever you want it:
            </p>
            <ul className="pro-list">
              {FEATURES_BY_TIER.pro.map((f) => (
                <li key={f.feature}>
                  <span className="pro-feature">{f.label}</span>
                  <span className="hint"> — {f.description}</span>
                </li>
              ))}
            </ul>
            <button className="primary" onClick={onUpgrade}>
              Upgrade (coming soon)
            </button>
          </>
        )}
      </section>
    </div>
  );
}
