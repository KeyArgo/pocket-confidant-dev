"""Petriarium - a tiny AI creature that eats moments and grows artifacts.

Run it:
    source .venv/bin/activate
    python apps/petriarium/app.py

DB defaults to ~/.petriarium/petriarium.db; override with PETRIARIUM_DB.
"""
from __future__ import annotations

import html
import inspect
import os
import sys
import time
import socket
import random
from pathlib import Path

# Make the repo root importable so `engine` resolves whether run from anywhere.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import gradio as gr

from engine.creature_store import CreatureStore, CreatureState
from engine import petriarium


DB_PATH = os.environ.get(
    "PETRIARIUM_DB", str(Path.home() / ".petriarium" / "petriarium.db")
)
PORT = int(os.environ.get("PETRIARIUM_PORT", "7861"))
DEFAULT_MODEL = os.environ.get("PETRIARIUM_MODEL", "qwen2.5:7b-instruct")
MODEL_CHOICES = [
    item.strip()
    for item in os.environ.get(
        "PETRIARIUM_MODELS",
        ",".join(
            [
                DEFAULT_MODEL,
                "qwen2.5:3b-instruct",
                "qwen2.5:14b-instruct",
                "minicpm-v:latest",
            ]
        ),
    ).split(",")
    if item.strip()
]

_THEME_CSS = (Path(__file__).resolve().parent / "theme.css").read_text(encoding="utf-8")
STORE = CreatureStore(DB_PATH)


def _esc(text: str) -> str:
    return html.escape((text or "").strip())


def _trait_meter(label: str, value: float) -> str:
    value = max(0.0, min(1.0, float(value)))
    return (
        '<div class="pet-trait">'
        f'<span class="pet-trait-name">{_esc(label)}</span>'
        '<span class="pet-trait-meter">'
        f'<i style="width:{value * 100:.0f}%"></i>'
        "</span>"
        f'<span class="pet-trait-value">{value:.2f}</span>'
        "</div>"
    )


def _mood_word(mood: str) -> str:
    return {
        "bright": "lit with attention",
        "shy": "pulled inward",
        "buzzing": "alive and twitchy",
        "stormy": "charged and restless",
        "sleepy": "soft and dim",
        "entranced": "locked onto the moment",
    }.get(mood, "settled")


