---
name: release-embedded-script-capability-guard
description: "Guard each new evidence retrieval inside a script that a release embeds, because the same script runs against earlier releases that lack the capability. Use when: (1) a change adds an API and, in the same change, adds a heredoc, bootstrap record, or generated script that calls it, (2) the script can execute against a pinned earlier release where the API does not exist, or (3) an unguarded call raises AttributeError or an equivalent missing-symbol failure only on pre-change versions."
category: tooling
date: 2026-10-27
version: "1.0.0"
user-invocable: false
tags: [release, embedded-script, heredoc, capability-guard, getattr, backward-compatibility, graceful-degradation, bootstrap, version-skew, evidence]
---

# Capability-Guard Scripts Embedded in a Release

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-27 |
| **Objective** | Add evidence retrieval to a script that ships inside a release artifact without breaking the same script on earlier releases. |
| **Outcome** | Successful; the retrieval became a guarded probe that degrades to a skip on pre-capability releases, and the change merged. |

A release artifact can embed executable text: a Python heredoc in a shell
installer, a bootstrap record, or a generated helper. That one text runs
against every release of the fleet, not only the release that introduced it.

When a change adds a capability, for example a database evidence function,
and in the same change extends the embedded script to call it, the call site
must not assume the capability. An earlier pinned release runs the new script
against code older than the capability. An unguarded call fails with a
missing-symbol error on exactly the versions that must continue to work.

Guard the retrieval with a capability probe, and degrade to an explicit skip
when the probe fails. The new release reports the new evidence; earlier
releases report that the evidence is not available, and continue.

## When to Use

- A pull request adds both a capability and, in an embedded script, a first
  caller of that capability.
- The embedded script runs against a fleet of pinned releases, and some are
  older than the change.
- A version that predates the capability must keep its pre-change behavior
  for the guarded step.
- You review embedded text and must decide whether each new call needs a
  probe.

## Verified Workflow

### Quick Reference

```python
# Inside the embedded heredoc: probe, then branch on the probe.
evidence_fn = getattr(db, "migration_ledger_evidence", None)
if evidence_fn is None:
    record["ledger"] = "unavailable: release predates the migration ledger"
else:
    record["ledger"] = evidence_fn()
```

### Suggested Approach

1. List each name the embedded text uses that the same change introduces.
   Each one needs a probe; names that predate the change do not.
2. Probe with `getattr(obj, "name", None)` or `hasattr` for an object member,
   and with a command-exists test for a shell-level tool. Do not probe by
   catching the failure: an exception handler hides unrelated defects in the
   same call.
3. On probe failure, write an explicit degradation record into the output, for
   example an `unavailable: ...` marker, and continue the script. A silent
   skip makes the absence indistinguishable from an empty result.
4. Test both branches: one fixture that offers the capability and one that
   lacks it. The lacking fixture proves the pre-release path stays alive.

Keep the probe at the retrieval site. Guarding at the caller of the whole
script hides which capability is missing and degrades more than the one new
step.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Direct call | The embedded script called the new evidence function unconditionally | Earlier releases raised a missing-symbol error on a step that did not exist for them | The script and the capability ship together but run apart; gate the call on the capability, not on the change |

## Results & Parameters

### Configuration

```bash
# Shell-level probe for an optional tool inside an installer heredoc:
if command -v ledger-digest >/dev/null 2>&1; then
  ledger-digest --verify
else
  echo "ledger digest: unavailable in this release" >&2
fi
```

### Expected Output

- On a release that has the capability, the script emits the new evidence.
- On a release that predates the capability, the script emits the explicit
  unavailable marker and exits with the pre-change success path.
- The failing case is never an unhandled missing-symbol traceback.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A database-backed release promotion gate | One PR; review recovered the unguarded retrieval before merge, the probe form merged green | Companion tree-listing practice in [git-tree-enumeration-prefixed-names](git-tree-enumeration-prefixed-names.md) |

## Related Entries

- [optional-cli-dependency-layered-degradation](optional-cli-dependency-layered-degradation.md) — degrade CLI behavior layer by layer when a dependency is absent
- [python-import-patterns-and-compatibility-guards](python-import-patterns-and-compatibility-guards.md) — import-time compatibility guards for optional modules
- [error-message-consistency-optional-dependency-pola](error-message-consistency-optional-dependency-pola.md) — keep the absent-dependency message consistent across versions
