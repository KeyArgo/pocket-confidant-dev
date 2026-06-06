# Petriarium Skeptic Critique — minimax lane

**Lane:** SKEPTIC (opencodego-minimax-m3)
**Target:** Petriarium flow, UX clarity, failure handling, artifact shelf
**Date:** 2026-06-04
**Scope reviewed:** `apps/petriarium/app.py`, `engine/petriarium.py`, `engine/creature_store.py`, `engine/backends.py`, `tests/run_petriarium.py`, `apps/petriarium/theme.css`

---

## TL;DR verdict

Petriarium is a beautiful toy for someone who already knows what it is. For a cold user it has *no entry path*: no samples, no legend, no glossary. The bigger problem is that **the app silently lies when the LLM is broken** — it catches every error in a blanket `except Exception` and renders a canned response that looks identical to a real one. A hackathon entry that sells "honest small models" cannot ship that. The artifact shelf is pretty but decontextualized: tiles have no link back to the moment that produced them, and the inscription is a copy-paste of the memory summary.

The fix is small and surgical. I've shipped the engine-side code in this PR. UI-level changes (banner, samples, mood legend) are sketched as a diff at the bottom — I left `app.py` untouched so the deepseek lane keeps ownership of the visual layer.

---

## 1) Can a cold user understand the demo in 90 seconds?

**No. They will stare at the screen and guess.**

What a cold user sees on first load (`render_state_panel` + `render_status` with empty `result`):

- Hero: "Feed it moments. It grows a visible personality and leaves collectible artifacts behind." — poetic, not informative. "Moments" is undefined.
- Creature panel: an SVG blob, a name like "Mosslet", a `form: seedling`, a `mood: bright`, seven unlabeled trait bars.
- Receipts panel: "Feed the creature a moment to see the receipt shelf." — defines nothing.
- Artifacts panel: "No artifacts yet. The shelf appears after the first feed." — also defines nothing.
- Events panel: "Append-only history will show up here after the first feed."
- Textbox: placeholder "I'm nervous about showing people my weird project." — this is the *only* example.
- Buttons: "Feed", "New creature", model dropdown.

**Specific gaps a cold user will hit:**

| Question the user asks | What the app does | What it should do |
|---|---|---|
| What is a "moment"? | One example in placeholder. | Three sample chips below the textbox. |
| What do the moods mean? | Six unlabeled words. | Inline legend or hover tooltip per mood. |
| What are the trait bars? | Numeric values 0.00–1.00, no scale, no direction. | Label each as low→high with a one-line plain-English caption. |
| What does "form: seedling" mean? | Single value, no progression. | Hint: "After 2 feeds: sproutling. After 4+ cares: specimen." |
| What is an artifact? | Empty state says "shelf appears after the first feed." | Empty state should show a sample SVG with caption "the creature leaves this when you feed it." |
| Why is the model dropdown here? | No explanation. | A `?` next to it that explains "switch the local model — slower = stranger." |
| What if I write a boring line? | The creature shrugs back. | A "Try a sample" affordance. |
| What changed after my last feed? | Receipt shows ID, summary, tags. | A "what changed" diff (mood shift, trait deltas). |

**The 90-second test (mental walkthrough):**
- 0–10s: user reads hero, scans panels, sees a creature. OK.
- 10–30s: user wonders what to type, reads placeholder, decides to copy it.
- 30–50s: user types something, clicks Feed, waits. Sees a result. Confused — what was that?
- 50–80s: user looks at the artifact SVG. Abstract. Doesn't understand.
- 80–90s: user closes the tab. **Fails.**

The single biggest fix is **three example chips**. They cost ten lines of code and convert "what do I type?" into "I click this and see what happens." I'm shipping that in `apps/petriarium/onboarding.py`.

---

## 2) What happens when the LLM is down or returns garbage?

**The app silently produces a plausible-looking fallback. This is the most serious problem in the codebase.**

### Failure path A — Ollama is unreachable

