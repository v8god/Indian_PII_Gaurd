"""Candidate detection and domain validation for Indian identifiers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from pii_guard.verhoeff import validate as validate_verhoeff

TYPE_AADHAAR: Final[str] = "AADHAAR"
TYPE_PAN: Final[str] = "PAN"
TYPE_MOBILE: Final[str] = "MOBILE"

STRICTNESS_AADHAAR: Final[int] = 3
STRICTNESS_PAN: Final[int] = 2
STRICTNESS_MOBILE: Final[int] = 1

# Aadhaar: 12 digits, first digit 2-9, optional identical separator (space or hyphen)
# between 4-digit groups, bounded by ASCII non-digits, not preceded by + or 4-digit card groups.
_AADHAAR_REGEX: Final[re.Pattern[str]] = re.compile(
    r"(?<![0-9+])(?<![0-9]{4}[ -])(?:([2-9][0-9]{3})([ -])([0-9]{4})\2([0-9]{4})|([2-9][0-9]{11}))(?![0-9])(?![ -][0-9]{4})"
)

# PAN: 5 letters (4th is entity code in PCHFATBLJG), 4 digits, 1 letter,
# case-insensitive, bounded by ASCII non-alphanumeric.
_PAN_REGEX: Final[re.Pattern[str]] = re.compile(
    r"(?<![A-Za-z0-9])([A-Za-z]{3}[PCHFATBLJGpchfatbljg][A-Za-z][0-9]{4}[A-Za-z])(?![A-Za-z0-9])"
)

# Mobile: 10 digits starting with 6-9, optional prefix (+91, 91, 0) with optional separator,
# optional single space/hyphen after 5th digit, bounded by ASCII non-alphanumeric.
_MOBILE_REGEX: Final[re.Pattern[str]] = re.compile(
    r"(?<![A-Za-z0-9+])(?:\+91[ -]?|(?<!\+)(?:91|0)[ -]?)[6-9][0-9]{4}[ -]?[0-9]{5}(?![A-Za-z0-9])|(?<![A-Za-z0-9])[6-9][0-9]{4}[ -]?[0-9]{5}(?![A-Za-z0-9])"
)


@dataclass(frozen=True)
class Span:
    """Represents a matched entity span within original text.

    Attributes:
        type: The entity type string ("AADHAAR", "PAN", or "MOBILE").
        start: Zero-based inclusive start character index.
        end: Zero-based exclusive end character index.
    """

    type: str
    start: int
    end: int


@dataclass(frozen=True)
class CandidateSpan:
    """Internal candidate span carrying strictness score for overlap resolution."""

    type: str
    start: int
    end: int
    strictness: int

    def to_span(self) -> Span:
        """Convert to public Span schema."""
        return Span(type=self.type, start=self.start, end=self.end)


def detect_aadhaar_candidates(text: str) -> list[CandidateSpan]:
    """Find and validate Aadhaar candidates in text."""
    if not text:
        return []

    candidates: list[CandidateSpan] = []
    for match in _AADHAAR_REGEX.finditer(text):
        matched_str = match.group()
        # Normalize digits by stripping separators
        digits = re.sub(r"[ -]", "", matched_str)
        if len(digits) == 12 and digits[0] in "23456789":
            if validate_verhoeff(digits):
                candidates.append(
                    CandidateSpan(
                        type=TYPE_AADHAAR,
                        start=match.start(),
                        end=match.end(),
                        strictness=STRICTNESS_AADHAAR,
                    )
                )

    return candidates


def detect_pan_candidates(text: str) -> list[CandidateSpan]:
    """Find and validate PAN candidates in text."""
    if not text:
        return []

    candidates: list[CandidateSpan] = []
    for match in _PAN_REGEX.finditer(text):
        candidates.append(
            CandidateSpan(
                type=TYPE_PAN,
                start=match.start(),
                end=match.end(),
                strictness=STRICTNESS_PAN,
            )
        )

    return candidates


def detect_mobile_candidates(text: str) -> list[CandidateSpan]:
    """Find and validate Indian mobile number candidates in text."""
    if not text:
        return []

    candidates: list[CandidateSpan] = []
    for match in _MOBILE_REGEX.finditer(text):
        candidates.append(
            CandidateSpan(
                type=TYPE_MOBILE,
                start=match.start(),
                end=match.end(),
                strictness=STRICTNESS_MOBILE,
            )
        )

    return candidates


def detect_all_candidates(text: str) -> list[CandidateSpan]:
    """Find all candidate spans across Aadhaar, PAN, and Mobile detectors."""
    if not text:
        return []

    candidates: list[CandidateSpan] = []
    candidates.extend(detect_aadhaar_candidates(text))
    candidates.extend(detect_pan_candidates(text))
    candidates.extend(detect_mobile_candidates(text))
    return candidates
