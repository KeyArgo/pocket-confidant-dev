// "Ask your journal anything" — the headline differentiator. Private RAG over the
// user's own entries: retrieve the most relevant past entries, answer ONLY from
// them, cite dates. No cloud app can offer this as trustworthily.

import type { Chat, Embedder, Entry } from "../core/types";
import { recall } from "../core/recall";
import { ASK_PERSONA, ASK_INSTRUCTION, ASK_FLOOR } from "../core/persona";

export interface AskResult {
  answer: string;
  sources: Entry[]; // the entries used — render as clickable date chips for trust
}

export async function askJournal(
  question: string,
  entries: Entry[],
  deps: { chat: Chat; embed: Embedder },
): Promise<AskResult> {
  const hits = await recall(question, entries, deps.embed, {
    k: 6,
    minScore: ASK_FLOOR, // broader than reflection: QA wants recall, not precision
  });

  if (hits.length === 0) {
    return {
      answer: "I don't see anything about that in your journal yet.",
      sources: [],
    };
  }

  const context = hits
    .map((h) => `(${h.day}) ${h.text.trim()}`)
    .join("\n\n");

  const answer = await deps.chat(ASK_PERSONA, ASK_INSTRUCTION(question, context), {
    temperature: 0.4,
  });

  return { answer: answer.trim(), sources: hits };
}