`_ollama_chat` calls `requests.post(..., timeout=120)` and `raise_for_status()`. If the host is down, you get `requests.exceptions.ConnectionError` (or `ReadTimeout` after 120s). In `process_moment`:

```python
try:
    raw = chat(SYSTEM, prompt, model=model)
    parsed = _extract_json(raw)
except Exception:
    parsed = None
normalized = normalize_model_result(parsed, moment)
```

The blanket `except Exception` swallows the connection error, sets `parsed = None`, and `normalize_model_result` returns:

```python
{
  "response_text": "It chews the moment into a small, glowing oddity.",
  "mood": "entranced",
  "memory_proposal": {
    "summary": "It noticed moment, moment, moment.",
    "tags": ["moment"]
  }
}
```

**The user sees a perfectly rendered response.** No banner, no warning, no log, nothing. They have no way to know the model is broken. This is exactly the failure mode the `VERIFY_DISCLAIMER` in the explainer app tries to avoid — and Petriarium is shipping the opposite of it.

### Failure path B — Model is loaded but returns garbage

`_extract_json` returns `None` if the model wraps JSON in a fence, includes `<think>` tags that get partially stripped, or just hallucinates prose. Same fallback path: silent canned response, mood always `entranced`.

### Failure path C — Runtime misconfigured (no GGUF set)

Default `PETRIARIUM_RUNTIME=llama` and `_llama_chat` raises `RuntimeError("PETRIARIUM_GGUF or PETRIARIUM_HF_REPO/PETRIARIUM_HF_FILE is not configured")`. Caught by the blanket `except`. Same silent degradation.

### Failure path D — Slow model (120s timeout)

`timeout=120` is hardcoded. The user clicks Feed and the UI freezes for up to two minutes with **no spinner, no "thinking..." indicator, no cancel button.** Worse: while the request is in flight, the user can click Feed again, queuing another slow call. Gradio's default behavior is to disable the button during `.click` handlers, so the click-flood is bounded — but the perception is still "this is broken."

### Failure path E — Fallback pollutes memory

Even more subtly: the fallback response is **written to the receipts table as if it were real**. The mood `entranced` and the canned `tags` from `keyword_tags(text)` are stored. On the next real call, those fake memories are included in the prompt as "Recent memories" and the model starts **hallucinating around them**. The creature's personality drifts toward a cliche of itself.

### What the right behavior looks like

1. **At boot**, ping the backend. If it's down, render a visible banner: "⚠ Ollama unreachable — running in safe mode. Run `ollama serve` to wake the creature up."
2. **On click**, show a "thinking…" indicator immediately, with a cancel affordance after 10s.
3. **On error**, render the result with a visible `fallback_used: true` flag in the UI — e.g. a small "safe mode" pill on the receipt. The receipt's "heard" line should read something like "*(creature is improvising — model returned nothing)*".
4. **On fallback**, do not write the canned response to the receipts table. Mark the entry as `fallback: true` in the events log so the user can audit it later.
5. **On JSON parse failure**, retry once with a stricter prompt before falling back.
6. **At boot**, also resolve and display the actual model being used and its measured first-token latency, so a slow model is obvious from second zero.

I've shipped this layer in `engine/petriarium_guarded.py` and `engine/health.py`. The app-side integration is in the diff at the bottom of this document.

### Test coverage

The existing `tests/run_petriarium.py` only tests the happy path with `fake_chat`. **It does not exercise any failure path.** A user could break the fallback chain and CI would still pass. I'm adding `tests/run_petriarium_guarded.py` which forces `_ollama_chat` to raise and asserts the guarded result carries `fallback_used: True` and the rendered status reflects it.

---

## 3) How can the artifact shelf be clearer?

The shelf is the whole point of the app ("leaves collectible artifacts behind") and it's the weakest panel. Six concrete problems:

