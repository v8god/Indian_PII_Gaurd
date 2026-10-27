"""Unit tests for Indian PII candidate detectors and domain validators."""

import pytest
from pii_guard.detectors import (
    TYPE_AADHAAR,
    TYPE_MOBILE,
    TYPE_PAN,
    detect_aadhaar_candidates,
    detect_all_candidates,
    detect_mobile_candidates,
    detect_pan_candidates,
)
from pii_guard.verhoeff import generate_check_digit


# Helper to generate a valid synthetic Aadhaar string with Verhoeff check digit
def make_valid_aadhaar_payload(prefix_11: str) -> str:
    check = generate_check_digit(prefix_11)
    return prefix_11 + check


# ============================================================================
# Aadhaar Tests (FR-A)
# ============================================================================


def test_aadhaar_accepts_valid_contiguous_12_digits():
    val = make_valid_aadhaar_payload("23456789012")
    text = f"User Aadhaar is {val} in document."
    candidates = detect_aadhaar_candidates(text)
    assert len(candidates) == 1
    assert candidates[0].type == TYPE_AADHAAR
    assert text[candidates[0].start : candidates[0].end] == val


def test_aadhaar_accepts_valid_space_separated_format():
    val_raw = make_valid_aadhaar_payload("34567890123")
    val_formatted = f"{val_raw[:4]} {val_raw[4:8]} {val_raw[8:]}"
    text = f"UIDAI: {val_formatted} verified."
    candidates = detect_aadhaar_candidates(text)
    assert len(candidates) == 1
    assert candidates[0].type == TYPE_AADHAAR
    assert text[candidates[0].start : candidates[0].end] == val_formatted


def test_aadhaar_accepts_valid_hyphen_separated_format():
    val_raw = make_valid_aadhaar_payload("45678901234")
    val_formatted = f"{val_raw[:4]}-{val_raw[4:8]}-{val_raw[8:]}"
    text = f"Record: {val_formatted} attached."
    candidates = detect_aadhaar_candidates(text)
    assert len(candidates) == 1
    assert candidates[0].type == TYPE_AADHAAR
    assert text[candidates[0].start : candidates[0].end] == val_formatted


def test_aadhaar_accepts_all_valid_starting_digits_2_to_9():
    for first_digit in "23456789":
        val = make_valid_aadhaar_payload(first_digit + "1234567890")
        candidates = detect_aadhaar_candidates(val)
        assert len(candidates) == 1
        assert candidates[0].type == TYPE_AADHAAR


def test_aadhaar_rejects_starting_digit_0_and_1():
    for first_digit in "01":
        val = make_valid_aadhaar_payload(first_digit + "1234567890")
        assert len(detect_aadhaar_candidates(val)) == 0


def test_aadhaar_rejects_mixed_separators():
    val_raw = make_valid_aadhaar_payload("23456789012")
    mixed_1 = f"{val_raw[:4]} {val_raw[4:8]}-{val_raw[8:]}"
    mixed_2 = f"{val_raw[:4]}-{val_raw[4:8]} {val_raw[8:]}"
    assert len(detect_aadhaar_candidates(mixed_1)) == 0
    assert len(detect_aadhaar_candidates(mixed_2)) == 0


def test_aadhaar_rejects_verhoeff_failing_numbers():
    val = make_valid_aadhaar_payload("23456789012")
    # Corrupt the check digit
    corrupted_digit = "0" if val[-1] != "0" else "1"
    corrupted_val = val[:-1] + corrupted_digit
    assert len(detect_aadhaar_candidates(corrupted_val)) == 0


def test_aadhaar_rejects_embedded_in_longer_digit_sequence():
    val = make_valid_aadhaar_payload("23456789012")
    assert len(detect_aadhaar_candidates(f"9{val}")) == 0
    assert len(detect_aadhaar_candidates(f"{val}9")) == 0
    assert len(detect_aadhaar_candidates(f"123{val}456")) == 0


def test_aadhaar_accepts_preceding_single_digit_and_space():
    val = make_valid_aadhaar_payload("23456789012")
    formatted = f"{val[:4]} {val[4:8]} {val[8:]}"
    # Ordinary text with single digit preceding Aadhaar number
    text = f"qty 7 {formatted}"
    candidates = detect_aadhaar_candidates(text)
    assert len(candidates) == 1
    assert text[candidates[0].start : candidates[0].end] == formatted

    # Another ordinary sentence pattern
    text2 = f"Order item 1: {formatted}"
    candidates2 = detect_aadhaar_candidates(text2)
    assert len(candidates2) == 1


def test_aadhaar_rejects_16_digit_card_grouping():
    # Card format 4-4-4-4 should not have any 3-group sub-match
    card_text = "Transaction card 5365 4195 1802 3806 processed."
    assert len(detect_aadhaar_candidates(card_text)) == 0


# ============================================================================
# PAN Tests (FR-P)
# ============================================================================


