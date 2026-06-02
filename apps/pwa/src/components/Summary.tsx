// "Reflect back" panel: weekly + yearly auto-summaries and a longitudinal
// "How I've changed" view. Presentational — all app state lives in App.tsx; this
// component owns only its own loading/result UI and calls the injected logic with
// the real chat transport passed down as a prop.

import { useState } from "react";
import type { Chat, Entry } from "../lib/core/types";
import { weeklySummary, yearlySummary } from "../lib/features/summaries";
import { howHaveIChanged } from "../lib/features/changed";

export interface SummaryProps {
  entries: Entry[];
  chat: Chat;
}

type PanelKey = "week" | "year" | "changed";

interface PanelDef {
  key: PanelKey;
  button: string;
  blurb: string;
  run: (entries: Entry[], chat: Chat) => Promise<string>;
}

const PANELS: PanelDef[] = [
  {
    key: "week",
    button: "This week",
    blurb: "A calm look back over the last seven days.",
    run: (entries, chat) => weeklySummary(entries, { chat }),
  },
  {
    key: "year",
    button: "This year",
    blurb: "The threads that have run through your year so far.",
    run: (entries, chat) => yearlySummary(entries, { chat }),
  },
  {
    key: "changed",
    button: "How I've changed",
    blurb: "An honest look at what's shifted between then and now.",
    run: (entries, chat) => howHaveIChanged(entries, { chat }),
  },
];

export default function Summary({ entries, chat }: SummaryProps) {
  const [active, setActive] = useState<PanelKey | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function open(panel: PanelDef) {
    if (busy) return;
    setActive(panel.key);
    setResult(null);
    setError(null);
    setBusy(true);
    try {
      setResult(await panel.run(entries, chat));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  if (entries.length === 0) {
    return (
      <section className="reflectback">
        <p className="hint">
          Insights you can't get anywhere else — drawn only from your own words, on
          your own device.
        </p>
        <p className="empty">
          Write a few entries and your weekly, yearly, and longer-arc reflections
          will appear here.
        </p>
      </section>
    );
  }

  return (
    <section className="reflectback">
      <p className="hint">
        Insights drawn only from your own words — generated on your device, seen by
        no one.
      </p>
      <div className="chips">
        {PANELS.map((p) => (
          <button
            key={p.key}
            className={"quiet" + (active === p.key ? " on" : "")}
            onClick={() => open(p)}
            disabled={busy}
          >
            {p.button}
          </button>
        ))}
      </div>

      {active && (
        <div className="card reflection">
          <p className="hint">{PANELS.find((p) => p.key === active)?.blurb}</p>
          {busy && <p className="empty">Looking back over your entries…</p>}
          {!busy && error && (
            <p className="hint error">Couldn't generate that just now: {error}</p>
          )}
          {!busy &&
            !error &&
            result &&
            result.split(/\n{2,}/).map((para, i) => <p key={i}>{para}</p>)}
        </div>
      )}
    </section>
  );
}
