"""Petriarium backend health check.

The SKEPTIC lane insists that the app should never silently fall back when the
LLM is unreachable. This module is the read-only first half of that promise:

  - one cheap HTTP call (`/api/tags`) per status refresh
  - explicit `ok: bool` + `error: str` for the UI
  - a 5-second cache so a click on Feed doesn't refetch

It is intentionally not used to *recover* from failure — recovery is the
responsibility of `petriarium_guarded.process_moment_guarded`, which surfaces
the status to the UI.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, asdict
from typing import Any

import requests


DEFAULT_HOST = os.environ.get("PETRIARIUM_OLLAMA", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("PETRIARIUM_MODEL", "qwen2.5:7b-instruct")
CACHE_TTL_SECONDS = 5.0
PROBE_TIMEOUT_SECONDS = 2.0


@dataclass
class BackendStatus:
    ok: bool
    backend: str
    model: str
    host: str
    latency_ms: int
    error: str
    last_check_ts: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_LAST: BackendStatus | None = None


def _coerce_error(exc: Exception) -> str:
    name = type(exc).__name__
    msg = str(exc) or "unknown error"
    if len(msg) > 140:
        msg = msg[:137] + "…"
    return f"{name}: {msg}"


def check_ollama(model: str = DEFAULT_MODEL, host: str = DEFAULT_HOST) -> BackendStatus:
    """Return a fresh BackendStatus. Always makes one HTTP call; respects no cache."""
    started = time.perf_counter()
    base = host.rstrip("/")
    try:
        resp = requests.get(f"{base}/api/tags", timeout=PROBE_TIMEOUT_SECONDS)
        resp.raise_for_status()
        names = [item.get("name", "") for item in resp.json().get("models", [])]
        if model not in names:
            return BackendStatus(
                ok=False,
                backend="ollama",
                model=model,
                host=base,
                latency_ms=int((time.perf_counter() - started) * 1000),
                error=f"model '{model}' not found in /api/tags (have {len(names)} models)",
                last_check_ts=time.time(),
            )
        return BackendStatus(
            ok=True,
            backend="ollama",
            model=model,
            host=base,
            latency_ms=int((time.perf_counter() - started) * 1000),
            error="",
            last_check_ts=time.time(),
        )
    except Exception as exc:  # noqa: BLE001 — we want the error string for the UI
        return BackendStatus(
            ok=False,
            backend="ollama",
            model=model,
            host=base,
            latency_ms=int((time.perf_counter() - started) * 1000),
            error=_coerce_error(exc),
            last_check_ts=time.time(),
        )


def check_backend(model: str = DEFAULT_MODEL, host: str = DEFAULT_HOST) -> BackendStatus:
    """Cached wrapper. Refreshes the cached status at most once per CACHE_TTL_SECONDS."""
    global _LAST
    now = time.time()
    if _LAST is not None and (now - _LAST.last_check_ts) < CACHE_TTL_SECONDS and _LAST.model == model:
        return _LAST
    _LAST = check_ollama(model=model, host=host)
    return _LAST


def last_status() -> BackendStatus | None:
    """Return the most recent status, even if it has expired. None if never checked."""
    return _LAST


def invalidate() -> None:
    """Drop the cached status. Useful for tests."""
    global _LAST
    _LAST = None
