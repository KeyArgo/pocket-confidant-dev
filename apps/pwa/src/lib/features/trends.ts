// On-device trend insights over the journal. Pure statistics — NO LLM, NO network.
// Drives the "Insights" tab and the headline retention hook
// ("You tend to feel lightest on Sundays"). Everything is derived from the
// mood/energy quick-tags the user attaches to entries, so it stays trustworthy
// and fully local. Guarded against thin data: a single Sunday entry is noise,
// not an insight.

import type { Entry } from "../core/types";

// 'day' is stored as 'YYYY-MM-DD'. Parse as a local date (avoid the UTC shift of
// `new Date('YYYY-MM-DD')`, which would mis-bucket evening entries by a weekday).
const WEEKDAY_LABELS = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
] as const;

const WEEKDAY_SHORT = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;

// Minimum entries (with mood) before we'll surface a headline insight at all.
const MIN_TAGGED_FOR_INSIGHT = 5;
// A weekday needs at least this many samples before we trust its average.
const MIN_SAMPLES_PER_WEEKDAY = 2;
// Headline only fires when the gap between best/worst weekday is meaningful,
// so we don't over-claim on near-flat data.
const INSIGHT_MOOD_GAP = 0.6;

/** Weekday index 0..6 (Sun..Sat) for a 'YYYY-MM-DD' day string. */
export function weekdayIndex(day: string): number {
  const [y, m, d] = day.split("-").map(Number);
  return new Date(y, (m ?? 1) - 1, d ?? 1).getDay();
}

export interface WeekdayStat {
  weekday: number; // 0..6, Sun..Sat
  label: string; // "Sunday"
  short: string; // "Sun"
  avgMood: number | null; // null = no tagged samples
  count: number; // number of mood-tagged entries that weekday
}

export interface MoodPoint {
  id: number;
  day: string;
  ts: number;
  mood: number; // 1..5
}

/**
 * Average mood per weekday, always 7 buckets in Sun..Sat order so the bar chart
 * has a stable x-axis. Weekdays with no tagged entries get avgMood: null.
 */
export function moodByWeekday(entries: Entry[]): WeekdayStat[] {
  const sums = new Array(7).fill(0);
  const counts = new Array(7).fill(0);
  for (const e of entries) {
    if (e.mood == null) continue;
    const wd = weekdayIndex(e.day);
    sums[wd] += e.mood;
    counts[wd] += 1;
  }
  return WEEKDAY_LABELS.map((label, wd) => ({
    weekday: wd,
    label,
    short: WEEKDAY_SHORT[wd],
    avgMood: counts[wd] > 0 ? sums[wd] / counts[wd] : null,
    count: counts[wd],
  }));
}

/**
 * Mood over time, oldest→newest, for a sparkline. Only tagged entries.
 * `limit` keeps the chart readable (default last 30 tagged entries).
 */
export function moodOverTime(entries: Entry[], limit = 30): MoodPoint[] {
  const tagged = entries
    .filter((e): e is Entry & { mood: number } => e.mood != null)
    .map((e) => ({ id: e.id, day: e.day, ts: e.ts, mood: e.mood }))
    .sort((a, b) => a.ts - b.ts || a.id - b.id);
  return limit > 0 ? tagged.slice(-limit) : tagged;
}

/** Same shape as moodOverTime but for the energy tag. */
export function energyOverTime(entries: Entry[], limit = 30): MoodPoint[] {
  const tagged = entries
    .filter((e): e is Entry & { energy: number } => e.energy != null)
    .map((e) => ({ id: e.id, day: e.day, ts: e.ts, mood: e.energy }))
    .sort((a, b) => a.ts - b.ts || a.id - b.id);
  return limit > 0 ? tagged.slice(-limit) : tagged;
}

/** Count of entries carrying a mood tag. Used to gate insights/empty states. */
export function taggedCount(entries: Entry[]): number {
  let n = 0;
  for (const e of entries) if (e.mood != null) n += 1;
  return n;
}

/**
 * The headline retention hook. Returns a single human sentence about the user's
 * strongest weekday mood pattern, or null when there isn't enough signal yet.
 *
 * Logic: needs >= MIN_TAGGED_FOR_INSIGHT tagged entries overall, and at least
 * two distinct weekdays that each clear MIN_SAMPLES_PER_WEEKDAY samples. Picks
 * the best and worst of those, and only speaks if their average mood differs by
 * INSIGHT_MOOD_GAP — otherwise the week is flat and we stay quiet rather than
 * inventing a pattern.
 */
export function pickInsight(entries: Entry[]): string | null {
  if (taggedCount(entries) < MIN_TAGGED_FOR_INSIGHT) return null;

  const stats = moodByWeekday(entries).filter(
    (s): s is WeekdayStat & { avgMood: number } =>
      s.avgMood != null && s.count >= MIN_SAMPLES_PER_WEEKDAY,
  );
  if (stats.length < 2) return null;

  let best = stats[0];
  let worst = stats[0];
  for (const s of stats) {
    if (s.avgMood > best.avgMood) best = s;
    if (s.avgMood < worst.avgMood) worst = s;
  }

  if (best.avgMood - worst.avgMood < INSIGHT_MOOD_GAP) return null;

  // Prefer the more emotionally distinctive end. A clearly bright day is a
  // warmer, more shareable insight than a low one; only lead with the low day
  // if it's the more extreme deviation from the neutral midpoint (3).
  const brightGap = best.avgMood - 3;
  const lowGap = 3 - worst.avgMood;
  if (lowGap > brightGap) {
    return `You tend to feel heaviest on ${worst.label}s.`;
  }
  return `You tend to feel lightest on ${best.label}s.`;
}
