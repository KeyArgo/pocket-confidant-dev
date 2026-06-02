# Running Pocket Confidant on llama.cpp (🦙 Llama Champion)

This guide explains how to run the journal companion against **llama.cpp**
instead of ollama, which is the runtime we ship on the Hugging Face Space.

> **Why this earns the badge:** the 🦙 Llama Champion merit badge is for running
> your model through **llama.cpp**. We do that via
> [`llama-cpp-python`](https://github.com/abetlen/llama-cpp-python) — the Python
> bindings **are llama.cpp under the hood** (it vendors and compiles llama.cpp;
> `Llama(...)` is a thin wrapper over the C++ inference engine). So a Space built
> on `llama-cpp-python` is a genuine llama.cpp deployment, not an API shim.

During local dev we use ollama (`engine/backends.py::OllamaBackend`,
`engine/confidant.py::_chat` -> ollama HTTP). For the Space we swap the runtime.
Everything stays 100% local — no cloud, no account.

---

## 1. Install `llama-cpp-python` with the right build flags

`llama-cpp-python` compiles llama.cpp at install time, so the CMake flags decide
whether you get CPU or GPU inference. Pick the line that matches the target.

**CPU only** (what HF Spaces' free CPU tier uses):

```bash
pip install "llama-cpp-python>=0.3.2"
```

**CUDA** (local dev box — RTX 4070 Ti, 12 GB — much faster):

```bash
CMAKE_ARGS="-DGGML_CUDA=on" pip install "llama-cpp-python>=0.3.2" --no-cache-dir
```

**Apple Metal** (if testing on a Mac):

```bash
CMAKE_ARGS="-DGGML_METAL=on" pip install "llama-cpp-python>=0.3.2" --no-cache-dir
```

Notes:
- `--no-cache-dir` forces a recompile so the flags actually take effect (pip
  loves to hand you a cached CPU wheel otherwise).
- This dep is already declared as the optional `space` extra in
  `pyproject.toml`:
  ```bash
  pip install -e ".[space]"
  ```
- On a CUDA build, set `n_gpu_layers=-1` to offload the whole model to the GPU
  (the `LlamaCppBackend` already does this). On the CPU-only Space, llama.cpp
  ignores GPU layers and runs on cores — slower but works in airplane mode.

---

## 2. Get the GGUF (where it goes)

GGUF files live in `../../models/` relative to this app (i.e. the repo's
top-level `models/` directory). They are **gitignored** — never committed.

Fetch them with the helper script:

```bash
# (a) text model for the journal companion (default pick)
scripts/fetch_gguf.sh text         # Qwen2.5-7B-Instruct-Q4_K_M.gguf  (~4.7 GB)

# smaller phone/low-RAM fallback
scripts/fetch_gguf.sh text-small   # Qwen2.5-3B-Instruct-Q4_K_M.gguf  (~2.0 GB)

# (b) MiniCPM-V multimodal (OpenBMB sponsor angle) — model + mmproj projector
scripts/fetch_gguf.sh minicpm
```

The companion's reflection loop is **text-only**, so the Qwen2.5 text GGUF is
the model you want behind `confidant.reflect`. MiniCPM-V is the multimodal model
wired into `LlamaCppBackend` (vision); it's the OpenBMB sponsor play, not what
the journaling chat needs.

On the Space: either run `scripts/fetch_gguf.sh` during the build, or attach the
`.gguf` as a Space LFS file.

---

## 3. How `engine/backends.py::LlamaCppBackend` is constructed

`LlamaCppBackend` is the **multimodal/vision** backend (MiniCPM-V). It takes the
model GGUF plus the mmproj (CLIP projector) and builds a `Llama` with a
`MiniCPMv26ChatHandler`. Do **not** edit `backends.py`; just construct it:

```python
from engine.backends import LlamaCppBackend

backend = LlamaCppBackend(
    model_path="models/minicpm-v-2_6-Q4_K_M.gguf",
    mmproj_path="models/minicpm-v-2_6-mmproj-f16.gguf",
)
result = backend.generate("What's in this image?", images=[png_bytes])
print(result.text)
```

Internally it does (see `backends.py`, do not change it):

```python
from llama_cpp import Llama
from llama_cpp.llama_chat_format import MiniCPMv26ChatHandler

handler = MiniCPMv26ChatHandler(clip_model_path=mmproj_path)
llm = Llama(model_path=model_path, chat_handler=handler,
            n_ctx=4096, n_gpu_layers=-1, verbose=False)
```

`n_gpu_layers=-1` means "offload everything to GPU"; harmless on a CPU build.

---

## 4. Pointing `confidant.reflect` at a llama.cpp-backed chat

`confidant.reflect(entry_text, store=..., model=..., before_id=...)` does its LLM
turn through `confidant._chat`, which currently POSTs to the **ollama** HTTP API.
There is no vision in the journaling path — it's plain chat with a JSON-only
response — so for the Space you point that one chat call at a **text** GGUF via
`llama-cpp-python`. Two clean ways:

### Option A — in-process `Llama` (recommended for the Space, fully offline)

Load the Qwen2.5 text GGUF directly and run the same `(PERSONA, user)` turn the
companion builds. This keeps everything in one process, no server, airplane-mode
safe. Wire it in the Space app (NOT in `confidant.py`/`backends.py`):

```python
from llama_cpp import Llama
from engine import confidant
from engine.store import Entry

# Load the text GGUF once at app startup.
LLM = Llama(
    model_path="models/Qwen2.5-7B-Instruct-Q4_K_M.gguf",
    n_ctx=4096,
    n_gpu_layers=-1,      # -1 = all layers on GPU (CUDA); ignored on CPU build
    verbose=False,
)

def llamacpp_chat(system: str, user: str) -> str:
    """Drop-in replacement for confidant._chat, backed by llama.cpp."""
    out = LLM.create_chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.7,
    )
    return out["choices"][0]["message"]["content"]

# Monkeypatch the single chat seam so reflect() now runs through llama.cpp.
# reflect() still owns the persona, the memory recall, and the JSON parsing —
# we only swap the transport. (Qwen2.5-Instruct doesn't emit <think> blocks, but
# confidant._strip_thinking handles them anyway, so qwen3 also works.)
confidant._chat = llamacpp_chat

reflection = confidant.reflect("Big day. The interview actually went well.", store=my_store)
print(reflection.render())
```

This is a deliberate, minimal seam: `confidant._chat(system, user, model=...)`
is the **only** place the companion talks to a model, so replacing it is the
whole swap. Memory recall (`store.recall`, the cosine `RECALL_FLOOR`) is
unaffected — it uses local ollama embeddings (`nomic-embed-text`) independently.
If you also want embeddings off ollama, that's a separate change in
`engine/store.py::embed` and out of scope here.

### Option B — `llama-cpp-python`'s OpenAI-compatible server

`llama-cpp-python` ships a server that mimics ollama/OpenAI chat:

```bash
python -m llama_cpp.server \
    --model models/Qwen2.5-7B-Instruct-Q4_K_M.gguf \
    --n_gpu_layers -1 --host 127.0.0.1 --port 8080
```

Then point the companion's chat at it. `_chat` calls `{host}/api/chat`, which is
ollama's route, not OpenAI's `/v1/chat/completions` — so use the monkeypatch in
Option A pointed at the server's OpenAI endpoint, or just prefer Option A
(in-process) for the Space since it needs no extra process and stays offline.

---

## 5. Quick smoke test

After installing `llama-cpp-python` and fetching the text GGUF:

```python
from llama_cpp import Llama
llm = Llama(model_path="models/Qwen2.5-7B-Instruct-Q4_K_M.gguf",
            n_ctx=2048, n_gpu_layers=-1, verbose=False)
out = llm.create_chat_completion(
    messages=[{"role": "user", "content": "Say hi in one short sentence."}])
print(out["choices"][0]["message"]["content"])
```

If that prints a sentence, llama.cpp is live and the Llama Champion path works.

---

## Model references (sanity-check these)

| target | HF repo | file(s) |
| --- | --- | --- |
| text (default) | `bartowski/Qwen2.5-7B-Instruct-GGUF` | `Qwen2.5-7B-Instruct-Q4_K_M.gguf` |
| text-small | `bartowski/Qwen2.5-3B-Instruct-GGUF` | `Qwen2.5-3B-Instruct-Q4_K_M.gguf` |
| minicpm (sponsor) | `openbmb/MiniCPM-V-2_6-gguf` | `ggml-model-Q4_K_M.gguf` + `mmproj-model-f16.gguf` |

All three are ≤8B params (well within the ≤32B hackathon limit). We use
bartowski's single-file Qwen GGUF because the official `Qwen/Qwen2.5-7B-Instruct-GGUF`
repo ships Q4_K_M as a 2-shard split, which is awkward for `llama-cpp-python`.
