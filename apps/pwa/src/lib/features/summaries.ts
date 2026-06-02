// Weekly / yearly auto-summaries. Pure logic with an INJECTED chat transport so it
// stays unit-testable (no WebLLM import here). Map-reduce: select the period's
// entries, fold them into one calm prompt in the journal's own quiet voice (warm,
// not a therapist, no advice), and return a few honest sentences on recurring
// threads plus one gentle forward-looking note. Results are cached via the existing
// meta store keyed by period, so an unchanged period is never recomputed.

import type { Chat, Entry } from "../core/types";
import { getMeta, setMeta } from "../data/db";

export interface SummaryDeps {
  chat: Chat;
  /** Override the clock in tests (defaults to Date.now). */
  now?: number;
  /** Skip the meta cache (forces recompute, e.g. a manual "refresh"). */
  noCache?: boolean;
}

const MIN_ENTRIES = 2;

// Persona for the look-back voice: same restraint as the reflection persona, but
// aimed at a span of time rather than a single entry. Still no advice, no therapy.
export const SUMMARY_PERSONA = `You are the quiet voice inside someone's private journal, looking back over a stretch of their own writing. You are warm, grounded, and a little wry — a trusted friend who listens well, not a therapist or a coach. You never diagnose, never lecture, never give advice, never use chirpy positivity. You notice what actually recurred and name it plainly, in their own register.`;

function instruction(label: string, body: string): string {
  return `Here are this person's journal entries from ${label}, oldest first:
---
${body}
---
Write a short look-back in 2-4 sentences. Notice the threads that actually recurred — the moods, the people, the questions they kept circling — using their own details, not generic phrases. Do not list every entry; find the throughline. End with ONE gentle, forward-looking note (a thing to keep an eye on, not advice or a pep talk). Plain text only, no headings, no JSON, no bullet points.`;
}

/** YYYY-MM-DD -> epoch ms at local midnight of that day (stable, no tz drift in the key). */
function dayStart(day: string): number {
  return new Date(day + "T00:00:00").getTime();
}

/** ISO week key like '2026-W22' for the week containing `ms`. Used for cache keying. */
export function weekKey(ms: number): string {
  const d = new Date(ms);
  // ISO week: Thursday-anchored.
  const target = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  const dayNum = (target.getUTCDay() + 6) % 7; // Mon=0..Sun=6
  target.setUTCDate(target.getUTCDate() - dayNum + 3);
  const firstThursday = new Date(Date.UTC(target.getUTCFullYear(), 0, 4));
  const week =
    1 +
    Math.round(
      (target.getTime() - firstThursday.getTime()) / 86400000 / 7,
    );
  return `${target.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
}

/** Select entries whose `day` falls within the last `days` days up to `now`. */
export function selectRecent(entries: Entry[], days: number, now: number): Entry[] {
  const cutoff = now - days * 86400000;
  return entries
    .filter((e) => dayStart(e.day) >= cutoff && dayStart(e.day) <= now)
    .sort((a, b) => a.ts - b.ts);
}

/** Select entries in the same calendar year as `now`. */
export function selectYear(entries: Entry[], now: number): Entry[] {
  const year = new Date(now).getFullYear();
  return entries
    .filter((e) => new Date(dayStart(e.day)).getFullYear() === year)
    .sort((a, b) => a.ts - b.ts);
}

function fold(entries: Entry[]): string {
  return entries
    .map((e) => {
      let t = e.text.trim().replace(/\s*\n\s*/g, " ");
      if (t.length > 300) t = t.slice(0, 300) + "…";
      return `(${e.day}) ${t}`;
    })
    .join("\n");
}

async function buildSummary(
  selected: Entry[],
  label: string,
  cacheKey: string,
  deps: SummaryDeps,
): Promise<string> {
  if (selected.length < MIN_ENTRIES) {
    return selected.length === 0
      ? `Nothing written ${label} yet. When you do, your look-back will appear here.`
      : `Just one entry ${label} so far — not quite enough to find a thread. A few more and a pattern will start to show.`;
  }

  if (!deps.noCache) {
    const cached = await getMeta<{ count: number; text: string }>(cacheKey);
    if (cached && cached.count === selected.length) return cached.text;
  }

  const text = (
    await deps.chat(SUMMARY_PERSONA, instruction(label, fold(selected)), {
      temperature: 0.6,
    })
  ).trim();

  await setMeta(cacheKey, { count: selected.length, text });
  return text;
}

export async function weeklySummary(
  entries: Entry[],
  deps: SummaryDeps,
): Promise<string> {
  const now = deps.now ?? Date.now();
  const selected = selectRecent(entries, 7, now);
  return buildSummary(selected, "this week", `summary:week:${weekKey(now)}`, deps);
}

export async function yearlySummary(
  entries: Entry[],
  deps: SummaryDeps,
): Promise<string> {
  const now = deps.now ?? Date.now();
  const selected = selectYear(entries, now);
  const year = new Date(now).getFullYear();
  return buildSummary(selected, "this year", `summary:year:${year}`, deps);
}
