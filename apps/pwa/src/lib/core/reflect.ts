// Port of engine/confidant.py reflect(). Pure: chat + embed transports injected.
// Builds the memory block from cosine-floored recall, calls the model, parses JSON,
// and guards against formulaic repetition (a top market-churn cause for AI journals).

import type { Chat, Embedder, Entry, Reflection } from "./types";
import { extractJson, asString, stripThinking } from "./parse";
import {
  PERSONA,
  REFLECT_INSTRUCTION,
  RECALL_FLOOR,
  memoryBlock,
} from "./persona";
import { recall } from "./recall";

function firstWords(s: string, n = 6): string {
  return s.trim().toLowerCase().split(/\s+/).slice(0, n).join(" ");
}

export interface ReflectDeps {
  chat: Chat;
  embed: Embedder;
  model: string;
  beforeId?: number | null;
  /** Openers of recent reflections, to detect + re-roll formulaic repeats. */
  recentOpeners?: string[];
}

export async function reflect(
  entryText: string,
  entries: Entry[],
  deps: ReflectDeps,
): Promise<Reflection> {
  const { chat, embed, model, beforeId = null, recentOpeners = [] } = deps;

  const recalled = await recall(entryText, entries, embed, {
    k: 3,
    minScore: RECALL_FLOOR,
    beforeId,
  });

  const user = REFLECT_INSTRUCTION(entryText.trim(), memoryBlock(recalled));

  const parse = (raw: string): Reflection => {
    const obj = extractJson(raw) ?? {};
    return {
      reflection: asString(obj.reflection) || stripThinking(raw).slice(0, 300),
      question: asString(obj.question),
      callback: asString(obj.callback),
      model,
    };
  };

  let raw = await chat(PERSONA, user, { temperature: 0.7 });
  let out = parse(raw);

  // Anti-formulaic guard: if this reflection opens like a recent one, re-roll
  // once at higher temperature for variety. Cheap, on-device, no extra deps.
  if (
    out.reflection &&
    recentOpeners.some((o) => o && o === firstWords(out.reflection))
  ) {
    raw = await chat(PERSONA, user, { temperature: 0.85 });
    out = parse(raw);
  }

  return out;
}
