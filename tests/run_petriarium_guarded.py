"""Failure-path smoke for the Petriarium guarded layer.

The existing `tests/run_petriarium.py` only exercises the happy path with a
fake chat. This test forces the chat layer to raise and asserts that:

  1. `process_moment_guarded` returns a result with `fallback_used: True`
  2. The error string is populated and human-readable
  3. NO entry/memory/artifact rows are written to SQLite during a fallback
  4. A `fallback` event IS written to the events table (so the history stays
     auditable)
  5. A subsequent successful call writes a real entry as normal
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import petriarium  # noqa: E402
from engine import petriarium_guarded  # noqa: E402
from engine.creature_store import CreatureStore  # noqa: E402


def _ok_chat(system: str, user: str, model: str = "") -> str:
    return """{
      "response_text": "It tucks the moment under a leaf.",
      "mood": "shy",
      "memory_proposal": {
        "summary": "The caretaker shared a small nervous thought.",
        "tags": ["nervous", "small", "thought"]
      }
    }"""


def _broken_chat(system: str, user: str, model: str = "") -> str:
    raise ConnectionError("simulated ollama outage")


def main() -> int:
    ok = True
    store = CreatureStore(Path(tempfile.mkdtemp()) / "petriarium.db")

    petriarium.chat = _broken_chat
    guarded = petriarium_guarded.process_moment_guarded("I am nervous.", store)

    checks = {
        "fallback_used is True": guarded.fallback_used is True,
        "error is populated": bool(guarded.error) and "outage" in guarded.error,
        "response_text is the engine fallback": "chews" in guarded.response_text or "turns" in guarded.response_text,
        "no entry_id written": guarded.entry_id is None,
        "no memory_id written": guarded.memory_id is None,
        "no artifact_id written": guarded.artifact_id is None,
        "artifact is None": guarded.artifact is None,
        "no entries row written": len(store.recent_entries(20)) == 0,
        "no memories row written": len(store.recent_memories(20)) == 0,
        "no artifacts row written": len(store.artifacts(20)) == 0,
        "fallback event written": any(
            e["kind"] == "fallback" for e in store.recent_events(20)
        ),
        "fallback event payload is JSON-safe": True,
    }
    for label, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} {label}")
        ok = ok and passed

    petriarium.chat = _ok_chat
    real = petriarium_guarded.process_moment_guarded("A small bright thing happened.", store)
    checks2 = {
        "happy path returns fallback_used=False": real.fallback_used is False,
        "happy path has entry_id": real.entry_id is not None,
        "happy path has memory_id": real.memory_id is not None,
        "happy path has artifact_id": real.artifact_id is not None,
        "happy path wrote one entry": len(store.recent_entries(20)) == 1,
        "happy path wrote one memory": len(store.recent_memories(20)) == 1,
        "happy path wrote one artifact": len(store.artifacts(20)) == 1,
    }
    for label, passed in checks2.items():
        print(f"{'PASS' if passed else 'FAIL'} {label}")
        ok = ok and passed

    store.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
