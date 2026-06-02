# Build Small 2026 — Local-AI hackathon entries

Two apps, one local engine (MiniCPM-V, OpenBMB sponsor model), no cloud AI.

- **apps/explainer** — "Plain-Paper": point your phone at a confusing document
  (medical bill, lease, official letter) and get a calm plain-English explanation.
  Backyard AI track. The model *understands & orients*; it flags exact figures for
  you to confirm rather than bluffing — an honest fit for a small local model.
- **apps/wood** — Thousand Token Wood: an offline text-adventure forest whose
  creatures are small-model NPCs. (in progress)

## Merit badges targeted
🔌 Off the Grid · 🦙 Llama Champion (llama-cpp-python on the Space) · 🎨 Off-Brand · 📓 Field Notes
Sponsor: 🎯 OpenBMB special category (MiniCPM-V)

## Dev quickstart
```
uv venv .venv && . .venv/bin/activate && uv pip install requests pillow gradio
python tests/run_explainer.py   # end-to-end engine smoke test (needs ollama + minicpm-v)
```
