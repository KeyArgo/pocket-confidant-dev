"""SQLite state store for Petriarium.

The store is intentionally small: the hackathon app needs persistence,
receipts, and deterministic state, not a full agent memory framework.
"""
from __future__ import annotations

import json
import random
import sqlite3
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DEFAULT_DB = Path.home() / ".petriarium" / "petriarium.db"

TRAITS = (
    "curiosity",
    "mischief",
    "tenderness",
    "orderliness",
    "appetite",
    "weirdness",
    "social_bond",
)

MOODS = ("bright", "shy", "buzzing", "stormy", "sleepy", "entranced")


@dataclass
class CreatureState:
    seed: int
    name: str
    form: str
    mood: str
    traits: dict[str, float]
    color_seed: str
    artifact_count: int = 0
    entry_count: int = 0


@dataclass
class MomentResult:
    entry_id: int
    artifact_id: int
    memory_id: int
    response_text: str
    artifact: dict[str, Any]
    state: CreatureState


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def make_genome(seed: int | None = None) -> CreatureState:
    seed = int(seed if seed is not None else time.time() * 1000) % 2_147_483_647
    rng = random.Random(seed)
    stems = ["Moss", "Blink", "Lint", "Orb", "Glyph", "Wisp", "Nook", "Flick"]
    suffixes = ["let", "mote", "kin", "bud", "ling", "node", "sprout", "bit"]
    traits = {trait: round(rng.uniform(0.18, 0.82), 3) for trait in TRAITS}
    color_seed = f"#{rng.randrange(0x38516A, 0xE8D98A):06x}"
    return CreatureState(
        seed=seed,
        name=rng.choice(stems) + rng.choice(suffixes),
        form="seedling",
        mood=rng.choice(MOODS),
        traits=traits,
        color_seed=color_seed,
    )


def keyword_tags(text: str) -> list[str]:
    words = [
        "".join(ch for ch in raw.lower() if ch.isalnum() or ch in "-_")
        for raw in text.split()
    ]
    stop = {
        "the",
        "and",
        "but",
        "for",
        "with",
        "that",
        "this",
        "about",
        "from",
        "have",
        "just",
        "really",
        "today",
        "tonight",
        "feel",
        "feeling",
    }
    tags: list[str] = []
    for word in words:
        if len(word) < 4 or word in stop or word in tags:
            continue
        tags.append(word)
        if len(tags) == 5:
            break
    return tags or ["moment"]


def mutate_traits(state: CreatureState, text: str, tags: list[str], mood: str) -> CreatureState:
    traits = dict(state.traits)
    lowered = text.lower()
    mood = mood if mood in MOODS else state.mood

    if "?" in text or any(t in lowered for t in ("wonder", "curious", "learn", "why")):
        traits["curiosity"] += 0.07
    if any(t in lowered for t in ("joke", "weird", "silly", "chaos", "prank")):
        traits["mischief"] += 0.07
    if any(t in lowered for t in ("sad", "nervous", "tired", "lonely", "afraid")):
        traits["tenderness"] += 0.08
        traits["social_bond"] += 0.04
    if any(t in lowered for t in ("deadline", "folder", "plan", "list", "schedule")):
        traits["orderliness"] += 0.08
    if len(text) > 140:
        traits["appetite"] += 0.05
    if any(t in lowered for t in ("impossible", "signal", "dream", "strange", "alien")):
        traits["weirdness"] += 0.08

    traits["social_bond"] += 0.025
    traits["appetite"] += min(0.04, len(tags) * 0.006)
    traits = {k: round(_clamp(v), 3) for k, v in traits.items()}

    form = state.form
    next_count = state.entry_count + 1
    if next_count >= 4 and traits.get("social_bond", 0) > 0.38:
        form = "specimen"
    elif next_count >= 2:
        form = "sproutling"

    return CreatureState(
        seed=state.seed,
        name=state.name,
        form=form,
        mood=mood,
        traits=traits,
        color_seed=state.color_seed,
        artifact_count=state.artifact_count,
        entry_count=state.entry_count,
    )


