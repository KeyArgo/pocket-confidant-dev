# Pocket Confidant v2 — Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Transform Pocket Confidant from a basic journal into a visually rich, demo-ready hackathon app with analytics, proper companion voice, and fresh deploy behavior.

**Architecture:** Add analytics engine, fix companion voice, restructure UI for fresh demos, add insights tab with charts.

**Tech Stack:** Python, Gradio 6.x, SQLite, Plotly (bundled with Gradio), existing engine/

---

## Context

**User feedback (June 5, 2026):**
1. Fresh session on deploy — demo data should not persist
2. Keep entry text visible after reflection
3. Companion speaks to "you" not "the person"
4. Add graphs/visualizations (leaderboard, busiest days, mood trends)
5. Multiple entries per day with timestamps
6. Show use cases: work, business, personal/play
7. Make eye candy with charts

**Current state:**
- App running at http://localhost:7860
- Companion voice fixed (speaks to "you")
- Entry visibility partially fixed (shows submitted entry)
- No analytics/insights tab yet
- No charts or visualizations

---

## Phase 1: Fresh Deploy + Demo Data Button (Day 1)

### Task 1.1: Create demo data JSON file

**Objective:** Export existing 341 entries to a portable JSON format.

**Files:**
- Create: `data/demo_entries.json`
- Create: `scripts/generate_demo_data.py`

**Step 1: Create demo data generator**

```python
#!/usr/bin/env python3
"""Generate demo_entries.json from existing SQLite database."""
import sqlite3
import json
from pathlib import Path

DB_PATH = Path.home() / ".pocket-confidant" / "journal.db"
OUTPUT = Path(__file__).parent.parent / "data" / "demo_entries.json"

def generate():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM entries ORDER BY created_at")
    entries = []
    for row in cur.fetchall():
        entries.append({
            "created_at": row["created_at"],
            "text": row["text"],
            "reflection": row.get("reflection", ""),
            "question": row.get("question", ""),
        })
    
    conn.close()
    
    OUTPUT.parent.mkdir(exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(entries, f, indent=2)
    
    print(f"Exported {len(entries)} entries to {OUTPUT}")

if __name__ == "__main__":
    generate()
```

**Step 2: Run the generator**
```bash
cd /mnt/homes/galileo/argo/Development/build-small-2026
python3 scripts/generate_demo_data.py
```

**Step 3: Verify output**
```bash
ls -la data/demo_entries.json
wc -l data/demo_entries.json
# Should show ~341 entries
```

---

### Task 1.2: Add seed_demo_data() to store.py

**Objective:** Load demo entries from JSON into fresh database.

**Files:**
- Modify: `engine/store.py`

**Step 1: Add import and function**

At the top of `engine/store.py`, add:
```python
import json
from pathlib import Path

DEMO_DATA_PATH = Path(__file__).parent.parent / "data" / "demo_entries.json"
```

After the `JournalStore` class, add:
```python
def seed_demo_data(db_path: str) -> int:
    """Load demo entries from JSON file into a fresh database.
    Returns the number of entries seeded.
    """
    if not DEMO_DATA_PATH.exists():
        raise FileNotFoundError(f"Demo data not found at {DEMO_DATA_PATH}")
    
    with open(DEMO_DATA_PATH) as f:
        entries = json.load(f)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    count = 0
    for entry in entries:
        cur.execute(
            """INSERT INTO entries (created_at, text, reflection, question)
                VALUES (?, ?, ?, ?)""",
            (entry["created_at"], entry["text"],
             entry.get("reflection", ""), entry.get("question", ""))
        )
        count += 1
    
    conn.commit()
    conn.close()
    return count


def is_db_empty(db_path: str) -> bool:
    """Check if the database has zero entries."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM entries")
    count = cur.fetchone()[0]
    conn.close()
    return count == 0
```

**Step 2: Test the functions**
```python
# Quick test
from engine.store import seed_demo_data, is_db_empty
print(f"DB empty: {is_db_empty(DB_PATH)}")
```

---

### Task 1.3: Add "Load Demo" button to UI

**Objective:** Show demo button when database is empty.

