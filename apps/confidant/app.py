"""Pocket Confidant — a private, fully-local AI journaling companion.

A diary is the most private thing you own — you would never send it to a cloud
AI. So the only honest fit is a small model running 100% on-device: no cloud, no
account, no subscription, works in airplane mode. Each entry, the companion gives
a short warm reflection, asks exactly ONE good question, and — only when genuinely
relevant — calls back to something you wrote days ago, using private on-device
semantic memory.

Run it:
    source .venv/bin/activate
    python apps/confidant/app.py

DB defaults to ~/.pocket-confidant/journal.db; override with POCKET_CONFIDANT_DB.
"""
from __future__ import annotations

import html
import inspect
import os
import sys
import time
from datetime import date
from pathlib import Path

# Make the repo root importable so `engine` resolves whether run from anywhere.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import gradio as gr

from engine import confidant
from engine.store import JournalStore

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
DB_PATH = os.environ.get(
    "POCKET_CONFIDANT_DB", str(Path.home() / ".pocket-confidant" / "journal.db")
)

# Small models the user can pick between, ranked by a warmth/specificity bake-off
# (tests/model_eval.py): qwen3.5:9b warmest, minicpm-v close 2nd + best specificity
# (and OpenBMB sponsor -> $10k category), qwen3:8b a touch wordy, gemma4:e4b too long.
MODELS = ["minicpm-v:latest", "qwen3.5:9b", "qwen3:8b", "gemma4:e4b"]
# Default = MiniCPM (OpenBMB sponsor) to compete in their $10k category; ~tied on
# warmth with qwen3.5:9b but best specificity. Override via POCKET_CONFIDANT_MODEL
# (e.g. set qwen3.5:9b if live journaling reveals it feels warmer to you).
DEFAULT_MODEL = os.environ.get("POCKET_CONFIDANT_MODEL", "qwen3.5:9b")

_THEME_CSS = (Path(__file__).resolve().parent / "theme.css").read_text(encoding="utf-8")

# One shared, on-device store. SQLite is single-process here; Gradio's default
# queue serializes calls, which keeps the connection safe for this demo.
STORE = JournalStore(DB_PATH)


# --------------------------------------------------------------------------- #
# Rendering helpers (return HTML strings for the styled cards)
# --------------------------------------------------------------------------- #
def _esc(text: str) -> str:
    return html.escape((text or "").strip())


def _card_html(reflection: str, question: str, callback: str, model: str) -> str:
    """The companion's response, as a styled paper card."""
    parts = ['<div class="pc-card">']
    if callback and callback.strip():
        parts.append(f'<div class="pc-callback">{_esc(callback)}</div>')
    if reflection and reflection.strip():
        parts.append(f'<div class="pc-reflection">{_esc(reflection)}</div>')
    if question and question.strip():
        parts.append(f'<div class="pc-question">{_esc(question)}</div>')
    parts.append(
        f'<div class="pc-meta">reflected locally · {_esc(model)} · on-device</div>'
    )
    parts.append("</div>")
    return "\n".join(parts)


def _empty_state_html() -> str:
    return (
        '<div class="pc-empty">'
        "Nothing here yet — and that's the point: this page is just yours.<br>"
        "Write a line about your day above. The companion will read it on this "
        "machine, reflect a little, and ask one question. Over time it starts to "
        "remember — privately, with no cloud and no account."
        "</div>"
    )


def _timeline_html() -> str:
    """History of past entries, most-recent first, with the companion's echo."""
    entries = STORE.all()
    if not entries:
        return _empty_state_html()
    blocks = ['<div class="pc-timeline-head">Your journal</div>']
    for e in reversed(entries):  # most recent first
        block = ['<div class="pc-entry-block">']
        block.append(f'<div class="pc-date">{_esc(e.when)}</div>')
        block.append(f'<div class="pc-text">{_esc(e.text)}</div>')
        if (e.reflection and e.reflection.strip()) or (e.question and e.question.strip()):
            echo = ['<div class="pc-echo">']
            if e.reflection and e.reflection.strip():
                echo.append(_esc(e.reflection))
            if e.question and e.question.strip():
                echo.append(f'<span class="pc-q"> {_esc(e.question)}</span>')
            echo.append("</div>")
            block.append("".join(echo))
        block.append("</div>")
        blocks.append("\n".join(block))
    return "\n".join(blocks)


