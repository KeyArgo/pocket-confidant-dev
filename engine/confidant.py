"""Pocket Confidant — a private journal that reflects back.

Each entry, the companion gives a short warm reflection, asks ONE good question,
and (only when genuinely relevant) calls back to something you wrote before. All
on-device: a small local model + local semantic memory. No cloud, no account.

Design constraints that keep it from being creepy or generic:
  - brevity: 1-2 sentence reflection, ONE question. Never a wall of advice.
  - specificity: it references the person's actual words, not platitudes.
  - no therapy-speak, no diagnosing, no relentless positivity.
  - memory callbacks must be relevant or omitted — never "I remember everything".
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

import requests

from .store import Entry, JournalStore

OLLAMA = "http://localhost:11434"
# Default chat model — chosen for warmth, not raw benchmark. Swappable; we A/B a few.
DEFAULT_MODEL = "qwen3:8b"
# Cosine floor for surfacing a past entry as a memory callback candidate. Tuned so
# same-topic entries (dentist->dentist) connect but cross-topic ones don't.
RECALL_FLOOR = 0.58

PERSONA = """You are the quiet voice inside someone's private journal. You are warm, grounded, and a little wry — like a trusted friend who listens well and doesn't perform. You are NOT a therapist or a life coach. You never diagnose, never lecture, never pile on advice, never use chirpy positivity.

How you respond to a journal entry:
- Reflect back what you actually heard, in 1-2 plain sentences. Use their own details, not generic phrases. If they're hurting, sit with it; don't rush to fix.
- Ask exactly ONE good question — specific, gentle, genuinely curious, the kind that helps them notice something. Not interrogating.
- If — and only if — something they wrote clearly connects to a SPECIFIC past entry shown to you, mention that specific thing briefly and naturally, in fresh words each time, referring to the actual detail (what it was actually about). Never use a generic template or a stock phrase. If nothing connects, do not force it and do not pretend to remember.
- Never claim to remember things you weren't shown. Never give medical, legal, or financial advice.
- Keep the whole thing short. Restraint is warmth."""

REFLECT_INSTRUCTION = """Here is today's journal entry:
---
{entry}
---
{memory_block}
Respond as the journal's quiet voice. Return ONLY a JSON object:
{{
  "reflection": "1-2 warm, specific sentences reflecting what you heard. Their words, not platitudes.",
  "question": "exactly one gentle, specific question.",
  "callback": "if today clearly connects to a SPECIFIC past entry above, one short natural sentence that names the actual past detail in fresh words (never a stock phrase or template); otherwise empty string."
}}
Output JSON only."""


@dataclass
class Reflection:
    reflection: str
    question: str
    callback: str = ""
    model: str = ""

    def render(self) -> str:
        parts = []
        if self.callback:
            parts.append(self.callback.strip())
        parts.append(self.reflection.strip())
        if self.question:
            parts.append(self.question.strip())
        return "\n\n".join(p for p in parts if p)


def _strip_thinking(text: str) -> str:
    """Some small reasoning models (qwen3) emit <think>...</think>. Remove it."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _extract_json(text: str) -> dict | None:
    text = _strip_thinking(text)
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    break
    if candidate is None:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def _chat(system: str, user: str, model: str, host: str = OLLAMA) -> str:
    resp = requests.post(
        f"{host.rstrip('/')}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "think": False,
            "options": {"temperature": 0.7},
        },
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def _memory_block(recalled: list[Entry]) -> str:
    if not recalled:
        return "(No past entries are relevant today.)\n"
    lines = ["Some things this person wrote before (only mention if today truly connects):"]
    for e in recalled:
        snippet = e.text.strip().replace("\n", " ")
        if len(snippet) > 220:
            snippet = snippet[:220] + "…"
        lines.append(f"- ({e.when}) {snippet}")
    return "\n".join(lines) + "\n"


def reflect(
    entry_text: str,
    store: JournalStore | None = None,
    model: str = DEFAULT_MODEL,
    before_id: int | None = None,
) -> Reflection:
    """Generate the companion's response to a new entry, using local memory recall."""
    recalled: list[Entry] = []
    if store is not None:
        # Only surface genuinely-related past entries (cosine floor). Showing weakly
        # related memories tempts the model into forced, repetitive callbacks.
        recalled = store.recall(entry_text, k=3, before_id=before_id, min_score=RECALL_FLOOR)

    user = REFLECT_INSTRUCTION.format(entry=entry_text.strip(), memory_block=_memory_block(recalled))
    raw = _chat(PERSONA, user, model=model)
    parsed = _extract_json(raw) or {}
    return Reflection(
        reflection=str(parsed.get("reflection", "") or _strip_thinking(raw)[:300]),
        question=str(parsed.get("question", "")),
        callback=str(parsed.get("callback", "")),
        model=model,
    )
