"""Petriarium guarded processing — the SKEPTIC lane's failure-handling layer.

`engine.petriarium.process_moment` swallows every exception and silently falls
back to a canned response. That's the wrong behavior for a hackathon entry
that sells "honest small models" — a user with a broken Ollama install has no
way to know their creature is improvising.

This module is a drop-in replacement that:

  1. Catches the same exceptions, but tags the result with `fallback_used: True`
     and an `error: str` so the UI can show it.
  2. Measures latency and exposes it on the result, so a slow model is obvious.
  3. Does NOT write the fallback response to the receipts table as if it were
     real. The event is logged with `fallback: true` in the payload so the
     history stays auditable, but the receipt shelf is not polluted.
  4. Retries the chat call once on `requests.exceptions.HTTPError` (5xx) before
     falling back, because Ollama sometimes 500s on the first call after
     loading a model.

It returns a `GuardedMoment` that is a superset of the original `result` dict
— the integrator can pass it to `render_status` and `render_state_panel` with
no shape change for the happy path.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

import requests

from . import petriarium
from .creature_store import CreatureStore


RETRYABLE_HTTP_STATUS = {500, 502, 503, 504}


@dataclass
class GuardedMoment:
    moment: str
    response_text: str
    memory: dict[str, Any]
    artifact: dict[str, Any] | None
    state: dict[str, Any]
    entry_id: int | None
    memory_id: int | None
    artifact_id: int | None
    fallback_used: bool = False
    error: str = ""
    latency_ms: int = 0
    backend: str = ""
    model: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_status_dict(self) -> dict[str, Any]:
        out = {
            "moment": self.moment,
            "response_text": self.response_text,
            "memory": self.memory,
            "state": self.state,
            "fallback_used": self.fallback_used,
            "error": self.error,
            "latency_ms": self.latency_ms,
            "backend": self.backend,
            "model": self.model,
        }
        if self.artifact is not None:
            out["artifact"] = self.artifact
        else:
            out["artifact"] = {
                "title": "(no artifact — model was unavailable)",
                "kind": "stub",
                "tags": [],
                "inscription": "",
                "svg": "",
            }
        return out


def _runtime_backend() -> str:
    if os.environ.get("PETRIARIUM_RUNTIME", "llama").lower() == "ollama":
        return "ollama"
    return "llama.cpp"


def _chat_with_retry(prompt: str, model: str) -> tuple[str, bool, str, int]:
    """Call `petriarium.chat` with one retry on retryable HTTP errors.

    Returns (raw_text, ok, error, latency_ms). On any failure, raw_text is ""
    and ok is False.
    """
    started = time.perf_counter()
    backend = _runtime_backend()
    last_error = ""
    for attempt in range(2):
        try:
            raw = petriarium.chat(petriarium.SYSTEM, prompt, model=model)
            latency_ms = int((time.perf_counter() - started) * 1000)
            return raw, True, "", latency_ms
        except requests.exceptions.HTTPError as exc:
            last_error = f"HTTP {exc.response.status_code if exc.response is not None else '?'} from {backend}"
            if exc.response is not None and exc.response.status_code in RETRYABLE_HTTP_STATUS and attempt == 0:
                continue
            latency_ms = int((time.perf_counter() - started) * 1000)
            return "", False, last_error, latency_ms
        except Exception as exc:  # noqa: BLE001 — we report the error to the UI
            name = type(exc).__name__
            msg = str(exc) or "unknown error"
            if len(msg) > 140:
                msg = msg[:137] + "…"
            latency_ms = int((time.perf_counter() - started) * 1000)
            return "", False, f"{name}: {msg}", latency_ms
    latency_ms = int((time.perf_counter() - started) * 1000)
    return "", False, last_error, latency_ms


def _emit_fallback_event(store: CreatureStore, moment: str, error: str) -> None:
    """Record a fallback event in the append-only events log without polluting
    the receipts or memories tables."""
    import json
    store.conn.execute(
        "INSERT INTO events (ts, kind, payload_json) VALUES (?, ?, ?)",
        (
            time.time(),
            "fallback",
            json.dumps(
                {
                    "moment": moment,
                    "error": error,
                    "fallback": True,
                },
                sort_keys=True,
            ),
        ),
    )
    store.conn.commit()


def process_moment_guarded(
    moment: str,
    store: CreatureStore,
    model: str | None = None,
) -> GuardedMoment:
    """Drop-in replacement for `petriarium.process_moment` that surfaces failures.

    On the happy path the return shape mirrors the original `result` dict and
    `fallback_used` is False. On failure the response is the engine's
    `normalize_model_result` fallback, but `fallback_used` is True, `error` is
    populated, and no entry/memory/artifact rows are written to SQLite.
    """
    moment = (moment or "").strip()
    if not moment:
        raise ValueError("moment is empty")

    chosen_model = model or petriarium.DEFAULT_MODEL
    backend = _runtime_backend()
    state = store.state()
    prompt = petriarium.build_prompt(state, store.recent_memories(), moment)

    raw, ok, error, latency_ms = _chat_with_retry(prompt, chosen_model)
    parsed = petriarium._extract_json(raw) if ok else None
    if ok and parsed is None:
        ok = False
        error = error or "model returned no parseable JSON"

    if not ok:
        _emit_fallback_event(store, moment, error or "unknown error")
        fallback = petriarium.normalize_model_result(None, moment)
        return GuardedMoment(
            moment=moment,
            response_text=fallback["response_text"],
            memory=fallback["memory_proposal"],
            artifact=None,
            state={"mood": fallback["mood"], "form": state.form, "name": state.name},
            entry_id=None,
            memory_id=None,
            artifact_id=None,
            fallback_used=True,
            error=error,
            latency_ms=latency_ms,
            backend=backend,
            model=chosen_model,
        )

    normalized = petriarium.normalize_model_result(parsed, moment)
    tags = normalized["memory_proposal"]["tags"]
    artifact = petriarium.make_artifact(moment, state, normalized)
    result = store.add_moment(
        text=moment,
        tags=tags,
        mood=normalized["mood"],
        response_text=normalized["response_text"],
        memory_summary=normalized["memory_proposal"]["summary"],
        artifact=artifact,
    )
    return GuardedMoment(
        moment=moment,
        response_text=normalized["response_text"],
        memory=normalized["memory_proposal"],
        artifact=artifact,
        state={
            "mood": normalized["mood"],
            "form": result.state.form,
            "name": result.state.name,
        },
        entry_id=result.entry_id,
        memory_id=result.memory_id,
        artifact_id=result.artifact_id,
        fallback_used=False,
        error="",
        latency_ms=latency_ms,
        backend=backend,
        model=chosen_model,
    )
