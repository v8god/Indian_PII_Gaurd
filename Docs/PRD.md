# PRD — indian-pii-guard

> Source of truth: `01-indian-pii-guard.md` brief. If this file and the brief disagree, stop and ask the owner.

## 1. Problem
Developers sometimes need to reduce exposure of Indian identifier patterns (Aadhaar, PAN, mobile numbers) in text before it goes to a test system or other processing. They need something offline, deterministic, explainable and measurable.

## 2. Product
A Python package + CLI that detects and masks three identifier-like patterns in plain text.
- A regex match is only a **candidate**. Validation decides acceptance.
- It is a pattern utility. It is **not** a complete PII detector and **not** a compliance product.

## 3. Target user
A developer who can call a Python function or pipe text through a CLI, get masked text back, and inspect detected spans — without any remote service.

## 4. Goals
| ID | Goal |
|---|---|
| G1 | Detect Aadhaar-like (Verhoeff-valid), PAN-like, and mobile-like values per the rules below |
| G2 | One label per character span (overlap resolution) |
| G3 | Two transforms: readable mask, and keyed HMAC tag |
| G4 | Python API + `pii-guard mask` CLI via stdin/stdout |
| G5 | Reproducible synthetic evaluation with precision/recall/F1 and a failure report |
| G6 | Honest README: real numbers, real failures, real limits |

## 5. Non-goals
Names, addresses, emails, bank accounts, images, PDFs, non-Indian IDs, network calls, telemetry, regulatory-compliance claims, real personal identifiers anywhere in the repo.

## 6. Functional requirements

### FR-A Aadhaar
1. 12 digits, contiguous or 3 groups of 4 separated by one space or hyphen.
2. First digit 2–9.
3. Full 12-digit value passes Verhoeff.
4. Not embedded in a longer digit sequence.

### FR-P PAN
1. `AAAAA9999A` shape, case-insensitive.
2. 4th char ∈ `P C H F A T B L J G`.
3. Not embedded in a longer alphanumeric token.

### FR-M Mobile
1. 10 digits, optional prefix `+91`, `91`, or `0`.
2. Optional single space/hyphen after the 5th digit of the 10-digit number.
3. First digit of the 10 digits is 6–9.
4. Not embedded in a longer digit sequence. A 10-digit run starting 0–5 is rejected.

### FR-O Overlaps
Priority: more strictly validated → longer span → earlier start. Every final span has exactly one type.

### FR-T Transforms
- **Mask:** Aadhaar keep last 4; mobile keep last 2; PAN keep last 1; others `X`; preserve separators; leave unrelated text untouched.
- **Tag:** `HMAC-SHA256(key, normalised_value)` → truncated hex → `[TYPE:tag]`. Key from `PII_GUARD_KEY`. Missing/empty key in tag mode ⇒ hard error, never an unkeyed fallback. Equivalent formats ⇒ same tag.

### FR-I Interfaces
- `find_spans(text)` and `mask_text(text, mode=...)` (see `Architecture.md` for the schema).
- CLI: `pii-guard mask < in.txt > out.txt`, with a documented mode switch.

## 7. Evaluation requirements
- ≥ 300 labelled synthetic lines, fixed seed, spans `(type, start, end)`.
- Includes positives (all formats), hard negatives (12-digit order IDs, 16-digit card-like, 10-digit starting 0–5, timestamps, malformed PAN, Verhoeff-failing Aadhaar-like) and ≥ 30 awkward/obfuscated cases (line-broken digits, dot separators, spelled-out digits, non-Latin digits) with explicit expected behaviour.
- `eval.py`: exact entity-level match; precision/recall/F1 per type and overall; writes all FPs/FNs to `eval/failures.md`.
- No tuning against the dataset used for the final score. If detectors change → new seed → report both runs.

## 8. Non-functional requirements
Offline. No telemetry. No temp files in the CLI path. Never log raw matches or the key. Synthetic data only. `.env` in `.gitignore`.

## 9. Success criteria
A new user can clone → install → run tests → run eval → reproduce README metrics → run `pii-guard mask` on synthetic input. Generated code without passing checks is **not** done.

## 10. Open decisions (resolve, don't guess — track in `memory.md`)
D1 span type strings & return container · D2 strictness ranking for overlaps · D3 whether mobile prefix digits are masked · D4 tag length (suggest 8 hex) · D5 CLI mode flag name · D6 PAN case normalisation before hashing · D7 license choice.
