"""Model A/B evaluation harness — pick the WARMEST small model for the companion.

We run the SAME simulated week (reused from run_confidant.py) through reflect()
for several local models, each with its own fresh JournalStore so memory is fair.
Then we print reflections/questions/callbacks side by side per day and compute a
few crude heuristic scores so a human can pick the warmest, most specific model.

Everything is on-device: ollama chat + ollama embeddings. No cloud calls.

Usage: python tests/model_eval.py            # all four candidate models
       python tests/model_eval.py qwen3:8b   # just one (debugging)

The heuristics are deliberately simple and honest — they are a WARMTH PROXY, not a
ground truth. Final call should still be eyeballed against the printed transcripts.
"""
from __future__ import annotations

import re
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.store import JournalStore  # noqa: E402
from engine.confidant import reflect, Reflection  # noqa: E402

# Reuse the exact simulated week from run_confidant.py — two recurring threads:
#   - the dentist (dread day 2 -> relief day 5)
#   - a side project (excited/overwhelmed day 1 -> progress day 4 -> doubt day 6)
WEEK = [
    ("2026-06-01", "Started a little side project tonight, a tiny app idea I've had for months. "
                   "Excited but honestly a bit overwhelmed — there's so much I don't know yet."),
    ("2026-06-02", "Have a dentist appointment Thursday and I'm dreading it. I always put these off. "
                   "Probably nothing, but my stomach knots up just thinking about the chair."),
    ("2026-06-03", "Rough one at work. I snapped at a coworker over something small and felt awful "
                   "the rest of the day. Not proud of that."),
    ("2026-06-04", "Spent an hour on the side project and actually got something working. First time "
                   "in a while I lost track of time. Felt good to make a thing again."),
    ("2026-06-05", "Dentist is done. It was completely fine — a cleaning and out in 30 minutes. "
                   "All that dread for nothing. Relieved more than anything."),
    ("2026-06-06", "Wondering if I should keep going on the project or let it fizzle like the others. "
                   "Part of me is tired. Part of me doesn't want to quit on it this time."),
]

# Candidate models. minicpm-v is the OpenBMB sponsor model (text use is fine here).
MODELS = ["qwen3:8b", "gemma4:e4b", "qwen3.5:9b", "minicpm-v:latest"]
SPONSOR_MODEL = "minicpm-v:latest"

# Warmth proxy: too short reads cold/curt; too long reads preachy/lecturing.
LONG_REFLECTION_WORDS = 60

# Words we ignore when scoring "did the reflection reuse the person's concrete nouns?"
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "to", "of", "in", "on", "at", "for",
    "with", "is", "are", "was", "were", "be", "been", "it", "its", "this", "that",
    "these", "those", "i", "you", "your", "youre", "im", "me", "my", "we", "they",
    "them", "their", "he", "she", "his", "her", "as", "so", "do", "did", "does",
    "have", "has", "had", "not", "no", "yes", "from", "about", "out", "up", "down",
    "over", "than", "then", "there", "here", "what", "when", "how", "why", "who",
    "all", "any", "some", "more", "most", "just", "like", "feel", "felt", "feels",
    "thing", "things", "got", "get", "going", "went", "day", "today", "really",
    "much", "something", "nothing", "part", "first", "time", "still", "would",
    "could", "should", "can", "will", "one", "little", "bit",
}

_WORD_RE = re.compile(r"[a-z0-9']+")


