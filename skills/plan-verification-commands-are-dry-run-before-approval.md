---
name: plan-verification-commands-are-dry-run-before-approval
description: "Dry-run each verification command in a plan before you present it, because a command that cannot pass, collects nothing, or matches a different artifact than the one edited turns plan approval into a false guarantee. Use when a plan or review lists grep, pytest, or shell checks as acceptance evidence, when the edited artifact moves lines relative to its original anchors, or when a named test does not exist yet."
category: architecture
date: 2026-11-07
version: "1.0.0"
user-invocable: false
tags:
  - verification-plan
  - plan-review
  - acceptance-criteria
  - non-vacuous-check
  - stale-anchor
  - line-number-drift
  - pytest-selection
  - idempotency
  - negative-control
---

# Plan Verification Commands Are Dry-Run Before Approval

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Stop a plan from shipping acceptance commands that cannot pass, or that pass without proving the claim. |
| **Outcome** | Operational: the dry runs found broken commands in three consecutive plan revisions that a careful anchor review had already declared sound. |

A plan that lists a verification command makes a promise: run this command,
get this result. Reviewers check file and line anchors and accept the
commands. The commands need their own check. Four failures repeat, and none
needs a test run against real infrastructure:

1. **Fails after the planned edit.** The command filters by a line number that
   the same plan's edits move.
2. **Passes without proving the claim.** The selection matches no test, or the
   pattern matches a different artifact.
3. **Self-defeating fix.** The planned change makes the plan's own blocking
   check report a finding.
4. **Assert a broken guard is a fault.** The guard under repair already
   satisfies the requirement.

## When to Use

- A plan, review, or issue lists shell, grep, or test commands as acceptance
  evidence.
- The plan edits a page or file with numbered anchors and later greps that
  file.
- A verification step names a test that the plan itself will create.
- A plan adds a file or behavior that a gate in the same plan scans for
  forbidden names.
- A review finding claims that a missing guard causes a failure.

## Verified Workflow

### Quick Reference

```bash
# 1. Anchor-free filters. Exclude by content, never by line number, when the
#    same plan deletes lines above the match.
grep -nEi '<pattern>' <file> | grep -v '<exact retained line text>'

# 2. Existing test names. Never accept a selection you did not see collected.
python -m pytest --collect-only -q <file> -k '<selector>'

# 3. Gate self-check. Build the artifact the plan creates, then run the gate.
```

### Suggested Approach

1. **Read the command as the post-edit tree.** Apply the plan's edit list in
   your head, then renumber. A `grep -v '^<line>:text'` exclusion breaks as
   soon as the plan deletes any line above that number. Exclude by content
   instead, and state the exact expected residue, for example one retained
   line, not "no output".
2. **Prove the selection is non-empty.** Run `--collect-only` with the
   selector. A selector that matches zero tests exits with code 5, and a
   selector that matches a docstring is not a test. Prefer named test IDs,
   and say plainly that the ID fails until the implementation order adds it.
3. **Trace the gate against the artifact you create.** When the plan adds a
   file or a name, find every gate that scans for that name. If the gate
   reports presence as a failure, the plan must remove the name from the
   gate's list, or move it to a state the gate accepts. State which clause
   still catches a stray copy.
4. **Test the claimed fault before you plan the repair.** Read the code that
   the review says fails. When the called command is idempotent, returns
   success, and documents that outcome, the missing guard is not a defect.
   Re-aim the edit instead of adding a guard.
5. **Add a negative control to a removal check.** After a "must be absent"
   check, create the forbidden artifact and confirm that the check reports
   it. A check that never fires and an absent artifact look the same.
6. **Record the base revision.** Compare the branch base against the default
   branch. A fix that the plan depends on can exist only upstream. State the
   base commit and the upstream commit that carries the fix.
7. **Keep the measured result out of the plan.** The plan states the command
   and the expected result; the evidence step records the actual output.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | --------------- |
| Attempt 1 | Exclude a retained line with a line-number anchor | The same plan deletes lines above it, so the anchor never matched | Exclude by content and state the expected residue |
| Attempt 2 | Select tests with a keyword filter | No test name matched, so the run collected zero tests | Verify the selection with `--collect-only` first |
| Attempt 3 | Guard a stop step that the review called non-idempotent | The stop already returned success when no target existed | Read the callee before you plan a guard |

## Results & Parameters

### Configuration

```text
Filter:    content-anchored exclusion, never a line number
Selector:  named test ID, verified with --collect-only
Gate:      enumerate every scan of a name the plan adds or removes
Fault:     read the callee's exit contract before you add a guard
Control:   create the forbidden artifact and re-run the removal check
Base:      record the branch base and the upstream commit of each dependency
```

### Expected Output

- Each verification command has a stated expected result.
- A test selector collects at least one test.
- A removal check reports the forbidden artifact when you create it.
- The plan names its base revision.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| Session evidence | Plan review rounds on one release-procedure issue | Dry runs and callee reads produced all four findings; the fixes remain unexecuted and are a planning discipline only. |

## References

- [Non-vacuous regression guards](testing-non-vacuous-regression-guards-behavior-unchanged.md)
- [Derived-artifact gate non-vacuity](derived-artifact-gate-non-vacuity.md)
- [Verify issue premise before implementing](planning-verify-issue-premise-before-implementing.md)