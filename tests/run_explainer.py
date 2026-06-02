"""End-to-end smoke test: render a synthetic confusing document, run the local
vision model on it, and print the structured explanation. Proves the engine works
before any UI exists.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import explain_document  # noqa: E402
from tests.make_sample import make_medical_bill  # noqa: E402


def main() -> int:
    img_path = Path(__file__).parent / "sample_docs" / "medical_bill.png"
    if not img_path.exists():
        make_medical_bill(img_path)
    print(f"[doc] {img_path}")

    t0 = time.time()
    exp = explain_document(img_path.read_bytes())
    dt = time.time() - t0

    print(f"[model] {exp.backend}:{exp.model}   [{dt:.1f}s]   confidence={exp.confidence}\n")
    print(f"  doc_type        : {exp.doc_type}")
    print(f"  from_who        : {exp.from_who}")
    print(f"  one_line        : {exp.one_line}")
    print(f"  amount_you_owe  : {exp.amount_you_owe}")
    print(f"  what_they_want  : {exp.what_they_want}")
    for n in exp.key_numbers:
        print(f"  key_number      : {n}")
    for dl in exp.deadlines:
        print(f"  deadline        : {dl}")
    for w in exp.watch_out:
        print(f"  watch_out       : {w}")
    print(f"  next_step       : {exp.suggested_next_step}")

    # Product contract: the model is reliable at UNDERSTANDING (type, sender, intent,
    # deadlines, traps) — NOT at exact OCR of small-print figures. We assert the former
    # and only *report* the latter, because the product never claims exact amounts.
    deadlines_blob = " ".join(exp.deadlines).lower()
    watch_blob = " ".join(exp.watch_out + [exp.what_they_want]).lower()
    checks = {
        "identified it as a bill/medical statement": any(
            w in (exp.doc_type + exp.one_line).lower()
            for w in ("bill", "medical", "health", "statement")),
        "named the sender (Meridian)": "meridian" in (exp.from_who + exp.one_line).lower(),
        "caught the payment deadline (06/12)": "12" in deadlines_blob and ("06" in deadlines_blob or "june" in deadlines_blob),
        "flagged a real trap (late fee / dispute / not-from-insurer)": any(
            w in watch_blob for w in ("late fee", "dispute", "insurance", "insurer", "collection")),
        "produced a bottom-line amount reading": exp.amount_you_owe not in ("", "none"),
    }
    # Informational only — exact OCR is explicitly out of scope for a small local model:
    exact_ok = "747" in exp.amount_you_owe
    print(f"\n[info] amount read = {exp.amount_you_owe!r}  "
          f"(ground truth $747.60; exact-match={'yes' if exact_ok else 'no — expected; flagged for human verify'})")
    print("\n[checks]")
    ok = True
    for label, passed in checks.items():
        print(f"  {'PASS' if passed else 'FAIL'}  {label}")
        ok = ok and passed
    print(f"\n{'ALL CHECKS PASSED' if ok else 'SOME CHECKS FAILED — inspect raw output below'}")
    if not ok:
        print("\n--- raw model output ---\n" + exp.raw)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
