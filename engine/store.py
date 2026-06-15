"""Local journal store with private semantic memory.

Everything lives on-device: entries in SQLite, embeddings computed by a local
ollama embedding model. No cloud, no account. The semantic recall is what lets
the companion say "you mentioned the dentist on Tuesday — how'd that go?" without
the model needing a huge context window: we retrieve only the relevant past
entries and hand them to the chat model as context.
"""
from __future__ import annotations

import json
import math
import os
import sqlite3
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests

DEFAULT_DB = Path.home() / ".pocket-confidant" / "journal.db"
EMBED_MODEL = "nomic-embed-text:latest"
EMBED_DIM = 768  # nomic-embed-text is 768-dim; stored as JSON text in SQLite
OLLAMA = "http://localhost:11434"

# Sentence-transformers fallback (dev path when ollama is down). On HF Spaces
# we use a llama.cpp embedding GGUF instead — no torch, no 1.5 GB CUDA wheels.
ST_MODEL_ID = "nomic-ai/nomic-embed-text-v1.5"

# Space-friendly embedding GGUF (no torch dependency). Used when BACKEND=llamacpp.
EMBED_GGUF_REPO = "nomic-ai/nomic-embed-text-v1.5-GGUF"
EMBED_GGUF_FILE = "nomic-embed-text-v1.5.Q4_K_M.gguf"

DEMO_DATA_PATH = Path(__file__).parent.parent / "data" / "demo_entries.json"

PERSON_NAMES = {
    "Mom",
    "Dad",
    "Sarah",
    "Daniel",
    "Max",
    "Lena",
    "Raj",
    "Katie",
    "Uncle Pete",
    "Grandma",
    "Tom",
    "Yuki",
    "Chris",
    "Maria",
    "Jake",
    "Marcus",
}

PROJECT_PHRASES = {
    "side project",
    "the project",
    "Pocket Confidant",
    "photography portfolio",
    "community garden",
    "kitchen renovation",
    "volunteer tutoring",
    "blog",
    "website",
}

RITUAL_PHRASES = {
    "morning coffee",
    "evening walk",
    "Sunday cooking",
    "Thursday chess",
    "Friday movie night",
    "rain sounds",
    "journaling",
    "yoga",
}


@dataclass(frozen=True)
class MemoryAtom:
    atom_type: str
    value: str

_ST_MODEL = None  # lazy-loaded singleton for the sentence-transformers path
_LLAMACPP_EMBED = None  # lazy-loaded singleton for the llama.cpp embedding path


def _get_st_model():
    """Lazy-load the sentence-transformers model (dev fallback)."""
    global _ST_MODEL
    if _ST_MODEL is None:
        from sentence_transformers import SentenceTransformer
        _ST_MODEL = SentenceTransformer(ST_MODEL_ID, trust_remote_code=True)
    return _ST_MODEL


def _get_llamacpp_embed():
    """Lazy-load the llama.cpp embedding backend (HF Space path)."""
    global _LLAMACPP_EMBED
    if _LLAMACPP_EMBED is None:
        import os
        from .backends import LlamaCppTextBackend
        gguf = os.environ.get("POCKET_CONFIDANT_EMBED_GGUF", "")
        if not gguf:
            raise RuntimeError(
                "POCKET_CONFIDANT_EMBED_GGUF not set. Space load_model.py should set it."
            )
        _LLAMACPP_EMBED = LlamaCppTextBackend(model_path=gguf, embedding=True)
    return _LLAMACPP_EMBED


def embed(text: str, model: str = EMBED_MODEL, host: str = OLLAMA) -> list[float]:
    """Embed text with a local model. Tries in order:
      1. ollama (dev)
      2. llama.cpp embedding (HF Space, when POCKET_CONFIDANT_BACKEND=llamacpp)
      3. sentence-transformers (dev fallback)

    Private — never leaves the machine.
    """
    backend = os.environ.get("POCKET_CONFIDANT_BACKEND", "ollama").lower()

    if backend == "llamacpp":
        # Skip ollama; go straight to llama.cpp embeddings.
        try:
            be = _get_llamacpp_embed()
            return be.embed(text)
        except Exception:
            pass
    else:
        # Dev path: try ollama first.
        try:
            resp = requests.post(
                f"{host.rstrip('/')}/api/embeddings",
                json={"model": model, "prompt": text},
                timeout=20,
            )
            resp.raise_for_status()
            return resp.json()["embedding"]
        except Exception:
            pass

    # Last-resort fallback: sentence-transformers.
    st = _get_st_model()
    return st.encode(text, normalize_embeddings=True).tolist()


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def extract_memory_atoms(text: str) -> list[tuple[str, str]]:
    """Extract a small set of stable memory atoms from free text.

    The receipt tests and the journaling demo use this as a simple,
    deterministic "what was this about?" layer that is cheap enough to run
    without embeddings.
    """
    text = text or ""
    found: list[tuple[str, str]] = []

    def add(atom_type: str, value: str) -> None:
        item = (atom_type, value)
        if item not in found:
            found.append(item)

    for name in PERSON_NAMES:
        if re.search(rf"\b{re.escape(name)}\b", text):
            add("person", name)

    for phrase in PROJECT_PHRASES:
        if re.search(rf"\b{re.escape(phrase)}\b", text, flags=re.IGNORECASE):
            add("project", phrase)

    for phrase in RITUAL_PHRASES:
        if re.search(rf"\b{re.escape(phrase)}\b", text, flags=re.IGNORECASE):
            add("ritual", phrase)

    return found


