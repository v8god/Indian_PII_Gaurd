"""Masking and keyed HMAC tag transformations for detected identifier spans."""

from __future__ import annotations

import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from typing import Final

from pii_guard.detectors import (
    Span,
    TYPE_AADHAAR,
    TYPE_MOBILE,
    TYPE_PAN,
)

MODE_MASK: Final[str] = "mask"
MODE_TAG: Final[str] = "tag"
TAG_HEX_LENGTH: Final[int] = 8


@dataclass(frozen=True)
class MaskResult:
    """The result of masking text with preserved original spans.

    Attributes:
        text: Transformed output text.
        spans: Original spans found in the input string.
    """

    text: str
    spans: list[Span]


def _mask_digits_keep_last(raw: str, keep_last: int) -> str:
    """Mask all digits with 'X' except for the last `keep_last` digits, preserving separators."""
    digit_indices = [i for i, ch in enumerate(raw) if ch.isdigit()]
    if keep_last > 0 and len(digit_indices) >= keep_last:
        mask_indices = set(digit_indices[:-keep_last])
    else:
        mask_indices = set(digit_indices)

    return "".join("X" if i in mask_indices else ch for i, ch in enumerate(raw))


def mask_entity(raw: str, entity_type: str) -> str:
    """Mask a detected identifier string per the PRD specification.

    - Aadhaar: Keep last 4 digits; replace prior digits with 'X'; preserve separators.
    - PAN: Keep last 1 character; replace prior 9 characters with 'X'.
    - Mobile: Keep last 2 digits; replace prior digits with 'X'; preserve prefixes and separators.
    """
    if entity_type == TYPE_AADHAAR:
        return _mask_digits_keep_last(raw, keep_last=4)
    elif entity_type == TYPE_PAN:
        if len(raw) == 10:
            return "X" * 9 + raw[-1]
        return "X" * len(raw)
    elif entity_type == TYPE_MOBILE:
        return _mask_digits_keep_last(raw, keep_last=2)
    else:
        # Fallback for unexpected type: mask all characters
        return "X" * len(raw)


def normalize_for_tag(raw: str, entity_type: str) -> str:
    """Normalize identifier value so equivalent formats yield identical tags.

    - Aadhaar: Strip spaces and hyphens -> 12 digits.
    - PAN: Uppercase string -> 10 uppercase chars.
    - Mobile: Strip all non-digits and strip +91/91/0 prefix -> canonical 10 digits.
    """
    if entity_type == TYPE_AADHAAR:
        return re.sub(r"[ -]", "", raw)
    elif entity_type == TYPE_PAN:
        return raw.upper()
    elif entity_type == TYPE_MOBILE:
        digits = re.sub(r"[^0-9]", "", raw)
        if len(digits) == 12 and digits.startswith("91"):
            return digits[2:]
        if len(digits) == 11 and digits.startswith("0"):
            return digits[1:]
        return digits
    return raw


def _is_invalid_key(key: str | bytes | None) -> bool:
    """Check if key is missing, empty, or contains only whitespace."""
    if key is None:
        return True
    if isinstance(key, str):
        return len(key.strip()) == 0
    if isinstance(key, bytes):
        return len(key.strip()) == 0
    return False


def compute_tag(raw: str, entity_type: str, key: str | bytes) -> str:
    """Generate a keyed HMAC tag formatted as [TYPE:hex8].

    Args:
        raw: The matched raw substring.
        entity_type: "AADHAAR", "PAN", or "MOBILE".
        key: Cryptographic key string or bytes.

    Returns:
        Formatted tag e.g. "[AADHAAR:ab12cd34]".

    Raises:
        ValueError: If key is empty, whitespace-only, or missing.
    """
    if _is_invalid_key(key):
        raise ValueError("PII_GUARD_KEY is not set; refusing to run in tag mode.")

    key_bytes = key.encode("utf-8") if isinstance(key, str) else key
    normalised = normalize_for_tag(raw, entity_type)
    digest = hmac.new(key_bytes, normalised.encode("utf-8"), hashlib.sha256).hexdigest()
    tag_hex = digest[:TAG_HEX_LENGTH].lower()
    return f"[{entity_type}:{tag_hex}]"


def apply_transforms(
    text: str,
    spans: list[Span],
    mode: str = MODE_MASK,
    key: str | None = None,
) -> MaskResult:
    """Apply mask or tag transformations to text over resolved spans.

    Transformations are applied in reverse order of start position (right-to-left)
    so that earlier span offsets remain valid.

    Args:
        text: The original text.
        spans: Resolved non-overlapping spans.
        mode: "mask" or "tag".
        key: Cryptographic key for tag mode (falls back to PII_GUARD_KEY environment variable).

    Returns:
        MaskResult containing transformed text and original spans.

    Raises:
        ValueError: If mode is unknown or if tag mode is requested without a key.
    """
    if mode not in (MODE_MASK, MODE_TAG):
        raise ValueError(f"Unknown mode '{mode}'; expected 'mask' or 'tag'.")

    if mode == MODE_TAG:
        resolved_key = key if key is not None else os.environ.get("PII_GUARD_KEY", "")
        if _is_invalid_key(resolved_key):
            raise ValueError("PII_GUARD_KEY is not set; refusing to run in tag mode.")
    else:
        resolved_key = ""

    # Sort spans right-to-left
    sorted_spans = sorted(spans, key=lambda s: s.start, reverse=True)

    result_chars = list(text)
    for span in sorted_spans:
        raw_match = text[span.start : span.end]
        if mode == MODE_MASK:
            replacement = mask_entity(raw_match, span.type)
        else:
            replacement = compute_tag(raw_match, span.type, resolved_key)

        result_chars[span.start : span.end] = list(replacement)

    # Return spans sorted by original text start position
    original_sorted_spans = sorted(spans, key=lambda s: s.start)
    return MaskResult(text="".join(result_chars), spans=original_sorted_spans)

