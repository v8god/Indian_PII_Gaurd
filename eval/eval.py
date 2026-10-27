"""Evaluation harness for indian-pii-guard.

Computes exact entity-level precision, recall, and F1 per identifier type
and overall against a synthetic evaluation dataset. Writes failure report
to eval/failures.md.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Ensure src/ is importable even without pip install -e .
_SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from pii_guard import find_spans
from pii_guard.detectors import TYPE_AADHAAR, TYPE_MOBILE, TYPE_PAN


@dataclass
class TypeMetrics:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def precision(self) -> float:
        total_pred = self.tp + self.fp
        return (self.tp / total_pred) if total_pred > 0 else (1.0 if self.fn == 0 else 0.0)

    @property
    def recall(self) -> float:
        total_gold = self.tp + self.fn
        return (self.tp / total_gold) if total_gold > 0 else 1.0

    @property
    def f1(self) -> float:
        p = self.precision
        r = self.recall
        return (2 * p * r / (p + r)) if (p + r) > 0 else 0.0


@dataclass
class FailureDetail:
    record_id: str
    category: str
    failure_type: str  # "FALSE_POSITIVE" or "FALSE_NEGATIVE"
    entity_type: str
    span_range: tuple[int, int]
    matched_text: str
    full_text: str
    expected_behavior: str
    known_limitation: bool


def calculate_metrics_for_sets(
    gold_spans_by_type: dict[str, set[tuple[int, int]]],
    pred_spans_by_type: dict[str, set[tuple[int, int]]],
    types: list[str],
) -> dict[str, TypeMetrics]:
    """Calculate exact entity-level TP, FP, FN metrics per type and overall."""
    results: dict[str, TypeMetrics] = {t: TypeMetrics() for t in types}
    overall = TypeMetrics()

    for t in types:
        gold = gold_spans_by_type.get(t, set())
        pred = pred_spans_by_type.get(t, set())

        tp = len(gold & pred)
        fp = len(pred - gold)
        fn = len(gold - pred)

        results[t].tp += tp
        results[t].fp += fp
        results[t].fn += fn

        overall.tp += tp
        overall.fp += fp
        overall.fn += fn

    results["OVERALL"] = overall
    return results


def run_evaluation(
    dataset_path: str,
    failures_output_path: str | None = None,
) -> tuple[dict[str, TypeMetrics], list[FailureDetail]]:
    """Run evaluation against a synthetic jsonl dataset.

    Args:
        dataset_path: Path to synthetic.jsonl file.
        failures_output_path: Optional path to write failures.md.

    Returns:
        Tuple of (metrics_by_type, list_of_failures).
    """
    types = [TYPE_AADHAAR, TYPE_PAN, TYPE_MOBILE]
    metrics = {t: TypeMetrics() for t in types}
    overall = TypeMetrics()
    failures: list[FailureDetail] = []

    with open(dataset_path, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    for record in records:
        text = record["text"]
        gold_spans = {(s["type"], s["start"], s["end"]) for s in record["spans"]}

        predicted_spans_list = find_spans(text)
        pred_spans = {(s.type, s.start, s.end) for s in predicted_spans_list}

        tp_set = gold_spans & pred_spans
        fp_set = pred_spans - gold_spans
        fn_set = gold_spans - pred_spans

        for t, start, end in tp_set:
            if t in metrics:
                metrics[t].tp += 1
            overall.tp += 1

        for t, start, end in fp_set:
            if t in metrics:
                metrics[t].fp += 1
            overall.fp += 1
            failures.append(
                FailureDetail(
                    record_id=record["id"],
                    category=record["category"],
                    failure_type="FALSE_POSITIVE",
                    entity_type=t,
                    span_range=(start, end),
                    matched_text=text[start:end],
                    full_text=text,
                    expected_behavior=record.get("expected_behavior", ""),
                    known_limitation=record.get("known_limitation", False),
                )
            )

        for t, start, end in fn_set:
            if t in metrics:
                metrics[t].fn += 1
            overall.fn += 1
            failures.append(
                FailureDetail(
                    record_id=record["id"],
                    category=record["category"],
                    failure_type="FALSE_NEGATIVE",
                    entity_type=t,
                    span_range=(start, end),
                    matched_text=text[start:end],
                    full_text=text,
                    expected_behavior=record.get("expected_behavior", ""),
                    known_limitation=record.get("known_limitation", False),
                )
            )

    metrics["OVERALL"] = overall

    if failures_output_path:
        write_failures_report(failures, metrics, len(records), failures_output_path)

    return metrics, failures


def write_failures_report(
    failures: list[FailureDetail],
    metrics: dict[str, TypeMetrics],
    total_samples: int,
    output_path: str,
) -> None:
    """Format and write failures.md report."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Evaluation Failure Report — indian-pii-guard\n\n")
        f.write(f"Total synthetic evaluation lines evaluated: **{total_samples}**\n\n")

        # Summary Table
        f.write("## Metric Summary\n\n")
        f.write("| Type | TP | FP | FN | Precision | Recall | F1 |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for t in [TYPE_AADHAAR, TYPE_PAN, TYPE_MOBILE, "OVERALL"]:
            m = metrics[t]
            f.write(
                f"| {t} | {m.tp} | {m.fp} | {m.fn} | "
                f"{m.precision:.4f} | {m.recall:.4f} | {m.f1:.4f} |\n"
            )
        f.write("\n---\n\n")

        # Failure Details
        f.write(f"## Failure Details ({len(failures)} total failures)\n\n")
        if not failures:
            f.write("Zero failures recorded on this dataset.\n")
            return

        for idx, fail in enumerate(failures, start=1):
            limitation_badge = " *(Known Limitation)*" if fail.known_limitation else ""
            f.write(f"### {idx}. [{fail.failure_type}] {fail.entity_type} in `{fail.record_id}`{limitation_badge}\n\n")
            f.write(f"- **Category:** `{fail.category}`\n")
            f.write(f"- **Expected behavior:** {fail.expected_behavior}\n")
            f.write(f"- **Span offset:** `[{fail.span_range[0]}, {fail.span_range[1]})`\n")
            f.write(f"- **Matched slice:** `{fail.matched_text}`\n")
            f.write(f"- **Line text:** `{fail.full_text}`\n")
            f.write(f"- **Known limitation:** `{fail.known_limitation}`\n\n")


def print_metrics_table(metrics: dict[str, TypeMetrics]) -> None:
    """Print formatted markdown metrics table to stdout."""
    header = "| Type | TP | FP | FN | Precision | Recall | F1 |"
    divider = "|---|---|---|---|---|---|---|"
    print(header)
    print(divider)
    for t in [TYPE_AADHAAR, TYPE_PAN, TYPE_MOBILE, "OVERALL"]:
        m = metrics[t]
        print(
            f"| {t:8s} | {m.tp:4d} | {m.fp:4d} | {m.fn:4d} | "
            f"{m.precision:9.4f} | {m.recall:6.4f} | {m.f1:6.4f} |"
        )


def main() -> int:
    """Run evaluation from command line."""
    parser = argparse.ArgumentParser(description="Evaluate indian-pii-guard detector accuracy")
    parser.add_argument(
        "--dataset",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "data", "synthetic.jsonl"),
        help="Path to synthetic jsonl evaluation dataset",
    )
    parser.add_argument(
        "--failures",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "failures.md"),
        help="Path to write failures markdown report",
    )
    args = parser.parse_args()

    metrics, failures = run_evaluation(args.dataset, args.failures)
    print_metrics_table(metrics)
    print(f"\nFailures written to: {args.failures} ({len(failures)} failures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