def render_creature_svg(state: CreatureState) -> str:
    mood_palette = {
        "bright": ("#e9c46a", "#f4a261", "#2a9d8f"),
        "shy": ("#d8c7e8", "#b56576", "#6d597a"),
        "buzzing": ("#a8dadc", "#4d908e", "#1d3557"),
        "stormy": ("#cdb4db", "#7f5539", "#264653"),
        "sleepy": ("#f1faee", "#a8dadc", "#457b9d"),
        "entranced": ("#e9edc9", "#84a98c", "#52796f"),
    }
    primary, secondary, accent = mood_palette.get(state.mood, ("#e9edc9", "#84a98c", "#52796f"))
    body_w = 132 if state.form == "seedling" else 148 if state.form == "sproutling" else 166
    body_h = 110 if state.form == "seedling" else 124 if state.form == "sproutling" else 132
    petal_count = 2 + int(round(state.traits.get("weirdness", 0.0) * 3))
    mouth_curve = 8 + int(state.traits.get("tenderness", 0.0) * 10)
    artifact_pebbles = min(4, 1 + state.artifact_count)
    view_seed = int(time.time() * 1000) + state.seed + state.entry_count * 37
    rng = random.Random(view_seed)
    motion = "pet-drift"
    if state.mood == "buzzing" or state.traits.get("mischief", 0.0) > 0.66:
        motion = "pet-wiggle"
    elif state.mood == "sleepy":
        motion = "pet-doze"
    elif state.traits.get("curiosity", 0.0) > 0.58:
        motion = "pet-peek"

    parts = [
        '<svg viewBox="0 0 420 320" class="pet-creature-svg" role="img" aria-label="Petriarium creature">',
        '<defs>',
        '<linearGradient id="pet-body" x1="0%" x2="100%" y1="0%" y2="100%">',
        f'<stop offset="0%" stop-color="{primary}"/>',
        f'<stop offset="100%" stop-color="{secondary}"/>',
        "</linearGradient>",
        '<linearGradient id="pet-glow" x1="0%" x2="100%" y1="0%" y2="100%">',
        f'<stop offset="0%" stop-color="{accent}" stop-opacity=".15"/>',
        '<stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>',
        "</linearGradient>",
        "</defs>",
        '<rect x="16" y="16" width="388" height="288" rx="20" fill="url(#pet-glow)"/>',
        '<g class="pet-world-layer">',
    ]
    for idx in range(12):
        x = 34 + rng.randrange(0, 350)
        y = 34 + rng.randrange(0, 210)
        r = 2 + rng.randrange(0, 5)
        delay = f"{rng.random() * 3:.2f}s"
        opacity = 0.16 + rng.random() * 0.34
        parts.append(
            f'<circle class="pet-firefly" style="animation-delay:{delay}" '
            f'cx="{x}" cy="{y}" r="{r}" fill="{accent}" opacity="{opacity:.2f}"/>'
        )
    for idx in range(7):
        x = 48 + rng.randrange(0, 310)
        h = 18 + rng.randrange(0, 42)
        bend = rng.randrange(-18, 20)
        parts.append(
            f'<path class="pet-grass" d="M {x} 270 C {x + bend} {270 - h // 2}, {x - bend} {270 - h}, {x + bend // 2} {268 - h}" '
            f'stroke="{secondary}" stroke-width="4" stroke-linecap="round" fill="none" opacity=".42"/>'
        )
    parts.extend(
        [
            "</g>",
            '<ellipse cx="210" cy="214" rx="124" ry="60" fill="#5b6c53" opacity=".18"/>',
            f'<g class="{motion}">',
        ]
    )

    stem_color = accent if state.form != "seedling" else secondary
    stem_count = 2 if state.form == "seedling" else 3 if state.form == "sproutling" else 4
    for idx in range(stem_count):
        sx = 182 + idx * 18 - (stem_count * 9)
        parts.append(
            f'<path d="M {sx} 184 C {sx - 10} 150, {sx - 5} 126, {sx + 2} 94" '
            f'stroke="{stem_color}" stroke-width="8" stroke-linecap="round" fill="none"/>'
        )
        parts.append(
            f'<ellipse cx="{sx + 4}" cy="{92 - idx * 2}" rx="22" ry="11" '
            f'fill="{secondary}" opacity=".75" transform="rotate({-24 + idx * 18} {sx + 4} {92 - idx * 2})"/>'
        )

    parts.extend(
        [
            f'<ellipse cx="210" cy="188" rx="{body_w // 2}" ry="{body_h // 2}" fill="url(#pet-body)" stroke="#264653" stroke-width="4"/>',
            '<circle cx="175" cy="172" r="9" fill="#264653"/>',
            '<circle cx="245" cy="172" r="9" fill="#264653"/>',
            f'<path d="M 178 202 Q 210 {202 + mouth_curve} 242 202" stroke="#264653" stroke-width="5" fill="none" stroke-linecap="round"/>',
        ]
    )

    for idx in range(petal_count):
        offset = idx - (petal_count - 1) / 2
        parts.append(
            f'<ellipse cx="{210 + offset * 22}" cy="{116 - abs(offset) * 4}" rx="18" ry="9" '
            f'fill="{accent}" opacity=".8" transform="rotate({-28 + idx * 16} {210 + offset * 22} {116 - abs(offset) * 4})"/>'
        )

    for idx in range(artifact_pebbles):
        px = 114 + idx * 36
        py = 234 + (idx % 2) * 12
        parts.append(
            f'<circle cx="{px}" cy="{py}" r="8" fill="{secondary}" opacity=".55"/>'
        )

    parts.append(
        f'<text x="210" y="288" text-anchor="middle" font-size="16" fill="#24403c" font-family="ui-sans-serif, system-ui, sans-serif">{_esc(state.name)}</text>'
    )
    parts.append("</g>")
    parts.append("</svg>")
    return "".join(parts)