def test_pan_accepts_standard_uppercase():
    text = "Account PAN is ABCPE1234F registered."
    candidates = detect_pan_candidates(text)
    assert len(candidates) == 1
    assert candidates[0].type == TYPE_PAN
    assert text[candidates[0].start : candidates[0].end] == "ABCPE1234F"


def test_pan_accepts_case_insensitive_lowercase_and_mixed():
    for pan in ["abcpe1234f", "AbCpE1234f", "ABCPe1234F"]:
        candidates = detect_pan_candidates(pan)
        assert len(candidates) == 1
        assert candidates[0].type == TYPE_PAN


def test_pan_accepts_all_official_holder_types():
    # 4th char must be one of: P, C, H, F, A, T, B, L, J, G
    valid_holder_codes = "PCHFATBLJG"
    for code in valid_holder_codes:
        pan = f"ABC{code}E1234F"
        candidates = detect_pan_candidates(pan)
        assert len(candidates) == 1, f"Failed for holder code: {code}"
        assert candidates[0].type == TYPE_PAN


def test_pan_rejects_invalid_holder_types():
    for invalid_code in "XYZMKNSRVUD":
        pan = f"ABC{invalid_code}E1234F"
        assert len(detect_pan_candidates(pan)) == 0, f"Allowed invalid code: {invalid_code}"


def test_pan_rejects_embedded_in_longer_alphanumeric_sequence():
    assert len(detect_pan_candidates("ZABCPE1234F")) == 0
    assert len(detect_pan_candidates("ABCPE1234FZ")) == 0
    assert len(detect_pan_candidates("1ABCPE1234F")) == 0
    assert len(detect_pan_candidates("ABCPE1234F1")) == 0


def test_pan_rejects_malformed_token_structures():
    # Wrong number of digits
    assert len(detect_pan_candidates("ABCPE123F")) == 0
    assert len(detect_pan_candidates("ABCPE12345F")) == 0
    # Ends in digit instead of letter
    assert len(detect_pan_candidates("ABCPE12345")) == 0
    # Digits in prefix
    assert len(detect_pan_candidates("AB1PE1234F")) == 0


# ============================================================================
# Mobile Tests (FR-M)
# ============================================================================


def test_mobile_accepts_plain_10_digits_starting_6_to_9():
    for first_digit in "6789":
        number = first_digit + "876543210"
        candidates = detect_mobile_candidates(number)
        assert len(candidates) == 1
        assert candidates[0].type == TYPE_MOBILE


def test_mobile_rejects_10_digits_starting_0_to_5():
    for first_digit in "012345":
        number = first_digit + "876543210"
        assert len(detect_mobile_candidates(number)) == 0


def test_mobile_accepts_split_after_fifth_digit_with_space_or_hyphen():
    candidates_space = detect_mobile_candidates("98765 43210")
    assert len(candidates_space) == 1
    assert candidates_space[0].type == TYPE_MOBILE

    candidates_hyphen = detect_mobile_candidates("98765-43210")
    assert len(candidates_hyphen) == 1
    assert candidates_hyphen[0].type == TYPE_MOBILE


def test_mobile_accepts_prefix_plus_91():
    cases = [
        "+919876543210",
        "+91 9876543210",
        "+91-9876543210",
        "+91 98765 43210",
        "+91 98765-43210",
        "+91-98765-43210",
    ]
    for case in cases:
        candidates = detect_mobile_candidates(case)
        assert len(candidates) == 1, f"Failed on valid mobile: {case}"
        assert candidates[0].type == TYPE_MOBILE
        assert case[candidates[0].start : candidates[0].end] == case


def test_mobile_accepts_prefix_91():
    cases = [
        "919876543210",
        "91 9876543210",
        "91-9876543210",
        "91 98765-43210",
    ]
    for case in cases:
        candidates = detect_mobile_candidates(case)
        assert len(candidates) == 1, f"Failed on valid mobile with 91 prefix: {case}"
        assert candidates[0].type == TYPE_MOBILE


def test_mobile_accepts_prefix_0():
    cases = [
        "09876543210",
        "0 9876543210",
        "0-9876543210",
        "0 98765-43210",
    ]
    for case in cases:
        candidates = detect_mobile_candidates(case)
        assert len(candidates) == 1, f"Failed on valid mobile with 0 prefix: {case}"
        assert candidates[0].type == TYPE_MOBILE


def test_mobile_rejects_embedded_in_longer_digit_sequence():
    assert len(detect_mobile_candidates("19876543210")) == 0
    assert len(detect_mobile_candidates("98765432101")) == 0
    assert len(detect_mobile_candidates("1239876543210456")) == 0
    assert len(detect_mobile_candidates("card 1234567812345678")) == 0
    assert len(detect_mobile_candidates("order 9876543210123")) == 0


def test_mobile_rejects_prefixed_invalid_starting_digit():
    assert len(detect_mobile_candidates("+91 1234567890")) == 0
    assert len(detect_mobile_candidates("91 5234567890")) == 0
    assert len(detect_mobile_candidates("01234567890")) == 0


def test_detect_all_empty_and_no_match():
    assert detect_all_candidates("") == []
    assert detect_all_candidates("Hello world with no PII here.") == []

