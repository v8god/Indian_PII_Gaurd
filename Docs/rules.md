# Rules — indian-pii-guard (read before every session)

## Hard rules
1. **Synthetic data only.** Never type, paste or commit a real Aadhaar/PAN/phone/key. Generated Aadhaar-like numbers may coincide with real ones; say so in docs.
2. **No network, no telemetry, no temp files** in package or CLI code.
3. **Never log or print** raw matched values or the key. Diagnostics may include type + offsets only.
4. **Tag mode fails closed.** No key ⇒ error. No silent unkeyed hash.
5. **Regex is a candidate, not proof.** Validate before accepting.
6. **Offsets refer to the original input**, zero-based, half-open.
7. **Do not tune on the final-report dataset.** Detector change ⇒ new seed ⇒ report both runs.
8. **Publish only numbers the script produced.** Never type metrics from memory.
9. Don't claim "robust", "comprehensive", "compliant", "enterprise-grade".
10. Known-unsupported forms are reported as limitations, never silently dropped.

## Engineering rules
- Standard library only for runtime code.
- Type hints on public functions; docstrings state the schema.
- One behaviour per test; test names say what is being proved.
- Fake test key must look obviously fake (e.g. `test-key-not-secret`).
- Keep modules small and single-purpose (see `Architecture.md`).
- If a requirement is ambiguous, record it in `memory.md` under Open decisions and ask the owner. Don't pick silently.

## Definition of done
Only the acceptance checklist in the brief §12 counts: clean clone → install → test → eval → README numbers reproduce → CLI demo. "Code generated" ≠ done.

## Forbidden
Adding detectors for names/emails/addresses · adding dependencies without approval · committing `.env` · publishing numbers from a tuned dataset · rewriting history to hide a failure.
