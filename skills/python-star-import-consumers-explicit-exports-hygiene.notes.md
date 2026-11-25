---
name: python-star-import-consumers-explicit-exports-hygiene
license: BSD-3-Clause
type: notes
---

# Notes: python-star-import-consumers-explicit-exports-hygiene

Supporting evidence for the canonical entry. Normal retrieval excludes this file.

## Source Context

- A shared automation library kept two aggregate hubs whose `__all__` lists re-exported stdlib
  names (typing helpers, json, logging, re, hashlib, and similar). Seven consumer modules imported
  both hubs with `import *` plus noqa F403/F405. An audit listed the unreached names as an audit
  shadow list.
- After conversion the audited surfaces held 56 and 39 domain-meaningful names.

## Conversion Decisions

| Observation | Disposition |
| --- | --- |
| Unresolved consumer names after conversion | Resolved to three renames of existing hub entries, not missing imports: one issue-mutation helper renamed to the hub entry it now re-exports, and three query helpers renamed to their hub-family entries. Call sites were renamed, not stubbed. |
| Stdlib names in hub `__all__` | Removed from both hub surfaces; consumers that need them import the stdlib directly. |
| Dead code surfaced by the conversion | Removed unused stdlib imports from the transport hub (for example hashlib and time) and dropped one entry that the surface listed but no consumer could reach through explicit imports. |

## Verification Evidence

- Hygiene guard: 22 behavior tests, RED/GREEN on both hubs, negative cases fail closed.
- Focused consumer suites green, including a direct-importer suite that proved explicit imports
  still satisfy the boundary contract.
- `ruff check`, `ruff format --check`, and the type check clean on all ten touched paths.
- Committed whole-tree run: 13,915 passed, 45 skipped, 15 failed; every failure baseline-identical
  to the main branch (environment-bound cases), none introduced by the conversion.
- Sandbox pre-flight rejections seen during an intermediate dirty-tree run passed after commit;
  root cause recorded in `automation-clean-checkout-intermediate-artifacts` (v1.1.0).

## Privacy Disposition

Source symbol names, hub names, consumer module names, and session evidence remain here or in Git
history only. The canonical entry keeps the generalized pattern, counts, and guard contract.
