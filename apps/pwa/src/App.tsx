import { useEffect, useMemo, useState } from "react";
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
} from "./lib/data/db";

type View = "write" | "history" | "ask";

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export function App() {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [view, setView] = useState<View>("write");
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [lastReflection, setLastReflection] = useState<string | null>(null);

  // Model lifecycle
  const [modelReady, setModelReady] = useState(false);
  const [loadPct, setLoadPct] = useState(0);
  const [loadMsg, setLoadMsg] = useState("");
  const [loadError, setLoadError] = useState<string | null>(null);
  const webgpu = useMemo(() => hasWebGPU(), []);

  // Ask-your-journal
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AskResult | null>(null);

  useEffect(() => {
    (async () => {
      await requestPersistence();
      setEntries(await allEntries());
      // Warm the small embedder immediately — recall/ask work even without WebGPU.
      initEmbedder().catch(() => {});
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
      let question = "";
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
        question = r.question;
        callback = r.callback;
        setLastReflection(renderReflection(r));
      }
      const saved = await addEntry({
        ts: Date.now(),
        day: today(),
        text,
        reflection: reflectionText,
        question,
        callback,
        embedding: vec,
        mood: null,
        energy: null,
        model,
        encrypted: false,
      });
      setEntries((prev) => [...prev, saved]);
      setDraft("");
    } finally {
      setBusy(false);
    }
  }

  async function ask() {
    const q = question.trim();
    if (!q || busy) return;
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
    const json = await exportJSON();
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `pocket-confidant-${today()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const byDayDesc = [...entries].reverse();

  return (
    <div className="app">
      <header className="masthead">
        <h1>Pocket Confidant</h1>
        <p className="tagline">Your private mind, understood — 100% on your device.</p>
        <nav>
          <button className={view === "write" ? "on" : ""} onClick={() => setView("write")}>
            Write
          </button>
          <button className={view === "ask" ? "on" : ""} onClick={() => setView("ask")}>
            Ask your journal
          </button>
          <button className={view === "history" ? "on" : ""} onClick={() => setView("history")}>
            History
          </button>
        </nav>
      </header>

      {!modelReady && (
        <section className="loader card">
          {loadPct === 0 && !loadError && (
            <>
              <p>
                Set up your private companion. This downloads a small model{" "}
                <strong>once</strong> — then it’s instant, offline, and nothing ever
                leaves this device.
              </p>
              <button className="primary" onClick={startModel}>
                {webgpu ? "Set up (one-time)" : "Continue without reflections"}
              </button>
              <p className="hint">You can start writing below while it loads.</p>
            </>
          )}
          {loadPct > 0 && (
            <>
              <div className="bar">
                <div className="fill" style={{ width: `${loadPct}%` }} />
              </div>
              <p className="hint">
                {loadPct}% · {loadMsg || "downloading…"} (resumes if interrupted)
              </p>
            </>
          )}
          {loadError && <p className="hint error">{loadError}</p>}
        </section>
      )}

      {view === "write" && (
        <section className="write">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="What’s on your mind?"
            rows={7}
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
          {!modelReady && <p className="hint">Set up the model above to ask questions.</p>}
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
