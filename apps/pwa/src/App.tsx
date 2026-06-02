import { useEffect, useMemo, useRef, useState } from "react";
import type { Entry } from "./lib/core/types";
import { renderReflection } from "./lib/core/types";
import { reflect } from "./lib/core/reflect";
import { askJournal, type AskResult } from "./lib/features/askJournal";
import {
  loadModel,
  chat,
  hasWebGPU,
  DEFAULT_MODEL,
  currentModel,
} from "./lib/ai/llm";
import { embed, initEmbedder } from "./lib/ai/embed";
import {
  addEntry,
  allEntries,
  requestPersistence,
  exportJSON,
  getMeta,
  setMeta,
} from "./lib/data/db";
import {
  encEnabled,
  encSalt,
  setEncSalt,
  enableEncryption,
  verifyKey,
  encryptEntry,
  decryptAll,
  ENC_ENABLED_KEY,
} from "./lib/data/encStore";

// Feature components built by the fleet.
import MoodEnergyTag from "./components/MoodEnergyTag";
import Trends from "./components/Trends";
import Summary from "./components/Summary";
import StreakBadge from "./components/StreakBadge";
import ReminderSettings from "./components/ReminderSettings";
import Settings from "./components/Settings";
import Paywall from "./components/Paywall";
import VoiceButton from "./components/VoiceButton";
import LockScreen from "./components/LockScreen";
import Welcome from "./components/Welcome";
import ModelLoader from "./components/ModelLoader";

// Feature logic.
import { maybeNotify } from "./lib/features/reminders";
import {
  getTier,
  setTier as persistTier,
  isAllowed,
  type Tier,
  type Feature,
} from "./lib/features/entitlements";

import "./components/settings.css";
import "./integration.css";

