"""Verhoeff checksum validation and check-digit generation.

The Verhoeff algorithm is based on the dihedral group D_5 and detects all
single-digit substitution errors and all adjacent transposition errors.
"""

from __future__ import annotations

# Dihedral group D_5 multiplication table
_MULTIPLICATION_TABLE: tuple[tuple[int, ...], ...] = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
    (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
    (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
    (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
    (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
    (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
    (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
    (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 0),
)

# Permutation table
_PERMUTATION_TABLE: tuple[tuple[int, ...], ...] = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
    (5, 8, 0, 3, 7, 9, 6, 1, 4, 2),
    (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
    (9, 4, 5, 3, 1, 2, 6, 8, 7, 0),
    (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
    (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
    (7, 0, 4, 6, 9, 1, 3, 2, 5, 8),
)

# Inverse table
_INVERSE_TABLE: tuple[int, ...] = (0, 4, 3, 2, 1, 5, 6, 7, 8, 9)


def validate(digits: str) -> bool:
    """Validate a numeric string using the Verhoeff checksum algorithm.

    Args:
        digits: A string of ASCII decimal digits including the check digit.

    Returns:
        True if the digits form a valid Verhoeff sequence; False otherwise.
    """
    if not isinstance(digits, str) or not digits or not digits.isdigit():
        return False

    c = 0
    for i, char in enumerate(reversed(digits)):
        c = _MULTIPLICATION_TABLE[c][_PERMUTATION_TABLE[i % 8][int(char)]]

    return c == 0


def generate_check_digit(payload: str) -> str:
    """Compute the Verhoeff check digit for a numeric payload.

    Args:
        payload: A non-empty string of ASCII decimal digits without the check digit.

    Returns:
        A single character string ('0'-'9') representing the Verhoeff check digit.

    Raises:
        ValueError: If payload is empty or contains non-digit characters.
    """
    if not isinstance(payload, str) or not payload or not payload.isdigit():
        raise ValueError("Payload must be a non-empty string of ASCII digits")

    c = 0
    for i, char in enumerate(reversed(payload), start=1):
        c = _MULTIPLICATION_TABLE[c][_PERMUTATION_TABLE[i % 8][int(char)]]

    return str(_INVERSE_TABLE[c])

