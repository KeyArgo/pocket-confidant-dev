import { describe, it, expect } from "vitest";
import type { Entry } from "../../core/types";
import {
  weekdayIndex,
  moodByWeekday,
  moodOverTime,
  energyOverTime,
  taggedCount,
  pickInsight,
} from "../trends";

// 2026-06-07 is a Sunday (verified locally below). Build entries from a day
// string + tags; everything else is filler the trend logic ignores.
let nextId = 1;
function entry(day: string, mood: number | null, energy: number | null = null): Entry {
  const id = nextId++;
  return {
    id,
    ts: new Date(`${day}T12:00:00`).getTime() + id, // unique, ordered within a day
    day,
    text: `entry ${id}`,
    reflection: "",
    question: "",
    callback: "",
    embedding: null,
    mood,
    energy,
    model: "test",
    encrypted: false,
  };
}

describe("weekdayIndex", () => {
  it("parses YYYY-MM-DD as a local weekday (Sun..Sat = 0..6)", () => {
    expect(weekdayIndex("2026-06-07")).toBe(0); // Sunday
    expect(weekdayIndex("2026-06-08")).toBe(1); // Monday
    expect(weekdayIndex("2026-06-13")).toBe(6); // Saturday
  });
});

describe("moodByWeekday", () => {
  it("always returns 7 buckets in Sun..Sat order", () => {
    const stats = moodByWeekday([]);
    expect(stats).toHaveLength(7);
    expect(stats.map((s) => s.short)).toEqual([
      "Sun",
      "Mon",
      "Tue",
      "Wed",
      "Thu",
      "Fri",
      "Sat",
    ]);
    expect(stats.every((s) => s.avgMood === null && s.count === 0)).toBe(true);
  });

  it("averages mood per weekday and ignores untagged entries", () => {
    const stats = moodByWeekday([
      entry("2026-06-07", 5), // Sun
      entry("2026-06-14", 3), // Sun
      entry("2026-06-08", null), // Mon, untagged -> ignored
      entry("2026-06-08", 2), // Mon
    ]);
    const sun = stats[0];
    const mon = stats[1];
    expect(sun.avgMood).toBe(4); // (5+3)/2
    expect(sun.count).toBe(2);
    expect(mon.avgMood).toBe(2);
    expect(mon.count).toBe(1);
  });
});

describe("moodOverTime / energyOverTime", () => {
  it("returns only tagged points, oldest -> newest", () => {
    const pts = moodOverTime([
      entry("2026-06-09", 4),
      entry("2026-06-07", 2),
      entry("2026-06-08", null),
    ]);
    expect(pts.map((p) => p.mood)).toEqual([2, 4]); // ts order, untagged dropped
  });

  it("limit keeps only the most recent N", () => {
    const all = Array.from({ length: 10 }, (_, i) =>
      entry(`2026-06-${String(i + 1).padStart(2, "0")}`, (i % 5) + 1),
    );
    expect(moodOverTime(all, 3)).toHaveLength(3);
  });

  it("energyOverTime reads the energy field", () => {
    const pts = energyOverTime([
      entry("2026-06-07", 5, 1),
      entry("2026-06-08", 5, null), // no energy -> dropped
      entry("2026-06-09", 5, 4),
    ]);
    expect(pts.map((p) => p.mood)).toEqual([1, 4]);
  });
});

describe("taggedCount", () => {
  it("counts entries with a mood tag", () => {
    expect(
      taggedCount([entry("2026-06-07", 3), entry("2026-06-08", null), entry("2026-06-09", 1)]),
    ).toBe(2);
  });
});

describe("pickInsight", () => {
  it("returns null with too little data", () => {
    expect(pickInsight([])).toBeNull();
    expect(pickInsight([entry("2026-06-07", 5), entry("2026-06-08", 1)])).toBeNull();
  });

  it("returns null when the week is flat (no meaningful gap)", () => {
    const flat = [
      entry("2026-06-07", 3),
      entry("2026-06-14", 3), // Sun
      entry("2026-06-08", 3),
      entry("2026-06-15", 3), // Mon
      entry("2026-06-09", 3),
      entry("2026-06-16", 3), // Tue
    ];
    expect(pickInsight(flat)).toBeNull();
  });

  it("surfaces the lightest weekday when the bright end is most distinctive", () => {
    const data = [
      // Sundays clearly high
      entry("2026-06-07", 5),
      entry("2026-06-14", 5),
      // Mondays middling
      entry("2026-06-08", 3),
      entry("2026-06-15", 3),
      // Tuesdays a bit lower but not extreme
      entry("2026-06-09", 3),
      entry("2026-06-16", 2),
    ];
    expect(pickInsight(data)).toBe("You tend to feel lightest on Sundays.");
  });

  it("surfaces the heaviest weekday when the low end is most distinctive", () => {
    const data = [
      // Mondays very low (extreme deviation below neutral)
      entry("2026-06-08", 1),
      entry("2026-06-15", 1),
      // Sundays mildly above neutral
      entry("2026-06-07", 4),
      entry("2026-06-14", 3),
      // Tuesdays neutral
      entry("2026-06-09", 3),
      entry("2026-06-16", 3),
    ];
    expect(pickInsight(data)).toBe("You tend to feel heaviest on Mondays.");
  });

  it("ignores weekdays with only one sample when picking the pattern", () => {
    const data = [
      // Sunday has 2 samples, solidly high
      entry("2026-06-07", 5),
      entry("2026-06-14", 5),
      // Wednesday has just 1 very low sample -> not trusted as worst
      entry("2026-06-10", 1),
      // Mondays give a second trusted weekday, middling
      entry("2026-06-08", 3),
      entry("2026-06-15", 3),
    ];
    // Worst trusted weekday is Monday (3), best is Sunday (5): gap 2 -> bright wins
    expect(pickInsight(data)).toBe("You tend to feel lightest on Sundays.");
  });
});
