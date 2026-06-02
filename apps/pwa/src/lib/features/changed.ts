// "How have I changed?" — a longitudinal look-back the user can't generate alone.
// Pure logic with an INJECTED chat transport (no model import here, so it stays
// unit-testable). Split the journal into an EARLIER window and a RECENT window and
// ask the journal's quiet voice for an honest, non-flattering note on what shifted
// in theme and tone. Embeddings are intentionally optional — this works on text.

import type { Chat, Entry } from "../core/types";

export interface ChangedDeps {
  chat: Chat;
}

// At least this many entries in EACH window, or there isn't enough to compare.
const MIN_PER_WINDOW = 3;

export const CHANGED_PERSONA = `You are the quiet voice inside someone's private journal, comparing how they wrote a while ago with how they write now. You are warm but honest — a trusted friend, not a therapist or a cheerleader. You name real shifts in what they dwell on and how they sound, including the unflattering ones, without judgement and without advice. You never flatter, never claim growth that isn't there, and never pretend nothing changed if it did.`;

export const CHANGED_INSTRUCTION = (earlier: string, recent: string) =>
  `EARLIER entries (further back), oldest first:
---
${earlier}
---
RECENT entries (lately), oldest first:
---
${recent}
---
In 2-4 plain sentences, say honestly how this person has — or hasn't — changed between then and now: what they dwell on, their tone, what's grown or gone quiet. Use their actual details. Be honest, not flattering; if little has changed, say that plainly. No advice, no headings, no JSON.`;

function fold(entries: Entry[]): string {
  return entries
    .map((e) => {
      let t = e.text.trim().replace(/\s*\n\s*/g, " ");
      if (t.length > 280) t = t.slice(0, 280) + "…";
      return `(${e.day}) ${t}`;
    })
    .join("\n");
}

/**
 * Split entries (assumed chronological by id/ts) into an earlier half and a
 * recent half. With an odd count the recent window gets the extra entry.
 */
export function splitWindows(entries: Entry[]): {
  earlier: Entry[];
  recent: Entry[];
} {
  const sorted = [...entries].sort((a, b) => a.ts - b.ts);
  const mid = Math.floor(sorted.length / 2);
  return { earlier: sorted.slice(0, mid), recent: sorted.slice(mid) };
}

export async function howHaveIChanged(
  entries: Entry[],
  deps: ChangedDeps,
): Promise<string> {
  const { earlier, recent } = splitWindows(entries);

  if (earlier.length < MIN_PER_WINDOW || recent.length < MIN_PER_WINDOW) {
    return "There's not enough history yet to see how you've changed. Keep writing — once there's a stretch of earlier entries to compare against, this will fill in.";
  }

  // Keep prompts bounded: the most recent slice of each window carries the signal.
  const earlierSlice = earlier.slice(-8);
  const recentSlice = recent.slice(-8);

  const text = await deps.chat(
    CHANGED_PERSONA,
    CHANGED_INSTRUCTION(fold(earlierSlice), fold(recentSlice)),
    { temperature: 0.6 },
  );
  return text.trim();
}
