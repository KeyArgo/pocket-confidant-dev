// Port of engine/store.py recall() + _cosine(). Pure: the embedder is injected,
// the entries are passed in, so this is fully unit-testable without a browser.

import type { Entry, Embedder } from "./types";

export function cosine(a: number[], b: number[]): number {
  let dot = 0;
  let na = 0;
  let nb = 0;
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  if (na === 0 || nb === 0) return 0;
  return dot / (Math.sqrt(na) * Math.sqrt(nb));
}

export interface RecallOpts {
  k?: number;
  minScore?: number;
  beforeId?: number | null;
}

/**
 * Return the semantically most-relevant past entries above a cosine floor.
 * Mirrors store.recall(): embed the query, score every entry that has an
 * embedding, keep >= minScore, sort desc, take k. `beforeId` excludes the
 * current draft and anything after it.
 */
export async function recall(
  query: string,
  entries: Entry[],
  embed: Embedder,
  opts: RecallOpts = {},
): Promise<Entry[]> {
  const { k = 3, minScore = 0, beforeId = null } = opts;
  let qe: number[];
  try {
    qe = await embed(query);
  } catch {
    return [];
  }
  const scored: Array<{ score: number; entry: Entry }> = [];
  for (const e of entries) {
    if (!e.embedding) continue;
    if (beforeId !== null && e.id >= beforeId) continue;
    const score = cosine(qe, e.embedding);
    if (score >= minScore) scored.push({ score, entry: e });
  }
  scored.sort((x, y) => y.score - x.score);
  return scored.slice(0, k).map((s) => s.entry);
}
