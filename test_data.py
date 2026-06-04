#!/usr/bin/env python3
"""Seed Pocket Confidant with realistic test journal entries.

Run once to populate the database with sample entries that exercise
the semantic recall feature (similar topics should connect, unrelated
ones should stay silent).

Usage:
    cd /mnt/homes/galileo/argo/Development/build-small-2026
    source .venv/bin/activate
    python test_data.py
"""
import datetime
import json
import time
import sys
from pathlib import Path
from datetime import date, timedelta

# Make engine importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from engine.store import JournalStore

DB = Path.home() / ".pocket-confidant" / "test-journal.db"

# Test entries — designed so some topics rhyme (dentist, exercise, sleep)
# and some are one-offs (cooking, travel). This lets you see recall fire
# on related entries and stay silent on unrelated ones.
ENTRIES = [
    {
        "day": "2026-05-28",
        "text": (
            "Had that dentist appointment today. The hygienist said my gums "
            "look better than last time — the new flossing routine is paying off. "
            "Still hate the sound of the drill though. Sat in the waiting room "
            "listening to bad elevator music for 20 minutes before they called me."
        ),
    },
    {
        "day": "2026-05-29",
        "text": (
            "Tried that new ramen place on 5th Street. The tonkotsu was solid "
            "but the broth was way too salty. Sat at the bar and watched the "
            "chef work — kind of meditative. Might go back for the spicy miso."
        ),
    },
    {
        "day": "2026-05-30",
        "text": (
            "Skipped my morning run again. The couch was just too comfortable "
            "at 6am. Told myself I'd go after work but then it rained. At least "
            "I walked to the store instead of driving, so that's something."
        ),
    },
    {
        "day": "2026-05-31",
        "text": (
            "Couldn't fall asleep until almost 2am. Laid there scrolling "
            "through my phone like an idiot. Woke up exhausted and snapped "
            "at coworkers about the budget spreadsheet. Not my best day."
        ),
    },
    {
        "day": "2026-06-01",
        "text": (
            "Mom called. She wants to visit next weekend and I haven't "
            "cleaned the guest room since last Thanksgiving. She also asked "
            "about the promotion again — I don't have the heart to tell her "
            "I'm not even sure I want it."
        ),
    },
    {
        "day": "2026-06-02",
        "text": (
            "Finally went for that run. Only 2 miles but the air felt amazing. "
            "Saw a neighbor walking her dog — the one with the tiny greyhound "
            "that always looks confused. We waved. Small thing but it made "
            "the whole morning better."
        ),
    },
    {
        "day": "2026-06-03",
        "text": (
            "Woke up tired again but made coffee and sat on the porch for "
            "10 minutes before starting work. Just watched the birds at the "
            "feeder. No phone, no agenda. It was the calmest part of my week."
        ),
    },
]


def seed():
    store = JournalStore(DB)
    existing = store.all()
    if existing:
        print(f"Database already has {len(existing)} entries at {DB}")
        print("Skipping seed. Delete the DB first if you want fresh data.")
        return

    print(f"Seeding {len(ENTRIES)} test entries into {DB}...")
    for i, e in enumerate(ENTRIES):
        day = e["day"]
        # Stagger timestamps so entries are in chronological order
        ts = datetime.datetime.fromisoformat(day).timestamp() + (i * 3600)
        entry = store.add(e["text"], day=day, ts=ts)
        print(f"  [{entry.id}] {day}: {e['text'][:60]}...")

    print(f"\nDone. {len(ENTRIES)} entries seeded.")
    print("Open http://localhost:7860 and try writing about:")
    print("  - 'Going to the dentist tomorrow, nervous about the drill'")
    print("    -> should recall May 28 entry (dentist connection)")
    print("  - 'Went for a run this morning, saw the confused greyhound'")
    print("    -> should recall June 2 entry (running + neighbor)")
    print("  - 'Made pasta tonight, tried a new recipe'")
    print("    -> should NOT recall anything (unrelated topic)")
    store.close()


if __name__ == "__main__":
    seed()