**Files:**
- Modify: `apps/confidant/app.py`

**Step 1: Add state and conditional layout**

In `build()`, after the entry textbox, add:
```python
# Demo data state
demo_loaded = gr.State(value=is_db_empty(DB_PATH))

# Landing page (shown when empty)
with gr.Column(visible=is_db_empty(DB_PATH)) as landing_empty:
    gr.Markdown("## Welcome to Pocket Confidant 📓")
    gr.Markdown("Your private journaling companion. Start writing to see the magic.")
    demo_btn = gr.Button("📚 Load Demo Story (341 entries)", variant="secondary")
    gr.Markdown("*Loads a 12-month journaling story so you can see how it works.*")

# Main content (shown when has data)
with gr.Column(visible=not is_db_empty(DB_PATH)) as landing_has_data:
    # ... existing UI components ...
```

**Step 2: Add callback function**

```python
def handle_load_demo():
    """Seed demo data and return updated UI state."""
    try:
        count = seed_demo_data(DB_PATH)
        return (
            gr.update(visible=False),  # landing_empty
            gr.update(visible=True),   # landing_has_data
            f"✅ Loaded {count} demo entries! Start writing above.",
        )
    except Exception as e:
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            f"⚠️ Could not load demo: {e}",
        )
```

**Step 3: Wire up the button**

```python
demo_btn.click(
    fn=handle_load_demo,
    outputs=[landing_empty, landing_has_data, status_message]
)
```

---

## Phase 2: Analytics Engine (Day 1-2)

### Task 2.1: Create engine/analytics.py

**Objective:** Build analytics functions for charts and stats.

**Files:**
- Create: `engine/analytics.py`

**Step 1: Write the analytics module**

