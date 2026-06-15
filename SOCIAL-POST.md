# 📓 Pocket Confidant — A private journal that actually remembers. All on my laptop.

*Built for the Build Small Hackathon · Backyard AI track · by Daniel LaForce (HF: LocutusofArgo)*

---

A diary is the most private thing you own. You would *never* paste it into ChatGPT.

So I built a journal companion that runs **100% on-device**, no cloud, no account, works in airplane mode. A small language model (Qwen 2.5 3B Q4_K_M via llama.cpp) reads each entry and gives back:

1. A **short warm reflection** that uses my own words
2. Exactly **one good question**
3. A **memory callback** — but only when it genuinely connects to something I wrote days ago, with a 🔗 similarity score so I can see why

It's been my actual journaling tool for a year. 376 real entries spanning July 2025 to June 2026. The model knows my coffee-on-the-porch mornings. The dentist dread. The 2am rain.

When nothing connects, it stays quiet. The restraint is the warmth.

---

**Tech:**
- `llama-cpp-python` on a Space (3B Q4_K_M, 2 GB) for verification
- `ollama` (Qwen 3.5 9B) on my laptop for the actual daily use
- SQLite + on-device embedding model for semantic memory recall
- Custom 13 KB Gradio theme (no default look)
- All inference local. Zero network calls at runtime.

**Why this wins (or at least fits):**
- 🔌 Off the Grid — no cloud APIs
- 🦙 Llama Champion — real llama.cpp path
- 🎨 Off-Brand — custom Gradio frontend
- 🏔️ Basecamp — quantized weights
- 🐜 Tiny Titan — 3B parameters
- 📓 Field Notes — see the write-up

**The honest-fit thesis:** small models aren't a compromise for private AI. They're the *correct* answer.

---

🎥 **Demo**: https://youtube.com/...
🛰️ **Space**: https://build-small-hackathon-pocket-confidant.hf.space
📓 **Field Notes**: https://github.com/KeyArgo/pocket-confidant-dev/blob/master/marketing/FIELD-NOTES.md
💻 **Code**: https://github.com/KeyArgo/pocket-confidant-dev

#BuildSmallHackathon #SmallModels #OnDeviceAI #Privacy
