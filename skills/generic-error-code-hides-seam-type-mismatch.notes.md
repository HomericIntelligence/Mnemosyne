# Notes: generic-error-code-hides-seam-type-mismatch

Supporting evidence for the main entry. Privacy-safe: no repository,
organization, host path, issue, or proprietary code identifiers.

## Source evidence

- A bounded worker pattern: a parent process spawns a restricted child, sends one
  serialized frame, and reads one JSON reply. The child folds every internal
  exception into one generic reply code by design (containment).
- The caller-side adapter wrapped its callee with
  `except Exception: raise DomainError(GENERIC) from error`.
- Symptom: a whole test group failed with the generic code only.
- First hypothesis (child-side serialization of a sequence field) was patched;
  the failure count did not change.
- Second probe: the child body, run in isolation with the exact frame, produced a
  valid success reply. The child was innocent.
- Third probe: an in-harness test called the parent-side steps one at a time and
  surfaced `AttributeError` in the frame builder: the object passed across the
  seam was the verified type (byte fields), while the callee required the sealed
  type (text fields), and the sealed type's dump method did not exist on it.
- Fix: seal the verified inputs once at the boundary (a constructor that accepts
  either form). Both the in-process path and the worker path then passed; the
  failing group went green.
- The child's stderr was discarded by the parent, which is why no traceback was
  reachable from the reply code alone.

## Relation to sibling entries

- `tooling-subprocess-json-fail-closed-result-validation`: how to build a
  validator wrapper that fails closed honestly. This entry starts where that one
  ends: the wrapper already fails closed, and the generic code now hides bugs.
- `verify-audit-issue-reproduces-before-fixing`: reproduce before fixing, for
  audit findings across revisions. This entry applies the same discipline to a
  runtime exception across a process or type boundary.

## Limits

- verified-local; the failing group went green after the fix, CI not observed.
- The containment design (one generic reply code) is intentional; the lesson does
  not argue against it. It argues for reachable causes (captured stderr or a
  logged cause) plus a seam-probe discipline when a failure class appears.