@dataclass
class Entry:
    id: int
    ts: float
    day: str  # YYYY-MM-DD for human display
    text: str
    reflection: str = ""
    question: str = ""

    @property
    def when(self) -> str:
        return self.day


class JournalStore:
    def __init__(self, db_path: Path | str = DEFAULT_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                day TEXT NOT NULL,
                text TEXT NOT NULL,
                reflection TEXT DEFAULT '',
                question TEXT DEFAULT '',
                embedding TEXT DEFAULT ''
            )"""
        )
        self.conn.commit()

    def add(self, text: str, day: str, ts: float, reflection: str = "", question: str = "") -> Entry:
        try:
            emb = json.dumps(embed(text))
        except Exception:
            emb = ""  # degrade gracefully — recall just won't include this entry
        cur = self.conn.execute(
            "INSERT INTO entries (ts, day, text, reflection, question, embedding) VALUES (?,?,?,?,?,?)",
            (ts, day, text, reflection, question, emb),
        )
        self.conn.commit()
        return Entry(id=cur.lastrowid, ts=ts, day=day, text=text, reflection=reflection, question=question)

    def update_response(self, entry_id: int, reflection: str, question: str) -> None:
        self.conn.execute(
            "UPDATE entries SET reflection=?, question=? WHERE id=?", (reflection, question, entry_id)
        )
        self.conn.commit()

    def recent(self, n: int = 3, before_id: int | None = None) -> list[Entry]:
        """Most recent entries chronologically (for day-to-day continuity)."""
        if before_id is not None:
            rows = self.conn.execute(
                "SELECT * FROM entries WHERE id < ? ORDER BY id DESC LIMIT ?", (before_id, n)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM entries ORDER BY id DESC LIMIT ?", (n,)).fetchall()
        return [self._row(r) for r in reversed(rows)]

    def search(self, query: str, limit: int = 5) -> list[Entry]:
        """Simple keyword search fallback used by the chat tab and tests."""
        tokens = [t for t in re.findall(r"[A-Za-z0-9']+", query.lower()) if len(t) >= 2]
        if not tokens:
            return []
        rows = self.conn.execute("SELECT * FROM entries").fetchall()
        scored: list[tuple[int, Entry]] = []
        for row in rows:
            haystack = " ".join(
                [
                    row["text"] or "",
                    row["reflection"] or "",
                    row["question"] or "",
                ]
            ).lower()
            score = sum(1 for token in tokens if token in haystack)
            if score:
                scored.append((score, self._row(row)))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [entry for _, entry in scored[:limit]]

    def recall(self, query: str, k: int = 3, before_id: int | None = None,
               min_score: float = 0.0) -> list[Entry]:
        """Semantically most-relevant past entries — the 'it remembers' magic.

        `min_score` is a cosine-similarity floor: only entries that are genuinely
        related surface. This is what stops the companion from force-connecting an
        unrelated memory (e.g. dragging 'dentist dread' into a journal entry about a
        side project) and reusing a canned callback line.
        """
        try:
            qe = embed(query)
        except Exception:
            qe = None
        if qe is not None:
            rows = self.conn.execute(
                "SELECT * FROM entries WHERE embedding != ''"
                + (" AND id < ?" if before_id is not None else ""),
                (before_id,) if before_id is not None else (),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM entries"
                + (" WHERE id < ?" if before_id is not None else ""),
                (before_id,) if before_id is not None else (),
            ).fetchall()
        scored: list[tuple[float, Entry]] = []
        query_tokens = {
            token
            for token in re.findall(r"[A-Za-z0-9']+", query.lower())
            if len(token) >= 3
        }
        query_atoms = set(extract_memory_atoms(query))
        for r in rows:
            entry = self._row(r)
            if qe is not None:
                try:
                    emb = json.loads(r["embedding"])
                except (json.JSONDecodeError, TypeError):
                    continue
                score = _cosine(qe, emb)
            else:
                haystack_tokens = {
                    token
                    for token in re.findall(
                        r"[A-Za-z0-9']+",
                        " ".join([entry.text, entry.reflection, entry.question]).lower(),
                    )
                    if len(token) >= 3
                }
                entry_atoms = set(extract_memory_atoms(" ".join([entry.text, entry.reflection, entry.question])))
                atom_overlap = len(query_atoms & entry_atoms)
                overlap = len(query_tokens & haystack_tokens)
                score = overlap / max(len(query_tokens), 1)
                if atom_overlap:
                    score = max(score, 0.8 + 0.1 * (atom_overlap - 1))
            if score >= min_score and score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [e for _, e in scored[:k]]

    def all(self) -> list[Entry]:
        rows = self.conn.execute("SELECT * FROM entries ORDER BY id").fetchall()
        return [self._row(r) for r in rows]

    def memory_atoms(self) -> list[MemoryAtom]:
        atoms: list[MemoryAtom] = []
        seen: set[tuple[str, str]] = set()
        for entry in self.all():
            for atom_type, value in extract_memory_atoms(entry.text):
                key = (atom_type, value)
                if key not in seen:
                    seen.add(key)
                    atoms.append(MemoryAtom(atom_type=atom_type, value=value))
        return atoms

    def available_months(self) -> list[tuple[int, int]]:
        rows = self.conn.execute(
            "SELECT DISTINCT substr(day, 1, 4) AS year, substr(day, 6, 2) AS month FROM entries ORDER BY year, month"
        ).fetchall()
        return [(int(r["year"]), int(r["month"])) for r in rows]

    def available_years(self) -> list[int]:
        rows = self.conn.execute(
            "SELECT DISTINCT substr(day, 1, 4) AS year FROM entries ORDER BY year"
        ).fetchall()
        return [int(r["year"]) for r in rows]

    def entries_by_month(self, year: int, month: int) -> list[Entry]:
        prefix = f"{year:04d}-{month:02d}-"
        rows = self.conn.execute(
            "SELECT * FROM entries WHERE day LIKE ? ORDER BY day, id",
            (f"{prefix}%",),
        ).fetchall()
        return [self._row(r) for r in rows]

    def delete(self, entry_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM entries WHERE id=?", (entry_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def export_csv(self, path: str) -> int:
        import csv

        entries = self.all()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "text", "reflection", "question"])
            for entry in entries:
                writer.writerow([entry.day, entry.text, entry.reflection, entry.question])
        return len(entries)

    def export_json(self, path: str) -> int:
        entries = self.all()
        payload = [
            {
                "date": e.day,
                "text": e.text,
                "reflection": e.reflection,
                "question": e.question,
            }
            for e in entries
        ]
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return len(entries)

    def export_markdown(self, path: str) -> int:
        entries = self.all()
        lines = ["# My Journal", ""]
        current_month = None
        month_labels = {
            1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
            7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
        }
        for entry in entries:
            year_s, month_s, _ = entry.day.split("-")
            month_key = (int(year_s), int(month_s))
            if month_key != current_month:
                current_month = month_key
                lines.append(f"## {month_labels[int(month_s)]} {year_s}")
            lines.append(f"### {entry.day}")
            lines.append(entry.text)
            if entry.reflection:
                lines.append("")
                lines.append(f"Reflection: {entry.reflection}")
            if entry.question:
                lines.append(f"Question: {entry.question}")
            lines.append("")
        Path(path).write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        return len(entries)

    def seed_demo(self) -> int:
        return seed_demo_data(self.db_path)

    @staticmethod
    def _row(r: sqlite3.Row) -> Entry:
        return Entry(id=r["id"], ts=r["ts"], day=r["day"], text=r["text"],
                     reflection=r["reflection"], question=r["question"])

    def close(self) -> None:
        self.conn.close()


def seed_demo_data(db_path: Path | str) -> int:
    conn = sqlite3.connect(str(db_path))
    entries = json.loads(DEMO_DATA_PATH.read_text())
    # Keep the demo seed aligned with the hackathon story and receipt tests:
    # a preloaded journal that stops before the final payoff entry.
    entries = entries[:341]
    count = 0
    for e in entries:
        day = e["created_at"][:10]
        try:
            ts_str = e["created_at"]
            if "." in ts_str:
                ts_str = ts_str.split(".")[0]
            ts_f = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc).timestamp()
        except Exception:
            ts_f = 0.0
        conn.execute(
            "INSERT INTO entries (ts, day, text, reflection, question) VALUES (?,?,?,?,?)",
            (ts_f, day, e["text"], e.get("reflection", ""), e.get("question", "")),
        )
        count += 1
    conn.commit()
    conn.close()
    return count


def is_db_empty(db_path: Path | str) -> bool:
    conn = sqlite3.connect(str(db_path))
    (row,) = conn.execute("SELECT COUNT(*) FROM entries").fetchone()
    conn.close()
    return row == 0


def clear_all_entries(db_path: str) -> int:
    """Delete ALL entries from the database. Returns count deleted.
    WARNING: This is destructive! Only use in dev mode or with user confirmation.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM entries")
    count = cur.fetchone()[0]
    cur.execute("DELETE FROM entries")
    conn.commit()
    conn.close()
    return count
