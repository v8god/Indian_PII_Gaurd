"""Unit tests for evaluation metric mathematics on hand-computed test cases."""

import pytest
from eval.eval import TypeMetrics, calculate_metrics_for_sets


def test_hand_computed_metrics_on_known_sets():
    # Type A:
    # Gold: {(0, 5), (10, 15)}
    # Predicted: {(0, 5), (20, 25)}
    # TP: (0, 5) => 1
    # FP: (20, 25) => 1
    # FN: (10, 15) => 1
    # Precision: 1 / 2 = 0.5
    # Recall: 1 / 2 = 0.5
    # F1: 0.5

    # Type B:
    # Gold: {(30, 40)}
    # Predicted: {(30, 40)}
    # TP: 1, FP: 0, FN: 0
    # Precision: 1.0, Recall: 1.0, F1: 1.0

    # Overall:
    # Total TP = 2
    # Total FP = 1
    # Total FN = 1
    # Overall Precision = 2 / 3
    # Overall Recall = 2 / 3
    # Overall F1 = 2 / 3

    gold_spans = {
        "TYPE_A": {(0, 5), (10, 15)},
        "TYPE_B": {(30, 40)},
    }
    pred_spans = {
        "TYPE_A": {(0, 5), (20, 25)},
        "TYPE_B": {(30, 40)},
    }

    metrics = calculate_metrics_for_sets(gold_spans, pred_spans, ["TYPE_A", "TYPE_B"])

    mA = metrics["TYPE_A"]
    assert mA.tp == 1
    assert mA.fp == 1
    assert mA.fn == 1
    assert mA.precision == pytest.approx(0.5)
    assert mA.recall == pytest.approx(0.5)
    assert mA.f1 == pytest.approx(0.5)

    mB = metrics["TYPE_B"]
    assert mB.tp == 1
    assert mB.fp == 0
    assert mB.fn == 0
    assert mB.precision == pytest.approx(1.0)
    assert mB.recall == pytest.approx(1.0)
    assert mB.f1 == pytest.approx(1.0)

    mO = metrics["OVERALL"]
    assert mO.tp == 2
    assert mO.fp == 1
    assert mO.fn == 1
    assert mO.precision == pytest.approx(2 / 3)
    assert mO.recall == pytest.approx(2 / 3)
    assert mO.f1 == pytest.approx(2 / 3)


def test_type_metrics_edge_cases_zero_division():
    # Empty predictions and empty gold
    empty = TypeMetrics(tp=0, fp=0, fn=0)
    assert empty.precision == 1.0
    assert empty.recall == 1.0
    assert empty.f1 == 1.0

    # No gold, but 1 false positive
    fp_only = TypeMetrics(tp=0, fp=1, fn=0)
    assert fp_only.precision == 0.0
    assert fp_only.recall == 1.0
    assert fp_only.f1 == 0.0

    # 1 gold, but 0 predictions (false negative only)
    fn_only = TypeMetrics(tp=0, fp=0, fn=1)
    assert fn_only.precision == 0.0
    assert fn_only.recall == 0.0
    assert fn_only.f1 == 0.0

