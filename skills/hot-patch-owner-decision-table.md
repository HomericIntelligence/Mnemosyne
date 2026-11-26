---
name: hot-patch-owner-decision-table
license: BSD-3-Clause
description: "Give an interim hot patch the exact decision table that the owner approved, and record where it diverges from the planned main fix. Use when an urgent patch must run against a live service, when the owner corrects a rule during an incident, or when a patch has destructive side effects on shared state."
category: tooling
date: 2026-11-26
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [hot-patch, interim-fix, decision-table, owner-rule, divergence-record, incident-response]
---

# Hot Patch Owner Decision Table

## Overview

| Field | Value |
| ------- | --------------- |
| **Date** | 2026-11-26 |
| **Objective** | Make an interim hot patch act exactly as the owner decided, and make its differences from the durable fix explicit. |
| **Outcome** | Operational. A patch written from a paraphrased rule acted on more objects than the owner allowed. The case table and the divergence record prevent a repeat. |

## When to Use

- An urgent patch must run against a live service before the durable fix ships.
- The patch changes shared or destructive state: it revokes, deletes, rewrites, or replaces objects that other users or lanes depend on.
- The owner states a rule during the incident, and a helper relays it.
- A patch is applied to a checkout or a running process while the durable fix continues on the default branch.

## Verified Workflow

### Quick Reference

```text
Write the owner's rule as a case -> action table.
Put the table in the patch ticket and in the patch itself (comment or test).
Name what the patch must never touch.
Record each deliberate difference from the planned durable fix.
Apply, then check every row against a read-only probe.
When the owner corrects a rule, re-check the applied patch before the next run.
```

### Suggested Approach

1. Get the rule as a table, not as a sentence. Ask for each case and its action: the object the rule names, the objects it must not touch, and the outcome when a precondition is absent. A sentence such as "move the old keys out of the way" hides the object set. "Revoke only the named prior key; a separate explicit flag revokes all keys" states it.
2. Write the table in two places. Put it in the patch ticket so reviewers can compare intent, and in the patch itself as a comment or a table-driven test so the code carries its contract.
3. Name the protected set. State the objects the patch must never change: other users' objects, service or administrator objects, protected branches, shared profiles. Check that the implementation names them too.
4. Record the divergence from the durable fix. State each place where the interim patch differs, and the condition to retire the patch. An interim patch that is broader than the upstream fix leaves a behavior difference for the next release unless the record names it.
5. Check each row before use. Run a read-only probe for the cases that the patch will act on, and compare the result with the table. A disagreement on one row is a reason to stop, not to continue with the other rows.
6. Re-check after every owner correction. Rules often change during an incident, and a relayed summary can drop one. When the rule changes, compare the running patch with the new table before the next run. Do not run a patch whose contract changed while it was applied.
7. Make the patch's effect visible. Log the action per case with the object class, not the object secret. A patch that acts silently cannot be audited against its table.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Build the patch from a paraphrase | Implemented "revoke the old keys" as every other active key of the requesting user | The owner's rule named only the key that the client had saved; the broader action revoked objects the owner protected | Ask for the case table, and write it into the patch |
| Reuse the first patch after the owner refined the rule | Left the applied patch in place while the rule changed | The applied behavior no longer matched the decision table, and a run would have acted on the wrong set | Re-check the patch against the new table before the next run |
| Apply the durable fix's semantics early | Made the interim patch simpler than the upstream fix and treated them as equal | The upstream fix had a narrower scope so that in-process checks kept their protection | Record each divergence and the retirement condition |

## Results & Parameters

### Configuration

```yaml
patch_contract:
  - case_table_in_ticket: required
  - case_table_in_patch: required   # comment or table-driven test
  - protected_set_named: required
  - divergence_record: required
verification:
  - probe_each_row_read_only
  - recheck_after_owner_correction
  - log_actions_by_object_class
```

### Expected Output

- The patch ticket contains the owner's case table and the protected set.
- The patch contains the same table.
- The divergence record names each difference from the durable fix and the retirement condition.
- A read-only probe agrees with every row before the patch acts.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private multi-agent incident (identifiers withheld) | An owner refined a rotation rule during an incident while a helper relayed summaries and an interim patch ran on a live service | See [notes](hot-patch-owner-decision-table.notes.md). |

## References

- Related: `daemon-startup-environment-provenance` (verify the running process's own configuration)
- Related: `debugging-absence-of-evidence-verify-with-authority` (verify with the authority, not with a relay)