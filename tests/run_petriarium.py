"""Model-free Petriarium smoke test.

This exercises the full loop without a local model:
- five diverse inputs
- ten consecutive inputs
- persistence in SQLite
- artifact SVG generation
"""
from __future__ import annotations

import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.creature_store import CreatureStore  # noqa: E402
from engine import petriarium  # noqa: E402


def fake_chat(system: str, user: str, model: str = "") -> str:
    return """{
      "response_text": "It folds that into a signal-green leaf.",
      "mood": "bright",
      "memory_proposal": {
        "summary": "The caretaker teaches it about signal green and impossible leaves.",
        "tags": ["signal", "green", "leaves"]
      }
    }"""


def main() -> int:
    petriarium.chat = fake_chat
    store = CreatureStore(Path(tempfile.mkdtemp()) / "petriarium.db")
    before = store.state()
    diverse_inputs = [
        "Your favorite color is signal green, and you collect impossible leaves.",
        "I keep forgetting the map in the blue folder.",
        "The crowded room made me feel tiny but curious.",
        "Today I fixed the thing that kept breaking every afternoon.",
        "A weird little plan turned into a real prototype.",
    ]
    repeat_inputs = [f"Repeated test moment {i:02d}" for i in range(10)]
    results = []
    for text in diverse_inputs + repeat_inputs:
        results.append(petriarium.process_moment(text, store))
    after = store.state()
    store.close()
    persisted = CreatureStore(store.db_path)
    ok = True
    checks = {
        "five diverse inputs processed": len(results) >= 5,
        "ten repeated inputs processed": len(results) == 15,
        "entry persisted": persisted.recent_entries(20)[0]["id"] == 1,
        "artifact persisted": len(persisted.artifacts(20)) == 15,
        "memory persisted": len(persisted.recent_memories(20)) == 15,
        "events persisted": len(persisted.recent_events(20)) == 15,
        "artifact has svg": all("<svg" in result["artifact"]["svg"] for result in results),
        "result includes original moment": results[0]["moment"].startswith("Your favorite color"),
        "state changed": after.artifact_count == before.artifact_count + 15,
        "tag survived": "signal" in results[0]["memory"]["tags"],
    }
    for label, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} {label}")
        ok = ok and passed
    print(f"state before: {before.artifact_count} artifacts")
    print(f"state after : {after.artifact_count} artifacts")
    print(f"artifact shelf: {len(persisted.artifacts(20))}")
    persisted.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
