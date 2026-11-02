---
name: local-test-env-involuntary-ancestor
description: "Keep a rebase or delivery task unblocked when permission-sensitive tests fail on an ancestor directory that the operator cannot change. Use when the failing check names a path above the writable root, such as a home or scratch mount, and a private temporary root cannot fix it because the rejected ancestor stays in the chain."
category: debugging
date: 2026-11-01
version: "1.0.0"
user-invocable: false
tags: [ci-parity, permissions, ancestor-directory, tmpdir, rebase, attribution, delivery]
---

# Local Test Environment: Involuntary Ancestor

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Separate an environment-caused failure from a code regression when the rejected path is an ancestor that the operator does not own, and keep the delivery task moving. |
| **Outcome** | Operational: the operator records the exact evidence, keeps the change, and makes no unpermitted repair. |

## When to Use

Use this skill when:

- a permission-sensitive test or guard fails and the message names an
  ancestor directory, not a file that the test created;
- the named ancestor is outside the task's writable scope, such as a shared,
  network-mounted, or administrative parent of the checked-out tree;
- setting a private temporary root does not clear the failure because the
  rejected ancestor stays in the path chain; and
- a separate task, such as a rebase or a delivery push, depends on the test
  result.

For cases where the operator controls the whole path chain, use
[`local-test-env-guard-divergence`](./local-test-env-guard-divergence.md)
instead. Set a private temporary root and a controlled umask first. Use this
skill only when that fix fails.

## Verified Workflow

### Quick Reference

Prove the failure is environmental before you report it:

```bash
# 1. Run the failing test under a private temporary root.
mkdir -p <private-temp> && chmod 700 <private-temp>
TMPDIR=<private-temp> <test command> <one failing node id>

# 2. Confirm that the rejected path is still the same ancestor.
stat -c '%a %u:%g %n' <named-ancestor>
```

If step 2 shows a mode or group that the guard rejects, and the reported
ancestor is outside your writable scope, the failure is environmental.

### Suggested Approach

1. Read the guard message. Record the check class, the expected state, the
   observed mode, and the exact path.
2. Compare the observed mode with the guard expectation. The observed mode is
   the evidence, not the guess.
3. Test the bounded fix first. Set a private temporary root with mode `700`
   and re-run one failing node.
4. Check whether the fix applies. If the rejected path is still the ancestor
   after the change, the fix cannot apply. The path chain is the constraint,
   not the temporary root.
5. Confirm the scope. A path outside your worktree, a shared home directory,
   or a mount that another owner administers is not yours to repair.
6. Do not relax the guard and do not edit the shared path. A guard change hides
   a real defect. A shared-path change affects other users and is outside the
   task authority.
7. Separate the dependent task from the test result. A rebase or a push
   changes the commit graph, not the behavior. Complete the dependent task
   when its own evidence is sufficient: the residual diff, a signed commit,
   and the conflict resolution.
8. Record three items in the report: the exact test command, the observed mode
   and path, and the owner who can repair the path. Then continue.

### Reporting Rule

State the environmental cause only with the observed mode and the rejected
path. Do not report a test run as green when it was not green. Do not report a
red run as a code regression when the mode evidence shows the environment.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Changed `TMPDIR` to a private owner-only directory and expected the ancestor failure to clear. | The guard still reported the same ancestor above the temporary root; the temporary root does not replace the parent chain. | Probe the named ancestor after the change. A private root helps only when the rejected parent is inside it. |
| Attempt 2 | Treated the red covering tests as a possible defect in the rebased change. | The failures stopped at the ancestor check before the changed module ran, and the rejected ancestor was outside the worktree. | Read where the stack fails. A failure that starts at the environment check gives no evidence about the rebased code. |

## Results & Parameters

### Configuration

| Parameter | Value | Meaning |
| --------- | ----- | ------- |
| private temporary root | mode `0700` | Removes shared-write bits below the chosen root. This is a bounded first fix. |
| rejected ancestor probe | `stat -c '%a %u:%g %n' <path>` | Shows the mode and owner that the guard named. |
| delivery gate | residual diff, signed commit, conflict resolution | Evidence for a dependent task that the environmental red run does not affect. |

### Verification

- One failing node was re-run under the private temporary root.
- The guard message still named the same ancestor with the same mode.
- The reported ancestor was outside the writable scope of the task.

## Provenance

Evidence came from a rebase task whose covering tests failed in an
environment check. The check rejected a group-write mode on a shared parent of
the workspace. A private temporary root did not change the result. The rebase
itself had a complete residual diff, a signed commit, and one resolved
import-only conflict. The report named the observed mode, the path, and the
owner of the repair.