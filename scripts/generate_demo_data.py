import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / ".pocket-confidant" / "journal.db"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "demo_entries.json"

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT ts, text, reflection, question FROM entries").fetchall()
conn.close()

entries = []
for row in rows:
    entries.append({
        "created_at": datetime.fromtimestamp(row["ts"]).isoformat(),
        "text": row["text"],
        "reflection": row["reflection"] or "",
        "question": row["question"] or "",
    })

OUT_PATH.write_text(json.dumps(entries, indent=2, ensure_ascii=False))
print(f"Exported {len(entries)} entries to {OUT_PATH}")
