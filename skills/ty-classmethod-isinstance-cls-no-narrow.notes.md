# Notes: ty-classmethod-isinstance-cls-no-narrow

Supporting evidence for the main entry. Privacy-safe: no repository,
organization, host path, issue, or proprietary code identifiers.

## Source evidence

- A classmethod rebuilt a sealed transport type from a union parameter:
  an already-sealed instance (text fields) or a verified instance (byte fields).
- The pass-through branch used `isinstance(value, cls)`.
- The checker (ty) reported, on the build lines:
  `Object of type 'Raw | Cooked' is not assignable to 'Raw'` and a
  missing-attribute error for `.decode` on a `bytes | str` union, at the two
  field-decode lines.
- Intermediate attempt: `source: Raw = verified` after the branch. Rejected with
  the same union-assignability error, which proved the branch had not narrowed.
- Fix: `isinstance(value, SealedType)` with the concrete class name. Both
  diagnostics cleared with no other change; the focused tests stayed green and
  the checker reported no diagnostics on the module.

## Tool notes

- The checker resolves `cls` in a classmethod as `type[Self]`; a union test
  against an unbound `type[Self]` gives no negative-branch narrowing.
- Sibling entry `mypy-narrow-cast-not-assert-ruff-s101` covers a different
  narrowing decision (cast versus assert under mypy with ruff S101). This entry
  covers the isinstance target itself under ty.

## Limits

- verified-local; one ty release observed. Later releases may narrow
  `type[Self]`; the Quick Reference test is one line to re-check.
- The pass-through branch also changed runtime behavior slightly: instances of
  the concrete class now return early. That was the intended contract.
