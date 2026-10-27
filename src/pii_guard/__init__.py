"""indian-pii-guard: Deterministic, offline Indian PII detector and masker."""

from __future__ import annotations

from pii_guard.detectors import (
    Span,
    TYPE_AADHAAR,
    TYPE_MOBILE,
    TYPE_PAN,
    detect_all_candidates,
)
from pii_guard.maskers import (
    MODE_MASK,
    MODE_TAG,
    MaskResult,
    apply_transforms,
)
from pii_guard.resolve import resolve_overlaps

__version__ = "0.1.0"
__all__ = [
    "Span",
    "MaskResult",
    "find_spans",
    "mask_text",
    "TYPE_AADHAAR",
    "TYPE_PAN",
    "TYPE_MOBILE",
    "MODE_MASK",
    "MODE_TAG",
]


def find_spans(text: str) -> list[Span]:
    """Find all valid, non-overlapping Indian identifier spans in text.

    Args:
        text: Input string to scan.

    Returns:
        List of resolved non-overlapping Span objects sorted by start offset.
    """
    candidates = detect_all_candidates(text)
    return resolve_overlaps(candidates)


def mask_text(
    text: str,
    mode: str = MODE_MASK,
    key: str | None = None,
) -> MaskResult:
    """Detect and transform Indian identifier spans in text.

    Args:
        text: Input string.
        mode: Transform mode, either 'mask' (default) or 'tag'.
        key: Cryptographic HMAC key for tag mode. If None, uses PII_GUARD_KEY env var.

    Returns:
        MaskResult containing transformed text and original spans.

    Raises:
        ValueError: If mode is invalid or if tag mode is used without a key.
    """
    spans = find_spans(text)
    return apply_transforms(text, spans, mode=mode, key=key)

