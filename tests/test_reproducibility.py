"""Tests for synthetic dataset generator reproducibility and schema compliance."""

import json
from pathlib import Path
from eval.generate import generate_dataset

DATA_DIR = Path(__file__).resolve().parent.parent / "eval" / "data"


def test_generator_is_byte_for_byte_reproducible_given_same_seed():
    records_run1 = generate_dataset(seed=42)
    records_run2 = generate_dataset(seed=42)

    json1 = [json.dumps(r, sort_keys=True) for r in records_run1]
    json2 = [json.dumps(r, sort_keys=True) for r in records_run2]

    assert json1 == json2


def test_generator_matches_committed_dev_dataset_on_disk():
    dev_path = DATA_DIR / "synthetic.jsonl"
    assert dev_path.exists(), f"Committed file {dev_path} not found"

    with open(dev_path, "r", encoding="utf-8") as f:
        disk_records = [json.loads(line) for line in f if line.strip()]

    fresh_records = generate_dataset(seed=42)
    assert len(disk_records) == 375
    assert len(fresh_records) == 375
    assert disk_records == fresh_records


def test_generator_matches_committed_final_dataset_on_disk():
    final_path = DATA_DIR / "synthetic_final.jsonl"
    assert final_path.exists(), f"Committed file {final_path} not found"

    with open(final_path, "r", encoding="utf-8") as f:
        disk_records = [json.loads(line) for line in f if line.strip()]

    fresh_records = generate_dataset(seed=1337)
    assert len(disk_records) == 375
    assert len(fresh_records) == 375
    assert disk_records == fresh_records


def test_generator_produces_at_least_300_lines():
    records = generate_dataset(seed=42)
    assert len(records) >= 300


def test_generator_contains_at_least_30_awkward_obfuscated_cases():
    records = generate_dataset(seed=42)
    awkward = [r for r in records if r["category"] == "awkward_obfuscated"]
    assert len(awkward) >= 30
    for item in awkward:
        assert "expected_behavior" in item
        assert "known_limitation" in item


def test_all_spans_in_generated_dataset_have_valid_offsets():
    records = generate_dataset(seed=42)
    for r in records:
        text = r["text"]
        for span in r["spans"]:
            start = span["start"]
            end = span["end"]
            assert 0 <= start < end <= len(text)
            extracted = text[start:end]
            assert len(extracted) == end - start

