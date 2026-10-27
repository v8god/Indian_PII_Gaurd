"""Command-line interface for pii-guard.

Reads plain text from standard input, processes detected Indian PII entities,
and writes transformed text to standard output.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from pii_guard import mask_text
from pii_guard.maskers import MODE_MASK, MODE_TAG


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser for pii-guard."""
    parser = argparse.ArgumentParser(
        prog="pii-guard",
        description="Offline, deterministic Indian PII detector and masker.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    mask_parser = subparsers.add_parser(
        "mask",
        help="Mask or tag Indian PII identifiers in text from stdin",
    )
    mask_parser.add_argument(
        "--mode",
        choices=[MODE_MASK, MODE_TAG],
        default=MODE_MASK,
        help="Transformation mode: 'mask' (default) or 'tag'",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for pii-guard CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command != "mask":
        parser.print_help(sys.stderr)
        return 2

    try:
        input_text = sys.stdin.read()
        result = mask_text(input_text, mode=args.mode)
        sys.stdout.write(result.text)
        return 0
    except ValueError as err:
        sys.stderr.write(f"error: {err}\n")
        return 1
    except Exception:
        # Never dump raw inputs or secrets to stderr
        sys.stderr.write("error: processing failed.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