# --------------------------------------------------------------------------- #
# Actions
# --------------------------------------------------------------------------- #
def on_submit(entry_text: str, model: str):
    """Reflect on a new entry, persist it, refresh the timeline."""
    text = (entry_text or "").strip()
    if not text:
        return (
            '<div class="pc-card"><div class="pc-reflection">'
            "Whenever you're ready — even one sentence is enough."
            "</div></div>",
            _timeline_html(),
            entry_text,
            "",  # no submitted entry to display
        )

    model = model or DEFAULT_MODEL
    today = date.today().isoformat()
    ts = time.time()

    try:
        # before_id=None: recall can see all prior entries (this one isn't stored yet).
        refl = confidant.reflect(text, store=STORE, model=model)
        reflection, question, callback = refl.reflection, refl.question, refl.callback
        used_model = refl.model or model
    except Exception as exc:  # local model offline / pulled mid-demo, etc.
        reflection = (
            "I couldn't reach the local model just now, so I've still saved what "
            "you wrote — it stays right here on your machine."
        )
        question = "Want to try the reflection again in a moment?"
        callback = ""
        used_model = model
        reflection += f"  ({type(exc).__name__})"

    # Persist (computes a private on-device embedding for future recall).
    try:
        STORE.add(text, day=today, ts=ts, reflection=reflection, question=question)
    except Exception:
        pass  # never lose the user's words to a storage hiccup in a demo

    card = _card_html(reflection, question, callback, used_model)
    # Show the submitted entry above the reflection card
    submitted_html = (
        '<div class="pc-submitted-entry">'
        '<div class="pc-submitted-label">Your entry</div>'
        f'<div class="pc-submitted-text">{_esc(text)}</div>'
        f'<div class="pc-submitted-date">{_esc(today)}</div>'
        "</div>"
    )
    # Don't clear the textarea — keep it visible for reference
    return card, _timeline_html(), entry_text, submitted_html


def on_week(model: str):
    """Gentle 2-3 sentence reflection on recurring threads across recent entries."""
    entries = STORE.recent(7)
    if len(entries) < 2:
        return (
            '<div class="pc-week"><div class="pc-week-head">This week</div>'
            "Once you have a few entries, this will gently notice the threads "
            "running through your week — quietly, on this device."
            "</div>"
        )

    model = model or DEFAULT_MODEL
    joined = "\n".join(f"- ({e.when}) {e.text.strip()}" for e in entries)
    system = (
        confidant.PERSONA
        + "\n\nNow you are looking back over the last several journal entries at once."
    )
    user = (
        "Here are your most recent journal entries, oldest first:\n"
        f"{joined}\n\n"
        "In 2-3 plain, warm sentences, gently reflect on any recurring threads, "
        "tensions, or small shifts you notice across these days. Use your own "
        "specifics. Do not diagnose, do not give advice, do not list. If there's "
        "no real pattern, say so honestly and briefly. Return plain prose only — "
        "no JSON, no headers."
    )
    try:
        raw = confidant._chat(system, user, model=model)
        note = confidant._strip_thinking(raw).strip()
    except Exception as exc:
        note = (
            "Couldn't reach the local model just now — but your entries are all "
            f"still here on this machine. ({type(exc).__name__})"
        )

    return (
        '<div class="pc-week"><div class="pc-week-head">This week — '
        f"{_esc(model)}, on-device</div>"
        f"{_esc(note)}"
        "</div>"
    )


# --------------------------------------------------------------------------- #
# Analytics helpers
# --------------------------------------------------------------------------- #
def get_entry_stats():
    from engine.analytics import get_entry_stats as _get
    return _get(DB_PATH)