class CreatureStore:
    def __init__(self, db_path: Path | str = DEFAULT_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self.ensure_state()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS creature_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                state_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                text TEXT NOT NULL,
                tags_json TEXT NOT NULL DEFAULT '[]'
            );
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                summary TEXT NOT NULL,
                tags_json TEXT NOT NULL DEFAULT '[]',
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                memory_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                kind TEXT NOT NULL,
                content_json TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                kind TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def ensure_state(self) -> CreatureState:
        row = self.conn.execute("SELECT state_json FROM creature_state WHERE id=1").fetchone()
        if row:
            return self._state_from_json(row["state_json"])
        state = make_genome()
        self.save_state(state)
        return state

    def state(self) -> CreatureState:
        return self.ensure_state()

    def save_state(self, state: CreatureState) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO creature_state (id, state_json) VALUES (1, ?)",
            (json.dumps(asdict(state), sort_keys=True),),
        )
        self.conn.commit()

    def recent_entries(self, n: int = 3) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM entries ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
        return [
            {"id": r["id"], "text": r["text"], "tags": json.loads(r["tags_json"])}
            for r in reversed(rows)
        ]

    def recent_memories(self, n: int = 6) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM memories ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
        return [
            {
                "id": r["id"],
                "entry_id": r["entry_id"],
                "summary": r["summary"],
                "tags": json.loads(r["tags_json"]),
            }
            for r in rows
        ]

    def artifacts(self, n: int = 12) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM artifacts ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
        return [self._artifact_row(r) for r in rows]

    def recent_events(self, n: int = 12) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
        events: list[dict[str, Any]] = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            summary = ", ".join(
                part
                for part in (
                    f"entry #{payload.get('entry_id')}" if payload.get("entry_id") else "",
                    f"memory #{payload.get('memory_id')}" if payload.get("memory_id") else "",
                    f"artifact #{payload.get('artifact_id')}" if payload.get("artifact_id") else "",
                    str(payload.get("mood", "")),
                )
                if part
            )
            events.append(
                {
                    "id": row["id"],
                    "kind": row["kind"],
                    "when": time.strftime("%H:%M:%S", time.localtime(row["ts"])),
                    "summary": summary or "moment recorded",
                    "payload": payload,
                }
            )
        return events

    def add_moment(
        self,
        text: str,
        tags: list[str],
        mood: str,
        response_text: str,
        memory_summary: str,
        artifact: dict[str, Any],
    ) -> MomentResult:
        now = time.time()
        state = mutate_traits(self.state(), text=text, tags=tags, mood=mood)
        entry_cur = self.conn.execute(
            "INSERT INTO entries (ts, text, tags_json) VALUES (?, ?, ?)",
            (now, text, json.dumps(tags)),
        )
        entry_id = int(entry_cur.lastrowid)
        memory_cur = self.conn.execute(
            "INSERT INTO memories (entry_id, summary, tags_json, created_at) VALUES (?, ?, ?, ?)",
            (entry_id, memory_summary, json.dumps(tags), now),
        )
        memory_id = int(memory_cur.lastrowid)
        artifact_cur = self.conn.execute(
            """
            INSERT INTO artifacts (entry_id, memory_id, title, kind, content_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                memory_id,
                str(artifact.get("title", "Untitled relic")),
                str(artifact.get("kind", "glyph")),
                json.dumps(artifact, sort_keys=True),
                now,
            ),
        )
        artifact_id = int(artifact_cur.lastrowid)
        state.artifact_count += 1
        state.entry_count += 1
        self.save_state(state)
        self.conn.execute(
            "INSERT INTO events (ts, kind, payload_json) VALUES (?, ?, ?)",
            (
                now,
                "moment",
                json.dumps(
                    {
                        "entry_id": entry_id,
                        "memory_id": memory_id,
                        "artifact_id": artifact_id,
                        "mood": mood,
                    },
                    sort_keys=True,
                ),
            ),
        )
        self.conn.commit()
        return MomentResult(
            entry_id=entry_id,
            artifact_id=artifact_id,
            memory_id=memory_id,
            response_text=response_text,
            artifact=artifact,
            state=state,
        )

    def reset(self, seed: int | None = None) -> CreatureState:
        self.conn.executescript(
            """
            DELETE FROM events;
            DELETE FROM artifacts;
            DELETE FROM memories;
            DELETE FROM entries;
            DELETE FROM creature_state;
            """
        )
        state = make_genome(seed)
        self.save_state(state)
        self.conn.commit()
        return state

    def close(self) -> None:
        self.conn.close()

    @staticmethod
    def _state_from_json(raw: str) -> CreatureState:
        data = json.loads(raw)
        return CreatureState(
            seed=int(data["seed"]),
            name=str(data["name"]),
            form=str(data["form"]),
            mood=str(data["mood"]),
            traits={k: float(v) for k, v in dict(data["traits"]).items()},
            color_seed=str(data["color_seed"]),
            artifact_count=int(data.get("artifact_count", 0)),
            entry_count=int(data.get("entry_count", 0)),
        )

    @staticmethod
    def _artifact_row(row: sqlite3.Row) -> dict[str, Any]:
        data = json.loads(row["content_json"])
        data.update(
            {
                "id": row["id"],
                "entry_id": row["entry_id"],
                "memory_id": row["memory_id"],
                "title": row["title"],
                "kind": row["kind"],
            }
        )
        return data