type View = "write" | "ask" | "insights" | "reflect" | "history" | "settings";

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export function App() {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [view, setView] = useState<View>("write");
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [lastReflection, setLastReflection] = useState<string | null>(null);

  // Mood/energy tags for the entry being written.
  const [mood, setMood] = useState<number | null>(null);
  const [energy, setEnergy] = useState<number | null>(null);

  // Model lifecycle
  const [modelReady, setModelReady] = useState(false);
  const [loadPct, setLoadPct] = useState(0);
  const [loadMsg, setLoadMsg] = useState("");
  const [loadError, setLoadError] = useState<string | null>(null);
  const webgpu = useMemo(() => hasWebGPU(), []);

  // Ask-your-journal
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AskResult | null>(null);

  // Onboarding (first-run welcome). null = still loading the flag.
  const [seenWelcome, setSeenWelcome] = useState<boolean | null>(null);

  // Entitlements + paywall.
  const [tier, setTier] = useState<Tier>("free");
  const [paywallFor, setPaywallFor] = useState<string | null>(null);

  // Encryption-at-rest (optional, OFF by default).
  const [encOn, setEncOn] = useState(false);
  const [salt, setSalt] = useState<string | null>(null);
  const [key, setKey] = useState<CryptoKey | null>(null);
  const [keyError, setKeyError] = useState<string | null>(null);
  // The SETUP LockScreen mints a salt and passes it to onSetup *before* onUnlock;
  // we stash it here so onUnlock can persist a salt that matches the derived key.
  const pendingSalt = useRef<string | null>(null);
  // While encryption is on but we have no key yet, the journal is locked.
  const locked = encOn && key === null;

  // Boot: load entries, flags, tier, encryption state; warm the embedder.
  useEffect(() => {
    (async () => {
      await requestPersistence();
      const [welcome, t, on, s] = await Promise.all([
        getMeta<boolean>("seenWelcome"),
        getTier(),
        encEnabled(),
        encSalt(),
      ]);
      setSeenWelcome(welcome ?? false);
      setTier(t);
      setEncOn(on);
      setSalt(s);
      // Only safe to read entries into the plaintext UI when not locked.
      if (!on) {
        setEntries(await allEntries());
      }
      // Warm the small embedder immediately — recall/ask work even without WebGPU.
      initEmbedder().catch(() => {});
      // Opportunistic, gentle reminder when the app is opened.
      void maybeNotify();
    })();
  }, []);

  const recentOpeners = useMemo(
    () =>
      entries
        .slice(-3)
        .map((e) => e.reflection.trim().toLowerCase().split(/\s+/).slice(0, 6).join(" ")),
    [entries],
  );

  async function startModel() {
    setLoadError(null);
    if (!webgpu) {
      setLoadError(
        "This browser has no WebGPU, so reflections are off — but journaling and ‘ask your journal’ still work fully on-device.",
      );
      return;
    }
    try {
      await loadModel(DEFAULT_MODEL, (r) => {
        setLoadPct(Math.round((r.progress ?? 0) * 100));
        setLoadMsg(r.text ?? "");
      });
      setModelReady(true);
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : String(e));
    }
  }

  async function submitEntry() {
    const text = draft.trim();
    if (!text || busy) return;
    setBusy(true);
    setLastReflection(null);
    try {
      const vec = await embed(text).catch(() => null);
      let reflectionText = "";
      let q = "";
      let callback = "";
      const model = currentModel() ?? "(none)";
      if (modelReady) {
        const r = await reflect(text, entries, {
          chat,
          embed,
          model,
          beforeId: null,
          recentOpeners,
        });
        reflectionText = r.reflection;
        q = r.question;
        callback = r.callback;
        setLastReflection(renderReflection(r));
      }
      // Encrypt text/reflection at rest when a key is held.
      const wrapped = await encryptEntry(
        { text, reflection: reflectionText, encrypted: false },
        key,
      );
      const saved = await addEntry({
        ts: Date.now(),
        day: today(),
        text: wrapped.text,
        reflection: wrapped.reflection,
        question: q,
        callback,
        embedding: vec,
        mood,
        energy,
        model,
        encrypted: wrapped.encrypted,
      });
      // Keep the in-memory copy as plaintext for display/recall.
      const plain: Entry = {
        ...saved,
        text,
        reflection: reflectionText,
        encrypted: false,
      };
      setEntries((prev) => [...prev, plain]);
      setDraft("");
      setMood(null);
      setEnergy(null);
    } finally {
      setBusy(false);
    }
  }

  async function ask() {
    const q = question.trim();
    if (!q || busy) return;
    if (!isAllowed("basic-ask", tier)) {
      setPaywallFor("unlimited-ask");
      return;
    }
    setBusy(true);
    setAnswer(null);
    try {
      const res = await askJournal(q, entries, { chat, embed });
      setAnswer(res);
    } finally {
      setBusy(false);
    }
  }

  async function doExport() {
    if (!isAllowed("export", tier)) {
      setPaywallFor("export");
      return;
    }
    const json = await exportJSON();
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `pocket-confidant-${today()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Gate a Pro-only view: navigate if allowed, else surface the paywall.
  function goto(target: View, feature?: Feature) {
    if (feature && !isAllowed(feature, tier)) {
      setPaywallFor(feature);
      return;
    }
    setView(target);
  }

  // --- Encryption unlock (existing journal) ------------------------------
  async function onUnlock(k: CryptoKey) {
    setKeyError(null);
    const ok = await verifyKey(k);
    if (!ok) {
      setKey(null);
      setKeyError("That passphrase didn't unlock your journal. Try again.");
      return;
    }
    setKey(k);
    const all = await allEntries();
    setEntries(await decryptAll(all, k));
  }

  // --- Encryption enable (from Settings, SETUP mode) ---------------------
  // LockScreen(saltB64=null) mints a salt -> onSetup(salt) -> onUnlock(key).
  // We capture the salt in onSetup, then finalize in onUnlock.
  async function finalizeEnable(k: CryptoKey) {
    const s = pendingSalt.current;
    if (!s) return;
    await setEncSalt(s);
    await enableEncryption(k);
    pendingSalt.current = null;
    setSalt(s);
    setEncOn(true);
    setKey(k);
    setKeyError(null);
  }

  async function disableEncryptionFlow() {
    await setMeta(ENC_ENABLED_KEY, false);
    setEncOn(false);
    setKey(null);
    setKeyError(null);
    setEntries(await allEntries());
  }

  const byDayDesc = [...entries].reverse();

  // 1) First-run welcome takeover.
  if (seenWelcome === false) {
    return (
      <div className="app">
        <header className="masthead">
          <h1>Pocket Confidant</h1>
        </header>
        <Welcome
          webgpu={webgpu}
          onBegin={() => {
            setSeenWelcome(true);
            void setMeta("seenWelcome", true);
          }}
        />
      </div>
    );
  }

  // Avoid a flash before the flag resolves.
  if (seenWelcome === null) {
    return (
      <div className="app">
        <header className="masthead">
          <h1>Pocket Confidant</h1>
        </header>
      </div>
    );
  }

  // 2) Encryption lock gate (only when encryption is enabled and not yet unlocked).
  if (locked) {
    return (
      <div className="app">
        <header className="masthead">
          <h1>Pocket Confidant</h1>
          <p className="tagline">Your private mind, understood — 100% on your device.</p>
        </header>
        {keyError && <p className="hint error">{keyError}</p>}
        <LockScreen
          saltB64={salt}
          onSetup={(s) => void setEncSalt(s)}
          onUnlock={(k) => void onUnlock(k)}
        />
      </div>
    );
  }

  return (
    <div className="app">
      <header className="masthead">
        <div className="masthead-top">
          <h1>Pocket Confidant</h1>
          <StreakBadge entries={entries} />
        </div>
        <p className="tagline">Your private mind, understood — 100% on your device.</p>
        <nav>
          <button className={view === "write" ? "on" : ""} onClick={() => setView("write")}>
            Write
          </button>
          <button className={view === "ask" ? "on" : ""} onClick={() => setView("ask")}>
            Ask
          </button>
          <button
            className={view === "insights" ? "on" : ""}
            onClick={() => goto("insights", "trends")}
          >
            Insights
          </button>
          <button
            className={view === "reflect" ? "on" : ""}
            onClick={() => goto("reflect", "yearly-summary")}
          >
            Reflect back
          </button>
          <button className={view === "history" ? "on" : ""} onClick={() => setView("history")}>
            History
          </button>
          <button className={view === "settings" ? "on" : ""} onClick={() => setView("settings")}>
            Settings
          </button>
        </nav>
      </header>

      {!modelReady && view === "write" && (
        <ModelLoader
          pct={loadPct}
          msg={loadMsg}
          error={loadError}
          onStart={startModel}
          webgpu={webgpu}
        />
      )}

      {view === "write" && (
        <section className="write">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="What’s on your mind?"
            rows={7}
          />
          <div className="write-tools">
            <VoiceButton onText={(t) => setDraft((d) => (d ? d + " " : "") + t)} />
          </div>
          <MoodEnergyTag
            mood={mood}
            energy={energy}
            onChange={(m, e) => {
              setMood(m);
              setEnergy(e);
            }}
          />
          <button className="primary" onClick={submitEntry} disabled={busy || !draft.trim()}>
            {busy ? "…" : modelReady ? "Reflect" : "Save entry"}
          </button>
          {lastReflection && (
            <div className="card reflection">
              {lastReflection.split("\n\n").map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </div>
          )}
          {entries.length === 0 && !lastReflection && (
            <p className="empty">
              Write your first entry. It stays here, on your device — no cloud, no
              account.
            </p>
          )}
        </section>
      )}

      {view === "ask" && (
        <section className="ask">
          <p className="hint">
            Ask anything about your own past — answered privately, only from your
            entries.
          </p>
          <div className="askrow">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="When did I last feel like this?"
              onKeyDown={(e) => e.key === "Enter" && ask()}
            />
            <button className="primary" onClick={ask} disabled={busy || !modelReady}>
              Ask
            </button>
          </div>
          {!modelReady && (
            <p className="hint">Set up the model on the Write tab to ask questions.</p>
          )}
          {answer && (
            <div className="card reflection">
              <p>{answer.answer}</p>
              {answer.sources.length > 0 && (
                <div className="chips">
                  {answer.sources.map((s) => (
                    <span key={s.id} className="chip">
                      {s.day}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>
      )}

      {view === "insights" && <Trends entries={entries} />}

      {view === "reflect" && <Summary entries={entries} chat={chat} />}

      {view === "history" && (
        <section className="history">
          <div className="historyhead">
            <span className="hint">{entries.length} entries · all on this device</span>
            <button className="quiet" onClick={doExport}>
              Export
            </button>
          </div>
          {byDayDesc.map((e) => (
            <div key={e.id} className="card entry">
              <div className="day">{e.day}</div>
              <p className="text">{e.text}</p>
              {e.reflection && (
                <p className="echo">
                  {e.callback ? e.callback + " " : ""}
                  {e.reflection} <span className="q">{e.question}</span>
                </p>
              )}
            </div>
          ))}
          {entries.length === 0 && <p className="empty">No entries yet.</p>}
        </section>
      )}

      {view === "settings" && (
        <section className="settings-view">
          <Settings
            entries={entries}
            onExport={doExport}
            tier={tier}
            onUpgrade={() => setPaywallFor("upgrade")}
            modelInfo={currentModel() ?? "not loaded"}
            webgpu={webgpu}
          />

          <ReminderSettings />

          {/* Optional at-rest encryption. OFF by default; the app works without it. */}
          <section className="card">
            <strong style={{ fontFamily: "var(--serif)", fontSize: "1.05rem" }}>
              At-rest encryption {encOn ? "(on)" : "(off)"}
            </strong>
            <p className="hint" style={{ marginTop: "0.4rem" }}>
              Everything already stays on this device. Turning this on adds a
              passphrase so new entries are encrypted in storage — if someone gets
              your browser's data, they only see ciphertext. The passphrase is never
              stored; lose it and those entries can't be recovered.
            </p>
            {!isAllowed("encryption", tier) ? (
              <button className="quiet" onClick={() => setPaywallFor("encryption")}>
                Encryption is a Pro feature
              </button>
            ) : encOn ? (
              <button className="quiet" onClick={() => void disableEncryptionFlow()}>
                Turn off encryption
              </button>
            ) : (
              <div className="enc-setup">
                {keyError && <p className="hint error">{keyError}</p>}
                <LockScreen
                  saltB64={null}
                  onSetup={(s) => {
                    pendingSalt.current = s;
                  }}
                  onUnlock={(k) => void finalizeEnable(k)}
                />
              </div>
            )}
          </section>

          {/* Plan preview (no payments in v1). */}
          <section className="card">
            <strong style={{ fontFamily: "var(--serif)", fontSize: "1.05rem" }}>Plan</strong>
            <p className="hint" style={{ marginTop: "0.4rem" }}>
              You're on the <strong>{tier}</strong> plan. Payments aren't available
              yet; you can preview Pro here.
            </p>
            <button
              className="quiet"
              onClick={async () => {
                const next: Tier = tier === "pro" ? "free" : "pro";
                await persistTier(next);
                setTier(next);
              }}
            >
              {tier === "pro" ? "Switch to free" : "Preview Pro"}
            </button>
          </section>
        </section>
      )}

      {paywallFor && (
        <Paywall
          feature={paywallFor}
          onClose={() => setPaywallFor(null)}
          onUpgrade={async () => {
            // No payments in v1 — preview Pro so the gated feature opens.
            await persistTier("pro");
            setTier("pro");
            setPaywallFor(null);
          }}
        />
      )}

      <footer className="foot">
        <span>🔌 offline</span>
        <span>·</span>
        <span>🔒 nothing leaves this device</span>
        <span>·</span>
        <span>{webgpu ? "WebGPU ✓" : "no WebGPU"}</span>
      </footer>
    </div>
  );
}
