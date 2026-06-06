"""Petriarium cold-start helpers — the SKEPTIC lane's 90-second UX layer.

The existing app drops a cold user onto an empty creature with one example in
the textbox placeholder and no explanation of what they're looking at. This
module is the smallest set of strings the integrator needs to convert "what is
this?" into "I get it" within 90 seconds:

  - SAMPLE_MOMENTS: three chips the user can click to see the loop in action
  - MOOD_LEGEND: plain-English captions for the six moods
  - FORM_PROGRESSION: a hint about the seedling -> sproutling -> specimen chain
  - render_status_banner: a visible OK/WARN bar from a BackendStatus
  - render_about / render_mood_legend / render_form_hint: small HTML panels

The CSS class names (`pet-banner-ok`, `pet-banner-warn`, `pet-sample-hint`,
`pet-mood-legend`, `pet-form-hint`) are the only contract with `theme.css`.
"""
from __future__ import annotations

import html
from typing import Any


SAMPLE_MOMENTS: list[str] = [
    "I'm nervous about showing people my weird project.",
    "I found a smooth green stone on the way home and kept it in my pocket.",
    "The deadline is in two hours and I've rewritten the same paragraph four times.",
    "A stranger laughed at my joke and I still feel warm about it.",
]

MOOD_LEGEND: dict[str, str] = {
    "bright": "alert and warm — the creature noticed something good",
    "shy": "pulled inward — soft, watchful, low-volume",
    "buzzing": "restless, twitchy — full of small, fast ideas",
    "stormy": "charged and tense — a sharp edge in the air",
    "sleepy": "soft and dim — the creature is conserving itself",
    "entranced": "locked onto the moment — can't look away",
}

FORM_PROGRESSION: list[dict[str, str]] = [
    {"form": "seedling", "hint": "what you start with"},
    {"form": "sproutling", "hint": "after 2 feeds"},
    {"form": "specimen", "hint": "after 4+ feeds with a strong social_bond"},
]

TRAIT_CAPTIONS: dict[str, str] = {
    "curiosity": "asks more questions",
    "mischief": "breaks small things on purpose",
    "tenderness": "cares about fragile things",
    "orderliness": "sorts things into folders",
    "appetite": "wants more moments, more often",
    "weirdness": "resists being categorized",
    "social_bond": "remembers who you are",
}


def _esc(text: str) -> str:
    return html.escape((text or "").strip())


def render_status_banner(status: Any | None) -> str:
    """Render a small OK/WARN bar. `status` is a BackendStatus or None."""
    if status is None:
        return (
            '<div class="pet-banner pet-banner-warn" role="status">'
            "<span>⚠</span><span>Backend not yet checked.</span></div>"
        )
    if status.ok:
        return (
            f'<div class="pet-banner pet-banner-ok" role="status">'
            f"<span>✓</span>"
            f"<span>Connected to <code>{_esc(status.model)}</code> via {_esc(status.backend)} "
            f"({status.latency_ms} ms).</span></div>"
        )
    return (
        f'<div class="pet-banner pet-banner-warn" role="status">'
        f"<span>⚠</span>"
        f"<span><strong>Safe mode.</strong> Could not reach {_esc(status.backend)} "
        f"at <code>{_esc(status.host)}</code>: {_esc(status.error)}. "
        f"Feed the creature and it will improvise, but no new artifacts will be saved.</span>"
        f"</div>"
    )


def render_fallback_banner(error: str, latency_ms: int) -> str:
    """Render a small banner that appears inside a receipt when a fallback fired."""
    return (
        '<div class="pet-banner pet-banner-warn" role="status">'
        f"<span>⚠</span>"
        f"<span>This receipt was synthesized because the model failed: "
        f"<code>{_esc(error)}</code> ({latency_ms} ms). The creature did not learn anything new.</span>"
        f"</div>"
    )


def render_about() -> str:
    return (
        '<div class="pet-about">'
        "<p><strong>Petriarium</strong> is a tiny local creature that eats "
        "short, honest moments and turns them into collectible artifacts.</p>"
        "<p>Each feed changes the creature's mood and traits. After 2 feeds it "
        "becomes a sproutling; after 4+ feeds with a strong social bond, a "
        "specimen. Artifacts accumulate on the shelf below.</p>"
        "<p>Everything is local: SQLite for state, a small instruct model for "
        "interpretation. No cloud, no account, no analytics.</p>"
        "</div>"
    )


def render_mood_legend() -> str:
    items = "".join(
        f'<li><strong>{_esc(mood)}</strong> — {_esc(caption)}</li>'
        for mood, caption in MOOD_LEGEND.items()
    )
    return (
        '<div class="pet-mood-legend">'
        '<div class="pet-panel-head">Moods</div>'
        f"<ul>{items}</ul>"
        "</div>"
    )


def render_form_hint() -> str:
    items = "".join(
        f'<li><strong>{_esc(row["form"])}</strong> — {_esc(row["hint"])}</li>'
        for row in FORM_PROGRESSION
    )
    return (
        '<div class="pet-form-hint">'
        '<div class="pet-panel-head">Form progression</div>'
        f"<ul>{items}</ul>"
        "</div>"
    )


def render_trait_legend() -> str:
    items = "".join(
        f'<li><strong>{_esc(trait.replace("_", " "))}</strong> — {_esc(caption)}</li>'
        for trait, caption in TRAIT_CAPTIONS.items()
    )
    return (
        '<div class="pet-trait-legend">'
        '<div class="pet-panel-head">Traits</div>'
        f"<ul>{items}</ul>"
        "</div>"
    )


def sample_chip_html() -> str:
    chips = " ".join(
        f'<button type="button" class="pet-sample-chip" data-sample="{_esc(m)}">{_esc(m[:36])}…</button>'
        for m in SAMPLE_MOMENTS
    )
    return (
        '<div class="pet-sample-hint">'
        '<div class="pet-panel-head">Try a sample</div>'
        f"{chips}"
        "</div>"
    )
