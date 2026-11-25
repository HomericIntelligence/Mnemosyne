---
name: python-star-import-consumers-explicit-exports-hygiene
license: BSD-3-Clause
description: "Convert star-import consumers of a shared Python hub to explicit name-as-name re-exports, keep the hub __all__ surface free of stdlib names, and guard the surface so audit shadow lists and import-graph drift cannot return. Use when an audit or linter flags star imports or an __all__ that re-exports stdlib names, when consumers rely on import * with noqa F403/F405, or when the audited export count must always match what consumers import."
category: architecture
date: 2026-11-24
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [python, star-import, explicit-re-export, all-hygiene, export-surface, audit, import-guard, f403, f405, public-api, boundary-test]
---

# Convert Star-Import Consumers to Explicit Exports and Keep the Hub Surface Clean

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-24 |
| **Objective** | Let a shared Python hub keep an auditable public surface: every consumer imports the hub names it uses, the hub `__all__` lists only domain-meaningful names, and a guard keeps both properties true. |
| **Outcome** | Zero `from hub import *` consumers and zero noqa F403/F405 suppressions; each consumer imports a subset of the audited hub names; the hygiene guard fails closed on stdlib and unintended private entries. |
| **Verification** | Verified locally with behavior-first RED/GREEN tests, focused consumer suites, ruff, the type check, and a whole-tree run whose residual failures were all baseline-identical environmental cases. |

## When to Use

- A code audit or linter reports `import *` consumers, `F403`/`F405` suppressions, or an audit
  shadow list of names that consumers reach through a hub.
- A hub `__all__` re-exports stdlib names (for example typing helpers, json, logging, re,
  hashlib), so the export count includes names the package does not own.
- A consumer refactor must keep type-checking or audit parity: the names a consumer imports stay
  inside the audited hub surface.
- A boundary test for the hub uses a text-prefix matcher and cannot follow a from-import
  re-export, so names can drift out of the audit set without a failure.

## Verified Workflow

### Quick Reference

```python
# Before: the consumer hides its real imports.
from hub import *  # noqa: F403,F405

# After: the consumer names what it uses.
from hub import fetch_one, fetch_many
```

```python
# Before: the hub re-exports names it does not own.
__all__ = ["Thing", "Any", "cast", "json"]

# After: the hub lists only domain-meaningful names.
__all__ = ["Thing", "fetch_one", "fetch_many"]
```

### Detailed Steps

1. **Inventory the surface.** List the hub `__all__` entries and every `from hub import *`
   consumer site. The audited count is the contract input: each consumer imports a subset of these
   names, and the total must equal the domain-meaningful surface.

2. **Strip stdlib and unrelated names from the hub.** A hub exports domain names only.
   `typing` helpers, `json`, `logging`, `re`, `hashlib`, and other stdlib names leave `__all__`;
   consumers that need a stdlib name import it from the stdlib directly.

3. **Convert each consumer to explicit name-as-name imports.** Replace `import *` and its noqa
   suppressions with a sorted explicit list. Delete per-consumer imports the conversion makes dead,
   including stdlib names the hub had silently re-exported and names listed in the hub surface
   that were defined nowhere downstream.

4. **Resolve every unresolved-name error as a decision, not a cleanup.** An F821 after conversion
   can mean a rename, not a missing import. Trace the hub history for a rename before you invent a
   new name.

5. **Freeze the surface before you run the gates.** Commit the hub and consumer edits first.
   Re-derive the audited counts from the frozen tree, then run the hygiene guard, ruff, the
   formatter, the type check, and the focused suites.

6. **Hold parity with the hygiene guard.** The guard rejects an `__all__` that contains a stdlib
   name, and rejects underscore-prefixed entries unless the owner lists them explicitly as
   intended. Run the guard in pre-commit so the surface cannot drift back.

7. **Prove the conversion at the trust boundary.** A consumer that imports an explicit name must
   still pass the dependency or boundary test that used to allow the star form, and a negative
   case must prove the guard refuses a stale star consumer.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Convert consumers only | Rewrote the star consumers to explicit imports and left the hub `__all__` entries untouched. | The audited hub surface still contained stdlib names, so export counts and the audit shadow list survived the conversion. | Convert hubs and consumers together; the guard owns the hub surface. |
| Add the guard without a negative test | Wrote the hygiene rule and one passing case per hub. | The rule could not prove it refused a bad entry, so a weakening of the matcher stayed green. | Give the guard a synthetic negative case that fails closed. |
| Treat every unresolved name as a new import to invent | After conversion, treated unresolved consumer names as missing symbols to add. | Several names were renames of existing hub entries; inventing a new name split the public API and broke the consumer. | Trace the hub history for a rename before you touch the surface. |

## Results & Parameters

### Public Contract

- The set of names each consumer imports is a subset of the audited hub names.
- The audited export count equals the number of domain-meaningful names in the hub `__all__`.
- The hub `__all__` contains no stdlib name.
- An underscore-prefixed entry needs an explicit owner assertion of intent.

### Hygiene Guard Behavior

```text
Reject:  an __all__ entry is a stdlib name (json, re, logging, hashlib, typing helpers).
Reject:  an __all__ entry starts with an underscore without an explicit allowlisted intent.
Accept:  every entry is a domain-meaningful name owned by the package.
```

### Expected Guard and Lint Outcome

```text
$ ruff check <hubs-and-consumers>
All checks passed!
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Python automation library | Seven star-import consumers of two aggregate hubs converted; hub surfaces freed of all stdlib entries; hygiene guard added | Consumer token sets traced to subset audits; unresolved names resolved to three renames of existing hub entries; guard RED/GREEN verified with 22 behavior tests; focused consumer suites green; ruff, format, and type check clean on all touched paths; whole-tree run residual failures all baseline-identical environmental cases. |

## Privacy Note

This entry stores the general pattern and counts only. Source symbol names and session evidence
that could identify a project remain in the companion notes file, which normal retrieval does not
include.

## References

- [Ruff F403/F405 documentation](https://docs.astral.sh/ruff/rules/undefined-local-with-import-star/)
- [PEP 8 public interface guidance](https://peps.python.org/pep-0008/#public-interface)
- [Automation checkout cleanliness](automation-clean-checkout-intermediate-artifacts.md)
- [Import patterns and compatibility guards](python-import-patterns-and-compatibility-guards.md)
- [Symbol-scoped import exemptions](symbol-scoped-import-exemptions.md)
