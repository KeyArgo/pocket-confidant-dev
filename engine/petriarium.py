"""Petriarium creature loop.

The LLM does the fun interpretive work: it senses a moment, names a mood, and
proposes what the creature learned. Python handles mutation and rendering so the
demo remains fast, bounded, and repairable.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
from dataclasses import asdict
from typing import Any

import requests

from .creature_store import CreatureState, CreatureStore, MOODS, keyword_tags


OLLAMA = os.environ.get("PETRIARIUM_OLLAMA", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("PETRIARIUM_MODEL", "qwen2.5:7b-instruct")
LLAMA_MODEL_PATH = os.environ.get("PETRIARIUM_GGUF", "")
LLAMA_REPO_ID = os.environ.get("PETRIARIUM_HF_REPO", "")
LLAMA_FILENAME = os.environ.get("PETRIARIUM_HF_FILE", "")

SYSTEM = """You are the little interpreting mind inside Petriarium.
You are not a chatbot. You are a tiny creature that eats moments and turns them
into collectible artifacts. Be specific, strange, and warm. Never diagnose,
advise, moralize, or mention that you are an AI model.

Return only JSON with exactly these keys:
{
  "response_text": "one short creature-like sentence, under 24 words",
  "mood": "one of: bright, shy, buzzing, stormy, sleepy, entranced",
  "memory_proposal": {
    "summary": "what the creature learned, under 18 words",
    "tags": ["1-5 lowercase tags"]
  }
}
"""

USER_TEMPLATE = """Creature state:
{state}

Recent memories:
{memories}

New moment to eat:
---
{moment}
---

