"""Local journal store with private semantic memory.

Everything lives on-device: entries in SQLite, embeddings computed by a local
ollama embedding model. No cloud, no account. The semantic recall is what lets
the companion say "you mentioned the dentist on Tuesday — how'd that go?" without
the model needing a huge context window: we retrieve only the relevant past
entries and feed those in.
"""
from __future__ import annotations

import json
import math
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

import requests

DEFAULT_DB = Path.home() / ".pocket-confidant" / "journal.db"
EMBED_MODEL = "nomic-embed-text:latest"
OLLAMA = "http://localhost:11434"


def embed(text: str, model: str = EMBED_MODEL, host: str = OLLAMA) -> list[float]:
    """Embed text with a local ollama model. Private — never leaves the machine."""
    resp = requests.post(
        f"{host.rstrip('/')}/api/embeddings",
        json={"model": model, "prompt": text},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


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
        self.conn = sqlite3.connect(self.db_path)
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
            return []
        rows = self.conn.execute(
            "SELECT * FROM entries WHERE embedding != ''"
            + (" AND id < ?" if before_id is not None else ""),
            (before_id,) if before_id is not None else (),
        ).fetchall()
        scored: list[tuple[float, Entry]] = []
        for r in rows:
            try:
                emb = json.loads(r["embedding"])
            except (json.JSONDecodeError, TypeError):
                continue
            score = _cosine(qe, emb)
            if score >= min_score:
                scored.append((score, self._row(r)))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [e for _, e in scored[:k]]

    def all(self) -> list[Entry]:
        rows = self.conn.execute("SELECT * FROM entries ORDER BY id").fetchall()
        return [self._row(r) for r in rows]

    @staticmethod
    def _row(r: sqlite3.Row) -> Entry:
        return Entry(id=r["id"], ts=r["ts"], day=r["day"], text=r["text"],
                     reflection=r["reflection"], question=r["question"])

    def close(self) -> None:
        self.conn.close()
