"""Pluggable vision-LLM backends.

Two interchangeable backends behind one interface:
  - OllamaBackend     : fast local iteration during dev (uses llama.cpp under the hood)
  - LlamaCppBackend   : the HF Space target -> real llama.cpp via llama-cpp-python,
                        which earns the Llama Champion merit badge.

The app code only ever sees `VisionBackend.generate(...)`, so swapping the
runtime for the final Space is a one-line change.
"""
from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class GenResult:
    text: str
    backend: str
    model: str


class VisionBackend(ABC):
    name: str = "abstract"
    model: str = "unknown"

    @abstractmethod
    def generate(self, prompt: str, images: list[bytes], system: str | None = None) -> GenResult:
        """Run a single multimodal turn. `images` is a list of raw image bytes."""
        raise NotImplementedError


class OllamaBackend(VisionBackend):
    """Local dev backend. Talks to the ollama HTTP API on localhost."""

    name = "ollama"

    def __init__(self, model: str = "minicpm-v:latest", host: str = "http://localhost:11434"):
        import requests  # local import so the module loads without the dep

        self._requests = requests
        self.model = model
        self.host = host.rstrip("/")

    def generate(self, prompt: str, images: list[bytes], system: str | None = None) -> GenResult:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append(
            {
                "role": "user",
                "content": prompt,
                "images": [base64.b64encode(img).decode("ascii") for img in images],
            }
        )
        resp = self._requests.post(
            f"{self.host}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.1},
            },
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json()
        return GenResult(text=data["message"]["content"], backend=self.name, model=self.model)


class LlamaCppBackend(VisionBackend):
    """HF Space target: real llama.cpp via llama-cpp-python (Llama Champion badge).

    Needs a MiniCPM-V GGUF + its mmproj projector. Implemented as a thin stub here;
    wired up when we package the Space so dev iteration isn't blocked on GGUF setup.
    """

    name = "llama.cpp"

    def __init__(self, model_path: str, mmproj_path: str, model: str = "minicpm-v-gguf"):
        from llama_cpp import Llama
        from llama_cpp.llama_chat_format import MiniCPMv26ChatHandler

        self.model = model
        self._handler = MiniCPMv26ChatHandler(clip_model_path=mmproj_path)
        self._llm = Llama(
            model_path=model_path,
            chat_handler=self._handler,
            n_ctx=4096,
            n_gpu_layers=-1,
            verbose=False,
        )

    def generate(self, prompt: str, images: list[bytes], system: str | None = None) -> GenResult:
        content = [{"type": "text", "text": prompt}]
        for img in images:
            b64 = base64.b64encode(img).decode("ascii")
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": content})
        out = self._llm.create_chat_completion(messages=messages, temperature=0.1)
        return GenResult(text=out["choices"][0]["message"]["content"], backend=self.name, model=self.model)


def default_backend() -> VisionBackend:
    """Dev default. The Space overrides this with LlamaCppBackend."""
    return OllamaBackend()
