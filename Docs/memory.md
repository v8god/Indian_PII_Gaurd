# Memory — indian-pii-guard

Living log. Update at the end of every session. Facts only; mark unknowns as unknown.

## Status
`DONE` — all phases 0 to 9 completed and verified.

## Locked facts (from the brief)
- Types: Aadhaar, PAN, Indian mobile. Offline, deterministic, stdlib-only runtime.
- Aadhaar: first digit 2–9 + Verhoeff. PAN holder types `PCHFATBLJG`. Mobile first digit 6–9, prefixes `+91|91|0`.
- Mask suffixes: Aadhaar 4, mobile 2, PAN 1.
- Tag: HMAC-SHA256, key in `PII_GUARD_KEY`, fail closed.
- Dataset ≥ 300 lines, ≥ 30 obfuscated, fixed seed, exact-match metrics.

## Decisions
| ID | Question | Suggested default | Decision |
|---|---|---|---|
| D1 | Span type strings / return container | `AADHAAR/PAN/MOBILE`, frozen dataclasses | Accepted: `Span(type, start, end)`, `MaskResult(text, spans)` |
| D2 | Strictness order | Aadhaar > PAN > Mobile | Accepted: Aadhaar (3) > PAN (2) > Mobile (1) |
| D3 | Mask mobile prefix digits too? | Mask all digits except last 2 | Accepted: Mask all digits except last 2; preserve `+` and separators |
| D4 | Tag length | 8 hex chars | Accepted: 8 lowercase hex chars |
| D5 | CLI mode flag | `--mode {mask,tag}` | Accepted: `--mode` flag with choices `mask`, `tag` (default `mask`) |
| D6 | PAN case before hashing | Uppercase | Accepted: Convert PAN candidate to uppercase before HMAC hashing |
| D7 | License | ask owner | Accepted: MIT License |

## Unknowns (do not guess)
- Python minimum version: requires >= 3.10 (tested and verified on Python 3.12.10).
- Repo public URL: local package `indian-pii-guard`.
- Owner's preferred license: MIT License.

## Evaluation runs
| Run | Seed | Lines | Precision | Recall | F1 | Notes |
|---|---|---|---|---|---|---|
| dev | 42 | 375 | 0.9797 | 0.9959 | 0.9877 | Fixed PAN 'g' lowercase, Aadhaar card/prefix lookaround, mobile letter boundary |
| final | 1337 | 375 | 0.9837 | 1.0000 | 0.9918 | Untouched seed. 4 FP in awkward/obfuscated known limitations; 0 FN. |

## Known failures / limitations discovered
1. Mobile number preceded by irregular spaces or punctuation like `(+91) ` or `++91 ` or `-91 ` detects the 10 digits as a standalone mobile number.
2. Irregular spacing with leading zero e.g. `0 98765 43210` parses as mobile candidate.
3. 12-digit number starting with 91 that coincidentally passes Verhoeff checksum is classified as Aadhaar due to strictness hierarchy (Aadhaar > Mobile).
4. Dot-separated, slash-separated, line-broken, spelled-out, and non-Latin numerals (Devanagari) are not matched (by design, ASCII only).

## Session log
| Date | What changed | Verified by |
|---|---|---|
| 2026-10-28 | Phase 0 completed: repo structure, pyproject.toml, LICENSE, .gitignore, venv setup, decisions D1-D7 resolved. | `pip install -e .` & `pytest` (1 passed) |
| 2026-10-28 | Phase 1 completed: verhoeff.py (validate + generate_check_digit) and test_verhoeff.py with standard vectors, error/transposition tests. | `pytest tests/test_verhoeff.py` (9 passed) |
| 2026-10-28 | Phase 2 completed: detectors.py (Aadhaar, PAN, Mobile candidate regexes + validation) and test_detectors.py covering all FR-A/P/M rules. | `pytest tests/test_detectors.py` (23 passed) |
| 2026-10-28 | Phase 3 completed: resolve.py (greedy overlap resolution by strictness > length > start) and test_resolve.py including 91 ambiguity. | `pytest tests/test_resolve.py` (8 passed) |
| 2026-10-28 | Phase 4 completed: maskers.py (mask mode + tag HMAC mode fail-closed), public API in __init__.py, test_maskers.py. | `pytest tests/test_maskers.py` (12 passed) |
| 2026-10-28 | Phase 5 completed: cli.py (argparse stdin->stdout pii-guard mask [--mode {mask,tag}]), test_cli.py. | `pytest tests/test_cli.py` & pipe demo verified |
| 2026-10-28 | Phase 6 completed: eval/generate.py (seedable generator, 375 records, 35 awkward cases), test_reproducibility.py. | `pytest tests/test_reproducibility.py` (4 passed) |
| 2026-10-28 | Phase 7 completed: eval/eval.py, test_metrics.py, Run 1 (dev seed 42: P=0.9797, R=0.9959, F1=0.9877) and Run 2 (final seed 1337: P=0.9837, R=1.0000, F1=0.9918). | `pytest tests/test_metrics.py` & eval script execution |
| 2026-10-28 | Phase 8 completed: README.md with exact copied metrics, docs/limitations.md with exhaustive limitations. | Readme and limitations docs cross-checked with test outputs |
| 2026-10-28 | Phase 9 completed: Final verification of clean installation, 64 pytest tests green, CLI pipeline verified, secret scan clean. Marked DONE. | `pytest -v` (64 passed in 0.46s), CLI pipe test, secret scan |
| 2026-10-28 | Quality Audit & Hardening: Refined Aadhaar lookarounds to 4-digit card groups (fixing 'qty 7 ...' leak), disallowed whitespace-only keys in tag mode, made test_cli cross-platform portable, bootstrapped eval.py/generate.py sys.path, bound reproducibility tests to committed on-disk JSONL files, and qualified ~10% bare 91-mobile collision rate in docs. | `pytest -v` (68 passed in 0.49s, 0 skipped), eval.py clean run |
