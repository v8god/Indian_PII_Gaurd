"""Unit tests for deterministic span overlap resolution."""

import pytest
from pii_guard.detectors import (
    CandidateSpan,
    Span,
    TYPE_AADHAAR,
    TYPE_MOBILE,
    TYPE_PAN,
    detect_all_candidates,
)
from pii_guard.resolve import resolve_overlaps
from pii_guard.verhoeff import generate_check_digit


def test_resolve_empty_list():
    assert resolve_overlaps([]) == []


def test_resolve_non_overlapping_candidates_preserved_sorted():
    candidates = [
        CandidateSpan(type=TYPE_PAN, start=20, end=30, strictness=2),
        CandidateSpan(type=TYPE_AADHAAR, start=0, end=14, strictness=3),
    ]
    resolved = resolve_overlaps(candidates)
    assert resolved == [
        Span(type=TYPE_AADHAAR, start=0, end=14),
        Span(type=TYPE_PAN, start=20, end=30),
    ]


def test_resolve_adjacent_touching_spans_do_not_conflict():
    # Spans touching at index 10: [0, 10) and [10, 20)
    candidates = [
        CandidateSpan(type=TYPE_AADHAAR, start=0, end=10, strictness=3),
        CandidateSpan(type=TYPE_MOBILE, start=10, end=20, strictness=1),
    ]
    resolved = resolve_overlaps(candidates)
    assert len(resolved) == 2
    assert resolved[0] == Span(type=TYPE_AADHAAR, start=0, end=10)
    assert resolved[1] == Span(type=TYPE_MOBILE, start=10, end=20)


def test_resolve_strictness_priority():
    # Aadhaar (strictness 3) vs Mobile (strictness 1) on overlapping span
    candidates = [
        CandidateSpan(type=TYPE_MOBILE, start=0, end=15, strictness=1),
        CandidateSpan(type=TYPE_AADHAAR, start=0, end=14, strictness=3),
    ]
    resolved = resolve_overlaps(candidates)
    assert len(resolved) == 1
    assert resolved[0].type == TYPE_AADHAAR
    assert resolved[0].start == 0
    assert resolved[0].end == 14


def test_resolve_length_priority_when_strictness_equal():
    # Equal strictness: longer span should win
    candidates = [
        CandidateSpan(type="TYPE_A", start=5, end=15, strictness=2),  # length 10
        CandidateSpan(type="TYPE_B", start=2, end=16, strictness=2),  # length 14
    ]
    resolved = resolve_overlaps(candidates)
    assert len(resolved) == 1
    assert resolved[0].type == "TYPE_B"
    assert resolved[0].start == 2
    assert resolved[0].end == 16


def test_resolve_start_priority_when_strictness_and_length_equal():
    # Equal strictness and length: earlier start should win
    candidates = [
        CandidateSpan(type="LATER", start=5, end=15, strictness=2),
        CandidateSpan(type="EARLIER", start=3, end=13, strictness=2),
    ]
    resolved = resolve_overlaps(candidates)
    assert len(resolved) == 1
    assert resolved[0].type == "EARLIER"
    assert resolved[0].start == 3
    assert resolved[0].end == 13


def test_aadhaar_vs_mobile_91_prefix_ambiguity_when_verhoeff_passes():
    # Construct a 12-digit string starting with 91 followed by 10 digits starting with 6-9
    # which also passes the Verhoeff checksum.
    # 91 + 9 (starts mobile) + 8 digits + check digit = 12 digits
    prefix_11 = "91987654321"
    check = generate_check_digit(prefix_11)
    val = prefix_11 + check  # e.g., '919876543210'-style valid Aadhaar

    # Both detectors match this text
    candidates = detect_all_candidates(val)
    types = {c.type for c in candidates}
    assert TYPE_AADHAAR in types
    assert TYPE_MOBILE in types

    # Resolution must pick Aadhaar due to checksum strictness
    resolved = resolve_overlaps(candidates)
    assert len(resolved) == 1
    assert resolved[0].type == TYPE_AADHAAR
    assert resolved[0].start == 0
    assert resolved[0].end == 12


def test_aadhaar_vs_mobile_91_prefix_ambiguity_when_verhoeff_fails():
    # Construct 12 digits: 91 + 10 digits starting 6-9, but corrupt check digit so it fails Verhoeff
    prefix_11 = "91987654321"
    real_check = generate_check_digit(prefix_11)
    corrupt_check = "0" if real_check != "0" else "1"
    val = prefix_11 + corrupt_check

    candidates = detect_all_candidates(val)
    # Aadhaar should reject it due to failed Verhoeff
    assert not any(c.type == TYPE_AADHAAR for c in candidates)
    # Mobile should detect it
    assert any(c.type == TYPE_MOBILE for c in candidates)

    resolved = resolve_overlaps(candidates)
    assert len(resolved) == 1
    assert resolved[0].type == TYPE_MOBILE

