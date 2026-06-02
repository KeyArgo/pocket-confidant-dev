// Core types for Pocket Confidant. Mirrors the Python engine's Entry/Reflection
// (engine/store.py, engine/confidant.py) with commercial extensions (mood/energy,
// callback persisted, encryption flag).

export interface Entry {
  id: number;
  ts: number; // epoch milliseconds
  day: string; // 'YYYY-MM-DD' — display + grouping; multiple entries per day allowed
  text: string;
  reflection: string;
  question: string;
  callback: string;
  embedding: number[] | null; // null = embedding unavailable -> excluded from recall
  mood: number | null; // 1-5 quick-tag (optional)
  energy: number | null; // 1-5 quick-tag (optional)
  model: string; // which model produced the reflection
  encrypted: boolean; // are text/reflection wrapped at rest
}

export interface Reflection {
  reflection: string;
  question: string;
  callback: string;
  model: string;
}

// Dependency-injected transports. The pure core never imports WebLLM or
// Transformers.js directly — it takes these functions, so it stays unit-testable.
export type Embedder = (text: string) => Promise<number[]>;
export type Chat = (
  system: string,
  user: string,
  opts?: { temperature?: number },
) => Promise<string>;

export function renderReflection(r: Reflection): string {
  return [r.callback, r.reflection, r.question]
    .map((p) => (p ?? "").trim())
    .filter(Boolean)
    .join("\n\n");
}
