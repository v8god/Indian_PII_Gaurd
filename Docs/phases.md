# Phases — indian-pii-guard

Mark each box only when the **exit gate** passes with command output you actually saw.

## Phase 0 — Setup & decisions
- [x] Create repo `indian-pii-guard` with the layout in `Architecture.md`
- [x] `pyproject.toml` (src layout, console script `pii-guard`), `LICENSE` (ask owner), `.gitignore` (`.env`, secrets)
- [x] Resolve D1–D7, record in `memory.md`
- **Gate:** `pip install -e .` works; `pytest` runs (even with 0 tests).

## Phase 1 — Verhoeff
- [x] `verhoeff.py`: `validate(digits)`, `generate_check_digit(payload)` (needed by the dataset generator)
- [x] `tests/test_verhoeff.py`: known-valid, known-invalid, single-digit-error and transposition cases
- **Gate:** tests green.

## Phase 2 — Detectors
- [x] Aadhaar, PAN, mobile candidate regexes with boundary lookarounds
- [x] Validation after candidate match
- [x] `tests/test_detectors.py`: accepted formats, rejections, no partial matches inside longer tokens
- **Gate:** all FR-A/P/M rules covered by named tests.

## Phase 3 — Overlap resolution
- [x] `resolve.py` with documented priority and tie-break
- [x] Tests incl. `91`+10-digit vs 12-digit Aadhaar ambiguity
- **Gate:** output spans are non-overlapping, one label each.

## Phase 4 — Maskers
- [x] Mask mode with separator preservation
- [x] Tag mode: HMAC, normalisation, fail-closed on missing key
- [x] Tests: suffix visibility, unrelated text intact, same tag for equivalent formats, missing key raises
- **Gate:** tests green; fake test key only.

## Phase 5 — CLI
- [x] `cli.py`: stdin→stdout, mode switch, clear errors, nothing logged, no temp files
- [x] CLI tests (subprocess or `CliRunner`-style)
- **Gate:** `echo "<synthetic>" | pii-guard mask` works.

## Phase 6 — Dataset generator
- [x] `eval/generate.py` with `--seed`; ≥ 300 lines; categories per PRD §7; ≥ 30 obfuscated with `expected_behavior`
- [x] Same seed ⇒ byte-identical `synthetic.jsonl` (test it)
- **Gate:** reproducibility test passes.

## Phase 7 — Evaluation
- [x] `eval/eval.py` exact-match P/R/F1 per type + overall, writes `failures.md`
- [x] Unit-test metric maths on a tiny hand-computed case
- [x] Run 1 (dev seed). Fix detectors only based on dev-seed failures.
- [x] Run 2 (**new** seed, untouched). This is the reportable score. Report both.
- **Gate:** numbers exist in terminal output and `failures.md`.

## Phase 8 — Docs
- [x] README (what/install/usage/how it works/results/failures/limitations/ethics)
- [x] `docs/limitations.md` with all mandatory limitations
- [x] Paste numbers **copied from script output**
- **Gate:** every README number traceable to a run.

## Phase 9 — Final verification
- [x] Fresh clone in a clean venv: install → test → eval → CLI demo
- [x] Grep history for real-looking IDs/keys
- [x] Update `memory.md` status to DONE with the verified commands
