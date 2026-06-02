"""Generate synthetic 'confusing document' images to test the explainer without
using anyone's real private mail. Renders a believable medical bill as a PNG.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _font(size: int):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_medical_bill(out_path: Path) -> Path:
    W, H = 850, 1100
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    big, mid, sm, tiny = _font(30), _font(20), _font(16), _font(12)

    d.text((50, 40), "MERIDIAN REGIONAL HEALTH SYSTEM", font=big, fill="black")
    d.text((50, 78), "Patient Financial Services  |  PO Box 88213, Dept 4471", font=sm, fill="black")
    d.line((50, 110, W - 50, 110), fill="black", width=2)

    d.text((50, 130), "STATEMENT OF PATIENT RESPONSIBILITY", font=mid, fill="black")
    d.text((50, 165), "Statement Date: 05/18/2026     Account: MRH-77-204918", font=sm, fill="black")
    d.text((50, 188), "Guarantor: J. DOE     Service Date(s): 04/02/2026", font=sm, fill="black")

    rows = [
        ("CPT 99284", "EMERGENCY DEPT VISIT, HIGH COMPLEX", "$1,840.00"),
        ("CPT 80053", "METABOLIC PANEL, COMPREHENSIVE", "$212.00"),
        ("CPT 71046", "RADIOLOGIC EXAM, CHEST, 2 VIEWS", "$398.00"),
        ("ADJ-PPO", "CONTRACTUAL ADJUSTMENT (PLAN)", "-$1,604.00"),
        ("PMT-INS", "INSURANCE PAYMENT RECEIVED", "-$498.40"),
    ]
    y = 240
    d.text((50, y), "CODE", font=sm, fill="black")
    d.text((200, y), "DESCRIPTION", font=sm, fill="black")
    d.text((680, y), "AMOUNT", font=sm, fill="black")
    y += 24
    d.line((50, y, W - 50, y), fill="gray", width=1)
    y += 12
    for code, desc, amt in rows:
        d.text((50, y), code, font=sm, fill="black")
        d.text((200, y), desc, font=sm, fill="black")
        d.text((680, y), amt, font=sm, fill="black")
        y += 30

    y += 10
    d.line((50, y, W - 50, y), fill="black", width=2)
    y += 16
    d.text((430, y), "AMOUNT DUE BY PATIENT:", font=mid, fill="black")
    d.text((680, y), "$747.60", font=mid, fill="black")
    y += 50
    d.rectangle((50, y, W - 50, y + 46), outline="black", width=2)
    d.text((60, y + 12), "PAYMENT DUE: 06/12/2026 — A $35.00 LATE FEE APPLIES AFTER DUE DATE.",
           font=sm, fill="black")

    y += 90
    fine = [
        "This is not a bill from your insurance company. Amounts shown reflect patient",
        "responsibility after plan adjudication. If you believe this was processed in error,",
        "you must submit a written dispute within 30 days. Accounts unpaid after 90 days may",
        "be referred to a third-party collection agency. To set up a payment plan, call the",
        "number on the reverse. Paperless enrollment auto-renews unless cancelled in writing.",
    ]
    for line in fine:
        d.text((50, y), line, font=tiny, fill="black")
        y += 18

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "sample_docs" / "medical_bill.png"
    p = make_medical_bill(out)
    print(f"wrote {p}  ({p.stat().st_size} bytes)")