def _words(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _content_nouns(text: str) -> set[str]:
    """Crude 'concrete words' set: tokens >=4 chars that aren't stopwords."""
    return {w for w in _words(text) if len(w) >= 4 and w not in _STOPWORDS}


def _count_questions(text: str) -> int:
    """How many '?'-terminated sentences. Persona wants exactly one."""
    return text.count("?")


@dataclass
class DayResult:
    day: str
    entry: str
    refl: Reflection
    refl_words: int
    n_questions: int
    callback_fired: bool
    specificity: float  # fraction of reflection's content words that echo the entry
    error: str = ""


@dataclass
class ModelResult:
    model: str
    days: list[DayResult] = field(default_factory=list)
    errors: int = 0

    # ---- aggregate scores (computed over successful days only) ----
    def _ok_days(self) -> list[DayResult]:
        return [d for d in self.days if not d.error]

    @property
    def avg_refl_words(self) -> float:
        ok = self._ok_days()
        return sum(d.refl_words for d in ok) / len(ok) if ok else 0.0

    @property
    def exactly_one_q_rate(self) -> float:
        ok = self._ok_days()
        return sum(1 for d in ok if d.n_questions == 1) / len(ok) if ok else 0.0

    @property
    def callbacks_fired(self) -> int:
        return sum(1 for d in self._ok_days() if d.callback_fired)

    @property
    def avg_specificity(self) -> float:
        ok = self._ok_days()
        return sum(d.specificity for d in ok) / len(ok) if ok else 0.0

    @property
    def too_long_count(self) -> int:
        return sum(1 for d in self._ok_days() if d.refl_words > LONG_REFLECTION_WORDS)


def run_model(model: str) -> ModelResult:
    """Run the full simulated week through one model with a fresh, isolated store."""
    db = Path(tempfile.mkdtemp()) / "week.db"
    store = JournalStore(db)
    result = ModelResult(model=model)

    for day, text in WEEK:
        try:
            r = reflect(text, store=store, model=model)
        except Exception as exc:  # network/model error — record and keep going
            result.errors += 1
            result.days.append(DayResult(
                day=day, entry=text, refl=Reflection("", "", "", model),
                refl_words=0, n_questions=0, callback_fired=False,
                specificity=0.0, error=f"{type(exc).__name__}: {exc}",
            ))
            continue

        # Persist today's entry (with response) so later days can recall it — exactly
        # as the real app does, so the memory-callback test is fair across models.
        ts = time.mktime(time.strptime(day, "%Y-%m-%d"))
        try:
            store.add(text, day=day, ts=ts, reflection=r.reflection, question=r.question)
        except Exception:
            pass  # embedding failure degrades recall only; don't abort the run

        entry_nouns = _content_nouns(text)
        refl_nouns = _content_nouns(r.reflection)
        overlap = entry_nouns & refl_nouns
        specificity = (len(overlap) / len(refl_nouns)) if refl_nouns else 0.0

        result.days.append(DayResult(
            day=day, entry=text, refl=r,
            refl_words=len(_words(r.reflection)),
            n_questions=_count_questions(r.question),
            callback_fired=bool(r.callback.strip()),
            specificity=specificity,
        ))

    store.close()
    return result


def _wrap(text: str, width: int = 76, indent: str = "        ") -> str:
    import textwrap
    if not text:
        return indent + "(none)"
    return textwrap.fill(text, width=width, initial_indent=indent, subsequent_indent=indent)


def print_per_day(results: list[ModelResult]) -> None:
    """For each day, show every model's reflection/question/callback side by side."""
    for di, (day, text) in enumerate(WEEK):
        print("=" * 88)
        print(f"DAY {day}")
        print(_wrap(text, indent="  you : "))
        print("-" * 88)
        for mr in results:
            dr = mr.days[di]
            print(f"  [{mr.model}]")
            if dr.error:
                print(f"        ERROR: {dr.error}")
                print()
                continue
            print(_wrap(dr.refl.reflection, indent="   refl  : "))
            print(_wrap(dr.refl.question, indent="   ask   : "))
            cb = dr.refl.callback.strip()
            print(_wrap(cb if cb else "(no callback)", indent="   recall: "))
            flags = []
            flags.append(f"{dr.refl_words}w" + (" TOO-LONG" if dr.refl_words > LONG_REFLECTION_WORDS else ""))
            flags.append("1Q" if dr.n_questions == 1 else f"{dr.n_questions}Q!")
            flags.append("callback" if dr.callback_fired else "—")
            flags.append(f"spec {dr.specificity:.2f}")
            print(f"        [{'  '.join(flags)}]")
            print()
    print("=" * 88)
    print()


def _score(mr: ModelResult) -> float:
    """Composite warmth/quality score for ranking. Higher = better.

    Honest about being a proxy. Components:
      - specificity: rewards reusing the person's actual words (the warmth signal)
      - one-question discipline: persona asks exactly ONE question
      - callbacks: the 'it remembers' magic firing at least once
      - length sweet spot: penalize too-short (cold) and too-long (preachy)
      - errors: heavy penalty
    """
    if not mr._ok_days():
        return 0.0
    score = 0.0
    score += mr.avg_specificity * 40.0
    score += mr.exactly_one_q_rate * 20.0
    score += min(mr.callbacks_fired, 3) * 5.0  # cap — 1-2 is the magic, spamming isn't
    # Length sweet spot ~18-45 words. Distance from 30 words, gently penalized.
    avg = mr.avg_refl_words
    if avg <= 0:
        length_pen = 30.0
    elif avg < 12:
        length_pen = (12 - avg) * 1.5  # too curt / cold
    elif avg > LONG_REFLECTION_WORDS:
        length_pen = (avg - LONG_REFLECTION_WORDS) * 1.0  # preachy
    else:
        length_pen = 0.0
    score -= length_pen
    score -= mr.errors * 10.0
    return score


def print_recommendation(results: list[ModelResult]) -> None:
    ranked = sorted(results, key=_score, reverse=True)

    print("#" * 88)
    print("# FINAL RECOMMENDATION — warmest small model for Pocket Confidant")
    print("#" * 88)
    print()
    header = (f"{'rank':<5}{'model':<20}{'score':>7}{'avg_words':>11}"
              f"{'1Q_rate':>9}{'callbacks':>11}{'specificity':>13}{'too_long':>10}{'errors':>8}")
    print(header)
    print("-" * len(header))
    for i, mr in enumerate(ranked, 1):
        print(f"{i:<5}{mr.model:<20}{_score(mr):>7.1f}{mr.avg_refl_words:>11.1f}"
              f"{mr.exactly_one_q_rate:>9.2f}{mr.callbacks_fired:>11d}"
              f"{mr.avg_specificity:>13.2f}{mr.too_long_count:>10d}{mr.errors:>8d}")
    print()

    best = ranked[0]
    print(f"WARMEST / MOST SPECIFIC (by heuristic): {best.model}")
    print(f"  avg reflection length {best.avg_refl_words:.0f} words, "
          f"specificity {best.avg_specificity:.2f}, "
          f"{best.callbacks_fired} memory callback(s), "
          f"asks exactly one question {best.exactly_one_q_rate*100:.0f}% of the time.")
    print()

    # Sponsor consideration.
    sponsor = next((m for m in results if m.model == SPONSOR_MODEL), None)
    print("SPONSOR CONSIDERATION (OpenBMB special category, $10k):")
    if sponsor is None:
        print(f"  {SPONSOR_MODEL} was not evaluated.")
    else:
        sponsor_rank = ranked.index(sponsor) + 1
        print(f"  {SPONSOR_MODEL} (MiniCPM, OpenBMB) ranked #{sponsor_rank} of {len(ranked)} "
              f"on raw warmth heuristics (score {_score(sponsor):.1f}).")
        if best.model == SPONSOR_MODEL:
            print("  It is ALSO the warmest — sponsor angle and quality align. Strong pick.")
        else:
            gap = _score(best) - _score(sponsor)
            print(f"  Tradeoff: the warmest model is {best.model} (lead of {gap:.1f} pts). "
                  f"Picking {SPONSOR_MODEL} chases the OpenBMB $10k category but may cost some warmth.")
            print("  Recommendation: ship the warmest model as default; document MiniCPM as a")
            print("  one-flag swappable backend so we still qualify for the sponsor badge.")
    print()
    print("NOTE: heuristics are a proxy. Read the per-day transcripts above before committing.")
    print("#" * 88)


class _Tee:
    """Mirror stdout to a report file so the full transcript is always durable
    (some harnesses/pipes drop un-flushed block-buffered output)."""

    def __init__(self, *streams):
        self._streams = streams

    def write(self, data):
        for s in self._streams:
            s.write(data)
            s.flush()
        return len(data)

    def flush(self):
        for s in self._streams:
            s.flush()


def main() -> int:
    # First arg picks a single model; "", "-", or "all" means all candidates.
    arg1 = sys.argv[1] if len(sys.argv) > 1 else ""
    models = MODELS if arg1 in ("", "-", "all") else [arg1]

    # Always mirror the full report to a file next to this script. Pass a path as a
    # second arg to override (e.g. python tests/model_eval.py qwen3:8b /tmp/eval.txt).
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent / "model_eval_report.txt"
    report_fh = open(out_path, "w")
    sys.stdout = _Tee(sys.__stdout__, report_fh)

    print(f"=== Pocket Confidant — model A/B warmth eval ===")
    print(f"models under test: {', '.join(models)}")
    print(f"(fresh isolated JournalStore per model; {len(WEEK)} simulated days each; no cloud)\n")

    results: list[ModelResult] = []
    for model in models:
        t0 = time.time()
        print(f">>> running {model} ...", flush=True)
        mr = run_model(model)
        dt = time.time() - t0
        status = f"done in {dt:.0f}s"
        if mr.errors:
            status += f" — {mr.errors} day(s) errored"
        print(f"    {status}\n", flush=True)
        results.append(mr)

    print()
    print_per_day(results)
    print_recommendation(results)
    print(f"\n(full report mirrored to {out_path})")

    sys.stdout = sys.__stdout__
    report_fh.close()

    # Exit non-zero only if EVERY model failed entirely — partial runs still useful.
    all_dead = all(not mr._ok_days() for mr in results)
    return 1 if all_dead else 0


if __name__ == "__main__":
    raise SystemExit(main())
