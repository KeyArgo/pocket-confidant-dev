"""Backfill daily reflections/questions into the Pocket Confidant demo data.

The shipped demo journal is meant to feel like a real daily habit:
each entry gets a short reflection and one grounded question, and any memory
callback should only depend on entries that already existed at that point in
time.

This script rewrites:
  - ./data/demo_entries.json
  - ./space/data/demo_entries.json
  - ./space/data/journal_preloaded.db

It preserves the original file order in the JSON files, but the generated
reflections are computed in chronological order before being mapped back.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.store import extract_memory_atoms


JSON_PATHS = [
    REPO_ROOT / "data" / "demo_entries.json",
    REPO_ROOT / "space" / "data" / "demo_entries.json",
]
DB_PATH = REPO_ROOT / "space" / "data" / "journal_preloaded.db"


TOPIC_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("dentist", ("dentist", "hygienist", "gums", "drill", "floss")),
    ("coffee", ("coffee", "mug", "caffeine", "porch")),
    ("home", ("apartment", "home", "kitchen", "closet", "boxes", "porch", "window")),
    ("rain", ("rain", "fogged", "storm")),
    ("walk", ("walk", "stroll", "evening walk")),
    ("work", ("project", "deadline", "team", "deliverable", "scope", "boss", "office", "coworker", "job")),
    ("garden", ("garden", "herbs", "basil", "tomato", "sunflower", "seedlings", "pesto")),
    ("family", ("mom", "dad", "sarah", "max", "grandma", "uncle pete", "jake", "katie")),
    ("yoga", ("yoga", "breathing", "posture", "stretch")),
    ("reading", ("read", "book", "library", "bookstore", "novel")),
    ("coding", ("code", "app", "hackathon", "prototype", "database", "ui", "github", "feature")),
    ("tutoring", ("tutor", "tutoring", "marcus", "chapter book", "reading level")),
    ("movie", ("movie", "film", "documentary", "screen")),
    ("camping", ("camping", "fire", "stove", "stars", "tent")),
    ("holiday", ("christmas", "thanksgiving", "new year's", "new year", "holiday", "solstice", "equinox", "halloween")),
    ("lonely", ("alone", "lonely", "missing", "quiet", "heavier", "waiting")),
]

POSITIVE_WORDS = {
    "good",
    "great",
    "better",
    "beautiful",
    "proud",
    "relieved",
    "nice",
    "lovely",
    "smiled",
    "alive",
    "worked",
    "helped",
    "aligned",
    "warm",
    "steady",
    "good",
    "comforting",
}

HEAVY_WORDS = {
    "hard",
    "brutal",
    "tired",
    "stress",
    "stressed",
    "lonely",
    "worry",
    "worried",
    "draining",
    "drained",
    "hurt",
    "scared",
    "afraid",
    "heavy",
    "late",
    "bad",
    "rough",
    "exhausted",
}

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "those",
    "these",
    "have",
    "has",
    "had",
    "been",
    "are",
    "was",
    "were",
    "you",
    "your",
    "yours",
    "our",
    "their",
    "they",
    "them",
    "then",
    "than",
    "just",
    "very",
    "still",
    "more",
    "less",
    "most",
    "what",
    "when",
    "where",
    "why",
    "how",
    "today",
    "tonight",
    "morning",
    "evening",
    "again",
    "into",
    "onto",
    "over",
    "under",
    "about",
    "after",
    "before",
    "there",
    "here",
    "like",
    "same",
    "really",
    "maybe",
    "could",
    "would",
    "should",
    "did",
    "doing",
    "done",
    "make",
    "made",
}

RECURRING_TOPICS = {
    "coffee",
    "rain",
    "walk",
    "work",
    "garden",
    "family",
    "yoga",
    "reading",
    "coding",
    "tutoring",
    "holiday",
    "home",
    "lonely",
    "camping",
}


def _load_entries(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_entries(path: Path, entries: list[dict]) -> None:
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _split_sentences(text: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", (text or "").strip())]
    return [part for part in parts if part]


def _title_case(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def _to_you(text: str) -> str:
    replacements = [
        (r"\bI'm\b", "you're"),
        (r"\bI’ve\b", "you've"),
        (r"\bI’ve\b", "you've"),
        (r"\bI've\b", "you've"),
        (r"\bI'd\b", "you'd"),
        (r"\bI’ll\b", "you'll"),
        (r"\bI'll\b", "you'll"),
        (r"\bI am\b", "you are"),
        (r"\bI was\b", "you were"),
        (r"\bI\b", "you"),
        (r"\bmy\b", "your"),
        (r"\bme\b", "you"),
        (r"\bmine\b", "yours"),
        (r"\bmyself\b", "yourself"),
    ]
    out = text
    for pattern, replacement in replacements:
        out = re.sub(pattern, replacement, out, flags=re.IGNORECASE)
    out = re.sub(r"\s+", " ", out).strip()
    if out and out[0].islower():
        out = out[0].upper() + out[1:]
    return out


def _shorten(text: str, limit: int = 95) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0]
    return cut + "…"


def _entry_atoms(text: str) -> set[tuple[str, str]]:
    return set(extract_memory_atoms(text))


def _topic(text: str) -> str:
    lowered = (text or "").lower()
    for topic, phrases in TOPIC_RULES:
        if any(phrase in lowered for phrase in phrases):
            return topic
    atoms = _entry_atoms(text)
    if any(atom_type == "person" for atom_type, _ in atoms):
        return "family"
    if any(atom_type == "project" for atom_type, _ in atoms):
        return "coding"
    if any(atom_type == "ritual" for atom_type, _ in atoms):
        return "ritual"
    return "general"


def _tone(text: str) -> str:
    lowered = (text or "").lower()
    if any(word in lowered for word in HEAVY_WORDS):
        return "heavy"
    if any(word in lowered for word in POSITIVE_WORDS):
        return "light"
    return "neutral"


def _describe_prior(prior: dict) -> str:
    prior_text = _shorten(_to_you(_split_sentences(prior["text"])[0]), 88)
    if prior_text:
        return prior_text.rstrip(".")
    return "that earlier entry"


def _match_prior(history: list[dict], current_text: str, topic: str) -> dict | None:
    current_atoms = _entry_atoms(current_text)
    current_people = {value for atom_type, value in current_atoms if atom_type == "person"}
    current_projects = {value for atom_type, value in current_atoms if atom_type == "project"}
    current_rituals = {value for atom_type, value in current_atoms if atom_type == "ritual"}
    current_tokens = {
        tok
        for tok in re.findall(r"[A-Za-z0-9']+", current_text.lower())
        if len(tok) >= 3 and tok not in STOPWORDS
    }
    for prior in reversed(history):
        prior_atoms = prior["atoms"]
        prior_people = {value for atom_type, value in prior_atoms if atom_type == "person"}
        prior_projects = {value for atom_type, value in prior_atoms if atom_type == "project"}
        prior_rituals = {value for atom_type, value in prior_atoms if atom_type == "ritual"}
        if current_people and prior_people and current_people & prior_people:
            return prior
        if current_projects and prior_projects and current_projects & prior_projects:
            return prior
        if current_rituals and prior_rituals and current_rituals & prior_rituals:
            return prior
        if topic in RECURRING_TOPICS and prior["topic"] == topic:
            return prior
        if current_atoms & prior_atoms:
            return prior
        prior_tokens = prior["tokens"]
        if topic in RECURRING_TOPICS and len(current_tokens & prior_tokens) >= 3:
            return prior
    return None


def _reflection_and_question(text: str, topic: str, tone: str, prior: dict | None) -> tuple[str, str]:
    sentences = _split_sentences(text)
    first = _to_you(sentences[0]) if sentences else _to_you(text)
    second = _to_you(sentences[1]) if len(sentences) > 1 else ""
    first = _shorten(first, 110)
    if second:
        second = _shorten(second, 110)

    lead = first
    if lead and not lead.endswith((".", "!", "?")):
        lead += "."

    if second:
        bridge = f"It sounds like {second[:1].lower() + second[1:]}"
        if not bridge.endswith((".", "!", "?")):
            bridge += "."
    elif tone == "heavy":
        bridge = "You're carrying a lot here, and it makes sense that it feels heavy."
    elif tone == "light":
        bridge = "There is a small steadiness in this one that seems worth keeping."
    elif topic == "coffee":
        bridge = "The ritual seems to be doing quiet work for you."
    elif topic == "dentist":
        bridge = "You're getting through a stressful appointment and keeping your footing."
    elif topic == "home":
        bridge = "The apartment still sounds like it is becoming your space."
    elif topic == "walk":
        bridge = "The walk seems to have given the day some breathing room."
    elif topic == "work":
        bridge = "You're still carrying the pressure, but you seem to be handling it with a little more shape."
    elif topic == "garden":
        bridge = "The garden still feels like a place where you have to slow down and notice details."
    elif topic == "family":
        bridge = "That person seems to have stayed with you longer than the rest of the day."
    elif topic == "coding":
        bridge = "The project feels more real every time you touch it."
    elif topic == "yoga":
        bridge = "Your body seems to be catching up with the calm."
    elif topic == "reading":
        bridge = "You gave yourself a quieter stretch of time, and it seems to have helped."
    elif topic == "tutoring":
        bridge = "Showing up for someone else also seems to be giving something back to you."
    elif topic == "holiday":
        bridge = "This feels like one of those calendar days that carries more memory than usual."
    else:
        bridge = "You're naming a small real moment instead of letting the day blur past."

    callback = ""
    if prior is not None:
        callback = (
            f"This also echoes back to {prior['created_at'][:10]}, when { _describe_prior(prior) }."
        )

    reflection_parts = [lead]
    if callback:
        reflection_parts.append(callback)
    reflection_parts.append(bridge)
    reflection = " ".join(part.strip() for part in reflection_parts if part.strip())

    if topic == "coffee":
        question = "Did the porch feel quieter today, or just familiar?"
    elif topic == "dentist":
        question = "Did the drill sound or the waiting room bother you more?"
    elif topic == "home":
        question = "What part of the apartment already feels like yours?"
    elif topic == "rain":
        question = "Did the rain make the day calmer or just slower?"
    elif topic == "walk":
        question = "What did the walk change for you, even a little?"
    elif topic == "work":
        question = "What part of work was asking the most of you?"
    elif topic == "garden":
        question = "What felt most alive in the garden today?"
    elif topic == "family":
        question = "What stayed with you most from that conversation?"
    elif topic == "yoga":
        question = "Did your body feel different after class?"
    elif topic == "reading":
        question = "What made the reading worth the time today?"
    elif topic == "coding":
        question = "Which part of the project feels most real now?"
    elif topic == "tutoring":
        question = "What moment from tutoring are you still thinking about?"
    elif topic == "movie":
        question = "What made that feel right for the evening?"
    elif topic == "camping":
        question = "What part of being away felt most restorative?"
    elif topic == "holiday":
        question = "What part of the day mattered most to you?"
    elif tone == "heavy":
        question = "What part of this feels heaviest right now?"
    else:
        question = "What detail from today do you want to keep?"

    return reflection, question


def main() -> None:
    source_entries = _load_entries(JSON_PATHS[0])
    chrono = sorted(enumerate(source_entries), key=lambda item: item[1]["created_at"])

    generated_by_index: dict[int, tuple[str, str]] = {}
    history: list[dict] = []

    for original_index, entry in chrono:
        text = entry["text"]
        topic = _topic(text)
        tone = _tone(text)
        prior = _match_prior(history, text, topic)
        reflection, question = _reflection_and_question(text, topic, tone, prior)
        generated_by_index[original_index] = (reflection, question)
        history.append(
            {
                "created_at": entry["created_at"],
                "text": text,
                "topic": topic,
                "tone": tone,
                "tokens": {
                    tok for tok in re.findall(r"[A-Za-z0-9']+", text.lower()) if len(tok) >= 3
                },
                "atoms": _entry_atoms(text),
            }
        )

    for path in JSON_PATHS:
        entries = _load_entries(path)
        for idx, entry in enumerate(entries):
            reflection, question = generated_by_index[idx]
            entry["reflection"] = reflection
            entry["question"] = question
        _save_entries(path, entries)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, ts, day, text FROM entries ORDER BY ts, id").fetchall()
    if len(rows) != len(chrono):
        raise RuntimeError(
            f"DB row count ({len(rows)}) does not match demo data ({len(chrono)})"
        )
    for (original_index, _), row in zip(chrono, rows):
        reflection, question = generated_by_index[original_index]
        conn.execute(
            "UPDATE entries SET reflection=?, question=? WHERE id=?",
            (reflection, question, row["id"]),
        )
    conn.commit()
    conn.close()

    print(f"Backfilled {len(chrono)} reflections/questions into JSON + DB")


if __name__ == "__main__":
    main()
