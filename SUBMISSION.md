# Pocket Confidant — Submission Playbook & Rubric Alignment

> One job for this file: **make sure we don't lose on a technicality, and maximize judge score.**
> The build is done (engine + Gradio app + marketing). This is the checklist that gets it *submitted correctly*.

- **Event:** Hugging Face **Build Small Hackathon** — *Small Models, Big Adventure*
- **Track:** **Backyard AI** (solve a real, recurring problem for a real person)
- **Entry:** **Pocket Confidant** — a private, fully-local AI journaling companion
- **Builder / the "real person":** Daniel LaForce (HF user **LocutusofArgo**) — and anyone who journals
- **Companion artifacts in this repo:**
  - App: `apps/confidant/` (`app.py`, `README.md` ← Space card, `theme.css`, `requirements.txt`)
  - Deploy steps: `apps/confidant/DEPLOY.md`
  - Engine: `engine/store.py`, `engine/confidant.py`, `engine/backends.py`
  - Marketing: `marketing/DEMO-VIDEO.md`, `marketing/SOCIAL-POST.md`, `marketing/FIELD-NOTES.md`

---

## 1. The 3 hard rules (do not fail on these)

| # | Hard rule | Our status | TODO |
|---|-----------|------------|------|
| 1 | **Model ≤ 32B parameters** | ✅ Pass with huge margin. Default `qwen3:8b` (8B); MiniCPM option is smaller. Embeddings via `nomic-embed-text` (tiny, local). No model anywhere near 32B. | **TODO:** State the exact model + param count in the README/Space card and demo so a judge can verify the ≤32B claim at a glance. |
| 2 | **App is a Gradio app hosted as a Hugging Face Space** | 🟡 App is built (`apps/confidant/app.py`, Gradio). Not yet pushed to a live Space. | **TODO (blocking):** Create the Gradio Space under the hackathon org and push. See `apps/confidant/DEPLOY.md`. |
| 3 | **Submission = short demo video + social media post** | 🟡 Both scripted (`marketing/DEMO-VIDEO.md`, `marketing/SOCIAL-POST.md`); not yet recorded/posted. | **TODO (blocking):** Record the video (incl. airplane-mode shot) and publish the social post with the required hashtags/links. |

### Key dates (calendar these now)

| Date | Milestone | Action |
|------|-----------|--------|
| **June 3, 2026** | **Registration closes** | **TODO (blocking, earliest deadline):** Register / join the hackathon org *before this date* — you can't submit later if you never registered. Do this FIRST. |
| **June 5–15, 2026** | Hack window | Build & ship the Space; journal daily for the "person actually used it" evidence. |
| **June 15, 2026** | **Submission deadline** | Space live + demo video + social post all submitted *before* end of day. |

> ⏰ **The single most failure-prone item is registration (June 3).** It is *before* the hack window opens. Miss it and the rest is wasted. Treat it as priority zero.

---

## 2. Backyard AI rubric → how Pocket Confidant satisfies it

The Backyard AI track rewards a **real, specific, recurring problem for a real person**, an **honest fit** between that problem and the small-model constraint, that **the person actually used it**, and **polish**. Mapping each:

| Judging criterion | How Pocket Confidant satisfies it | Evidence to show |
|---|---|---|
| **Problem is specific & real** | "I want to journal and have something reflect back warmly — but a diary is the most private thing I own, so I will *never* send it to a cloud AI." That's a concrete, recurring, daily problem with a hard privacy constraint. Not a generic "AI assistant." | The honest-fit paragraph in `apps/confidant/README.md`; the builder's own daily journaling habit; `marketing/FIELD-NOTES.md` framing the lived problem. |
| **Honest fit between problem and the small-model constraint** | This is our strongest card. Because the data must *never leave the device*, a **local small model is the only honest answer** — not a compromise, the correct design. The app does what a small model is reliably good at (understand, reflect, ask one question, recall a relevant past entry) and is **honest about its limits** (no diagnosing, no advice; persona enforces this in `engine/confidant.py`). It avoids tasks small models bluff at. | The "honest fit" section of the README; the persona/guardrails in `confidant.py` (no therapy-speak, no medical/legal/financial advice); the `RECALL_FLOOR = 0.58` design that makes the model **stay silent rather than force a memory** — restraint as a feature. |
| **The person actually used it** | The builder journals *daily during the hack window* using the live app, accumulating real entries so the semantic-memory callback fires on genuine connections (not a staged demo). | Real-but-redacted entries from the builder's own `~/.pocket-confidant/journal.db`; a callback in the demo that references an *actual* earlier entry; entry-count / date span shown on camera. |
| **Polish of the Gradio app** | Custom warm theme (`apps/confidant/theme.css`), not the default Gradio look; clear single-action UX ("write → Reflect → short reflection + one question + occasional callback"); graceful degradation (store `add()` and `recall()` swallow embed failures so the app never hard-crashes offline). | The Off-Brand custom theme on the live Space; smooth click-through in the demo video; the README Space-card front-matter (emoji/colors/title) rendering cleanly. |

> **Score-maximizing framing to repeat everywhere:** *"A diary is the most private thing you own, so a 100%-local small model isn't a constraint we tolerated — it's the only honest design. The model is reliable at understanding and reflecting, and honest about what it can't do."* That sentence is the honest-fit thesis the judges score.

