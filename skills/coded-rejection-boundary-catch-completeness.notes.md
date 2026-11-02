# Notes: coded-rejection-boundary-catch-completeness

Supporting evidence for the main entry. Privacy screened: no repository,
organization, user, issue, or internal path identifiers.

## Trigger evidence

A request route accepted a path string with only a minimum-length check. The
path reached a path-based intake under a boundary that caught two typed errors.
The intake ran three calls that can fail:

| Order | Call | Fault for this input | Type raised | Caught? |
| --- | --- | --- | --- | --- |
| 1 | Best-effort size read before a quota reservation | Embedded NUL byte | `ValueError` | No |
| 2 | Strict path resolution | Embedded NUL byte | `ValueError` | No |
| 2 | Strict path resolution | Symbolic-link loop | `RuntimeError` | No |
| 2 | Strict path resolution | Untraversable parent | `OSError` | Yes |
| 3 | Authorized open | Missing file, permission fault | `OSError` | Yes |

The uncaught faults reached the framework default handler and returned HTTP 500.
The change under review claimed that client-input faults return a 4xx. The claim
was false for the malformed-path cases.

## Reproduction detail

The fault is deterministic and needs no special setup. Confirm the exception
type on the runtime that serves the code:

```python
from pathlib import Path

bug = Path("/allowed/root/name\x00.jsonl")
try:
    bug.resolve(strict=True)
except OSError:
    print("caught")
except ValueError as error:
    print("value error:", error)   # malformed path: embedded null character
```

Build the loop case with two links that point at each other inside an allowed
root. Confirm the type that resolution raises on your interpreter before you add
the test.

## What the repair changed

- The resolution call caught `(OSError, ValueError, RuntimeError)`.
- The best-effort size read caught `(OSError, ValueError)`.
- Both faults mapped to one code and one public message. The detailed text went
  to the server log only.
- The interface sentence changed from "before any filesystem access" to "before
  it opens the file". This matched the real order.

## Test evidence

Each regression test failed against the unrepaired boundary. The failures showed
the raw `ValueError`, the raw `RuntimeError`, and the HTTP 500 response. The
tests passed after the repair. The project suites for the batch intake, the
command line, the quotas, and the route passed. Lint and the documentation build
passed on the changed files.

## Review-process evidence

A coordination note named three defect shapes in a competing change. One shape
matched this code. The other two did not hold on the reviewed head. The note was
treated as a lead, not as a finding, and each shape was reproduced again on the
current head before it was trusted or dismissed.

## Relation to other entries

- [Generic error code hides seam type mismatch](../skills/generic-error-code-hides-seam-type-mismatch.md)
  covers one code that folds many causes. This entry covers a boundary that does
  not reach the code at all.
- [Strip embedded NUL at subprocess egress](../skills/subprocess-embedded-null-byte-sanitize.md)
  covers NUL at subprocess argument construction. This entry covers NUL in a
  filesystem path, where the type is `ValueError` from `pathlib` and the
  filesystem calls.
- [Typed boundary cause diagnostic on exit](https://github.com/HomericIntelligence/Mnemosyne/pull/3747)
  is an open change. It prints the cause at a typed boundary. It does not change
  which types the boundary catches, so there is no overlap.