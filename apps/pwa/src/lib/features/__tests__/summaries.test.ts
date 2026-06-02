import { describe, it, expect, vi, beforeEach } from "vitest";

// The pure logic caches summaries through db.ts (IndexedDB), which doesn't exist
// in the Node test environment. Mock the meta store with an in-memory map so the
// caching behaviour is exercised without a browser.
const metaStore = new Map<string, unknown>();
vi.mock("../../data/db", () => ({
  getMeta: async (key: string) => metaStore.get(key),
  setMeta: async (key: string, value: unknown) => {
    metaStore.set(key, value);
  },
}));

import type { Entry, Chat } from "../../core/types";
import {
  weeklySummary,
  yearlySummary,
  selectRecent,
  selectYear,
  weekKey,
} from "../summaries";
import { splitWindows, howHaveIChanged } from "../changed";

// A fake chat: records calls, echoes back a deterministic string. No real model.
function fakeChat(reply = "a calm look back"): Chat & { calls: string[][] } {
  const calls: string[][] = [];
  const fn = (async (system: string, user: string) => {
    calls.push([system, user]);
    return reply;
  }) as Chat & { calls: string[][] };
  fn.calls = calls;
  return fn;
}

const DAY = 86400000;

function entry(id: number, day: string, ts: number, text: string): Entry {
  return {
    id,
    ts,
    day,
    text,
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

// A fixed "now" so day-window math is deterministic (mid-day, June 2026).
const NOW = new Date("2026-06-15T12:00:00").getTime();

beforeEach(() => {
  metaStore.clear();
});

function dayOffset(days: number): string {
  return new Date(NOW - days * DAY).toISOString().slice(0, 10);
}

describe("selectRecent", () => {
  const entries: Entry[] = [
    entry(1, dayOffset(20), NOW - 20 * DAY, "old"),
    entry(2, dayOffset(5), NOW - 5 * DAY, "within week"),
    entry(3, dayOffset(1), NOW - 1 * DAY, "yesterday"),
  ];

  it("keeps only entries within the last 7 days", () => {
    const sel = selectRecent(entries, 7, NOW);
    expect(sel.map((e) => e.id)).toEqual([2, 3]);
  });

  it("returns them oldest-first", () => {
    const sel = selectRecent(entries, 7, NOW);
    expect(sel[0].ts).toBeLessThan(sel[1].ts);
  });
});

describe("selectYear", () => {
  it("keeps only the current calendar year", () => {
    const entries: Entry[] = [
      entry(1, "2025-12-30", new Date("2025-12-30").getTime(), "last year"),
      entry(2, "2026-01-02", new Date("2026-01-02").getTime(), "this year"),
      entry(3, "2026-06-01", new Date("2026-06-01").getTime(), "this year too"),
    ];
    expect(selectYear(entries, NOW).map((e) => e.id)).toEqual([2, 3]);
  });
});

describe("weekKey", () => {
  it("is stable within a week and changes across weeks", () => {
    const a = weekKey(new Date("2026-06-01T09:00:00Z").getTime());
    const b = weekKey(new Date("2026-06-03T09:00:00Z").getTime());
    const c = weekKey(new Date("2026-06-10T09:00:00Z").getTime());
    expect(a).toBe(b);
    expect(a).not.toBe(c);
    expect(a).toMatch(/^\d{4}-W\d{2}$/);
  });
});

describe("weeklySummary degradation", () => {
  it("returns a graceful note with zero entries (no chat call)", async () => {
    const chat = fakeChat();
    const out = await weeklySummary([], { chat, now: NOW });
    expect(out).toMatch(/nothing written/i);
    expect(chat.calls).toHaveLength(0);
  });

  it("returns a graceful note with a single entry (no chat call)", async () => {
    const chat = fakeChat();
    const entries = [entry(1, dayOffset(1), NOW - DAY, "just one")];
    const out = await weeklySummary(entries, { chat, now: NOW });
    expect(out).toMatch(/one entry/i);
    expect(chat.calls).toHaveLength(0);
  });

  it("calls chat once when there are enough entries", async () => {
    const chat = fakeChat("recurring threads here");
    const entries = [
      entry(1, dayOffset(4), NOW - 4 * DAY, "felt anxious about the move"),
      entry(2, dayOffset(2), NOW - 2 * DAY, "the move again, calmer today"),
    ];
    const out = await weeklySummary(entries, { chat, now: NOW, noCache: true });
    expect(out).toBe("recurring threads here");
    expect(chat.calls).toHaveLength(1);
    // The folded prompt should include the period's entry text.
    expect(chat.calls[0][1]).toContain("the move again");
  });

  it("excludes entries outside the 7-day window from the prompt", async () => {
    const chat = fakeChat();
    const entries = [
      entry(1, dayOffset(40), NOW - 40 * DAY, "ancient history here"),
      entry(2, dayOffset(3), NOW - 3 * DAY, "recent thing one"),
      entry(3, dayOffset(1), NOW - DAY, "recent thing two"),
    ];
    await weeklySummary(entries, { chat, now: NOW, noCache: true });
    expect(chat.calls[0][1]).not.toContain("ancient history");
    expect(chat.calls[0][1]).toContain("recent thing one");
  });
});

describe("yearlySummary degradation", () => {
  it("degrades gracefully with too few entries", async () => {
    const chat = fakeChat();
    const out = await yearlySummary(
      [entry(1, "2026-02-01", new Date("2026-02-01").getTime(), "alone")],
      { chat, now: NOW },
    );
    expect(out).toMatch(/one entry/i);
    expect(chat.calls).toHaveLength(0);
  });
});

describe("splitWindows", () => {
  it("splits chronologically; recent window gets the extra on odd counts", () => {
    const entries = [1, 2, 3, 4, 5].map((i) =>
      entry(i, `2026-0${i}-01`, new Date(`2026-0${i}-01`).getTime(), `e${i}`),
    );
    const { earlier, recent } = splitWindows(entries);
    expect(earlier.map((e) => e.id)).toEqual([1, 2]);
    expect(recent.map((e) => e.id)).toEqual([3, 4, 5]);
  });

  it("sorts by ts before splitting (input order independent)", () => {
    const entries = [
      entry(3, "2026-03-01", new Date("2026-03-01").getTime(), "c"),
      entry(1, "2026-01-01", new Date("2026-01-01").getTime(), "a"),
      entry(2, "2026-02-01", new Date("2026-02-01").getTime(), "b"),
    ];
    const { earlier, recent } = splitWindows(entries);
    expect(earlier[0].id).toBe(1);
    expect(recent.map((e) => e.id)).toContain(3);
  });
});

describe("howHaveIChanged degradation", () => {
  it("returns a not-enough-history note when a window is too small", async () => {
    const chat = fakeChat();
    const entries = [1, 2, 3, 4].map((i) =>
      entry(i, `2026-0${i}-01`, new Date(`2026-0${i}-01`).getTime(), `e${i}`),
    );
    const out = await howHaveIChanged(entries, { chat });
    expect(out).toMatch(/not enough history/i);
    expect(chat.calls).toHaveLength(0);
  });

  it("compares earlier vs recent windows once there's enough", async () => {
    const chat = fakeChat("you dwell less on work, more on people");
    const entries = Array.from({ length: 8 }, (_, i) =>
      entry(
        i + 1,
        `2026-0${i + 1}-01`.replace(/0(\d\d)/, "$1"),
        new Date(2026, i, 1).getTime(),
        i < 4 ? `work stress week ${i}` : `dinner with friends ${i}`,
      ),
    );
    const out = await howHaveIChanged(entries, { chat });
    expect(out).toBe("you dwell less on work, more on people");
    expect(chat.calls).toHaveLength(1);
    const prompt = chat.calls[0][1];
    expect(prompt).toContain("EARLIER");
    expect(prompt).toContain("RECENT");
    expect(prompt).toContain("work stress");
    expect(prompt).toContain("dinner with friends");
  });
});

describe("summary caching", () => {
  it("does not call chat twice for an unchanged period (meta cache hit)", async () => {
    const chat = fakeChat("cached look back");
    const entries = [
      entry(1, dayOffset(4), NOW - 4 * DAY, "thread one"),
      entry(2, dayOffset(2), NOW - 2 * DAY, "thread two"),
    ];
    const first = await weeklySummary(entries, { chat, now: NOW });
    const second = await weeklySummary(entries, { chat, now: NOW });
    expect(first).toBe(second);
    // Second call should hit cache (same count) — exactly one chat call total.
    expect(chat.calls.length).toBe(1);
  });
});
