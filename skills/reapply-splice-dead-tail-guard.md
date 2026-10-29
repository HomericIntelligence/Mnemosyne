---
name: reapply-splice-dead-tail-guard
description: "Detect a splice that silently absorbs an adjacent definition into a re-applied function as dead tail code; use when you re-apply, cherry-pick, transplant, or conflict-resolve a hunk that inserts a test or function directly before an existing one."
category: testing
date: 2026-10-27
version: "1.0.0"
user-invocable: false
tags:
  - splice
  - re-apply
  - dead-tail-code
  - definition-count
  - merge-conflict
  - conflict-resolution
  - silent-test-loss
  - execution-blindness
  - cherry-pick
  - transplant
---

# A re-applied hunk can absorb the neighbor definition as dead tail code

**Supporting cases:** [notes](./reapply-splice-dead-tail-guard.notes.md)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-27 |
| **Objective** | Prevent the silent loss of an addressable test or function contract when a hunk is inserted directly before an existing definition. |
| **Outcome** | Successful. A definition-count guard found the absorbed definition, and a two-line restoration recovered the contract. A later rewrite of the same work repeated the same splice and shipped it. |

A splice defect occurs when an edit that must insert a new function above an
existing one replaces the neighbor's `def` line instead. The neighbor's body
then executes as dead tail code of the new function.

Execution evidence cannot see this loss. The absorbed statements still run,
still pass, and still count as coverage — under the wrong name. The real
damage is to the contract: the lost definition name, its failure attribution,
and its independent failure signal. In a long module the loss is invisible in
summary output, so a green run over the spliced file proves nothing about the
lost contract.

## When to Use

- You re-apply, cherry-pick, patch, or transplant a hunk that inserts a test or function directly before an existing definition.
- You resolve a merge conflict by inserting one function next to another.
- You regenerate or restructure a long module and plan to trust pass/fail output as the only verification.
- You review a diff whose hunk boundary touches the line before an existing `def`.

## Verified Workflow

### Quick Reference

Compare definition counts across the edit. The delta must equal the number of
definitions you intended to add:

```bash
git show <pre-edit-ref>:path/to/module.py | grep -c '^def test_'   # before
grep -c '^def test_' path/to/module.py                            # after: expect before + N
grep -n '^def ' path/to/module.py | sed -n '/splice-region/,+3p'  # boundary intact
```

A delta below the intended count is a splice defect, even when the suite is
green.

### Suggested Approach

- Read the result region around each insertion point after the edit. Confirm that both definitions exist, each with its own `def` line and separating blank lines. A diff does not make absorbed context lines visible.
- Keep the before/after definition counts in the verification notes for long modules. One lost line in a module with hundreds of definitions has no visible signal in aggregate output.
- When a collector is cheap and already available in the verified environment, use it as a second independent count (for example `pytest --collect-only -q` on the module).
- During review, treat a count that stays constant when one test is added as a finding: one definition was added and one was absorbed.
- Repair before any other edit in the same file. Restoration is usually two lines: the blank line and the absorbed `def` line, placed so both functions compile and collect independently again.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust the green run | Ran the full module after the splice; every test passed. | The absorbed assertions execute inside the wrong function, so pass/fail and coverage stay green. | Execution evidence is blind to absorption. Use a structural count, not only execution. |
| Review the diff | Read the re-applied diff hunks for correctness. | Diff hunks show changed lines; an absorbed `def` line can sit in un-displayed context or read as an intentional replacement. | Inspect the boundary in the result file and compare definition counts. Trust requires the result, not the delta text. |

## Results & Parameters

### Configuration

No configuration is required. The guard uses the pre-edit ref, the result file,
and a one-line definition pattern that matches the module's convention (for
example `^def test_` for flat pytest modules).

### Expected Output

- The definition-count delta equals the number of intended additions.
- The boundary grep shows two independent `def` lines separated by blank lines.
- Optional collector output agrees with the file-level count.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An internal deployment-control codebase | A re-applied conflict-free transplant spliced over an existing test; a count guard (138 vs expected 139) exposed it and a two-line restore repaired it; a later external rewrite of the same branch repeated the splice and shipped it. | See [notes](./reapply-splice-dead-tail-guard.notes.md). |

## References

- Related whole-file clobber variant between refs: [checkout-other-ref-silent-file-clobber](checkout-other-ref-silent-file-clobber.md)
