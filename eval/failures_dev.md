# Evaluation Failure Report — indian-pii-guard

Total synthetic evaluation lines evaluated: **375**

## Metric Summary

| Type | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| AADHAAR | 79 | 1 | 0 | 0.9875 | 1.0000 | 0.9937 |
| PAN | 79 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| MOBILE | 83 | 4 | 1 | 0.9540 | 0.9881 | 0.9708 |
| OVERALL | 241 | 5 | 1 | 0.9797 | 0.9959 | 0.9877 |

---

## Failure Details (6 total failures)

### 1. [FALSE_POSITIVE] AADHAAR in `syn-0155`

- **Category:** `positive_mobile`
- **Expected behavior:** detect_mobile
- **Span offset:** `[25, 37)`
- **Matched slice:** `919558523986`
- **Line text:** `Call customer service on 919558523986 between 9 AM and 6 PM.`
- **Known limitation:** `False`

### 2. [FALSE_NEGATIVE] MOBILE in `syn-0155`

- **Category:** `positive_mobile`
- **Expected behavior:** detect_mobile
- **Span offset:** `[25, 37)`
- **Matched slice:** `919558523986`
- **Line text:** `Call customer service on 919558523986 between 9 AM and 6 PM.`
- **Known limitation:** `False`

### 3. [FALSE_POSITIVE] MOBILE in `syn-0370` *(Known Limitation)*

- **Category:** `awkward_obfuscated`
- **Expected behavior:** reject_irregular_spaces
- **Span offset:** `[26, 39)`
- **Matched slice:** `0 98765 43210`
- **Line text:** `Leading zero with spaces: 0 98765 43210 invalid spacing.`
- **Known limitation:** `True`

### 4. [FALSE_POSITIVE] MOBILE in `syn-0373` *(Known Limitation)*

- **Category:** `awkward_obfuscated`
- **Expected behavior:** reject_leading_hyphen
- **Span offset:** `[19, 32)`
- **Matched slice:** `91 9876543210`
- **Line text:** `Hyphen before 91: -91 9876543210 rejected.`
- **Known limitation:** `True`

### 5. [FALSE_POSITIVE] MOBILE in `syn-0374` *(Known Limitation)*

- **Category:** `awkward_obfuscated`
- **Expected behavior:** reject_multiple_plus
- **Span offset:** `[26, 36)`
- **Matched slice:** `9876543210`
- **Line text:** `Multiple plus signs: ++91 9876543210 rejected.`
- **Known limitation:** `True`

### 6. [FALSE_POSITIVE] MOBILE in `syn-0375` *(Known Limitation)*

- **Category:** `awkward_obfuscated`
- **Expected behavior:** reject_parenthesized_prefix
- **Span offset:** `[28, 38)`
- **Matched slice:** `9876543210`
- **Line text:** `Parenthesized prefix: (+91) 9876543210 awkward.`
- **Known limitation:** `True`

