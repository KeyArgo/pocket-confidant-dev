// Non-punishing streaks (Finch-style). Rewards EFFORT, not perfection.
//
// Design intent (read before changing):
// - A "streak" counts consecutive *active* days, where a day is active if at
//   least one entry exists for it. Multiple entries on the same day count once.
// - One free "grace day" per rolling 7-day window: a single skipped day does NOT
//   break the streak, as long as you've used no grace in the prior 7 days. This
//   means a single miss is forgiven, but two misses in the same week ends the run.
// - We never say "you broke your streak." Copy celebrates showing up.
//
// `day` strings are 'YYYY-MM-DD' (UTC) exactly as produced by the app
// (new Date().toISOString().slice(0,10)). We do all date math in UTC on these
// strings so we never depend on the local timezone of whoever runs the tests.

import type { Entry } from "../core/types";

export interface StreakInfo {
  current: number; // length of the current active run (incl. forgiven gaps)
  longest: number; // best run ever achieved, same grace rules applied
  lastDay: string | null; // most recent active day, or null if no entries
  activeToday: boolean; // did the user already journal today?
}

const MS_PER_DAY = 86_400_000;

/** Parse 'YYYY-MM-DD' to a UTC-midnight epoch (ms). Returns NaN if malformed. */
function dayToUTC(day: string): number {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(day);
  if (!m) return NaN;
  return Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
}

/** Whole-day gap between two 'YYYY-MM-DD' strings (later - earlier). */
function dayGap(earlier: string, later: string): number {
  return Math.round((dayToUTC(later) - dayToUTC(earlier)) / MS_PER_DAY);
}

/** Today's day string in the same UTC format the app stores. */
function todayUTC(now: number): string {
  return new Date(now).toISOString().slice(0, 10);
}

/**
 * Sorted, de-duplicated list of active days (ascending). Same-day multiple
 * entries collapse to one. Entries with malformed days are ignored.
 */
function activeDays(entries: Entry[]): string[] {
  const set = new Set<string>();
  for (const e of entries) {
    if (e.day && !Number.isNaN(dayToUTC(e.day))) set.add(e.day);
  }
  return Array.from(set).sort();
}

/**
 * Walk a run forward from one active day to the next, applying the grace rule.
 * A gap of 1 (consecutive) always continues. A gap of 2 (exactly one skipped
 * day) continues *only* if no grace day has been spent within the prior 7-day
 * window — that skipped day becomes the grace day. Any larger gap, or a second
 * grace within the window, ends the run.
 *
 * Returns the day-count contributed by a run so we can track current/longest.
 */
function runLengths(days: string[]): { runs: number[]; currentRunDays: string[] } {
  const runs: number[] = [];
  let runStartIdx = 0;
  // Track the day on which we last "spent" a grace, to enforce 1 per 7 days.
  let lastGraceDay: string | null = null;

  for (let i = 1; i < days.length; i++) {
    const gap = dayGap(days[i - 1], days[i]);
    let continues = false;
    if (gap === 1) {
      continues = true;
    } else if (gap === 2) {
      // Exactly one skipped day. The skipped day is days[i-1] + 1.
      const skipped = todayUTC(dayToUTC(days[i - 1]) + MS_PER_DAY);
      const graceAvailable =
        lastGraceDay === null || dayGap(lastGraceDay, skipped) > 7;
      if (graceAvailable) {
        continues = true;
        lastGraceDay = skipped;
      }
    }
    if (!continues) {
      runs.push(days.slice(runStartIdx, i).length);
      runStartIdx = i;
      lastGraceDay = null;
    }
  }
  runs.push(days.slice(runStartIdx).length);
  return { runs, currentRunDays: days.slice(runStartIdx) };
}

/**
 * Length (in active days) of the run that includes `lastActive`, given that
 * "now" is `nowDay`. The current streak is only alive if the last active day is
 * today, yesterday, or — using this period's grace — the day before that.
 */
function currentStreak(
  days: string[],
  currentRunDays: string[],
  nowDay: string,
): number {
  if (days.length === 0) return 0;
  const lastActive = days[days.length - 1];
  const gapToNow = dayGap(lastActive, nowDay);

  if (gapToNow <= 0) {
    // Active today (gap 0) — or a future-dated entry; treat as active.
    return currentRunDays.length;
  }
  if (gapToNow === 1) {
    // Missed today so far, but yesterday was active — streak still standing.
    return currentRunDays.length;
  }
  if (gapToNow === 2) {
    // Missed exactly one day before today. The current run can absorb this as
    // its grace day, provided the run didn't already spend grace this week.
    // Re-walk just the tail to see if grace is still available at the edge.
    const tail = [...currentRunDays, nowDay];
    const { runs } = runLengths(tail);
    // If the appended `nowDay` stayed in one run, grace covered the gap.
    if (runs.length === 1) return currentRunDays.length;
    return 0;
  }
  // Two or more fully-missed days with no journaling: the run has lapsed.
  // We never call this "broken" in copy — the streak simply rests at 0.
  return 0;
}

/**
 * Compute streak stats from raw entries. Pure: pass `now` in tests for
 * determinism; defaults to Date.now().
 */
export function computeStreak(entries: Entry[], now: number = Date.now()): StreakInfo {
  const days = activeDays(entries);
  const nowDay = todayUTC(now);

  if (days.length === 0) {
    return { current: 0, longest: 0, lastDay: null, activeToday: false };
  }

  const { runs, currentRunDays } = runLengths(days);
  const longest = runs.reduce((a, b) => Math.max(a, b), 0);
  const current = currentStreak(days, currentRunDays, nowDay);
  const lastDay = days[days.length - 1];
  const activeToday = dayGap(lastDay, nowDay) <= 0;

  return { current, longest, lastDay, activeToday };
}

/**
 * Warm, non-punishing copy for a badge. Never guilt-trips, never says "broken."
 * Celebrates effort and gently welcomes a return after a rest.
 */
export function streakMessage(s: StreakInfo): string {
  if (s.lastDay === null) return "Your first reflection is waiting";

  if (s.current === 0) {
    // The run is resting. Invite a return without any blame.
    return s.longest > 0
      ? "Pick up where you left off — your space is here"
      : "A quiet moment whenever you're ready";
  }

  if (s.current === 1) {
    return s.activeToday ? "You showed up today" : "One day of showing up";
  }

  const days = `${s.current} days of showing up`;
  if (!s.activeToday) {
    // Streak alive on grace/yesterday; nudge gently, never warn.
    return `${days} — come sit with it again`;
  }
  if (s.current >= 30) return `${days} — that's real devotion`;
  if (s.current >= 7) return `${days} — a steady rhythm`;
  return days;
}
