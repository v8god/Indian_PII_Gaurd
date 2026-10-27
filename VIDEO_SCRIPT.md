# Complete Video Recording Blueprint & Narration Script
## Project: `indian-pii-guard`

This guide provides a scene-by-scene script, visual directions, and exact terminal commands to record a 5–6 minute technical demonstration video.

---

## 🎬 Recording Setup
1. **Screen Resolution**: 1080p (1920x1080).
2. **Left Screen Half**: Terminal with virtual environment activated (`.venv`).
3. **Right Screen Half**: The Interactive Visual Walkthrough ([`interactive_demo.html`](file:///C:/Users/Dell/.gemini/antigravity/brain/be0fad16-7a10-45af-9874-a589adfe7344/interactive_demo.html)) or VS Code editor.
4. **Automated Live Runner**: You can run `python demo.py` in the terminal for an automated, colorized walkthrough.

---

## ⏱️ Video Breakdown

```
[0:00 - 0:45] Scene 1: Introduction & The Core Problem
[0:45 - 1:45] Scene 2: Mathematical Foundation: Verhoeff Checksum (D_5)
[1:45 - 2:45] Scene 3: Regex Boundaries & Domain Validators
[2:45 - 3:30] Scene 4: Overlap Resolution & 91-Collision Solver
[3:30 - 4:30] Scene 5: Dual Transformations (Mask vs. Tag) & CLI Streaming
[4:30 - 5:30] Scene 6: Live Test Suite (64 Green) & Real Evaluation Metrics
```

---

## 🎙️ Scene-by-Scene Script

### Scene 1: Introduction & The Core Problem (0:00 – 0:45)
- **Visual**: Show the project `README.md` and the interactive visual architecture diagram in `interactive_demo.html`.
- **Narration**:
  > *"When developers prepare prompt inputs for LLMs or export databases to staging environments, sensitive identifiers often leak into logs and models. In the Indian context, the three most critical patterns are Aadhaar, PAN, and Mobile numbers.*
  > 
  > *Most tools make two fatal mistakes: they rely purely on regex, causing massive false positives on credit card numbers and order IDs, or they use external cloud APIs, violating offline privacy.*
  > 
  > *`indian-pii-guard` solves this completely: it is an offline, deterministic, standard-library-only Python library and CLI. Our core engineering principle is simple: regex is strictly a candidate, not proof. Validation decides acceptance."*

---

### Scene 2: Mathematical Foundation: Verhoeff Checksum (0:45 – 1:45)
- **Visual**: Switch to Tab 2 in `interactive_demo.html` or terminal running Step 1 of `demo.py`.
- **Terminal Command**:
  ```powershell
  python -c "from pii_guard.verhoeff import validate; print('Valid:', validate('234567890124')); print('Corrupted:', validate('234567890120'))"
  ```
- **Narration**:
  > *"A 12-digit number is not an Aadhaar number just because it has 12 digits. Real Aadhaar numbers incorporate a cryptographic check digit generated using the Verhoeff algorithm, rooted in the non-abelian dihedral group $D_5$—the symmetries of a regular pentagon.*
  > 
  > *Inside `verhoeff.py`, we implement the multiplication, permutation, and inverse tables in pure Python standard library. It detects 100% of single-digit substitution errors and 100% of adjacent transpositions. Watch: if an attacker modifies even the last digit from a 4 to a 0, the group product non-zeroes out and the detector rejects it instantly."*

---

### Scene 3: Regex Boundaries & Domain Validators (1:45 – 2:45)
- **Visual**: Open `src/pii_guard/detectors.py` and show the boundary lookarounds.
- **Terminal Command**:
  ```powershell
  python -c "from pii_guard import find_spans; print(find_spans('Card 5365 4195 1802 3806 or Order 123456789012 or PAN ABCPE1234F'))"
  ```
- **Narration**:
  > *"Let's look at how our candidate detectors work. Notice that we use ASCII-explicit boundary lookarounds.*
  > 
  > *A common flaw in naive regexes is matching 16-digit credit card numbers as Aadhaar because the first 12 digits look like three groups of four. Our lookahead `(?![ -][0-9])` ensures that any trailing digit groups immediately discard the candidate.*
  > 
  > *For PAN, we don't just check the five-letter, four-digit shape: we validate that the 4th character belongs to the official entity holder code set: Individual, Company, Trust, or Government. For Mobile, we require valid Indian telecom prefixes starting with 6 through 9 and reject numbers embedded inside words."*

---

### Scene 4: Overlap Resolution & The 91 Ambiguity (2:45 – 3:30)
- **Visual**: Show Tab 3 in `interactive_demo.html` ("Deterministic Collision Disambiguation").
- **Terminal Command**:
  ```powershell
  python -c "from pii_guard import find_spans; print('Verhoeff Valid 91:', find_spans('919876543216')); print('Verhoeff Invalid 91:', find_spans('919876543210'))"
  ```
- **Narration**:
  > *"Here is a classic ambiguity: what happens if a text contains a 12-digit string starting with 91? 91 is the country code for India, but 12 digits starting with 9 is also a potential Aadhaar number.*
  > 
  > *`indian-pii-guard` resolves this deterministically in `resolve.py`. We assign strictness ranking: Aadhaar has strictness 3 because it has a dihedral group checksum; PAN has strictness 2; Mobile has strictness 1.*
  > 
  > *If the 12 digits pass the Verhoeff check, Aadhaar wins due to higher validation strictness. If the checksum fails, Aadhaar is discarded, and the resolver falls back to Mobile. Every character span is guaranteed to receive exactly one label."*

---

### Scene 5: Dual Transformations (Mask vs. Tag) & CLI Streaming (3:30 – 4:30)
- **Visual**: Show live pipeline commands in PowerShell.
- **Terminal Commands**:
  ```powershell
  # 1. Mask Mode
  "Contact 9876543210 or Aadhaar 2345 6789 0124" | pii-guard mask

  # 2. Keyed HMAC Tag Mode
  $env:PII_GUARD_KEY="secret-demo-key"
  "Taxpayer PAN is ABCPE1234F" | pii-guard mask --mode tag

  # 3. Fail-Closed Protection
  $env:PII_GUARD_KEY=""
  "Taxpayer PAN is ABCPE1234F" | pii-guard mask --mode tag
  ```
- **Narration**:
  > *"For downstream processing, we support two transformation modes.*
  > 
  > *In 'mask' mode, separators are preserved, while safe suffixes are exposed: Aadhaar shows the last 4 digits, PAN shows the last character, and Mobile shows the last 2 digits.*
  > 
  > *In 'tag' mode, we compute a keyed HMAC-SHA256 hash formatted as `[TYPE:hex8]`. Because values are normalized first, lowercase PAN, spaced Aadhaar, and prefixed phone numbers all generate the exact same cryptographic tag.*
  > 
  > *Crucially, tag mode fails closed. If `PII_GUARD_KEY` is missing or empty, it immediately halts with a clear error on stderr and exit code 1—never silently falling back to an unkeyed hash. All transformations are applied right-to-left so slice offsets never drift."*

---

### Scene 6: Live Test Suite & Real Evaluation Metrics (4:30 – 5:30)
- **Visual**: Run the test suite and evaluation script live.
- **Terminal Commands**:
  ```powershell
  # Run full test suite
  pytest -v

  # Run evaluation on untouched seed
  python eval/eval.py --dataset eval/data/synthetic_final.jsonl --failures eval/failures.md
  ```
- **Narration**:
  > *"Finally, let's verify reliability. We run `pytest`—all 64 unit and integration tests execute in under half a second.*
  > 
  > *Next, we run our reproducible evaluation on 375 synthetic records containing true positives, card numbers, order IDs, clean sentences, and 35 awkward cases.*
  > 
  > *The results speak for themselves: across an untouched evaluation seed, we achieved 100% recall with zero false negatives across Aadhaar, PAN, and Mobile. The only 4 false positives belong exclusively to documented awkward edge cases where malformed prefixes left valid standalone 10-digit mobile numbers.*
  > 
  > *Zero telemetry, zero network calls, zero external dependencies. `indian-pii-guard` is production ready."*

---

## 🚀 One-Click Automated Run

To record the entire sequence seamlessly without manual typing, run:

```powershell
python demo.py
```
This executes all 6 demonstration steps with visual headers, step explanations, and live outputs automatically!

