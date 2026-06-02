import { describe, it, expect } from "vitest";
import { computeStreak, streakMessage } from "../streaks";
import type { Entry } from "../../core/types";

// Minimal Entry factory — only the fields streaks.ts reads matter.
function entry(day: string, id = 0): Entry {
  return {
    id,
    ts: Date.parse(`${day}T12:00:00Z`),
    day,
    text: "x",
    reflection: "",
    question: "",
    callback: "",
    embedding: null,
    mood: null,
    energy: null,
    model: "test",
    encrypted: false,
  };
}

// A fixed "now" so tests don't depend on the wall clock. Noon UTC on the 15th.
const NOW = Date.parse("2026-06-15T12:00:00Z");

describe("computeStreak", () => {
  it("returns zeros for an empty journal", () => {
    const s = computeStreak([], NOW);
    expect(s).toEqual({
      current: 0,
      longest: 0,
      lastDay: null,
      activeToday: false,
    });
  });

  it("counts a single active day today as a streak of 1", () => {
    const s = computeStreak([entry("2026-06-15")], NOW);
    expect(s.current).toBe(1);
    expect(s.longest).toBe(1);
    expect(s.activeToday).toBe(true);
    expect(s.lastDay).toBe("2026-06-15");
  });

  it("counts consecutive days", () => {
    const days = ["2026-06-13", "2026-06-14", "2026-06-15"];
    const s = computeStreak(days.map((d) => entry(d)), NOW);
    expect(s.current).toBe(3);
    expect(s.longest).toBe(3);
    expect(s.activeToday).toBe(true);
  });

  it("collapses multiple entries on the same day to one", () => {
    const entries = [
      entry("2026-06-14", 1),
      entry("2026-06-15", 2),
      entry("2026-06-15", 3),
      entry("2026-06-15", 4),
    ];
    const s = computeStreak(entries, NOW);
    expect(s.current).toBe(2); // not 4
    expect(s.longest).toBe(2);
  });

  it("keeps the streak alive when yesterday was active but not today yet", () => {
    // Last entry yesterday; today hasn't happened. Streak still standing.
    const days = ["2026-06-12", "2026-06-13", "2026-06-14"];
    const s = computeStreak(days.map((d) => entry(d)), NOW);
    expect(s.current).toBe(3);
    expect(s.activeToday).toBe(false);
  });

  describe("grace-day rule (one free skip per week)", () => {
    it("forgives a single skipped day inside a run", () => {
      // 10,11, skip 12, 13,14,15 -> all one run via grace on the 12th.
      const days = [
        "2026-06-10",
        "2026-06-11",
        "2026-06-13",
        "2026-06-14",
        "2026-06-15",
      ];
      const s = computeStreak(days.map((d) => entry(d)), NOW);
      expect(s.current).toBe(5);
      expect(s.longest).toBe(5);
    });

    it("forgives a single missed day before today (grace at the edge)", () => {
      // Active through the 13th, missed the 14th, today is the 15th with no
      // entry yet. One missed day -> grace keeps the run alive.
      const days = ["2026-06-11", "2026-06-12", "2026-06-13"];
      const s = computeStreak(days.map((d) => entry(d)), NOW);
      expect(s.current).toBe(3);
      expect(s.activeToday).toBe(false);
    });

    it("breaks on a SECOND skip within the same week", () => {
      // skip 12 (grace) then skip 14 (second skip, <7 days later) -> run ends.
      // Days: 11, [skip 12], 13, [skip 14], 15.
      const days = ["2026-06-11", "2026-06-13", "2026-06-15"];
      const s = computeStreak(days.map((d) => entry(d)), NOW);
      // The run from 11->13 uses grace; 13->15 wants grace again within 7 days,
      // denied, so the current run is just today (the 15th).
      expect(s.current).toBe(1);
      // Longest run is the 2-day "11,13" segment (grace-joined).
      expect(s.longest).toBe(2);
    });

    it("allows a second grace once the 7-day window has passed", () => {
      // Grace on the 4th, then again on the 12th (>7 days later) — both allowed.
      const days = [
        "2026-06-03",
        // skip 04 (grace #1)
        "2026-06-05",
        "2026-06-06",
        "2026-06-07",
        "2026-06-08",
        "2026-06-09",
        "2026-06-10",
        "2026-06-11",
        // skip 12 (grace #2, >7 days after grace #1)
        "2026-06-13",
        "2026-06-14",
        "2026-06-15",
      ];
      const s = computeStreak(days.map((d) => entry(d)), NOW);
      expect(s.current).toBe(11);
      expect(s.longest).toBe(11);
    });
  });

  it("resets to 0 after a long gap (more than one missed day)", () => {
    // Active a week ago, nothing since. Two+ missed days -> current rests at 0.
    const days = ["2026-06-01", "2026-06-02", "2026-06-03"];
    const s = computeStreak(days.map((d) => entry(d)), NOW);
    expect(s.current).toBe(0);
    expect(s.longest).toBe(3);
    expect(s.lastDay).toBe("2026-06-03");
    expect(s.activeToday).toBe(false);
  });

  it("tracks longest separately from a reset current streak", () => {
    const days = [
      // a long past run (4 days)
      "2026-05-01",
      "2026-05-02",
      "2026-05-03",
      "2026-05-04",
      // big gap, then a fresh 2-day run ending today
      "2026-06-14",
      "2026-06-15",
    ];
    const s = computeStreak(days.map((d) => entry(d)), NOW);
    expect(s.current).toBe(2);
    expect(s.longest).toBe(4);
  });

  it("ignores entries with malformed day strings", () => {
    const entries = [
      entry("2026-06-15", 1),
      { ...entry("2026-06-14", 2), day: "not-a-date" },
    ];
    const s = computeStreak(entries, NOW);
    expect(s.current).toBe(1);
    expect(s.lastDay).toBe("2026-06-15");
  });
});

describe("streakMessage", () => {
  it("never guilt-trips or says 'broke'", () => {
    const cases = [
      computeStreak([], NOW),
      computeStreak([entry("2026-06-15")], NOW),
      computeStreak(
        ["2026-06-13", "2026-06-14", "2026-06-15"].map((d) => entry(d)),
        NOW,
      ),
      computeStreak(["2026-06-01"].map((d) => entry(d)), NOW), // resting
    ];
    for (const s of cases) {
      const msg = streakMessage(s).toLowerCase();
      expect(msg).not.toContain("broke");
      expect(msg).not.toContain("broken");
      expect(msg).not.toContain("failed");
      expect(msg).not.toContain("lost");
      expect(msg.length).toBeGreaterThan(0);
    }
  });

  it("celebrates effort for an active multi-day streak", () => {
    const s = computeStreak(
      ["2026-06-13", "2026-06-14", "2026-06-15"].map((d) => entry(d)),
      NOW,
    );
    expect(streakMessage(s)).toContain("3 days of showing up");
  });

  it("invites a gentle return when resting", () => {
    const s = computeStreak(["2026-06-01"].map((d) => entry(d)), NOW);
    expect(s.current).toBe(0);
    expect(streakMessage(s).length).toBeGreaterThan(0);
  });

  it("welcomes the very first reflection", () => {
    expect(streakMessage(computeStreak([], NOW))).toContain("first");
  });
});
