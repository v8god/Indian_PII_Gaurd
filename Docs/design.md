# Design — indian-pii-guard (developer experience)

There is no GUI. "Design" here means API ergonomics, CLI behaviour, output formats and report formats.

## Principles
Small surface · deterministic · explainable (spans, not magic) · fail closed · never echo sensitive input.

## Python API
```python
from pii_guard import find_spans, mask_text

spans = find_spans("call +91 98765-43210")
# [Span(type="MOBILE", start=5, end=21)]   (offsets: zero-based, half-open, on the ORIGINAL string)

result = mask_text("call +91 98765-43210", mode="mask")
result.text    # "call XXXXXXXXX-XX210"-style output; exact form is fixed by tests
result.spans   # same spans as find_spans
```
`mode` ∈ `"mask"` | `"tag"`. Tag mode reads `PII_GUARD_KEY`; missing key raises a clear exception.

## Mask output examples (illustrative — tests are authoritative)
| Type | Input shape | Output shape |
|---|---|---|
| Aadhaar | `2345 6789 0123`-style | `XXXX XXXX 0123` |
| PAN | `ABCPD1234E`-style | `XXXXXXXXXE` |
| Mobile | 10 digits | `XXXXXXXX` + last 2 digits |

## Tag output
`[AADHAAR:ab12cd34]` — upper-case type label, fixed-length lowercase hex tag (length documented).

## CLI
```bash
pii-guard mask < in.txt > out.txt                 # default mode
PII_GUARD_KEY=fake-test-key pii-guard mask --mode tag < in.txt > out.txt
```
- Output only on stdout. Errors on stderr, exit code ≠ 0.
- Errors never contain raw input or the key; at most `type` and position.
- Flag name (`--mode`) is decision D5.

## Error messages (examples)
- `error: PII_GUARD_KEY is not set; refusing to run in tag mode.`
- `error: unknown mode 'x'; expected 'mask' or 'tag'.`

## Report formats
- `eval.py` prints a table: `type | TP | FP | FN | precision | recall | F1`, plus `overall`.
- `failures.md`: one section per FP/FN with `id`, `type`, `start-end`, and the synthetic line.
- Each obfuscated/limitation case is labelled `known limitation` rather than hidden.

## README tone
Plain, specific, honest. No "robust", "comprehensive", "enterprise-grade", "compliant".