def get_writing_streak():
    from engine.analytics import get_writing_streak as _get
    return _get(DB_PATH)


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #
def build() -> gr.Blocks:
    # Gradio 4/5 took `css`/`theme` on the Blocks constructor; Gradio 6 moved them
    # to launch(). Detect which this version supports so the Off-Brand theme renders
    # either way (and we avoid a deprecation warning / silently-dropped css).
    _ctor_params = inspect.signature(gr.Blocks.__init__).parameters
    _accepts_ctor_css = "css" in _ctor_params and "theme" in _ctor_params

    _blocks_kwargs = dict(title="Pocket Confidant", analytics_enabled=False)
    if _accepts_ctor_css:
        _blocks_kwargs.update(css=_THEME_CSS, theme=gr.themes.Base())

    with gr.Blocks(**_blocks_kwargs) as demo:
        # Theme toggle button (sun/moon)
        gr.HTML(
            '<button id="pc-theme-toggle" onclick="toggleTheme()" title="Toggle dark/light mode">☀️</button>'
            '<script>'
            'function toggleTheme() {'
            '  const btn = document.getElementById("pc-theme-toggle");'
            '  const isDark = document.body.classList.toggle("dark");'
            '  if (isDark) {'
            '    btn.textContent = "🌙";'
            '    localStorage.setItem("pc-theme", "dark");'
            '  } else {'
            '    btn.textContent = "☀️";'
            '    localStorage.setItem("pc-theme", "light");'
            '  }'
            '}'
            'document.addEventListener("DOMContentLoaded", function() {'
            '  const saved = localStorage.getItem("pc-theme");'
            '  if (saved === "dark") {'
            '    document.body.classList.add("dark");'
            '    const btn = document.getElementById("pc-theme-toggle");'
            '    if (btn) btn.textContent = "🌙";'
            '  }'
            '});'
            '</script>'
        )

        gr.HTML(
            '<div id="pc-masthead">'
            '<p class="pc-title">Pocket Confidant</p>'
            '<p class="pc-sub">a private journal that reflects back</p>'
            "</div>"
            '<div id="pc-privacy">'
            "100% on your device"
            '<span class="pc-dot">·</span>no cloud, no account'
            '<span class="pc-dot">·</span>works in airplane mode'
            "</div>"
        )

        with gr.Tabs():
            with gr.Tab("Journal"):
                entry = gr.Textbox(
                    elem_id="pc-entry",
                    label="Today",
                    placeholder="What's on your mind today? Even one sentence is enough…",
                    lines=6,
                    show_label=False,
                )

                with gr.Row():
                    submit = gr.Button("Reflect", elem_id="pc-submit", elem_classes=["pc-primary"])
                    week = gr.Button("This week", elem_classes=["pc-quiet"])
                    model = gr.Dropdown(
                        choices=MODELS,
                        value=DEFAULT_MODEL,
                        label="model",
                        elem_id="pc-model",
                        interactive=True,
                    )

                response = gr.HTML(value="")
                submitted_entry = gr.HTML(value="")
                week_panel = gr.HTML(value="")
                timeline = gr.HTML(value=_timeline_html())

                submit.click(
                    on_submit,
                    inputs=[entry, model],
                    outputs=[response, timeline, entry, submitted_entry],
                )
                entry.submit(
                    on_submit,
                    inputs=[entry, model],
                    outputs=[response, timeline, entry, submitted_entry],
                )
                week.click(on_week, inputs=[model], outputs=[week_panel])

            with gr.Tab("Insights"):
                gr.Markdown("## Your Journal Insights")
                stats = get_entry_stats()
                streak = get_writing_streak()
                gr.Markdown(
                    f'**{stats["total_entries"]}** entries | **{stats["avg_words"]}** avg words'
                    f' | **{streak["current"]}** day streak | **{streak["longest"]}** longest streak'
                )
                gr.Markdown("*Charts coming soon!*")

        with gr.Accordion("\U0001f527 Developer Tools", open=False):
            gr.Markdown("**Warning:** These actions are destructive and cannot be undone.")
            with gr.Row():
                clear_btn = gr.Button("\U0001f5d1 Clear All Data", variant="stop")
                reload_btn = gr.Button("\U0001f504 Reload Demo Data")
            dev_status = gr.Markdown("")

            def on_clear_data():
                from engine.store import clear_all_entries
                count = clear_all_entries(DB_PATH)
                return f"Deleted {count} entries. Refresh page to see changes."

            def on_reload_demo():
                from engine.store import seed_demo_data, clear_all_entries
                clear_all_entries(DB_PATH)
                count = seed_demo_data(DB_PATH)
                return f"Cleared and reloaded {count} demo entries."

            clear_btn.click(on_clear_data, outputs=[dev_status])
            reload_btn.click(on_reload_demo, outputs=[dev_status])

    # Remember whether the theme/css still need to be supplied at launch() time.
    demo._pc_needs_launch_css = not _accepts_ctor_css
    
    # GitHub link at bottom
    gr.HTML(
        '<div style="text-align: center; padding: 20px 0; margin-top: 20px; '
        'border-top: 1px solid #e0d4bd;">'
        '<a href="https://github.com/KeyArgo/pocket-confidant" target="_blank" '
        'style="color: #6b6253; text-decoration: none; font-size: 0.9rem;">'
        '📦 View on GitHub: KeyArgo/pocket-confidant'
        '</a>'
        '</div>'
    )
    
    return demo


def main() -> None:
    demo = build()
    launch_kwargs = dict(server_name="0.0.0.0")
    if getattr(demo, "_pc_needs_launch_css", False):
        # Gradio 6 path: theme + css belong on launch().
        launch_kwargs.update(css=_THEME_CSS, theme=gr.themes.Base())
    demo.launch(**launch_kwargs)


if __name__ == "__main__":
    main()

