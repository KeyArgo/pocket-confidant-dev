"""Offline checks for Pocket Confidant memory receipts and store features.

Run from the repo root:
    .venv/bin/python tests/test_confidant_receipts.py
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import engine.store as store_module
from engine import confidant
from engine.store import Entry, JournalStore, extract_memory_atoms


class FakeStore:
    def __init__(self, entries: list[Entry]):
        self.entries = entries

    def recall(self, query: str, k: int = 3, before_id=None, min_score: float = 0.0) -> list[Entry]:
        assert query == "The dentist went better than I expected."
        assert k == 3
        assert min_score == confidant.RECALL_FLOOR
        return self.entries


def test_reflection_carries_recalled_entries() -> None:
    recalled = [
        Entry(
            id=1,
            ts=1.0,
            day="2026-06-01",
            text="I keep putting off the dentist because the chair makes my stomach knot up.",
        )
    ]
    original_chat = confidant._chat
    try:
        confidant._chat = lambda *args, **kwargs: (
            '{"reflection":"You sound relieved that the appointment was smaller than the dread.",'
            '"question":"What made it feel survivable this time?",'
            '"callback":"Earlier, the dentist chair was the part your body kept bracing for."}'
        )
        result = confidant.reflect(
            "The dentist went better than I expected.",
            store=FakeStore(recalled),
            model="fake-local-model",
        )
    finally:
        confidant._chat = original_chat

    assert result.recalled == recalled
    assert "dentist chair" in result.callback


def load_confidant_app():
    db_dir = Path(tempfile.mkdtemp())
    os.environ["POCKET_CONFIDANT_DB"] = str(db_dir / "journal.db")
    path = Path(__file__).resolve().parents[1] / "apps" / "confidant" / "app.py"
    spec = importlib.util.spec_from_file_location("confidant_app_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_receipt_html_is_escaped_and_limited() -> None:
    app = load_confidant_app()
    try:
        html = app._receipt_html(
            [
                Entry(
                    id=1,
                    ts=1.0,
                    day="2026-06-01",
                    text="<script>alert('private')</script>\n" + ("dentist " * 40),
                ),
                Entry(id=2, ts=2.0, day="2026-06-02", text="Second recalled entry."),
                Entry(id=3, ts=3.0, day="2026-06-03", text="This third receipt should not render."),
            ]
        )
    finally:
        app.STORE.close()

    assert "source receipts" in html
    assert "2026-06-01" in html
    assert "2026-06-02" in html
    assert "2026-06-03" not in html
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "..." in html


def test_memory_atoms_and_keyword_recall_work_without_embeddings() -> None:
    db = Path(tempfile.mkdtemp()) / "journal.db"
    store = JournalStore(db)
    original_embed = store_module.embed
    try:
        store_module.embed = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline"))
        first = store.add(
            "Lost three hours on the side project and felt like myself.",
            day="2026-06-01",
            ts=time.time(),
        )
        second = store.add(
            "Mom called and the phone call left me drained.",
            day="2026-06-02",
            ts=time.time() + 1,
        )
        recalled = store.recall(
            "I miss time that is just mine for the side project.",
            k=2,
            min_score=confidant.RECALL_FLOOR,
        )
        atoms = store.memory_atoms()
    finally:
        store_module.embed = original_embed
        store.close()

    assert first.id != second.id
    assert recalled
    assert recalled[0].text.startswith("Lost three hours")
    assert any(a.atom_type == "project" and a.value == "side project" for a in atoms)
    assert any(a.atom_type == "person" and a.value == "Mom" for a in atoms)


def test_extract_memory_atoms_dedupes() -> None:
    atoms = extract_memory_atoms("Mom called Mom about my side project. I miss quiet time.")
    assert atoms.count(("person", "Mom")) == 1
    assert ("project", "side project") in atoms


def test_demo_seed_leaves_payoff_entry_for_user() -> None:
    db = Path(tempfile.mkdtemp()) / "journal.db"
    store = JournalStore(db)
    original_embed = store_module.embed
    try:
        store_module.embed = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline"))
        added = store.seed_demo()
        texts = [e.text for e in store.all()]
    finally:
        store_module.embed = original_embed
        store.close()

    # Full-year demo: 341 entries, all before 6/7/2026 (hackathon end).
    assert added == 341
    # The payoff entry the user is prompted to write.
    assert not any(t.startswith("Slammed all week") for t in texts)
    # Cross-referenced details that demonstrate recall.
    assert any("the project" in t for t in texts)
    assert any("Sarah" in t for t in texts)
    assert any("Mom" in t for t in texts)
    assert any("morning coffee" in t for t in texts)


def test_fts5_search_finds_entries() -> None:
    db = Path(tempfile.mkdtemp()) / "journal.db"
    store = JournalStore(db)
    original_embed = store_module.embed
    try:
        store_module.embed = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline"))
        store.add("Morning coffee on the porch before anyone else woke up.", day="2026-06-01", ts=1.0)
        store.add("Worked late and skipped the walk.", day="2026-06-02", ts=2.0)
        store.add("Sarah asked if I'm okay.", day="2026-06-03", ts=3.0)

        results = store.search("coffee porch")
        assert len(results) >= 1
        assert any("coffee" in e.text for e in results)

        results2 = store.search("Sarah")
        assert len(results2) >= 1
        assert any("Sarah" in e.text for e in results2)

        results3 = store.search("xyznonexistent")
        assert len(results3) == 0
    finally:
        store_module.embed = original_embed
        store.close()


def test_available_months_and_years() -> None:
    db = Path(tempfile.mkdtemp()) / "journal.db"
    store = JournalStore(db)
    original_embed = store_module.embed
    try:
        store_module.embed = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline"))
        store.add("Entry one", day="2026-04-05", ts=1.0)
        store.add("Entry two", day="2026-04-20", ts=2.0)
        store.add("Entry three", day="2026-06-10", ts=3.0)

        months = store.available_months()
        assert (2026, 4) in months
        assert (2026, 6) in months
        assert len(months) == 2

        years = store.available_years()
        assert 2026 in years
        assert len(years) == 1
    finally:
        store_module.embed = original_embed
        store.close()


def test_entries_by_month_filtering() -> None:
    db = Path(tempfile.mkdtemp()) / "journal.db"
    store = JournalStore(db)
    original_embed = store_module.embed
    try:
        store_module.embed = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline"))
        store.add("April entry", day="2026-04-10", ts=1.0)
        store.add("May entry", day="2026-05-15", ts=2.0)
        store.add("June entry", day="2026-06-20", ts=3.0)

        april = store.entries_by_month(2026, 4)
        assert len(april) == 1
        assert april[0].text == "April entry"

        june = store.entries_by_month(2026, 6)
        assert len(june) == 1
        assert june[0].text == "June entry"

        empty = store.entries_by_month(2025, 12)
        assert len(empty) == 0
    finally:
        store_module.embed = original_embed
        store.close()


def test_export_csv() -> None:
    db = Path(tempfile.mkdtemp()) / "journal.db"
    store = JournalStore(db)
    original_embed = store_module.embed
    try:
        store_module.embed = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline"))
        store.add("First entry", day="2026-06-01", ts=1.0, reflection="Warm", question="How?")
        store.add("Second entry", day="2026-06-02", ts=2.0)

        out = Path(tempfile.mkdtemp()) / "test.csv"
        count = store.export_csv(str(out))
        assert count == 2
        content = out.read_text()
        assert "date,text,reflection,question" in content
        assert "First entry" in content
        assert "Second entry" in content
        assert "Warm" in content
    finally:
        store_module.embed = original_embed
        store.close()


def test_export_json() -> None:
    import json as _json
    db = Path(tempfile.mkdtemp()) / "journal.db"
    store = JournalStore(db)
    original_embed = store_module.embed
    try:
        store_module.embed = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline"))
        store.add("JSON test entry", day="2026-06-01", ts=1.0, reflection="Yes", question="Why?")

        out = Path(tempfile.mkdtemp()) / "test.json"
        count = store.export_json(str(out))
        assert count == 1
        data = _json.loads(out.read_text())
        assert len(data) == 1
        assert data[0]["date"] == "2026-06-01"
        assert data[0]["text"] == "JSON test entry"
        assert data[0]["reflection"] == "Yes"
    finally:
        store_module.embed = original_embed
        store.close()


def test_export_markdown() -> None:
    db = Path(tempfile.mkdtemp()) / "journal.db"
    store = JournalStore(db)
    original_embed = store_module.embed
    try:
        store_module.embed = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline"))
        store.add("MD entry one", day="2026-06-01", ts=1.0, reflection="Nice", question="Really?")
        store.add("MD entry two", day="2026-06-15", ts=2.0)

        out = Path(tempfile.mkdtemp()) / "test.md"
        count = store.export_markdown(str(out))
        assert count == 2
        content = out.read_text()
        assert "# My Journal" in content
        assert "## June 2026" in content
        assert "MD entry one" in content
        assert "Nice" in content
        assert "Really?" in content
    finally:
        store_module.embed = original_embed
        store.close()


def test_delete_entry() -> None:
    db = Path(tempfile.mkdtemp()) / "journal.db"
    store = JournalStore(db)
    original_embed = store_module.embed
    try:
        store_module.embed = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline"))
        e1 = store.add("Delete me", day="2026-06-01", ts=1.0)
        e2 = store.add("Keep me", day="2026-06-02", ts=2.0)

        # Delete the first entry.
        assert store.delete(e1.id) is True
        # Second entry still exists.
        remaining = store.all()
        assert len(remaining) == 1
        assert remaining[0].text == "Keep me"

        # Deleting a non-existent entry returns False.
        assert store.delete(9999) is False

        # Deleting again returns False.
        assert store.delete(e1.id) is False
    finally:
        store_module.embed = original_embed
        store.close()


def main() -> int:
    test_reflection_carries_recalled_entries()
    test_receipt_html_is_escaped_and_limited()
    test_memory_atoms_and_keyword_recall_work_without_embeddings()
    test_extract_memory_atoms_dedupes()
    test_demo_seed_leaves_payoff_entry_for_user()
    test_fts5_search_finds_entries()
    test_available_months_and_years()
    test_entries_by_month_filtering()
    test_export_csv()
    test_export_json()
    test_export_markdown()
    test_delete_entry()
    print("PASS confidant memory receipts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