def render_state_panel(state: CreatureState) -> str:
    trait_html = "".join(
        _trait_meter(label, state.traits.get(label, 0.0))
        for label in (
            "curiosity",
            "mischief",
            "tenderness",
            "orderliness",
            "appetite",
            "weirdness",
            "social_bond",
        )
    )
    return (
        '<div class="pet-panel pet-creature">'
        '<div class="pet-panel-head">Creature</div>'
        f"{render_creature_svg(state)}"
        '<div class="pet-state-grid">'
        f'<div><span>name</span><strong>{_esc(state.name)}</strong></div>'
        f'<div><span>form</span><strong>{_esc(state.form)}</strong></div>'
        f'<div><span>mood</span><strong>{_esc(state.mood)}</strong></div>'
        f'<div><span>count</span><strong>{state.entry_count}</strong></div>'
        "</div>"
        f'<div class="pet-mood-line">{_esc(state.name)} is {_esc(_mood_word(state.mood))}.</div>'
        f'<div class="pet-traits">{trait_html}</div>'
        "</div>"
    )


def render_receipts(entries, memories) -> str:
    if not entries:
        return (
            '<div class="pet-panel">'
            '<div class="pet-panel-head">Receipts</div>'
            '<div class="pet-empty">Feed the creature a moment to see the receipt shelf.</div>'
            "</div>"
        )
    memory_by_entry = {item["entry_id"]: item for item in memories}
    blocks = ['<div class="pet-panel"><div class="pet-panel-head">Receipts</div>']
    for entry in reversed(entries[:6]):
        memory = memory_by_entry.get(entry["id"])
        blocks.append('<div class="pet-receipt">')
        blocks.append(
            f'<div class="pet-receipt-top"><span>{_esc(str(entry["id"]))}</span><span>{_esc(memory["summary"] if memory else "learned later")}</span></div>'
        )
        blocks.append(f'<div class="pet-receipt-moment">{_esc(entry["text"])}</div>')
        if memory:
            blocks.append(
                f'<div class="pet-receipt-tags">{" ".join(f"<span>#{_esc(tag)}</span>" for tag in memory["tags"][:4])}</div>'
            )
        blocks.append("</div>")
    blocks.append("</div>")
    return "".join(blocks)


def render_artifacts(artifacts) -> str:
    if not artifacts:
        return (
            '<div class="pet-panel">'
            '<div class="pet-panel-head">Artifacts</div>'
            '<div class="pet-empty">No artifacts yet. The shelf appears after the first feed.</div>'
            "</div>"
        )
    blocks = ['<div class="pet-panel"><div class="pet-panel-head">Artifacts</div>']
    blocks.append('<div class="pet-artifact-grid">')
    for artifact in reversed(artifacts[:8]):
        tags = " ".join(f"<span>#{_esc(tag)}</span>" for tag in artifact.get("tags", [])[:4])
        blocks.append(
            '<div class="pet-artifact">'
            f'<div class="pet-artifact-svg">{artifact.get("svg", "")}</div>'
            f'<div class="pet-artifact-title">{_esc(artifact.get("title", "Untitled"))}</div>'
            f'<div class="pet-artifact-inscription">{_esc(artifact.get("inscription", ""))}</div>'
            f'<div class="pet-artifact-tags">{tags}</div>'
            "</div>"
        )
    blocks.append("</div></div>")
    return "".join(blocks)


def render_events(events) -> str:
    if not events:
        return (
            '<div class="pet-panel">'
            '<div class="pet-panel-head">Events</div>'
            '<div class="pet-empty">Append-only history will show up here after the first feed.</div>'
            "</div>"
        )
    blocks = ['<div class="pet-panel"><div class="pet-panel-head">Events</div>']
    for event in reversed(events[:10]):
        blocks.append(
            '<div class="pet-event">'
            f'<span class="pet-event-kind">{_esc(event["kind"])}</span>'
            f'<span class="pet-event-text">{_esc(event["summary"])}</span>'
            f'<span class="pet-event-ts">{_esc(event["when"])}</span>'
            "</div>"
        )
    blocks.append("</div>")
    return "".join(blocks)