```python
"""Analytics engine for Pocket Confidant Insights tab."""
import sqlite3
from datetime import datetime, timedelta
from collections import Counter, defaultdict


def get_entries_per_period(db_path: str, period: str = "day") -> dict:
    """Count entries grouped by day, week, or month."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    if period == "day":
        group_fmt = "%Y-%m-%d"
        limit = 90
    elif period == "week":
        group_fmt = "%Y-W%W"
        limit = 52
    elif period == "month":
        group_fmt = "%Y-%m"
        limit = 12
    
    cur.execute(f"""
        SELECT strftime('{group_fmt}', created_at) as period, COUNT(*) as cnt
        FROM entries
        GROUP BY period
        ORDER BY period DESC
        LIMIT {limit}
    """)
    rows = cur.fetchall()
    conn.close()
    
    return {
        "labels": [r[0] for r in reversed(rows)],
        "counts": [r[1] for r in reversed(rows)]
    }


def get_writing_streak(db_path: str) -> dict:
    """Calculate current streak, longest streak, and total active days."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT DATE(created_at) as day FROM entries ORDER BY day")
    days = [datetime.strptime(r[0], "%Y-%m-%d").date() for r in cur.fetchall()]
    conn.close()
    
    if not days:
        return {"current": 0, "longest": 0, "total_days": 0}
    
    streaks = []
    current = 1
    for i in range(1, len(days)):
        if (days[i] - days[i-1]).days == 1:
            current += 1
        else:
            streaks.append(current)
            current = 1
    streaks.append(current)
    
    today = datetime.now().date()
    if days[-1] == today or days[-1] == today - timedelta(days=1):
        current_streak = streaks[-1]
    else:
        current_streak = 0
    
    return {
        "current": current_streak,
        "longest": max(streaks),
        "total_days": len(days)
    }


def get_top_topics(db_path: str, limit: int = 15) -> dict:
    """Extract most mentioned words/themes from entries."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT text FROM entries")
    rows = cur.fetchall()
    conn.close()
    
    all_text = " ".join(r[0] for r in rows).lower()
    
    stop_words = {
        'the', 'a', 'an', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours',
        'you', 'your', 'yours', 'he', 'him', 'his', 'she', 'her', 'hers',
        'it', 'its', 'they', 'them', 'their', 'what', 'which', 'who', 'whom',
        'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did',
        'and', 'but', 'or', 'if', 'because', 'as', 'until', 'while', 'of',
        'at', 'by', 'for', 'with', 'about', 'against', 'between', 'through',
        'to', 'from', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
        'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
        'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
        'than', 'too', 'very', 'just', 'could', 'would', 'should', 'may',
        'might', 'shall', 'will', 'can', 'need', 'dare', 'ought', 'used',
        'like', 'also', 'back', 'even', 'still', 'well', 'way', 'much',
        'got', 'get', 'think', 'know', 'really', 'today', 'going', 'feel',
    }
    
    words = [w.strip(".,!?;:\"'()-") for w in all_text.split()]
    words = [w for w in words if len(w) > 2 and w not in stop_words]
    freq = Counter(words).most_common(limit)
    
    return {
        "topics": [f[0] for f in freq],
        "counts": [f[1] for f in freq]
    }


def get_busiest_days(db_path: str) -> dict:
    """Find which days of the week and hours are most active."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT CASE CAST(strftime('%w', created_at) AS INTEGER)
            WHEN 0 THEN 'Sun' WHEN 1 THEN 'Mon' WHEN 2 THEN 'Tue'
            WHEN 3 THEN 'Wed' WHEN 4 THEN 'Thu' WHEN 5 THEN 'Fri'
            WHEN 6 THEN 'Sat' END as day_name,
            COUNT(*) as cnt
        FROM entries
        GROUP BY strftime('%w', created_at)
        ORDER BY strftime('%w', created_at)
    """)
    dow = cur.fetchall()
    
    cur.execute("""
        SELECT strftime('%H', created_at) as hour, COUNT(*) as cnt
        FROM entries
        GROUP BY hour
        ORDER BY hour
    """)
    hours = cur.fetchall()
    
    conn.close()
    
    return {
        "day_of_week": {
            "labels": [r[0] for r in dow],
            "counts": [r[1] for r in dow]
        },
        "hour_of_day": {
            "labels": [f"{int(r[0]):02d}:00" for r in hours],
            "counts": [r[1] for r in hours]
        }
    }


def get_entry_stats(db_path: str) -> dict:
    """Overall stats: total entries, avg words per entry, date range."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM entries")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT MIN(created_at), MAX(created_at) FROM entries")
    first, last = cur.fetchone()
    
    cur.execute("SELECT AVG(LENGTH(text) - LENGTH(REPLACE(text, ' ', '')) + 1) FROM entries")
    avg_words = cur.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "total_entries": total,
        "first_entry": first,
        "last_entry": last,
        "avg_words": round(avg_words, 1)
    }
```

**Step 2: Test the functions**
```python
from engine.analytics import get_entry_stats, get_writing_streak
stats = get_entry_stats(DB_PATH)
print(f"Total entries: {stats['total_entries']}")
print(f"Avg words: {stats['avg_words']}")
```

---

### Task 2.2: Create Insights tab in app.py

**Objective:** Add visual analytics dashboard.

**Files:**
- Modify: `apps/confidant/app.py`

**Step 1: Add Plotly import**

```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots
```

**Step 2: Add chart generation functions**

