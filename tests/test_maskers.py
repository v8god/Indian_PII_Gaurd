"""Unit tests for mask and tag transformations."""

import os
import pytest
from pii_guard import find_spans, mask_text
from pii_guard.detectors import TYPE_AADHAAR, TYPE_MOBILE, TYPE_PAN
from pii_guard.maskers import compute_tag, mask_entity, normalize_for_tag
from pii_guard.verhoeff import generate_check_digit

FAKE_TEST_KEY = "test-key-not-secret"


def make_valid_aadhaar(prefix_11: str) -> str:
    chk = generate_check_digit(prefix_11)
    return prefix_11 + chk


def test_mask_aadhaar_preserves_separators_and_exposes_last_four():
    raw_spaced = "2345 6789 0123"
    masked_spaced = mask_entity(raw_spaced, TYPE_AADHAAR)
    assert masked_spaced == "XXXX XXXX 0123"

    raw_hyphen = "2345-6789-0123"
    masked_hyphen = mask_entity(raw_hyphen, TYPE_AADHAAR)
    assert masked_hyphen == "XXXX-XXXX-0123"

    raw_plain = "234567890123"
    masked_plain = mask_entity(raw_plain, TYPE_AADHAAR)
    assert masked_plain == "XXXXXXXX0123"


def test_mask_pan_exposes_last_character():
    raw_pan = "ABCPE1234F"
    masked_pan = mask_entity(raw_pan, TYPE_PAN)
    assert masked_pan == "XXXXXXXXXF"

    raw_lower = "abcpe1234f"
    masked_lower = mask_entity(raw_lower, TYPE_PAN)
    assert masked_lower == "XXXXXXXXXf"


def test_mask_mobile_preserves_delimiters_and_exposes_last_two():
    assert mask_entity("+91 98765-43210", TYPE_MOBILE) == "+XX XXXXX-XXX10"
    assert mask_entity("9876543210", TYPE_MOBILE) == "XXXXXXXX10"
    assert mask_entity("98765-43210", TYPE_MOBILE) == "XXXXX-XXX10"
    assert mask_entity("09876543210", TYPE_MOBILE) == "XXXXXXXXX10"


def test_mask_text_preserves_unrelated_text():
    aadhaar = make_valid_aadhaar("23456789012")
    text = f"Prefix notice: customer ID is {aadhaar}, contact at +91 98765-43210 immediately."
    result = mask_text(text, mode="mask")

    expected_aadhaar_mask = f"XXXXXXXX{aadhaar[-4:]}"
    assert f"Prefix notice: customer ID is {expected_aadhaar_mask}" in result.text
    assert "contact at +XX XXXXX-XXX10 immediately." in result.text
    assert len(result.spans) == 2


def test_tag_mode_output_format():
    tag = compute_tag("ABCPE1234F", TYPE_PAN, FAKE_TEST_KEY)
    assert tag.startswith("[PAN:")
    assert tag.endswith("]")
    hex_part = tag[len("[PAN:") : -1]
    assert len(hex_part) == 8
    assert all(c in "0123456789abcdef" for c in hex_part)


def test_tag_mode_normalisation_yields_same_tag_for_equivalent_aadhaar():
    aadhaar_raw = make_valid_aadhaar("34567890123")
    aadhaar_spaced = f"{aadhaar_raw[:4]} {aadhaar_raw[4:8]} {aadhaar_raw[8:]}"
    aadhaar_hyphen = f"{aadhaar_raw[:4]}-{aadhaar_raw[4:8]}-{aadhaar_raw[8:]}"

    tag_raw = compute_tag(aadhaar_raw, TYPE_AADHAAR, FAKE_TEST_KEY)
    tag_spaced = compute_tag(aadhaar_spaced, TYPE_AADHAAR, FAKE_TEST_KEY)
    tag_hyphen = compute_tag(aadhaar_hyphen, TYPE_AADHAAR, FAKE_TEST_KEY)

    assert tag_raw == tag_spaced == tag_hyphen


def test_tag_mode_normalisation_yields_same_tag_for_case_variants_of_pan():
    tag_upper = compute_tag("ABCPE1234F", TYPE_PAN, FAKE_TEST_KEY)
    tag_lower = compute_tag("abcpe1234f", TYPE_PAN, FAKE_TEST_KEY)
    tag_mixed = compute_tag("AbCpE1234f", TYPE_PAN, FAKE_TEST_KEY)

    assert tag_upper == tag_lower == tag_mixed


def test_tag_mode_normalisation_yields_same_tag_for_equivalent_mobile():
    formats = [
        "9876543210",
        "98765-43210",
        "98765 43210",
        "+91 98765-43210",
        "+919876543210",
        "919876543210",
        "91 9876543210",
        "09876543210",
    ]
    tags = [compute_tag(f, TYPE_MOBILE, FAKE_TEST_KEY) for f in formats]
    assert len(set(tags)) == 1


def test_tag_mode_raises_when_key_is_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PII_GUARD_KEY", raising=False)
    with pytest.raises(ValueError, match="PII_GUARD_KEY is not set"):
        mask_text("call 9876543210", mode="tag")


def test_tag_mode_raises_when_key_is_empty(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PII_GUARD_KEY", "")
    with pytest.raises(ValueError, match="PII_GUARD_KEY is not set"):
        mask_text("call 9876543210", mode="tag")


def test_tag_mode_raises_when_key_is_whitespace_only(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PII_GUARD_KEY", "    ")
    with pytest.raises(ValueError, match="PII_GUARD_KEY is not set"):
        mask_text("call 9876543210", mode="tag")

    with pytest.raises(ValueError, match="PII_GUARD_KEY is not set"):
        mask_text("call 9876543210", mode="tag", key="   \t\n  ")


def test_mask_text_raises_on_invalid_mode():
    with pytest.raises(ValueError, match="Unknown mode 'invalid'"):
        mask_text("call 9876543210", mode="invalid")


def test_tag_mode_succeeds_with_explicit_key_or_env_var(monkeypatch: pytest.MonkeyPatch):
    text = "PAN ABCPE1234F attached."
    # Test with explicit key parameter
    res1 = mask_text(text, mode="tag", key=FAKE_TEST_KEY)
    assert res1.text.startswith("PAN [PAN:")
    assert res1.text.endswith("] attached.")

    # Test with environment variable
    monkeypatch.setenv("PII_GUARD_KEY", FAKE_TEST_KEY)
    res2 = mask_text(text, mode="tag")
    assert res1.text == res2.text