def render_status(result: dict[str, object] | None, model: str, action: str) -> str:
    if not result:
        return (
            '<div class="pet-panel pet-result">'
            '<div class="pet-panel-head">Receipt</div>'
            '<div class="pet-empty">Say something to the creature.</div>'
            "</div>"
        )
    artifact = result["artifact"]
    memory = result["memory"]
    return (
        '<div class="pet-panel pet-result">'
        '<div class="pet-panel-head">Receipt</div>'
        '<div class="pet-result-grid">'
        f'<div><span>fed</span><strong>{_esc(result["moment"])}</strong></div>'
        f'<div><span>heard</span><strong>{_esc(result["response_text"])}</strong></div>'
        f'<div><span>learned</span><strong>{_esc(memory["summary"])}</strong></div>'
        f'<div><span>made</span><strong>{_esc(artifact["title"])}</strong></div>'
        f'<div><span>mood</span><strong>{_esc(str(result["state"]["mood"]))}</strong></div>'
        f'<div><span>model</span><strong>{_esc(model)}</strong></div>'
        "</div>"
        f'<div class="pet-result-action">{_esc(action)}</div>'
        "</div>"
    )


def _snapshot() -> dict[str, object]:
    state = STORE.state()
    entries = STORE.recent_entries(12)
    memories = STORE.recent_memories(12)
    artifacts = STORE.artifacts(12)
    events = STORE.recent_events(12)
    return {
        "state_html": render_state_panel(state),
        "receipts_html": render_receipts(entries, memories),
        "artifacts_html": render_artifacts(artifacts),
        "events_html": render_events(events),
    }


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def _choose_port(preferred: int) -> int:
    for port in range(preferred, preferred + 20):
        if _port_is_free(port):
            return port
    raise RuntimeError(f"No free port found near {preferred}")


def on_feed(moment: str, model: str):
    text = (moment or "").strip()
    if not text:
        snap = _snapshot()
        return (
            render_status(None, model or DEFAULT_MODEL, "Type a moment and press Feed."),
            snap["state_html"],
            snap["receipts_html"],
            snap["artifacts_html"],
            snap["events_html"],
            moment,
        )

    used_model = model or DEFAULT_MODEL
    try:
        result = petriarium.process_moment(text, STORE, model=used_model)
    except Exception as exc:
        snap = _snapshot()
        fallback = {
            "moment": text,
            "response_text": f"The creature tapped the glass but could not digest that yet. ({type(exc).__name__})",
            "memory": {"summary": "The moment was not stored.", "tags": ["retry"]},
            "artifact": {"title": "No artifact made", "kind": "none"},
            "state": {"mood": STORE.state().mood},
        }
        return (
            render_status(fallback, used_model, "Nothing was saved. Try again with a shorter moment."),
            snap["state_html"],
            snap["receipts_html"],
            snap["artifacts_html"],
            snap["events_html"],
            moment,
        )
    snap = _snapshot()
    return (
        render_status(result, used_model, "A new artifact was added to the shelf."),
        snap["state_html"],
        snap["receipts_html"],
        snap["artifacts_html"],
        snap["events_html"],
        "",
    )


def on_fresh(confirm_new: bool):
    if not confirm_new:
        snap = _snapshot()
        result = {
            "moment": "new creature requested",
            "response_text": "The current creature presses both hands to the glass.",
            "memory": {"summary": "Replacement was blocked until confirmed.", "tags": ["protected"]},
            "artifact": {"title": "Creature still here", "kind": "guard"},
            "state": {"mood": STORE.state().mood},
        }
        return (
            render_status(result, DEFAULT_MODEL, "Check the confirmation box before replacing this creature."),
            snap["state_html"],
            snap["receipts_html"],
            snap["artifacts_html"],
            snap["events_html"],
            "",
            False,
        )
    seed = int(time.time() * 1000)
    state = STORE.reset(seed=seed)
    snap = _snapshot()
    result = {
        "moment": "fresh start",
        "response_text": f"{state.name} wakes up in a new shape.",
        "memory": {"summary": "A new creature was grown.", "tags": ["fresh", "start"]},
        "artifact": {"title": f"{state.name} Seedling", "kind": "relic"},
        "state": {"mood": state.mood},
    }
    return (
        render_status(result, DEFAULT_MODEL, "Fresh creature created. The shelf has been cleared."),
        snap["state_html"],
        snap["receipts_html"],
        snap["artifacts_html"],
        snap["events_html"],
        "",
        False,
    )


