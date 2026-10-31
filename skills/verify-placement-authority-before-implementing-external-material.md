---
name: verify-placement-authority-before-implementing-external-material
license: BSD-3-Clause
description: "Confirm placement authority before you implement material that belongs to an external project. Use when a plan or issue asks you to port or adapt such material. Use it also when an approval seems to authorize the port, or when the owner rejects the placement."
category: architecture
date: 2026-10-30
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - placement-authority
  - distribution-ownership
  - cross-repo
  - third-party-content
  - owner-authority
  - plan-approval
  - rejection-recovery
  - pr-cleanup
  - issue-closure
  - porting
  - control-profile
---

# Verify Placement Authority Before You Implement External Material

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-10-30 |
| **Objective** | Put each artifact in the distribution that owns it. Stop material without placement authority before implementation starts. |
| **Outcome** | Successful. A rejected placement was withdrawn fully. The pull request closed, the head branch was deleted, and the issue closed. No automation item could re-implement it. |

## When to Use

- A plan or issue asks you to port, copy, or adapt a component, profile, or configuration from an external project into the current distribution.
- An approved plan or a review verdict seems to authorize that port. No owner confirmed where the material belongs.
- You must decide whether a distribution keeps, moves, or removes material that another project owns.
- The owner rejects the placement after implementation starts. You must recover without leftover state.

## Verified Workflow

### Quick Reference

```text
Before you write code -> find the distribution that owns each artifact. Ask the owner if the placement is not recorded.
Approved plan         -> proves the change is correct. It does not prove the placement is authorized.
Owner rejects         -> close the pull request, delete the head branch, close the issue. Do not merge partial material.
Keep the lesson       -> record the placement rule with general nouns. Do not record project names or identifiers.
```

### Suggested Approach

1. Classify the material before implementation. For each artifact, answer one question: does the host distribution own it, or does an external project own it? A control profile or validation suite that an external project maintains ships from that project's own distribution. The host distribution ships the mechanism that consumes it. It does not carry a copy.
2. Treat approvals as scope evidence, not placement authority. A plan approval or a review verdict says the change is correct. It does not give the host distribution authority to carry the material. Ask the owner of the host distribution before you write code.
3. Record the placement decision. Write the decision, the authority, and the date in the issue or the plan. If the owner places the material elsewhere, remove it from this change. Deliver the part that the host distribution owns if that part is independent.
4. Recover from a rejection in this order:

   1. Close the pull request. Do not merge partial material.
   2. Delete the head branch. A deleted branch removes the implementation from the remote.
   3. Close the issue. Record the owner decision in the closing comment.
   4. Check the open automation state. A closed issue stops a loop that would re-dispatch the rejected work.

5. Keep the knowledge after the recovery. Record the placement rule and the recovery steps. Use general nouns such as "a mechanism host distribution" and "an external reviewed project". Do not record project names, issue numbers, or internal paths.

If a step is unavailable, continue safely:

- If the owner is not available, keep the external material out of the change. Deliver the owned part. Ask for the placement decision as a separate item.
- If you cannot delete the remote head branch, report the exact branch name. Keep the local worktree until an operator decides.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Implement the approved plan directly | An approval covered a port of a control profile from an external project. Implementation treated the approval as placement authority. | The owner rejected the premise. No content from the external project belongs in the host distribution. Approval proves correctness, not authorization. | Ask the owner about placement before implementation. |
| Close the issue but keep the delivery artifacts | The rejected issue closed while the pull request and its head branch stayed in place. | The owner directed a full withdrawal. Leftover branches and open issues can re-dispatch the same rejected work. | Withdraw fully in one sequence: close the pull request, delete the head branch, close the issue. |

## Results & Parameters

### Configuration

```text
Material ownership            Placement decision
Host distribution owns it     Implement in the host distribution.
External project owns it      Ship from that project's own distribution. The host distribution consumes it.
Shared or unclear             Ask the owner. Record the decision before implementation.
```

### Expected Output

- A recorded placement decision with the owner as the authority.
- A change that contains only material the host distribution owns.
- After a rejection: a closed pull request, a deleted head branch, a closed issue, and no open automation item for the rejected placement.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Private multi-project automation session (identifiers withheld) | An approved plan ported an external control profile. The owner rejected the placement, and the change was withdrawn fully. | Recovery closed the pull request, deleted the head branch, and closed the issue in one sequence. |

## References

- Related: `cross-repo-script-and-library-porting` (port mechanics after a placement is authorized).
- Related: `planning-verify-issue-premise-before-implementing` (plan validity against the current code).
- Related: `conflicting-co-issued-instructions-escalate-conflict` (conflicting instructions from different authorities).
