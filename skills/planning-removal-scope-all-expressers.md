---
name: planning-removal-scope-all-expressers
license: BSD-3-Clause
description: "Scope a requested removal by every gate that expresses the defect, not by the one function the issue names. Use when removing a pre-flight refusal, a capacity or budget check, a policy guard, or a node-count derivation; when the issue attributes the refusal to one check and names several removals of different kinds (behaviour, measurement record, error reporting); or when a removal must not delete shared arithmetic that rendering and placement still use."
category: architecture
date: 2026-11-07
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - planning
  - removal-scope
  - removal-blast-radius
  - guard-removal
  - refusal-removal
  - capacity-check
  - preflight-refusal
  - duplicate-expressers
  - responsibility-reassignment
  - bounded-fallback-removal
  - shared-arithmetic-retention
  - diagnostic-only-record
---

# Planning: Scope a Removal by Every Expresser

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Plan the removal of a refusal without leaving a second refusal in the start path, without deleting arithmetic that other consumers still need, and without weakening the diagnostic that must replace the refusal |
| **Outcome** | A repeatable scoping rule: enumerate every gate that produces the refused outcome, split the issue scope by change kind, bound the deletion to the gating call and not the shared computation, and keep or add the post-hoc diagnostic |
| **Verification** | verified-local — a read-only evidence audit; no removal was implemented or validated |

An issue that removes a refusal usually names one function. The refusal can come from more than one
call in the same start path. If you remove only the named function, the start stays refused and the
acceptance test still fails. The same issue can also ask to keep a record, to improve a diagnostic,
and to delete a derivation. Each ask needs its own disposition and its own test. One change class
must not absorb another.

## When to Use

- An issue removes a pre-flight refusal and names one validating function.
- An issue says "no code path derives X" or "remove the derivation" when the derivation also feeds
  rendering, placement, reporting, or a schema cost.
- An issue marks an existing configuration record as report-only or diagnostic-only.
- An issue asks for a post-hoc failure report with specific fields, such as an identifier, a
  placement target, a policy name, and a message.
- A first plan names fewer removal sites than the number of calls that raise the refusal.

## Verified Workflow

### Quick Reference

```bash
# 1. Find EVERY call that can raise the refused outcome, not only the named one.
rg -n 'validate_|require_|refuse|raise ValueError' src/ | rg -n 'start|post_init|hook'
# 2. Follow each caller to its own inner refusal. One caller can call a second validator.
# 3. For each derivation symbol, list every reader before you delete it.
rg -n 'replica_slots_for|node_count_for' src/
```

Use the commands that match the language of the repository. The rule is the search shape, not the
tool.

### Suggested Approach

1. **Reproduce the refusal path, from the entry point back.** Start at the function that starts the
   deployment or job. List each call that can raise before the first external submission. The issue
   names one. Read the others.
2. **Classify each site that raises the refused outcome.**
   - in scope: it refuses the start for the reason the issue removes;
   - out of scope: it refuses for a different reason, such as a shape rule or an identity check;
   - a look-alike that must remain.
   Name each site in the plan with its evidence. A silent omission reads as an oversight.
3. **Split the issue scope by change kind.** Use a separate step for each item:
   - behaviour removal of the refusal;
   - retention of a record that becomes report-only;
   - diagnostic reporting of the new failure;
   - configuration values that record the new request.
   A removal step must not also change reporting, and a reporting step must not change the refusal.
4. **Distinguish the derived number from the number that stays.** If the issue says "no path derives
   a node count", find the value that holds and the conversions that use it. Slot cost or
   per-replica capacity can stay. The conversion of a replica target to a node bound, when it gates
   a start, goes. Record the readers that legitimately remain.
5. **Keep the diagnostic that takes over the responsibility.** A removed refusal transfers its job
   to the scheduler or the remote service. The plan must name where the new failure surfaces and
   which fields it records. The fields the issue names are part of the acceptance criteria, not
   optional detail.
6. **Plan the tests as behaviour, not as an absence of a symbol.** The acceptance test must drive a
   start that exceeds the old record and assert that submission calls occur. A test that asserts a
   function is missing proves deletion, not behaviour.
7. **Delete tests that pin the removed refusal, or rewrite them to assert submission.** Record each
   such test in the plan.
8. **Record an external closure separately.** If the scope includes closing another issue or
   record, mark that step as a forge operation with no code change.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Scope a removal by the function the issue names | Planned one validator removal from the start path | A second validator in the same start path also refused the start, so the start stayed refused | Enumerate every call that raises the refused outcome before you scope |
| Treat "remove the derivation" as one deletion | Planned to delete the capacity arithmetic with the refusal | The same arithmetic feeds rendering and placement, which still need it | Delete the gating call, not the shared computation; list the readers that stay |
| Trust the issue's line numbers for the cited functions | Planned against the cited coordinates | Both cited functions had moved to earlier lines; the finding held and the coordinates did not | Relocate each cite by its symbol name before you quote it |

## Results & Parameters

| Parameter | Rule |
| --------- | ---- |
| Refusal sites | Every start-path call that can raise the refused outcome |
| Change kinds | One plan step for each kind: removal, retention, diagnostic, configuration |
| Derivation | Remove the node bound that gates a start; keep the slot cost that other consumers read |
| Record | A report-only record may inform an alert; it must not refuse |
| Diagnostic | The fields named in the issue are acceptance criteria |
| Test | Drive a start above the old record and assert submission; do not test for a missing symbol |
| External closure | A linked-record closure is a forge step, not a code step |

Supporting case detail is in the [notes](./planning-removal-scope-all-expressers.notes.md).

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| an isolated checkout | Read-only requirements audit of a removal issue | [notes](./planning-removal-scope-all-expressers.notes.md) — two start-path gates and one shared derivation were found; no removal was implemented |