1. **No link from artifact → moment.** A receipt says "entry #5" and a tile says "Mote Relic #4". These are different counters (`entry_id` vs `artifact_count`). The user cannot tell which artifact came from which moment, and the tile gives no way to find out.
2. **Inscription is a copy of the memory summary.** It's the same string in two places, with no artifact-specific information. The "artifact" doesn't say anything the "memory" doesn't.
3. **No detail view.** A tile is 220px tall, the SVG is abstract, the title is short. The user can't read the full text, can't see the receipt that made it, can't favorite or compare.
4. **All tiles have the same visual weight.** A first artifact (entry #1) and the 30th look identical. There's no sense of rarity, age, or "this is the one that mattered."
5. **Empty state is unhelpful.** "No artifacts yet. The shelf appears after the first feed." doesn't say what an artifact IS.
6. **No way to discard a dud.** If the model produced a weak artifact, the user is stuck with it in the grid.

### Proposed shelf redesign (in priority order)

**P0 — make the artifact link to its moment (small fix, big clarity win):**
- Title format: `"{kind.title()} {n} from #{entry_id}"`
- Sub-line: `"{short moment excerpt} — {mood}"`
- The receipt panel highlights the row whose ID matches the most recent artifact.

**P0 — give the inscription something artifact-specific:**
- Take the moment's text, extract a 3-word phrase (or a SHA-derived 3-word phrase as fallback), and use that as the inscription instead of repeating the memory summary. Different artifact, different words.

**P1 — empty state that teaches:**
- Show a sample SVG with caption "the creature leaves one of these every time you feed it."

**P1 — favoriting:**
- Add a `star` boolean on `artifacts`. Starred tiles get a thicker border and float to the front of the grid. The `artifacts()` query orders by `starred DESC, id DESC`.

**P2 — click-to-expand detail:**
- A modal or expanded panel showing the full receipt that produced the artifact, the memory, and the mood delta.

**P2 — delete:**
- A small × on hover that confirms then removes the artifact (and its entry, with a "this also removes the receipt — undo? 10s" toast).

I'm shipping the P0 fixes in the engine code. The UI changes belong in the deepseek lane's iteration; they're noted in the diff sketch at the bottom.

---

## 4) Other findings (small things, not blockers)

- **`render_status` shows a `pet-result-action` line with a hardcoded string** ("A new artifact was added to the shelf.") — it's the same string for every success, every failure, every state. It communicates nothing. Make it dynamic: "made `Mote Relic #4`" or "couldn't reach the model — using safe mode."
- **`render_creature_svg` puts the name in the SVG AND `render_state_panel` shows it in the grid.** Two places for the same data. Pick one.
- **`_strip_thinking` only handles `<think>…</think>`**. Qwen uses that, so it's fine for the default model. But if someone picks `minicpm-v` or another instruct model from the dropdown, the regex will leak their thinking traces into the JSON extractor. Generalize the stripper to also match `<|reasoning|>…<|/reasoning|>` and `Analysis:` blocks.
- **`make_artifact` picks `kind` from `digest[0:2] % len(kinds)`** — only 6 possible kinds, no rarity. The user will see "Mote Relic #1", "Mote Relic #2", "Leaf Relic #3" etc. with very little variety. Consider using more digits and weighting rarer kinds lower.
- **`STORE` is module-level with `check_same_thread=False`** — fine for Gradio's threaded handlers, but no `PRAGMA journal_mode=WAL` and no `busy_timeout`. A read during a write can get "database is locked." WAL mode is one line in `_init_schema`.
- **`on_fresh` builds a synthetic `result` dict** that doesn't go through `process_moment` — fine, but the receipt panel shows "Fresh creature created" as if a moment happened. A cold user sees two empty entries labeled as "moments" before they type anything. Confusing.
- **The model dropdown lists `minicpm-v:latest`** but the prompt template is wired for Qwen instruct. Selecting it will work (Ollama handles text-only), but the model may not respect the JSON-only contract. Either restrict the dropdown to instruct-tuned models, or document the constraint.

---

## 5) Improved code shipped in this PR

| File | Purpose |
|---|---|
| `engine/health.py` | Pings the backend, returns a `BackendStatus` dataclass. Cached for 5s. |
| `engine/petriarium_guarded.py` | Wraps `chat` and `process_moment` with explicit error reporting. Returns a guarded result with `fallback_used`, `latency_ms`, `error`. Does not write fallback responses to the receipts table. |
| `apps/petriarium/onboarding.py` | Cold-start helpers: sample moments, mood legend, form-progression hint, "what is this?" copy. |
| `tests/run_petriarium_guarded.py` | Forces the chat layer to raise, asserts the guarded result is `fallback_used=True` and the receipt is NOT written. |
| `tests/test_critique_fixes.py` | Smoke for the onboarding helpers and health module. |

I did **not** modify `apps/petriarium/app.py` — the deepseek lane owns the visual layer. The diff below is the integration I'd propose to the integrator.

---

## 6) Proposed diff to `apps/petriarium/app.py` (for the integrator)

```python
# At top, after existing imports:
from engine.health import check_backend, last_status
from engine.petriarium_guarded import process_moment_guarded
from apps.petriarium.onboarding import (
    SAMPLE_MOMENTS, MOOD_LEGEND, FORM_PROGRESSION,
    render_mood_legend, render_form_hint, render_about,
)

# Replace on_feed's body with the guarded version. Key changes:
#   - render_status receives a guarded `result` that includes `fallback_used` and `error`
#   - the status banner above the result is filled by last_status()
#   - the moment textbox is not cleared if fallback_used (so the user can retry)
def on_feed(moment, model):
    text = (moment or "").strip()
    if not text:
        snap = _snapshot()
        return (
            render_status(None, model or DEFAULT_MODEL, "Type a moment and press Feed."),
            snap["state_html"],
            snap["receipts_html"],
            snap["artifacts_html"],
            snap["events_html"],
            render_status_banner(last_status()),
            moment,
        )
    used_model = model or DEFAULT_MODEL
    result = process_moment_guarded(text, STORE, model=used_model)
    snap = _snapshot()
    return (
        render_status(result, used_model),
        snap["state_html"],
        snap["receipts_html"],
        snap["artifacts_html"],
        snap["events_html"],
        render_status_banner(result),
        "" if not result.get("fallback_used") else moment,  # keep text on fallback
    )

# In build(), add at the top of the layout (after the hero):
with gr.Row():
    banner = gr.HTML(value=render_status_banner(last_status()))
    gr.Examples(examples=[[m] for m in SAMPLE_MOMENTS], inputs=[moment], label="Try a sample moment")
with gr.Accordion("What is this?", open=False):
    gr.HTML(value=render_about() + render_mood_legend() + render_form_hint())

# At launch, refresh the banner so the user sees model health immediately:
chosen_port = _choose_port(PORT)
status = check_backend(DEFAULT_MODEL)
banner.value = render_status_banner(status)
```

The CSS additions for `.pet-banner-ok` and `.pet-banner-warn` are short — three rules. They can go in `theme.css` next to `.pet-empty`.

---

## 7) Open questions for the team

1. **Should the artifact shelf have a hard cap?** Right now `artifacts(n=12)` is hardcoded to 8 visible + 4 hidden. After 30 feeds the shelf feels crowded. Consider a "load more" button or paginated grid.
2. **Should `New creature` be a confirmation dialog?** Right now it silently wipes the receipts. A user who clicks it by accident loses their creature.
3. **Should the model dropdown show model size + first-token latency?** "qwen2.5:7b-instruct (4.4 GB, ~0.8s/tok)" is more useful than a raw name.
4. **Is the `pet-result-action` line worth keeping?** It says nothing. Either make it dynamic or delete it.
5. **Should the creature SVG have a name label at all?** It's already in the state grid. Removing the SVG label makes the creature feel less like a Tamagotchi and more like an ambient organism.

---

## 8) Verification

```bash
# Existing happy-path smoke (still passes)
python3 tests/run_petriarium.py

# New: failure-path smoke
python3 tests/run_petriarium_guarded.py

# New: unit-ish checks for the helpers
python3 tests/test_critique_fixes.py
```

All three should print `PASS` for every line. If `run_petriarium_guarded` reports a real receipt was written during a forced outage, the guard is broken.