```python
def _create_entries_chart(period: str = "day") -> go.Figure:
    """Bar chart of entries per period."""
    from engine.analytics import get_entries_per_period
    data = get_entries_per_period(DB_PATH, period)
    
    fig = go.Figure(data=[
        go.Bar(
            x=data["labels"],
            y=data["counts"],
            marker_color='#b07a4f',
            hovertemplate='%{x}: %{y} entries<extra></extra>'
        )
    ])
    fig.update_layout(
        title=f"Entries per {period}",
        xaxis_title="Period",
        yaxis_title="Entries",
        template="plotly_white",
        height=300,
        margin=dict(l=40, r=20, t=40, b=40)
    )
    return fig


def _create_topics_chart() -> go.Figure:
    """Horizontal bar chart of top topics."""
    from engine.analytics import get_top_topics
    data = get_top_topics(DB_PATH)
    
    fig = go.Figure(data=[
        go.Bar(
            y=data["topics"][::-1],
            x=data["counts"][::-1],
            orientation='h',
            marker_color='#8a9a7b'
        )
    ])
    fig.update_layout(
        title="Most Mentioned Topics",
        xaxis_title="Count",
        template="plotly_white",
        height=400,
        margin=dict(l=100, r=20, t=40, b=40)
    )
    return fig


def _create_busiest_chart() -> go.Figure:
    """Chart of busiest days and hours."""
    from engine.analytics import get_busiest_days
    data = get_busiest_days(DB_PATH)
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("By Day of Week", "By Hour of Day")
    )
    
    fig.add_trace(
        go.Bar(
            x=data["day_of_week"]["labels"],
            y=data["day_of_week"]["counts"],
            marker_color='#b07a4f',
            name="Day"
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=data["hour_of_day"]["labels"],
            y=data["hour_of_day"]["counts"],
            marker_color='#8a9a7b',
            name="Hour"
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=300,
        template="plotly_white",
        showlegend=False,
        margin=dict(l=40, r=20, t=50, b=40)
    )
    return fig
```

**Step 3: Build the Insights tab**

```python
def build_insights_tab():
    """Build the Insights tab with charts and visualizations."""
    from engine.analytics import get_entry_stats, get_writing_streak
    
    with gr.Tab("Insights"):
        gr.Markdown("## 📊 Your Journal Insights")
        
        # Stats cards
        stats = get_entry_stats(DB_PATH)
        streak = get_writing_streak(DB_PATH)
        
        with gr.Row():
            gr.Markdown(f"""
            | Total Entries | Avg Words | Writing Streak | Longest Streak |
            |--------------|-----------|----------------|----------------|
            | {stats['total_entries']} | {stats['avg_words']} | {streak['current']} days | {streak['longest']} days |
            """)
        
        # Charts
        period_selector = gr.Radio(
            ["day", "week", "month"],
            value="day",
            label="View by",
            inline=True
        )
        
        entries_chart = gr.Plot(value=_create_entries_chart("day"))
        topics_chart = gr.Plot(value=_create_topics_chart())
        busiest_chart = gr.Plot(value=_create_busiest_chart())
        
        # Update charts on period change
        period_selector.change(
            fn=_create_entries_chart,
            inputs=[period_selector],
            outputs=[entries_chart]
        )
```

---

## Phase 3: UI Polish + Use Cases (Day 2)

### Task 3.1: Add use case cards to landing page

**Objective:** Show Personal/Work/Creative use cases on empty state.

**Files:**
- Modify: `apps/confidant/app.py`

**Step 1: Add use case HTML**

```python
USE_CASE_CARDS = """
<div style="display: flex; gap: 16px; margin: 20px 0;">
    <div style="flex: 1; padding: 20px; border: 1px solid #e0d4bd; border-radius: 12px; background: #f7f1e6;">
        <h3 style="margin: 0 0 8px 0; color: #3a342b;">📝 Personal</h3>
        <p style="margin: 0; color: #6b6253; font-size: 0.9rem;">Journal your thoughts, track moods, reflect on your day.</p>
    </div>
    <div style="flex: 1; padding: 20px; border: 1px solid #e0d4bd; border-radius: 12px; background: #f7f1e6;">
        <h3 style="margin: 0 0 8px 0; color: #3a342b;">💼 Work</h3>
        <p style="margin: 0; color: #6b6253; font-size: 0.9rem;">Track projects, decisions, and professional growth.</p>
    </div>
    <div style="flex: 1; padding: 20px; border: 1px solid #e0d4bd; border-radius: 12px; background: #f7f1e6;">
        <h3 style="margin: 0 0 8px 0; color: #3a342b;">🎨 Creative</h3>
        <p style="margin: 0; color: #6b6253; font-size: 0.9rem;">Capture ideas,灵感, and creative breakthroughs.</p>
    </div>
</div>
"""
```

**Step 2: Add to landing page**

```python
with gr.Column(visible=is_db_empty(DB_PATH)) as landing_empty:
    gr.Markdown("## Welcome to Pocket Confidant 📓")
    gr.Markdown("Your private journaling companion. Start writing to see the magic.")
    gr.HTML(USE_CASE_CARDS)
    demo_btn = gr.Button("📚 Load Demo Story (341 entries)", variant="secondary")
```

