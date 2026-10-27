"""Unit tests for Verhoeff checksum algorithm implementation."""

import pytest
from pii_guard.verhoeff import generate_check_digit, validate


def test_validate_accepts_known_valid_standard_vectors():
    # Standard academic test vectors for Verhoeff
    assert validate("2363") is True
    assert validate("1428570") is True
    assert validate("123451") is True
    assert validate("843563") is True


def test_generate_check_digit_computes_expected_digit():
    assert generate_check_digit("236") == "3"
    assert generate_check_digit("142857") == "0"
    assert generate_check_digit("12345") == "1"
    assert generate_check_digit("84356") == "3"


def test_generate_then_validate_roundtrip_for_synthetic_numbers():
    payloads = ["23456789012", "98765432109", "31415926535", "55555555555"]
    for payload in payloads:
        chk = generate_check_digit(payload)
        full_number = payload + chk
        assert validate(full_number) is True


def test_validate_rejects_single_digit_substitution_errors():
    payload = "23456789012"
    valid_number = payload + generate_check_digit(payload)

    for idx in range(len(valid_number)):
        for replacement in "0123456789":
            if replacement != valid_number[idx]:
                corrupted = valid_number[:idx] + replacement + valid_number[idx + 1 :]
                assert validate(corrupted) is False, f"Failed to reject substitution at {idx}"


def test_validate_rejects_adjacent_transposition_errors():
    payload = "23456789012"
    valid_number = payload + generate_check_digit(payload)

    for idx in range(len(valid_number) - 1):
        if valid_number[idx] != valid_number[idx + 1]:
            transposed = (
                valid_number[:idx]
                + valid_number[idx + 1]
                + valid_number[idx]
                + valid_number[idx + 2 :]
            )
            assert validate(transposed) is False, f"Failed to reject transposition at {idx}"


def test_validate_rejects_non_digit_characters():
    assert validate("1234a5") is False
    assert validate("123 45") is False
    assert validate("123-45") is False
    assert validate("") is False


def test_validate_rejects_non_string_inputs():
    assert validate(123451) is False  # type: ignore[arg-type]
    assert validate(None) is False  # type: ignore[arg-type]


def test_generate_check_digit_raises_on_empty_string():
    with pytest.raises(ValueError, match="non-empty string"):
        generate_check_digit("")


def test_generate_check_digit_raises_on_non_digits():
    with pytest.raises(ValueError, match="non-empty string"):
        generate_check_digit("1234a")

