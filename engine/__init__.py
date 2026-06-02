"""Shared local-AI engine for the Build Small hackathon entries.

One engine, two apps:
  - apps/explainer : "Plain-Paper" — Backyard AI document explainer (#9)
  - apps/wood      : Thousand Token Wood text adventure (#93)
"""
from .backends import VisionBackend, OllamaBackend, LlamaCppBackend, default_backend, GenResult
from .explainer import explain_document, Explanation, SYSTEM, PROMPT, VERIFY_DISCLAIMER

__all__ = [
    "VisionBackend",
    "OllamaBackend",
    "LlamaCppBackend",
    "default_backend",
    "GenResult",
    "explain_document",
    "Explanation",
    "SYSTEM",
    "PROMPT",
    "VERIFY_DISCLAIMER",
]
