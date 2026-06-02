"""Document Explainer — the load-bearing logic for the Backyard AI app (#9).

Point a small *local* vision model at a confusing piece of paper (a medical bill,
a lease, an official letter, a lab result) and get back a calm, plain-English
explanation: what it is, what they want, any deadline, anything fishy, what to do.

Why local-small is the honest fit: these documents are exactly the things you
should NOT pipe to a cloud API. The whole value proposition is "this never leaves
your device." A 7-8B vision model is plenty for read-and-explain.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict

from .backends import VisionBackend, default_backend

SYSTEM = (
    "You are a calm, trustworthy assistant who helps ordinary people understand "
    "confusing documents. You read what is actually on the page. You never invent "
    "facts, amounts, names, or dates that are not visible. If something is unclear "
    "or unreadable, you say so plainly. You explain like you are talking to a smart "
    "friend who is stressed and busy. No jargon. You are careful and humble about "
    "exact numbers: small print is easy to misread, so you treat every amount as a "
    "best-effort reading the person should confirm against the page."
)

# Core honesty contract for the UI. A local 8B vision model is great at *understanding*
# a document but is NOT a reliable OCR engine for exact small-print figures. We surface
# this rather than hide it — that honesty is the whole point of "small models, big adventure".
VERIFY_DISCLAIMER = (
    "I read this on-device with a small local model. I'm reliable for *what this is* and "
    "*what they want*, but please double-check exact dollar amounts and account numbers "
    "against the page itself — small print is easy to misread."
)

# We ask for strict JSON so the UI can render fields, but always keep a text fallback.
PROMPT = """Look carefully at this document image and explain it for someone who finds it confusing.

Return ONLY a JSON object with these exact keys:
{
  "doc_type": "what kind of document this is (e.g. medical bill, lease, utility notice). If unsure, say 'unclear'.",
  "from_who": "who sent it / the organization, if visible. Else 'not visible'.",
  "one_line": "a single plain sentence: what this is, in human terms.",
  "amount_you_owe": "THE single bottom-line amount the reader is being asked to pay (the final total / amount due), exactly as printed. If the document is not asking for money, use 'none'. Do NOT put a line-item here — only the final total.",
  "what_they_want": "what the document is asking the reader to do or know.",
  "key_numbers": ["important figures actually printed on the page, each as a short string like 'CPT 99284 ER visit: $1,840.00'"],
  "deadlines": ["any dates or deadlines actually printed on the page, each as a short string like '06/12/2026 — payment due'; empty list if none"],
  "watch_out": ["anything the reader should be cautious about: fees, fine print, signs it could be a scam. Empty list if nothing notable."],
  "suggested_next_step": "one concrete, low-risk next action the reader could take.",
  "confidence": "high | medium | low — how clearly you could read and understand the page."
}

Rules:
- Only use information visible in the image. Do not guess amounts or dates.
- amount_you_owe must be the FINAL total due, not a single line item. Look for words like 'amount due', 'total', 'balance', 'patient responsibility'.
- Every item in key_numbers and deadlines must be a plain string, not a nested object.
- If the page is blurry or partial, set confidence to "low" and say what you could not read in one_line.
- Output JSON only. No prose before or after."""


@dataclass
class Explanation:
    doc_type: str = "unclear"
    from_who: str = "not visible"
    one_line: str = ""
    amount_you_owe: str = "none"
    what_they_want: str = ""
    key_numbers: list[str] = field(default_factory=list)
    deadlines: list[str] = field(default_factory=list)
    watch_out: list[str] = field(default_factory=list)
    suggested_next_step: str = ""
    confidence: str = "low"
    raw: str = ""  # always keep the model's raw text for debugging / fallback display
    backend: str = ""
    model: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _extract_json(text: str) -> dict | None:
    """Pull the first balanced JSON object out of a model response."""
    # Strip code fences if the model added them despite instructions.
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


def _as_str_list(value) -> list[str]:
    """Coerce a model-returned list into clean strings. Small models sometimes return
    rich objects (e.g. {'code':..,'description':..,'amount':..}) instead of strings —
    flatten those into readable one-liners rather than dumping raw dicts in the UI."""
    if not value:
        return []
    if isinstance(value, str):
        value = [value]
    out: list[str] = []
    for item in value:
        if isinstance(item, dict):
            # join the dict's values in a readable order, dropping empties
            parts = [str(v) for v in item.values() if v not in (None, "", [])]
            out.append(" — ".join(parts) if parts else "")
        else:
            out.append(str(item))
    return [s for s in (p.strip() for p in out) if s]


def explain_document(image_bytes: bytes, backend: VisionBackend | None = None) -> Explanation:
    """Run the explainer on a single document image. Never raises on bad JSON —
    falls back to putting the raw text in `one_line` so the UI always shows something."""
    backend = backend or default_backend()
    result = backend.generate(PROMPT, images=[image_bytes], system=SYSTEM)
    parsed = _extract_json(result.text) or {}

    exp = Explanation(
        doc_type=str(parsed.get("doc_type", "unclear")),
        from_who=str(parsed.get("from_who", "not visible")),
        one_line=str(parsed.get("one_line", "") or result.text.strip()[:300]),
        amount_you_owe=str(parsed.get("amount_you_owe", "none")),
        what_they_want=str(parsed.get("what_they_want", "")),
        key_numbers=_as_str_list(parsed.get("key_numbers")),
        deadlines=_as_str_list(parsed.get("deadlines")),
        watch_out=_as_str_list(parsed.get("watch_out")),
        suggested_next_step=str(parsed.get("suggested_next_step", "")),
        confidence=str(parsed.get("confidence", "low")),
        raw=result.text,
        backend=result.backend,
        model=result.model,
    )
    return exp