def build() -> gr.Blocks:
    _ctor_params = inspect.signature(gr.Blocks.__init__).parameters
    _accepts_ctor_css = "css" in _ctor_params and "theme" in _ctor_params

    _blocks_kwargs = dict(title="Petriarium", analytics_enabled=False)
    if _accepts_ctor_css:
        _blocks_kwargs.update(css=_THEME_CSS, theme=gr.themes.Base())

    with gr.Blocks(**_blocks_kwargs) as demo:
        gr.HTML(
            '<div class="pet-hero">'
            '<div class="pet-kicker">Chapter Two - Thousand Token Wood</div>'
            '<h1>Petriarium</h1>'
            '<p>Feed it moments. It grows a visible personality and leaves collectible artifacts behind.</p>'
            '<div class="pet-badges">'
            '<span>local model</span><span>SQLite state</span><span>artifact shelf</span><span>receipt view</span>'
            "</div>"
            "</div>"
        )

        with gr.Row():
            with gr.Column(scale=5):
                creature = gr.HTML(value=render_state_panel(STORE.state()))
            with gr.Column(scale=7):
                moment = gr.Textbox(
                    label="Feed a moment",
                    placeholder="I'm nervous about showing people my weird project.",
                    lines=6,
                    show_label=False,
                    elem_id="pet-moment",
                )
                with gr.Row():
                    feed = gr.Button("Feed", elem_id="pet-feed", elem_classes=["pet-primary"])
                    fresh = gr.Button("New creature", elem_id="pet-fresh", elem_classes=["pet-secondary"])
                    model = gr.Dropdown(
                        choices=MODEL_CHOICES,
                        value=DEFAULT_MODEL,
                        label="model",
                        interactive=True,
                        elem_id="pet-model",
                    )
                confirm_new = gr.Checkbox(
                    label="Replace the current creature and clear its shelf",
                    value=False,
                    elem_id="pet-confirm-new",
                )
                status = gr.HTML(value=render_status(None, DEFAULT_MODEL, "Waiting for the first moment."))

        with gr.Row():
            receipts = gr.HTML(value=render_receipts(STORE.recent_entries(), STORE.recent_memories()))
            artifacts = gr.HTML(value=render_artifacts(STORE.artifacts()))

        events = gr.HTML(value=render_events(STORE.recent_events()))

        feed.click(
            on_feed,
            inputs=[moment, model],
            outputs=[status, creature, receipts, artifacts, events, moment],
        )
        moment.submit(
            on_feed,
            inputs=[moment, model],
            outputs=[status, creature, receipts, artifacts, events, moment],
        )
        fresh.click(
            on_fresh,
            inputs=[confirm_new],
            outputs=[status, creature, receipts, artifacts, events, moment, confirm_new],
        )

    demo._petriarium_needs_launch_css = not _accepts_ctor_css
    return demo


def main() -> None:
    demo = build()
    launch_params = inspect.signature(demo.launch).parameters
    chosen_port = _choose_port(PORT)
    print(f"Petriarium listening on http://127.0.0.1:{chosen_port}")
    launch_kwargs = dict(
        server_name="127.0.0.1",
        server_port=chosen_port,
        share=False,
    )
    if "show_api" in launch_params:
        launch_kwargs["show_api"] = False
    if getattr(demo, "_petriarium_needs_launch_css", False):
        launch_kwargs.update(css=_THEME_CSS, theme=gr.themes.Base())
    demo.launch(**launch_kwargs)


if __name__ == "__main__":
    main()
