"""Deterministic overlap resolution for candidate identifier spans.

When multiple detectors match overlapping text, candidates are sorted by:
1. Strictness (descending): AADHAAR (checksum) > PAN (entity code) > MOBILE (prefix)
2. Span length (descending): longer span preferred
3. Start offset (ascending): earlier start preferred

The algorithm greedily selects non-overlapping spans and returns them
sorted by original text start position.
"""

from __future__ import annotations

from pii_guard.detectors import CandidateSpan, Span


def _overlaps(span_a: CandidateSpan, span_b: CandidateSpan) -> bool:
    """Check if two half-open intervals [start, end) overlap."""
    return span_a.start < span_b.end and span_b.start < span_a.end


def resolve_overlaps(candidates: list[CandidateSpan]) -> list[Span]:
    """Resolve overlapping candidate spans into a non-overlapping list of Spans.

    Args:
        candidates: A list of candidate spans, each carrying a strictness rank.

    Returns:
        A list of resolved, non-overlapping Span objects sorted by start offset.
    """
    if not candidates:
        return []

    # Sort key:
    # 1. strictness (descending, so negated)
    # 2. length (descending, so negated)
    # 3. start offset (ascending)
    sorted_candidates = sorted(
        candidates,
        key=lambda c: (-c.strictness, -(c.end - c.start), c.start),
    )

    accepted: list[CandidateSpan] = []
    for cand in sorted_candidates:
        if not any(_overlaps(cand, acc) for acc in accepted):
            accepted.append(cand)

    # Return accepted spans sorted by original text start position
    accepted.sort(key=lambda c: c.start)
    return [c.to_span() for c in accepted]

