# Petriarium

Petriarium is the Chapter Two hackathon app: feed a tiny AI creature a moment,
watch it learn something small, and collect the artifact it leaves behind.

## Run locally

```bash
uv pip install -r apps/petriarium/requirements.txt
python apps/petriarium/app.py
```

Environment variables:

- `PETRIARIUM_DB` - SQLite path, defaults to `~/.petriarium/petriarium.db`
- `PETRIARIUM_PORT` - Gradio port, defaults to `7861`
- `PETRIARIUM_MODEL` - local Ollama model name, defaults to `qwen2.5:7b-instruct`
- `PETRIARIUM_RUNTIME` - `llama` (default) or `ollama`
- `PETRIARIUM_GGUF` / `PETRIARIUM_HF_REPO` / `PETRIARIUM_HF_FILE` - Space/runtime GGUF lookup

## Smoke test

```bash
python tests/run_petriarium.py
```

The smoke test is model-free. It patches the chat layer with a fixed response so
the state machine, persistence, and artifact rendering can be checked without a
local model.
