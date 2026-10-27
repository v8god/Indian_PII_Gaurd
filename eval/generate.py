"""Deterministic synthetic dataset generator for Indian PII evaluation.

Produces labeled synthetic text samples for evaluating precision, recall,
and failure modes of Aadhaar, PAN, and Indian mobile number detectors.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path
from typing import Any

# Ensure src/ is importable even without pip install -e .
_SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from pii_guard.detectors import TYPE_AADHAAR, TYPE_MOBILE, TYPE_PAN
from pii_guard.verhoeff import generate_check_digit

VALID_PAN_HOLDERS = list("PCHFATBLJG")
ALL_LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def _make_aadhaar(rng: random.Random) -> str:
    """Generate a 12-digit valid Aadhaar-like number."""
    first = str(rng.randint(2, 9))
    rest_10 = "".join(str(rng.randint(0, 9)) for _ in range(10))
    payload = first + rest_10
    check = generate_check_digit(payload)
    return payload + check


def _make_invalid_verhoeff_aadhaar(rng: random.Random) -> str:
    """Generate a 12-digit number starting with 2-9 that fails Verhoeff."""
    first = str(rng.randint(2, 9))
    rest_10 = "".join(str(rng.randint(0, 9)) for _ in range(10))
    payload = first + rest_10
    real_check = generate_check_digit(payload)
    bad_check = str((int(real_check) + rng.randint(1, 9)) % 10)
    return payload + bad_check


def _make_pan(rng: random.Random, uppercase: bool = True) -> str:
    """Generate a valid PAN-like identifier."""
    p1 = "".join(rng.choices(ALL_LETTERS, k=3))
    holder = rng.choice(VALID_PAN_HOLDERS)
    p2 = rng.choice(ALL_LETTERS)
    digits = "".join(str(rng.randint(0, 9)) for _ in range(4))
    last = rng.choice(ALL_LETTERS)
    pan = f"{p1}{holder}{p2}{digits}{last}"
    return pan if uppercase else pan.lower()


def _make_mobile_10(rng: random.Random) -> str:
    """Generate 10 digits starting with 6-9."""
    first = str(rng.randint(6, 9))
    rest = "".join(str(rng.randint(0, 9)) for _ in range(9))
    return first + rest


def generate_dataset(seed: int = 42, count: int = 350) -> list[dict[str, Any]]:
    """Generate deterministic synthetic test samples.

    Args:
        seed: Random seed for 100% reproducible data.
        count: Minimum number of samples to generate (at least 300).

    Returns:
        A list of dictionary objects conforming to the synthetic data schema.
    """
    rng = random.Random(seed)
    items: list[dict[str, Any]] = []
    item_id = 1

    def add_item(
        category: str,
        text: str,
        spans: list[dict[str, Any]],
        expected_behavior: str,
        known_limitation: bool = False,
    ) -> None:
        nonlocal item_id
        items.append(
            {
                "id": f"syn-{item_id:04d}",
                "category": category,
                "text": text,
                "spans": spans,
                "expected_behavior": expected_behavior,
                "known_limitation": known_limitation,
            }
        )
        item_id += 1

    # 1. Positives: Aadhaar (55 items)
    aadhaar_templates = [
        "Customer provided Aadhaar {val} for KYC verification.",
        "Please note UIDAI number {val} on the registration form.",
        "Aadhaar card copy with number {val} verified by agent.",
        "The applicant's identity proof is {val}.",
        "Record updated: Aadhaar {val}.",
    ]
    for _ in range(55):
        raw = _make_aadhaar(rng)
        fmt_choice = rng.choice(["plain", "space", "hyphen"])
        if fmt_choice == "space":
            val = f"{raw[:4]} {raw[4:8]} {raw[8:]}"
        elif fmt_choice == "hyphen":
            val = f"{raw[:4]}-{raw[4:8]}-{raw[8:]}"
        else:
            val = raw

        template = rng.choice(aadhaar_templates)
        start = template.find("{val}")
        text = template.replace("{val}", val)
        end = start + len(val)
        add_item(
            "positive_aadhaar",
            text,
            [{"type": TYPE_AADHAAR, "start": start, "end": end}],
            "detect_aadhaar",
        )

    # 2. Positives: PAN (55 items)
    pan_templates = [
        "Income tax return filed under PAN {val}.",
        "Bank account opened using PAN card {val}.",
        "Permanent Account Number is {val} as per records.",
        "Verify tax deduction certificate for {val}.",
        "PAN {val} verified on NSDL portal.",
    ]
    for _ in range(55):
        case_choice = rng.choice(["upper", "lower", "mixed"])
        if case_choice == "upper":
            val = _make_pan(rng, uppercase=True)
        elif case_choice == "lower":
            val = _make_pan(rng, uppercase=False)
        else:
            raw_pan = _make_pan(rng, uppercase=True)
            val = "".join(c.lower() if rng.random() > 0.5 else c for c in raw_pan)

        template = rng.choice(pan_templates)
        start = template.find("{val}")
        text = template.replace("{val}", val)
        end = start + len(val)
        add_item(
            "positive_pan",
            text,
            [{"type": TYPE_PAN, "start": start, "end": end}],
            "detect_pan",
        )

    # 3. Positives: Mobile (55 items)
    mobile_templates = [
        "Call customer service on {val} between 9 AM and 6 PM.",
        "OTP sent to registered mobile {val}.",
        "User confirmed contact number is {val}.",
        "Delivery executive will call {val} before arrival.",
        "Emergency phone: {val}.",
    ]
    for _ in range(55):
        m10 = _make_mobile_10(rng)
        fmt = rng.choice(
            [
                "plain",
                "split_space",
                "split_hyphen",
                "plus91_plain",
                "plus91_space",
                "plus91_hyphen",
                "plus91_split",
                "91_space",
                "91_plain",
                "zero_plain",
                "zero_space",
            ]
        )
        if fmt == "plain":
            val = m10
        elif fmt == "split_space":
            val = f"{m10[:5]} {m10[5:]}"
        elif fmt == "split_hyphen":
            val = f"{m10[:5]}-{m10[5:]}"
        elif fmt == "plus91_plain":
            val = f"+91{m10}"
        elif fmt == "plus91_space":
            val = f"+91 {m10}"
        elif fmt == "plus91_hyphen":
            val = f"+91-{m10}"
        elif fmt == "plus91_split":
            val = f"+91 {m10[:5]}-{m10[5:]}"
        elif fmt == "91_space":
            val = f"91 {m10}"
        elif fmt == "91_plain":
            val = f"91{m10}"
        elif fmt == "zero_plain":
            val = f"0{m10}"
        else:
            val = f"0 {m10}"

        template = rng.choice(mobile_templates)
        start = template.find("{val}")
        text = template.replace("{val}", val)
        end = start + len(val)
        add_item(
            "positive_mobile",
            text,
            [{"type": TYPE_MOBILE, "start": start, "end": end}],
            "detect_mobile",
        )

    # 4. Positives: Multi-entity lines (30 items)
    for _ in range(30):
        aadhaar_val = _make_aadhaar(rng)
        pan_val = _make_pan(rng, uppercase=True)
        mob_val = f"+91 {rng.choice(['9', '8', '7', '6'])}{rng.randint(100000000, 999999999)}"

        pattern_choice = rng.choice(["aadhaar_pan", "aadhaar_mob", "pan_mob", "all_three"])
        if pattern_choice == "aadhaar_pan":
            text = f"Primary UID {aadhaar_val} linked with PAN {pan_val}."
            s1 = text.find(aadhaar_val)
            s2 = text.find(pan_val)
            spans = [
                {"type": TYPE_AADHAAR, "start": s1, "end": s1 + len(aadhaar_val)},
                {"type": TYPE_PAN, "start": s2, "end": s2 + len(pan_val)},
            ]
        elif pattern_choice == "aadhaar_mob":
            text = f"Applicant {aadhaar_val} registered mobile {mob_val}."
            s1 = text.find(aadhaar_val)
            s2 = text.find(mob_val)
            spans = [
                {"type": TYPE_AADHAAR, "start": s1, "end": s1 + len(aadhaar_val)},
                {"type": TYPE_MOBILE, "start": s2, "end": s2 + len(mob_val)},
            ]
        elif pattern_choice == "pan_mob":
            text = f"Taxpayer {pan_val} updated contact to {mob_val}."
            s1 = text.find(pan_val)
            s2 = text.find(mob_val)
            spans = [
                {"type": TYPE_PAN, "start": s1, "end": s1 + len(pan_val)},
                {"type": TYPE_MOBILE, "start": s2, "end": s2 + len(mob_val)},
            ]
        else:
            text = f"KYC dossier: UID {aadhaar_val}, PAN {pan_val}, phone {mob_val}."
            s1 = text.find(aadhaar_val)
            s2 = text.find(pan_val)
            s3 = text.find(mob_val)
            spans = [
                {"type": TYPE_AADHAAR, "start": s1, "end": s1 + len(aadhaar_val)},
                {"type": TYPE_PAN, "start": s2, "end": s2 + len(pan_val)},
                {"type": TYPE_MOBILE, "start": s3, "end": s3 + len(mob_val)},
            ]

        # Sort spans by start offset
        spans.sort(key=lambda s: s["start"])
        add_item("positive_multi", text, spans, "detect_multi")

    # 5. Hard Negatives: Order IDs / 12-digit runs starting with 0-1 (25 items)
    for _ in range(25):
        first_d = rng.choice(["0", "1"])
        rest = "".join(str(rng.randint(0, 9)) for _ in range(11))
        order_num = first_d + rest
        text = f"Order reference #{order_num} has been dispatched via BlueDart."
        add_item("hard_negative_order_id", text, [], "reject_non_aadhaar_digits")

    # 6. Hard Negatives: Card-like 16 digits (20 items)
    for _ in range(20):
        c16 = "".join(str(rng.randint(0, 9)) for _ in range(16))
        fmt_c16 = f"{c16[:4]} {c16[4:8]} {c16[8:12]} {c16[12:]}"
        text = f"Transaction processed on card {fmt_c16} successfully."
        add_item("hard_negative_card", text, [], "reject_card_digits")

    # 7. Hard Negatives: 10 digits starting with 0-5 (20 items)
    for _ in range(20):
        bad_first = str(rng.randint(0, 5))
        d10 = bad_first + "".join(str(rng.randint(0, 9)) for _ in range(9))
        text = f"Internal tracking code {d10} generated by warehouse system."
        add_item("hard_negative_mobile_prefix", text, [], "reject_bad_mobile_prefix")

    # 8. Hard Negatives: Timestamps & dates (20 items)
    for _ in range(20):
        ts = f"20261028{rng.randint(10, 23)}{rng.randint(10, 59)}{rng.randint(10, 59)}"
        text = f"Event logged at timestamp {ts} by worker node."
        add_item("hard_negative_timestamp", text, [], "reject_timestamp")

    # 9. Hard Negatives: Malformed PAN (20 items)
    for _ in range(20):
        # Invalid 4th char (e.g. X, Z, M) or embedded
        invalid_holder = rng.choice(["X", "Z", "M", "Q", "U", "V"])
        bad_pan = f"ABC{invalid_holder}E{rng.randint(1000, 9999)}F"
        text = f"Reference ticket code {bad_pan} reviewed by compliance."
        add_item("hard_negative_pan", text, [], "reject_invalid_pan")

    # 10. Hard Negatives: Verhoeff-failing 12-digit Aadhaar candidates (20 items)
    for _ in range(20):
        failing_aadhaar = _make_invalid_verhoeff_aadhaar(rng)
        fmt = f"{failing_aadhaar[:4]} {failing_aadhaar[4:8]} {failing_aadhaar[8:]}"
        text = f"Suspicious identifier {fmt} submitted on portal."
        add_item("hard_negative_aadhaar_verhoeff", text, [], "reject_verhoeff_failing")

    # 11. Clean Text without any PII (20 items)
    clean_lines = [
        "Quarterly financial review scheduled for Monday at 10 AM.",
        "Total revenue increased by 14.5% compared to the prior fiscal year.",
        "Please bring your laptops and notebooks to the conference hall.",
        "The quick brown fox jumps over the lazy dog.",
        "Server CPU utilization is currently at 34 percent with no errors.",
        "Documentation updated to reflect latest architectural choices.",
        "Meeting minutes will be circulated by end of day.",
        "All 24 test suites passed successfully with zero warnings.",
        "Deploying release candidate version 2.4.1 to staging cluster.",
        "Weather forecast predicts cloudy skies with light rain.",
    ]
    for i in range(20):
        text = clean_lines[i % len(clean_lines)]
        add_item("clean_text", text, [], "no_pii_present")

    # 12. Obfuscated / Awkward Cases (>= 30 items)
    awkward_cases = [
        # Line-broken digits (expected: no match, known limitation)
        ("Phone number:\n98765\n43210 for inquiries.", [], "reject_line_break", True),
        ("Aadhaar:\n2345 6789\n0123 submitted.", [], "reject_line_break", True),
        ("PAN:\nABCPE\n1234F submitted.", [], "reject_line_break", True),
        # Dot-separated digits (expected: no match, known limitation)
        ("Aadhaar dot-separated: 2345.6789.0123 in table.", [], "reject_dot_separator", True),
        ("Contact mobile with dots: 98765.43210 here.", [], "reject_dot_separator", True),
        ("Alternative phone: +91.98765.43210 today.", [], "reject_dot_separator", True),
        ("Alternative phone: 91.98765.43210 listed.", [], "reject_dot_separator", True),
        # Slash-separated digits (expected: no match, known limitation)
        ("UID format: 2345/6789/0123 was scanned.", [], "reject_slash_separator", True),
        ("Call us: 98765/43210 during office hours.", [], "reject_slash_separator", True),
        # Spelled-out numbers (expected: no match, known limitation)
        ("Phone: nine eight seven six five four three two one zero.", [], "reject_words", True),
        ("Aadhaar: two three four five six seven eight nine zero one two three.", [], "reject_words", True),
        # Non-Latin (Devanagari) numerals (expected: no match, known limitation)
        ("मोबाइल नंबर: ९८७६५४३२१० संपर्क करें।", [], "reject_devanagari", True),
        ("आधार संख्या: २३४५ ६७८९ ०१२३ दर्ज की गई।", [], "reject_devanagari", True),
        # Embedded in words without boundary (expected: no match, boundary enforcement)
        ("CustomerUID234567890123registered.", [], "reject_embedded_token", False),
        ("MyIDABCPE1234Fwas verified.", [], "reject_embedded_token", False),
        ("CallMe9876543210Now.", [], "reject_embedded_token", False),
        ("ItemRef#ABCPE1234F9extra.", [], "reject_embedded_token", False),
        ("Batch123456789012345rejected.", [], "reject_embedded_token", False),
        # PII surrounded by punctuation/brackets (expected: matches inside brackets)
        (
            "Emergency contact: [9876543210] on duty.",
            [{"type": TYPE_MOBILE, "start": 20, "end": 30}],
            "detect_bracketed_mobile",
            False,
        ),
        (
            "Verified PAN: (ABCPE1234F) attached.",
            [{"type": TYPE_PAN, "start": 15, "end": 25}],
            "detect_parenthesized_pan",
            False,
        ),
        (
            "Ref 'ABCPE1234F' in quotes.",
            [{"type": TYPE_PAN, "start": 5, "end": 15}],
            "detect_quoted_pan",
            False,
        ),
        (
            "Call {9876543210} for help.",
            [{"type": TYPE_MOBILE, "start": 6, "end": 16}],
            "detect_braced_mobile",
            False,
        ),
        (
            "Query `ABCPE1234F` in backticks.",
            [{"type": TYPE_PAN, "start": 7, "end": 17}],
            "detect_backticked_pan",
            False,
        ),
        # Trailing/leading non-digit punctuation
        (
            "Contact: +91 98765-43210! Please call.",
            [{"type": TYPE_MOBILE, "start": 9, "end": 24}],
            "detect_mobile_with_exclamation",
            False,
        ),
        (
            "PAN: ABCPE1234F? Check record.",
            [{"type": TYPE_PAN, "start": 5, "end": 15}],
            "detect_pan_with_question_mark",
            False,
        ),
        (
            "Phone: +91 98765-43210.",
            [{"type": TYPE_MOBILE, "start": 7, "end": 22}],
            "detect_mobile_with_period",
            False,
        ),
        (
            "PAN: ABCPE1234F;",
            [{"type": TYPE_PAN, "start": 5, "end": 15}],
            "detect_pan_with_semicolon",
            False,
        ),
        # Non-breaking space or irregular spaces (expected: no match, known limitation)
        ("Irregular spaced Aadhaar: 2345  6789  0123 here.", [], "reject_double_spaces", True),
        ("Irregular mobile: 98765  43210 here.", [], "reject_double_spaces", True),
        ("Leading zero with spaces: 0 98765 43210 invalid spacing.", [], "reject_irregular_spaces", True),
        ("Mixed separator Aadhaar: 2345-6789 0123 invalid.", [], "reject_mixed_separators", False),
        ("Mixed separator Aadhaar: 2345 6789-0123 invalid.", [], "reject_mixed_separators", False),
        ("Hyphen before 91: -91 9876543210 rejected.", [], "reject_leading_hyphen", True),
        ("Multiple plus signs: ++91 9876543210 rejected.", [], "reject_multiple_plus", True),
        ("Parenthesized prefix: (+91) 9876543210 awkward.", [], "reject_parenthesized_prefix", True),
    ]

    for text, spans, exp_beh, limitation in awkward_cases:
        add_item("awkward_obfuscated", text, spans, exp_beh, limitation)

    return items


def main() -> int:
    """Generate and write synthetic dataset to file."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic evaluation dataset for indian-pii-guard"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic generation",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "data", "synthetic.jsonl"),
        help="Path to output jsonl file",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=350,
        help="Target number of records to generate (>= 300)",
    )
    args = parser.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    records = generate_dataset(seed=args.seed, count=args.count)

    with open(args.output, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(
        f"Generated {len(records)} records with seed {args.seed} to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