---

### Task 3.2: Add timestamp to entries

**Objective:** Show time (HH:MM) for each entry, allow multiple per day.

**Files:**
- Modify: `engine/store.py`
- Modify: `apps/confidant/app.py`

**Step 1: Update add() to include full timestamp**

In `engine/store.py`, the `add()` method already uses `created_at` which is a TEXT field. Just ensure we're storing full timestamps:

```python
def add(self, text: str, created_at: str = None, reflection: str = "", question: str = "") -> Entry:
    """Add a new entry with full timestamp (YYYY-MM-DD HH:MM:SS)."""
    if created_at is None:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # ... rest of add method
```

**Step 2: Update timeline display**

In `apps/confidant/app.py`, update `_timeline_html()` to show time:

```python
def _timeline_html(entries=None) -> str:
    """Render timeline with timestamps."""
    if entries is None:
        entries = STORE.all()
    if not entries:
        return _empty_state_html()
    
    blocks = ['<div class="pc-timeline-head">Your journal</div>']
    for e in reversed(entries):
        # Parse and format timestamp
        try:
            dt = datetime.strptime(e.when, "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%b %d, %Y")
            time_str = dt.strftime("%H:%M")
        except:
            date_str = e.when[:10]
            time_str = ""
        
        block = ['<div class="pc-entry-block">']
        block.append(f'<div class="pc-date">{date_str}</div>')
        if time_str:
            block.append(f'<div class="pc-time">{time_str}</div>')
        block.append(f'<div class="pc-text">{_esc(e.text)}</div>')
        # ... rest of block
```

---

## Phase 4: Testing + Commit (Day 2-3)

### Task 4.1: Run all tests

**Objective:** Verify everything works.

**Files:**
- tests/test_confidant_receipts.py

**Step 1: Run tests**
```bash
cd /mnt/homes/galileo/argo/Development/build-small-2026
python -m pytest tests/ -v
```

**Step 2: Manual testing checklist**
- [ ] Fresh deploy shows empty state with use case cards
- [ ] "Load Demo" button works, loads 341 entries
- [ ] Entry text visible after reflection
- [ ] Companion says "you" not "the person"
- [ ] Insights tab shows charts
- [ ] Charts update when changing period
- [ ] Multiple entries per day work
- [ ] Timestamps display correctly

---

### Task 4.2: Commit changes

**Objective:** Save all work.

**Step 1: Stage files**
```bash
git add -A
```

**Step 2: Commit**
```bash
git commit -m "feat: add analytics dashboard, fresh deploy, entry visibility

- Add engine/analytics.py with chart generation
- Add Insights tab with Plotly charts
- Add demo data loader for fresh deploys
- Fix entry visibility after reflection
- Add use case cards to landing page
- Add timestamps to entries"
```

**Step 3: Push**
```bash
git push origin hackathon-submission
git push github hackathon-submission
```

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `data/demo_entries.json` | Create | Portable demo data |
| `scripts/generate_demo_data.py` | Create | Export script |
| `engine/analytics.py` | Create | Analytics functions |
| `engine/store.py` | Modify | Add seed functions |
| `apps/confidant/app.py` | Modify | UI updates |
| `apps/confidant/theme.css` | Modify | Add styles |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Plotly not available | Already bundled with Gradio |
| Demo data too large | 341 entries is fine, ~50KB JSON |
| Charts slow on load | Use lazy loading, show stats first |
| Fresh deploy loses data | By design — demo button reloads |

---

## Success Criteria

- [ ] Fresh deploy shows empty state with demo button
- [ ] Demo loads 341 entries successfully
- [ ] Entry text visible after reflection
- [ ] Companion speaks to "you"
- [ ] Insights tab shows 3+ charts
- [ ] Charts are interactive (Plotly)
- [ ] Multiple entries per day work
- [ ] All tests pass
- [ ] Code committed and pushed

---

*9 days until submission. Focus on demo-ready features.*
