# Deploying Pocket Confidant to a Hugging Face Space

Concise notes for pushing during the hack window. Read once before you create the Space.

## Key dates (don't miss these)

- **Registration closes: June 3, 2026** — register the team/account before this.
- **Hack window: June 5–15, 2026.**
- **Submission deadline: June 15, 2026** — Space must be live + demo video + social post submitted.

## 1. Create the Space

Create a **Gradio** Space under the hackathon org (confirm exact org name with the human — see open questions).

```bash
# from a machine with `huggingface-cli login` done:
huggingface-cli repo create pocket-confidant --type space --space_sdk gradio --organization <HACKATHON_ORG>
git clone https://huggingface.co/spaces/<HACKATHON_ORG>/pocket-confidant
```

Copy into the Space repo root so the Space sees them at top level:

- `app.py`              (from `apps/confidant/app.py`)
- `requirements.txt`    (from `apps/confidant/requirements.txt`)
- `README.md`           (from `apps/confidant/README.md` — its YAML front-matter is the Space card)
- the `engine/` package (so `from engine.confidant import reflect` resolves on the Space)

A Space reads `app_file: app.py` and `requirements.txt` from its **repo root**, so flatten on push (don't keep the `apps/confidant/` nesting on the Space).

## 2. Hardware: this needs a GPU for good UX

A Qwen / MiniCPM GGUF on **CPU is too slow** for an interactive journaling feel (multi-second-per-token stalls kill the "warm companion" effect). Two viable paths:

- **HF ZeroGPU (recommended).** Free, on-demand GPU bursts. Decorate the generation call with `@spaces.GPU` so inference grabs a GPU slice only while reflecting. Best UX for a judge clicking around. Add `spaces` to requirements if you go this route and confirm ZeroGPU is enabled for the org tier.
- **Small CPU-friendly quant (fallback).** A heavily-quantized small model (e.g. a Q4_K_M of a ~3–4B model, or MiniCPM at low quant) can run on the free CPU Space — usable but noticeably slower. Acceptable as a fallback if ZeroGPU isn't available; set expectations in the demo.

Pick ZeroGPU if the org has it; otherwise ship the small CPU quant and lean harder on the offline-laptop footage in the video.

## 3. Model weights

Don't bake multi-GB GGUF files into the repo. `app.py` should `hf_hub_download` the GGUF at startup (that's why `huggingface_hub` is in requirements). On a CPU Space, prefer the smallest quant that still reads warmly; on ZeroGPU you can afford a larger/sharper quant.

Note the swap from dev: locally the engine talks to **ollama**; on the Space it must run through **llama-cpp-python** (real llama.cpp). The `LlamaCppBackend` in `engine/backends.py` is the Space target — wire `app.py` to it rather than to `OllamaBackend`.

## 4. The offline / airplane-mode story (badge nuance)

The 🔌 **Off the Grid** badge is about **no cloud inference *APIs*** — not about the Space being airless. Self-hosted local inference *on the Space* (llama.cpp running on the Space's own GPU/CPU) fully qualifies: no request ever leaves to a third-party model API.

To make this unmistakable to judges, the demo video should **also** show it running fully offline on a laptop:

1. Pull the model once with ollama.
2. **Turn off Wi-Fi / enable airplane mode** on camera.
3. Write an entry, get a reflection + callback — with the network visibly down.

That single shot proves the privacy claim better than any paragraph: your diary genuinely never had anywhere to go.

## 5. Pre-submission checklist

- [ ] Space builds green (check the build logs; `llama-cpp-python` wheel resolves for the chosen hardware).
- [ ] First reflection returns in a reasonable time on the chosen hardware.
- [ ] Memory callback fires on a related second entry and stays silent on an unrelated one.
- [ ] README front-matter renders as a proper Space card (emoji, colors, title).
- [ ] Demo video recorded, including the airplane-mode laptop shot.
- [ ] Social media post drafted.
- [ ] Submitted before **June 15, 2026**.

## Open question for the human

- **Exact hackathon org name** to push the Space under (and whether ZeroGPU is enabled on that org's tier).