---

## 3. Merit-badge checklist (each with the artifact that proves it)

| Badge | What it requires | Proof artifact | Status |
|---|---|---|---|
| 🔌 **Off the Grid** | No cloud inference **APIs**; all generation self-hosted. | On the Space, inference runs via **llama-cpp-python** on the Space's own hardware — no third-party model API call. Locally it's ollama. **Plus** an on-camera **airplane-mode** laptop shot proving the journal never phones home. (Nuance per `DEPLOY.md`: the badge is about no cloud *APIs*, not an airless Space.) | 🟡 Built; needs live Space + airplane-mode footage. |
| 🦙 **Llama Champion** | Use llama.cpp. | `engine/backends.py` `LlamaCppBackend` (the Space target) runs real **llama.cpp via llama-cpp-python** on GGUF weights; `scripts/fetch_gguf.sh` / `hf_hub_download` pulls the GGUF. | 🟡 Code path exists; verify the wheel builds green on Space hardware. |
| 🎨 **Off-Brand** | Custom Gradio frontend, not the default theme. | `apps/confidant/theme.css` — custom warm indigo→pink theme; non-default layout. | 🟡 Built; confirm it renders on the live Space. |
| 📓 **Field Notes** | A blog post / write-up of the build. | `marketing/FIELD-NOTES.md`. | 🟡 Drafted; needs to be published (HF blog / personal blog) and linked from the submission. |
| 🎯 **OpenBMB (sponsor / MiniCPM)** | Use OpenBMB's MiniCPM small model. | MiniCPM is a supported swappable model option (`minicpm-v` is pulled locally); the engine's `model=` arg makes it a one-line switch. | 🟡 **Decision pending:** ship MiniCPM as the Space model (claims the sponsor badge) **or** keep `qwen3:8b` as default and document MiniCPM as a supported option. Pick before push. |

---

## 4. The 4 submission steps (actionable checklist)

**Step 1 — Register / join the org (by June 3 — do this first)**
- [ ] Confirm the **exact hackathon org name** on Hugging Face (open question in `DEPLOY.md`).
- [ ] Register the account (`LocutusofArgo`) and **join the org before June 3, 2026**.
- [ ] Confirm whether **ZeroGPU** is enabled on that org's tier (affects Space hardware choice).

**Step 2 — Build & ship the Space (during June 5–15 window)**
- [ ] Flatten app to Space repo root: `app.py`, `requirements.txt`, `README.md` (Space card), and the `engine/` package — per `DEPLOY.md` §1.
- [ ] Wire `app.py` to `LlamaCppBackend` (not `OllamaBackend`); `hf_hub_download` the GGUF at startup (don't commit multi-GB weights).
- [ ] Choose hardware: **ZeroGPU** (`@spaces.GPU`, best UX) or a small CPU-friendly quant fallback — per `DEPLOY.md` §2.
- [ ] Push; confirm the **Space builds green** and a first reflection returns in reasonable time.
- [ ] Verify the memory callback **fires on a related entry and stays silent on an unrelated one** (the headline feature).

**Step 3 — Demo video (short)**
- [ ] Record per `marketing/DEMO-VIDEO.md`: write an entry → get reflection + one question; show a **real callback** to an earlier entry; include the **airplane-mode laptop shot**; state the model name + ≤32B.
- [ ] Keep it short; upload and grab the link.

**Step 4 — Social media post**
- [ ] Publish `marketing/SOCIAL-POST.md` with required hashtags + links (Space + video).
- [ ] **Publish `marketing/FIELD-NOTES.md`** as the blog post and link it (claims 📓 Field Notes).
- [ ] **Submit** the Space + video + post through the official form **before June 15, 2026**.

---

## 5. Risks & how we de-risk them

| Risk | De-risk |
|---|---|
| **"Person actually used it" looks staged** | Builder journals **daily during the live window** in the real app; demo surfaces a callback to a genuine earlier entry; show real-but-**redacted** entries and the entry-count/date span on camera. Real history > a scripted two-entry demo. |
| **Latency kills the "warm companion" feel on a CPU Space** | Prefer **ZeroGPU** (`@spaces.GPU`); if unavailable, ship the **smallest readable quant** and lean on the offline-laptop (RTX 4070 Ti) footage in the video. Set expectations honestly in the demo. (`DEPLOY.md` §2–3.) |
| **Privacy/"Off the Grid" claim is doubted** | The **airplane-mode shot** is the proof: network visibly down, entry written, reflection + callback returned. One shot beats any paragraph. |
| **Registration missed (June 3)** | Priority-zero TODO; it precedes the hack window. Calendar + reminder set now. |
| **`llama-cpp-python` wheel fails to build on Space hardware** | Validate the wheel resolves for the chosen hardware **early in the window**, not on June 14. Have the CPU-quant fallback ready. |
| **Sponsor badge ambiguity (MiniCPM vs qwen3)** | Decide before push (§3). If claiming 🎯 OpenBMB, ship MiniCPM as the Space model and say so explicitly in README + video. |
| **Over-claiming / dishonesty (kills judge trust)** | The app is honest by design (no diagnosing, no advice; stays silent rather than forcing a memory). Keep marketing copy matched to what actually runs — no aspirational features in the video. |

---

*Local model + local memory. Your journal stays yours. Now go register before June 3.*
