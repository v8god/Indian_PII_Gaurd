# Architecture — indian-pii-guard

## Layout
```text
indian-pii-guard/
  README.md  LICENSE  pyproject.toml  .gitignore
  src/pii_guard/
    __init__.py     # exports find_spans, mask_text
    verhoeff.py     # checksum validate + check-digit generation
    detectors.py    # candidate regex + validation per type
    resolve.py      # overlap resolution
    maskers.py      # mask + keyed tag transforms
    cli.py          # stdin -> stdout
  tests/            # test_verhoeff / detectors / maskers / resolve (+ cli, generate, eval metrics)
  eval/
    generate.py  data/synthetic.jsonl  eval.py  failures.md
  docs/limitations.md
```

## Data flow
```text
text ─► detectors (3x: regex candidates)
      ─► validate each candidate (Verhoeff / holder-type / prefix)
      ─► Span(type, start, end, strictness)  [offsets on original text]
      ─► resolve overlaps (strictness ▸ length ▸ earlier start)
      ─► maskers (mask | tag) applied right-to-left so offsets stay valid
      ─► MaskResult(text, spans)
```

## Core types
```python
@dataclass(frozen=True)
class Span:
    type: str    # "AADHAAR" | "PAN" | "MOBILE"  (D1)
    start: int   # inclusive, zero-based
    end: int     # exclusive

@dataclass(frozen=True)
class MaskResult:
    text: str
    spans: list[Span]
```
Strictness is internal to resolution and not part of the public schema.

## Detector regex notes
- Digits: `(?<!\d)` … `(?!\d)`. Alphanumeric tokens (PAN): `(?<![A-Za-z0-9])` … `(?![A-Za-z0-9])`.
- Use ASCII digit classes (`[0-9]`), **not** `\d`, so non-Latin digits are an explicit documented limitation, not an accident.
- Aadhaar: `[2-9][0-9]{3}([ -]?)[0-9]{4}\1[0-9]{4}` style (same separator both places) → strip separators → Verhoeff.
- PAN: `[A-Za-z]{3}[PCHFATBLJGpchfatblj][A-Za-z][0-9]{4}[A-Za-z]`.
- Mobile: `(?:\+91|91|0)?[6-9][0-9]{4}[ -]?[0-9]{5}`.
- Ambiguity to test: `91` + 10 digits is also 12 digits; checksum decides whether it's Aadhaar.

## Overlap resolution
Sort candidates by (strictness desc, length desc, start asc); greedily accept those not overlapping accepted spans; return sorted by start. Default strictness ranking (D2, confirm): Aadhaar (checksum) > PAN (structure+holder type) > Mobile (prefix only).

## Tag mode
1. Normalise: Aadhaar strip spaces/hyphens; PAN uppercase (D6); Mobile strip separators and `+91/91/0` ⇒ 10 digits.
2. `hmac.new(key_bytes, normalised.encode(), sha256).hexdigest()[:N]` (N documented, suggest 8).
3. Use `hmac.compare_digest` anywhere comparison is needed. Key never stored, printed or logged.

## CLI
`argparse`, reads `sys.stdin.read()`, writes `sys.stdout.write()`. No files, no logging of content, no network imports.

## Evaluation
```text
generate.py --seed S ─► data/synthetic.jsonl
   line: {id, category, text, spans:[{type,start,end}], expected_behavior, known_limitation}
eval.py ─► find_spans(text) ─► exact (type,start,end) set compare ─► P/R/F1 ─► failures.md
```
Generator uses `random.Random(seed)` only; uses `verhoeff.generate_check_digit` for valid Aadhaar and corrupts the last digit for Verhoeff-failing negatives.

## Dependencies
Standard library only for the package. `pytest` for dev. Keep it that way unless the owner approves.
