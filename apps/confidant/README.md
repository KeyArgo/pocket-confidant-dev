---
title: Pocket Confidant
emoji: 📓
colorFrom: indigo
colorTo: pink
sdk: gradio
sdk_version: 6.15.2
app_file: app.py
pinned: false
license: mit
---

# 📓 Pocket Confidant

**A private AI journaling companion that runs 100% on-device. No cloud, no account, no subscription — it works in airplane mode.**

Built for the Hugging Face **Build Small Hackathon** — *Small Models, Big Adventure* · **Backyard AI** track.

---

## The honest fit

A diary is the most private thing you own. You would *never* paste it into a cloud chatbot. So the only honest design is one where **nothing ever leaves your machine** — a small model running locally is not a compromise here, it's the *correct* answer to the problem.

Pocket Confidant reads each entry you write and gives back three small things:

1. A **warm, specific reflection** — 1–2 plain sentences that show it actually heard you, using *your* words, not platitudes. No therapy-speak, no relentless positivity, no walls of advice.
2. **Exactly one good question** — gentle, specific, the kind that helps you notice something.
3. **A memory callback — but only when it genuinely fits.** Using private, on-device semantic memory, it can say *"you mentioned dreading that dentist visit last week — how did it go?"* — and crucially, it stays quiet when nothing connects, instead of force-fitting a canned line.

That last point is the whole pitch: a small model can't bluff its way through hard reasoning, but it *can* be reliable at **understanding, reflecting, and remembering** — and honest about its limits. The judges score exactly this kind of honest fit between a real recurring problem and the small-model constraint.

## Why on-device matters here

- 🔒 **Your journal never leaves the machine.** Entries live in a local SQLite file. Embeddings for semantic recall are computed locally. There is no API key field, no account, no telemetry.
- ✈️ **Works offline.** Pull the model once, then it runs in airplane mode — on a laptop, and increasingly on a phone.
- 🧠 **"It remembers" without a giant context window.** Instead of stuffing your whole history into the prompt, it does local semantic recall and feeds in only the handful of past entries that are *actually* relevant (cosine-similarity floor of 0.58, tuned so same-topic entries connect and unrelated ones don't).

## Merit badges

- 🔌 **Off the Grid** — zero cloud inference APIs; all generation is self-hosted.
- 🦙 **Llama Champion** — on the Space the model runs via **llama-cpp-python** (real llama.cpp, GGUF weights).
- 🎨 **Off-Brand** — a custom warm Gradio theme, not the default look.
- 📓 **Field Notes** — accompanied by a write-up of the build.
- 🎯 **OpenBMB special category** — MiniCPM is a supported small-model option.

## How to use

1. Open the Space.
2. Write whatever's on your mind in the entry box — a few words or a few paragraphs.
3. Press **Reflect.** You'll get a short reflection, one question, and (sometimes) a gentle callback to something you wrote before.
4. Keep coming back. The more you write, the more its memory has to draw on — all of it private and on your machine.

> Pocket Confidant is a journaling companion, not a therapist or a crisis service. It never diagnoses and never gives medical, legal, or financial advice. If you're in crisis, please reach out to a real person or a local helpline.

## Run it locally (truly offline)

The same engine runs on your own laptop with [ollama](https://ollama.com):

```bash
git clone <this-space>
cd build-small-2026
uv venv .venv && . .venv/bin/activate
uv pip install -r apps/confidant/requirements.txt
ollama pull qwen3:8b && ollama pull nomic-embed-text
python apps/confidant/app.py
```

Then disconnect your network and keep journaling — nothing breaks, because nothing was ever phoning home.

---

*Local model + local memory. Your journal stays yours.*
