# Pocket Confidant

**A private AI journaling companion that runs 100% on-device.**

Built for the Hugging Face **Build Small Hackathon** — *Small Models, Big Adventure* · **Backyard AI** track.

The current UI foregrounds the point of the app immediately: a private journal, a visible memory pulse, and a companion that only calls back when the connection is real.

## What it does

A diary is the most private thing you own. You would never paste it into a cloud chatbot. Pocket Confidant reads each entry you write and gives back:

1. A **warm, specific reflection** — 1-2 sentences using your words, not platitudes
2. **Exactly one good question** — gentle, specific, helps you notice something
3. **A memory callback** — only when it genuinely connects to a past entry

## How it works

- **100% on-device** — no cloud, no account, no subscription
- **Works in airplane mode** — all inference runs locally
- **Small model** — qwen3:8b (8B params) or MiniCPM-V
- **Semantic memory** — SQLite + FTS5 + local embeddings

## Project structure

```
apps/confidant/     Gradio app (hackathon submission)
apps/pwa/           Vite React PWA (commercial product)
engine/             Core engine (store, confidant, backends)
marketing/          Demo video, social post, field notes
tests/              Test suite
```

## Quick start (local dev)

```bash
# Requires: Python 3.11+, Ollama running
cd apps/confidant
pip install -r requirements.txt
python app.py
# Opens at http://localhost:7860
```

## Hugging Face Space

🔗 **Live demo:** [huggingface.co/spaces/LocutusofArgo/pocket-confidant](https://huggingface.co/spaces/LocutusofArgo/pocket-confidant)

## Merit badges targeted

- 🔌 **Off the Grid** — no cloud inference APIs
- 🦙 **Llama Champion** — llama-cpp-python on the Space
- 🎨 **Off-Brand** — custom warm paper theme
- 📓 **Field Notes** — builder's daily journaling log

## License

MIT