Return JSON only."""


def _strip_thinking(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL).strip()


def _extract_json(text: str) -> dict[str, Any] | None:
    text = _strip_thinking(text)
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        for i, ch in enumerate(text[start:], start=start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    break
    if not candidate:
        return None
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _download_gguf() -> str:
    if LLAMA_MODEL_PATH:
        return LLAMA_MODEL_PATH
    if not (LLAMA_REPO_ID and LLAMA_FILENAME):
        return ""
    from huggingface_hub import hf_hub_download

    return hf_hub_download(repo_id=LLAMA_REPO_ID, filename=LLAMA_FILENAME)


_LLAMA = None


def _llama_chat(system: str, user: str) -> str:
    global _LLAMA
    model_path = _download_gguf()
    if not model_path:
        raise RuntimeError("PETRIARIUM_GGUF or PETRIARIUM_HF_REPO/PETRIARIUM_HF_FILE is not configured")
    if _LLAMA is None:
        from llama_cpp import Llama

        _LLAMA = Llama(
            model_path=model_path,
            n_ctx=int(os.environ.get("PETRIARIUM_N_CTX", "2048")),
            n_threads=int(os.environ.get("PETRIARIUM_THREADS", "4")),
            verbose=False,
        )
    result = _LLAMA.create_chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.72,
        max_tokens=220,
    )
    return result["choices"][0]["message"]["content"]


def _ollama_chat(system: str, user: str, model: str = DEFAULT_MODEL) -> str:
    resp = requests.post(
        f"{OLLAMA.rstrip('/')}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "think": False,
            "options": {"temperature": 0.72},
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def chat(system: str, user: str, model: str = DEFAULT_MODEL) -> str:
    if os.environ.get("PETRIARIUM_RUNTIME", "llama").lower() == "ollama":
        return _ollama_chat(system, user, model=model)
    return _llama_chat(system, user)


def normalize_model_result(parsed: dict[str, Any] | None, text: str) -> dict[str, Any]:
    fallback_tags = keyword_tags(text)
    if not parsed:
        return {
            "response_text": "It chews the moment into a small, glowing oddity.",
            "mood": "entranced",
            "memory_proposal": {
                "summary": f"It noticed {', '.join(fallback_tags[:3])}.",
                "tags": fallback_tags,
            },
        }
    mood = str(parsed.get("mood", "entranced")).strip().lower()
    if mood not in MOODS:
        mood = "entranced"
    response_text = str(parsed.get("response_text", "")).strip()
    if not response_text:
        response_text = "It turns the moment over like a warm pebble."
    memory = parsed.get("memory_proposal") if isinstance(parsed.get("memory_proposal"), dict) else {}
    summary = str(memory.get("summary", "")).strip()
    if not summary:
        summary = f"It learned about {', '.join(fallback_tags[:3])}."
    raw_tags = memory.get("tags", fallback_tags)
    tags = []
    if isinstance(raw_tags, list):
        for item in raw_tags:
            tag = re.sub(r"[^a-z0-9_-]+", "", str(item).lower())
            if len(tag) >= 3 and tag not in tags:
                tags.append(tag)
            if len(tags) == 5:
                break
    tags = tags or fallback_tags
    return {
        "response_text": response_text[:220],
        "mood": mood,
        "memory_proposal": {"summary": summary[:160], "tags": tags},
    }


def build_prompt(state: CreatureState, memories: list[dict[str, Any]], moment: str) -> str:
    memory_text = "\n".join(
        f"- {m['summary']} ({', '.join(m.get('tags', [])[:4])})" for m in memories[:5]
    ) or "(none yet)"
    state_text = json.dumps(
        {
            "name": state.name,
            "form": state.form,
            "mood": state.mood,
            "traits": state.traits,
            "artifacts": state.artifact_count,
        },
        sort_keys=True,
    )
    return USER_TEMPLATE.format(state=state_text, memories=memory_text, moment=moment.strip())


def palette_for(seed: str) -> tuple[str, str, str]:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    a = f"#{digest[0:6]}"
    b = f"#{digest[6:12]}"
    c = f"#{digest[12:18]}"
    return a, b, c


def make_artifact(moment: str, state: CreatureState, model_result: dict[str, Any]) -> dict[str, Any]:
    memory = model_result["memory_proposal"]
    tags = memory["tags"]
    seed = f"{state.seed}|{state.artifact_count}|{moment}|{state.mood}|{','.join(tags)}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    primary, secondary, accent = palette_for(seed)
    kinds = ["glyph", "leaf", "signal", "mote", "relic", "shell"]
    kind = kinds[int(digest[0:2], 16) % len(kinds)]
    tag_name = tags[0].replace("_", "-") if tags else "moment"
    title = f"{tag_name.title()} {kind.title()} #{state.artifact_count + 1}"
    shape_count = 3 + int(digest[2:4], 16) % 5
    inscription = memory["summary"]
    svg = render_artifact_svg(
        title=title,
        kind=kind,
        primary=primary,
        secondary=secondary,
        accent=accent,
        shape_count=shape_count,
        digest=digest,
    )
    return {
        "title": title,
        "kind": kind,
        "tags": tags,
        "palette": [primary, secondary, accent],
        "inscription": inscription,
        "svg": svg,
    }


def render_artifact_svg(
    title: str,
    kind: str,
    primary: str,
    secondary: str,
    accent: str,
    shape_count: int,
    digest: str,
) -> str:
    parts = [
        '<svg viewBox="0 0 240 170" xmlns="http://www.w3.org/2000/svg" role="img">',
        f'<rect width="240" height="170" rx="18" fill="{html.escape(primary)}" opacity=".18"/>',
        f'<rect x="10" y="10" width="220" height="150" rx="14" fill="#fffdf7" stroke="{html.escape(secondary)}" stroke-width="2"/>',
    ]
    for i in range(shape_count):
        chunk = digest[i * 6 : i * 6 + 6].ljust(6, "0")
        x = 34 + int(chunk[0:2], 16) % 160
        y = 34 + int(chunk[2:4], 16) % 86
        r = 8 + int(chunk[4:6], 16) % 22
        color = [primary, secondary, accent][i % 3]
        if kind in {"leaf", "shell"}:
            parts.append(
                f'<ellipse cx="{x}" cy="{y}" rx="{r + 8}" ry="{max(6, r - 2)}" '
                f'fill="{html.escape(color)}" opacity=".68" transform="rotate({(i * 29) % 90} {x} {y})"/>'
            )
        else:
            parts.append(
                f'<circle cx="{x}" cy="{y}" r="{r}" fill="{html.escape(color)}" opacity=".66"/>'
            )
    parts.append(f'<text x="120" y="142" text-anchor="middle" font-size="12" fill="#2b2b2b">{html.escape(title[:28])}</text>')
    parts.append("</svg>")
    return "".join(parts)


def process_moment(moment: str, store: CreatureStore, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    moment = (moment or "").strip()
    if not moment:
        raise ValueError("moment is empty")
    state = store.state()
    prompt = build_prompt(state, store.recent_memories(), moment)
    try:
        raw = chat(SYSTEM, prompt, model=model)
        parsed = _extract_json(raw)
    except Exception:
        parsed = None
    normalized = normalize_model_result(parsed, moment)
    tags = normalized["memory_proposal"]["tags"]
    artifact = make_artifact(moment, state, normalized)
    result = store.add_moment(
        text=moment,
        tags=tags,
        mood=normalized["mood"],
        response_text=normalized["response_text"],
        memory_summary=normalized["memory_proposal"]["summary"],
        artifact=artifact,
    )
    return {
        "moment": moment,
        "entry_id": result.entry_id,
        "memory_id": result.memory_id,
        "artifact_id": result.artifact_id,
        "response_text": normalized["response_text"],
        "state": asdict(result.state),
        "artifact": artifact,
        "memory": normalized["memory_proposal"],
    }
