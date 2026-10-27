# Known Limitations — indian-pii-guard

This document transparently records the architectural boundaries, intentionally unsupported formats, and known edge-case behaviors of `indian-pii-guard`.

---

## 1. Scope and Non-Goals

`indian-pii-guard` is a pattern utility designed specifically for three Indian identifier formats: **Aadhaar**, **PAN**, and **Indian Mobile Numbers**.

The following are explicit non-goals:
- **Other Personal Identifiers**: Person names, physical addresses, email addresses, passport numbers, voter ID (EPIC), driving licenses, and bank account / IFSC numbers are not detected.
- **Unstructured / Binary Formats**: Only plain text strings are supported. Scanned images, PDFs, Word documents, audio, and video files are not parsed.
- **Non-Indian Identifiers**: Social Security Numbers (SSN), UK National Insurance numbers, European IBANs, and non-Indian international phone numbers are out of scope.
- **Compliance Certification**: This package is a pattern utility and does not constitute a regulatory compliance product or GDPR / DPDP Act certification tool.

---

## 2. Unsupported Formatting Variations

### A. Non-ASCII Digits (Devanagari, etc.)
- **Behavior**: All regex detectors strictly use ASCII digit classes (`[0-9]`). Non-Latin numerals (e.g., Devanagari `०१२३४५६७८९`) are not detected.
- **Reasoning**: Deterministic behavior without Unicode normalization ambiguities.

### B. Spelled-Out Numbers
- Numbers written out in words (e.g., *"nine eight seven six five four three two one zero"*) are not detected.

### C. Line Breaks and Non-Standard Delimiters
- **Line Breaks**: Values broken across line boundaries (e.g., `98765\n43210`) are not matched.
- **Dot and Slash Delimiters**: Delimiters other than single spaces or hyphens (e.g., `98765.43210`, `2345/6789/0123`) are not matched.
- **Irregular Spacing**: Double spaces or mismatched separators (e.g., `2345 6789-0123`) are rejected.

---

## 3. Discovered Ambiguities & Edge-Case Behaviors

### A. 12-Digit Mobile (`91` + 10 digits) vs. Aadhaar Collision
- **Scenario**: A 12-digit sequence starting with `91` followed by 10 digits starting with `6–9` (e.g. `919558523986`) matches both Mobile and Aadhaar candidate shapes.
- **Resolution**: If the full 12 digits happen to satisfy the Verhoeff dihedral group checksum, the overlap resolver awards the span to **Aadhaar** due to validation strictness (`Aadhaar` > `Mobile`). If Verhoeff validation fails, it resolves to **Mobile**.
- **Collision Frequency**: Because the Verhoeff check digit occupies 1 of 10 states ($0..9$), exactly $\approx 10\%$ (1 in 10) of random bare `91` 10-digit mobile numbers (e.g. `919558523986`) will coincidentally satisfy the Verhoeff checksum. In empirical tests of 3,000 bare `91` mobile strings, exactly 300 (10.0%) were resolved as Aadhaar. Consequently, recall on bare `91` mobile numbers without `+` or spaces is bounded at $\approx 90\%$.

### B. Malformed Prefixes Followed by Separators
- **Scenario**: Inputs like `(+91) 9876543210`, `-91 9876543210`, or `++91 9876543210` feature malformed prefixes followed by a space.
- **Resolution**: The standard 10-digit number following the space (`9876543210`) is detected as a standalone mobile number span because it satisfies all 10-digit mobile criteria. The preceding malformed prefix characters are not absorbed into the span.

### C. 16-Digit Card vs. Preceding Digit Boundaries
- **Scenario**: 16-digit credit and debit cards are commonly formatted as four groups of four digits (`4-4-4-4`).
- **Resolution**: Aadhaar regex lookarounds specifically look behind and ahead for 4-digit card chunks (`(?<![0-9]{4}[ -])` and `(?![ -][0-9]{4})`). This ensures 16-digit card numbers are rejected even if their first 12 digits satisfy Verhoeff, while correctly allowing valid Aadhaar numbers preceded by single digits in normal text (e.g. `qty 7 2345 6789 0124`).

### D. Synthetic vs. Real Data Coincidence
- The Verhoeff check digit generation produces mathematically valid numbers based on random synthetic payloads. In rare instances, generated synthetic numbers may coincidentally match assigned numbers in the physical world. This tool was developed, evaluated, and tested exclusively using synthetic payloads.

---

## 4. Failure Summary from Evaluation

As recorded in `eval/failures.md`, across 375 evaluation lines:
- **0 False Negatives** (100% recall on valid formats).
- **4 False Positives** strictly originating from the documented awkward/obfuscated test cases where malformed prefixes left valid standalone 10-digit sequences.

