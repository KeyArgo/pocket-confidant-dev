import { describe, it, expect } from "vitest";
import { cosine, recall } from "../recall";
import type { Entry, Embedder } from "../types";

describe("cosine", () => {
  it("is 1 for identical direction", () => {
    expect(cosine([1, 0], [2, 0])).toBeCloseTo(1);
  });
  it("is 0 for orthogonal", () => {
    expect(cosine([1, 0], [0, 1])).toBeCloseTo(0);
  });
  it("handles zero vectors safely", () => {
    expect(cosine([0, 0], [1, 1])).toBe(0);
  });
});

function entry(id: number, text: string, embedding: number[] | null): Entry {
  return {
    id,
    ts: id,
    day: "2026-06-01",
    text,
    reflection: "",
    question: "",
    callback: "",
    embedding,
    mood: null,
    energy: null,
    model: "test",
    encrypted: false,
  };
}

// Fake embedder: maps known phrases to fixed vectors so we can assert recall.
const VECS: Record<string, number[]> = {
  dentist: [1, 0, 0],
  project: [0, 1, 0],
  weather: [0, 0, 1],
};
const fakeEmbed: Embedder = async (text) => VECS[text] ?? [0, 0, 0];

describe("recall", () => {
  const entries = [
    entry(1, "dentist", [1, 0, 0]),
    entry(2, "project", [0, 1, 0]),
    entry(3, "weather", [0, 0, 1]),
    entry(4, "no-embedding", null),
  ];

  it("surfaces the topically matching entry above the floor", async () => {
    const hits = await recall("dentist", entries, fakeEmbed, {
      k: 3,
      minScore: 0.5,
    });
    expect(hits.map((h) => h.id)).toEqual([1]);
  });

  it("returns nothing when no entry clears the floor", async () => {
    // 'project' query is orthogonal (cosine 0) to dentist/weather; only matches id 2
    const hits = await recall("project", entries, fakeEmbed, {
      k: 3,
      minScore: 0.99,
    });
    expect(hits.map((h) => h.id)).toEqual([2]);
  });

  it("excludes entries with id >= beforeId", async () => {
    const hits = await recall("dentist", entries, fakeEmbed, {
      k: 3,
      minScore: 0.5,
      beforeId: 1,
    });
    expect(hits).toEqual([]);
  });

  it("skips entries without an embedding", async () => {
    const hits = await recall("dentist", entries, fakeEmbed, {
      k: 10,
      minScore: -1,
    });
    expect(hits.find((h) => h.id === 4)).toBeUndefined();
  });

  it("respects k", async () => {
    const hits = await recall("dentist", entries, fakeEmbed, {
      k: 1,
      minScore: -1,
    });
    expect(hits).toHaveLength(1);
  });
});
