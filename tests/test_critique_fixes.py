"""Quick checks for the SKEPTIC lane's helper modules.

This test does not make network calls. It exercises:
  - onboarding.html helpers produce the expected DOM shapes
  - onboarding.SAMPLE_MOMENTS has at least 3 entries
  - petriarium_guarded.GuardedMoment.to_status_dict is safe when artifact is None
  - health.check_ollama against a known-unreachable port returns ok=False
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from apps.petriarium import onboarding  # noqa: E402
from engine import health  # noqa: E402
from engine import petriarium_guarded  # noqa: E402


def main() -> int:
    ok = True
    checks: dict[str, bool] = {}

    checks["SAMPLE_MOMENTS has at least 3"] = len(onboarding.SAMPLE_MOMENTS) >= 3
    checks["MOOD_LEGEND covers all 6 moods"] = set(onboarding.MOOD_LEGEND.keys()) >= {
        "bright", "shy", "buzzing", "stormy", "sleepy", "entranced"
    }
    checks["FORM_PROGRESSION has 3 stages"] = len(onboarding.FORM_PROGRESSION) == 3
    checks["TRAIT_CAPTIONS covers all 7 traits"] = set(onboarding.TRAIT_CAPTIONS.keys()) >= {
        "curiosity", "mischief", "tenderness", "orderliness", "appetite", "weirdness", "social_bond"
    }

    about = onboarding.render_about()
    legend = onboarding.render_mood_legend()
    form = onboarding.render_form_hint()
    trait_legend = onboarding.render_trait_legend()
    chips = onboarding.sample_chip_html()

    checks["render_about includes 'tiny local creature'"] = "tiny local creature" in about
    checks["render_mood_legend mentions 'bright'"] = "bright" in legend.lower()
    checks["render_form_hint mentions 'specimen'"] = "specimen" in form
    checks["render_trait_legend mentions 'curiosity'"] = "curiosity" in trait_legend
    checks["sample_chip_html includes class 'pet-sample-chip'"] = "pet-sample-chip" in chips
    checks["sample_chip_html has 4 chips"] = chips.count("pet-sample-chip") == len(onboarding.SAMPLE_MOMENTS)

    none_banner = onboarding.render_status_banner(None)
    checks["banner for None status says 'not yet checked'"] = "not yet checked" in none_banner

    class _FakeStatus:
        ok = True
        backend = "ollama"
        model = "qwen2.5:7b-instruct"
        host = "http://localhost:11434"
        latency_ms = 42
        error = ""

    ok_banner = onboarding.render_status_banner(_FakeStatus())
    checks["OK banner says 'Connected'"] = "Connected" in ok_banner
    checks["OK banner has pet-banner-ok class"] = "pet-banner-ok" in ok_banner

    class _FakeWarn:
        ok = False
        backend = "ollama"
        model = "qwen2.5:7b-instruct"
        host = "http://localhost:11434"
        latency_ms = 2003
        error = "ConnectionError: refused"

    warn_banner = onboarding.render_status_banner(_FakeWarn())
    checks["WARN banner says 'Safe mode'"] = "Safe mode" in warn_banner
    checks["WARN banner includes the error"] = "refused" in warn_banner
    checks["WARN banner has pet-banner-warn class"] = "pet-banner-warn" in warn_banner

    guarded = petriarium_guarded.GuardedMoment(
        moment="x",
        response_text="r",
        memory={"summary": "s", "tags": []},
        artifact=None,
        state={"mood": "shy"},
        entry_id=None,
        memory_id=None,
        artifact_id=None,
        fallback_used=True,
        error="simulated",
    )
    status_dict = guarded.to_status_dict()
    checks["GuardedMoment.to_status_dict has fallback_used"] = status_dict.get("fallback_used") is True
    checks["GuardedMoment.to_status_dict synthesizes a stub artifact"] = (
        status_dict["artifact"].get("title", "").startswith("(no artifact")
    )

    health.invalidate()
    bad = health.check_ollama(model="qwen2.5:7b-instruct", host="http://127.0.0.1:1")
    checks["health.check_ollama against port 1 returns ok=False"] = bad.ok is False
    checks["health.check_ollama error mentions ConnectionError"] = "ConnectionError" in bad.error

    for label, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'} {label}")
        ok = ok and passed
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
