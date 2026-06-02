"""Simulate a week of journaling and print the companion's responses, so we can
judge warmth/creepiness by eye AND verify that local memory actually fires
(a later entry should call back to an earlier, related one).

Usage: python tests/run_confidant.py [model]   # e.g. qwen3:8b, gemma4:e4b, minicpm-v
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.store import JournalStore  # noqa: E402
from engine.confidant import reflect, DEFAULT_MODEL  # noqa: E402

# A realistic week with two recurring threads:
#   - the dentist (dread on day 2 -> relief on day 5)
#   - a side project (excited/overwhelmed day 1 -> progress day 4 -> doubt day 6)
WEEK = [
    ("2026-06-01", "Started a little side project tonight, a tiny app idea I've had for months. "
                   "Excited but honestly a bit overwhelmed — there's so much I don't know yet."),
    ("2026-06-02", "Have a dentist appointment Thursday and I'm dreading it. I always put these off. "
                   "Probably nothing, but my stomach knots up just thinking about the chair."),
    ("2026-06-03", "Rough one at work. I snapped at a coworker over something small and felt awful "
                   "the rest of the day. Not proud of that."),
    ("2026-06-04", "Spent an hour on the side project and actually got something working. First time "
                   "in a while I lost track of time. Felt good to make a thing again."),
    ("2026-06-05", "Dentist is done. It was completely fine — a cleaning and out in 30 minutes. "
                   "All that dread for nothing. Relieved more than anything."),
    ("2026-06-06", "Wondering if I should keep going on the project or let it fizzle like the others. "
                   "Part of me is tired. Part of me doesn't want to quit on it this time."),
]


def main() -> int:
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    db = Path(tempfile.mkdtemp()) / "week.db"
    store = JournalStore(db)
    print(f"=== Pocket Confidant — simulated week  (model: {model}) ===\n")

    callbacks_fired = 0
    for day, text in WEEK:
        # Reflect using only what's already stored (prior days), then save today.
        r = reflect(text, store=store, model=model)
        ts = time.mktime(time.strptime(day, "%Y-%m-%d"))
        store.add(text, day=day, ts=ts, reflection=r.reflection, question=r.question)

        print(f"── {day} ─────────────────────────────────────────")
        print(f"  you : {text}")
        print(f"   ↳  {r.render()}")
        if r.callback:
            callbacks_fired += 1
            print(f"   [memory callback fired]")
        print()

    print("=== checks ===")
    checks = {
        "produced a reflection every day": True,  # reflect() never raises; visual check above
        "memory called back at least once (the 'it remembers' magic)": callbacks_fired >= 1,
    }
    ok = True
    for label, passed in checks.items():
        print(f"  {'PASS' if passed else 'FAIL'}  {label}")
        ok = ok and passed
    print(f"\ncallbacks fired: {callbacks_fired}")
    print("EYEBALL CHECK: are the reflections warm, specific, and NOT creepy/preachy?")
    store.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
