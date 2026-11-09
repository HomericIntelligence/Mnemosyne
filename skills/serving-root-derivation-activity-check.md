---
name: serving-root-derivation-activity-check
license: BSD-3-Clause
description: "Show a path change in a deployment-rendered service also reaches the active job. Use when a plan changes a directory, scope, or allowlist in an entry point, when the serving process reads that value at start, and when a deployment-rendering path may stop at a protected directory that only the service account can enter. Read the deployed executable, then plan the name and reject the plan if the activation surface is not shown."
category: architecture
date: 2026-11-07
version: "1.0.0"
user-invocable: false
tags:
  - deployment-rendering
  - rendered-value
  - start-time-read
  - activation-surface
  - stale-config
  - protected-directory
  - writable-parent
  - ownership
  - deployment-context
  - plan-review
---

# Serving-Root Derivation Activity Check

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Prevent a plan from changing where a deployment-rendered service reads or writes, without a step that makes the change active and the target usable. |
| **Outcome** | Operational: the check changed one plan from a root derivation that could not deploy to a plan that states the active executable, the fallback operation, and the ownership of the created directory. Verification level is verified-local for the source reading; the change is not yet implemented. |

A rendered service reads its deployment values when the process starts. A source change
that derives a new path from those values is correct in tests. It is absent in the active
job until that job is re-rendered or restarted with the new code. The change is also absent
when the rendering stops at a protected directory. No render step can then create the new
path. Tests do not show either condition, because tests start a fresh process with a test
root.

## When to Use

- A plan changes a directory, scope, allowlist, or ownership rule that a serving entry
  point reads. The service gets that value at process start.
- A plan introduces a new path below a directory that deployment templates render, and
  an account that is not the service account must write there.
- A plan states an acceptance criterion such as "the service resolves the new path", but
  the repository has no step that replaces the executable of an active job.
- A deployment path is created by a bootstrap or installer step, and that step runs with
  a different set of privileges than the serving process.

## Verified Workflow

### Quick Reference

Do three checks. Keep each result in the plan, because each can change the plan.

```bash
# 1. Bind the deployed executable and its activation verb.
#    Read the supervision, installer, and promotion entry points, not only the app code.
# 2. Trace the value from its renderer to its reader.
#    The reader binds it at process start (a resolved deployment context, a launcher
#    environment, or a rendered job file). A source-only change does not update it.
# 3. Prove the target is writable by the required account.
#    Open each parent of the new path without a directory-symlink follow.
#    A parent that accepts only the service account blocks every later writer.
```

### Suggested Approach

1. **Name the active executable and its activation verb.** Find the command the
   supervisor, installer, or promotion step runs. Name the step that replaces the
   executable an active job uses. If no step exists, the plan must state the restart or
   re-render operation, and it must also state that this operation is outside the code
   change.
2. **Trace the value from renderer to reader.** Record where the value is produced and
   where the serving process reads it. When the process reads it at start, the value is
   not a configuration file that an operator edits. It is part of the executable and
   the rendered environment.
3. **Prove the writable parent.** A user account must write below the derived path. Each
   parent must then permit entry by that account, and it must give a group that the service
   and the users share. A protected parent with only service-account entry blocks the
   creation. The derived path then stays empty. Read the creation code in the bootstrap or
   installer. State the mode and the owner of each created directory. Reject the plan when
   the creation step cannot set that mode.
4. **Record the activation as a plan step with an owner.** The step is either a code
   change in the installer or a nominated operator operation. Do not write an
   acceptance criterion that no named step can satisfy.
5. If the activation surface cannot be shown, keep the code change and mark the
   behavior as unverified in deployment. Do not claim the behavior active.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | A plan changed the derived directory from a mount string to a path from the resolved deployment context. Tests covered each accept and refuse rule. | The service reads the deployment context at process start. No step replaced the executable of the active job, so the new path stayed inactive until the next render. The tests passed against a fresh test root. | Trace the renderer and the start-time reader before you plan a path change. Plan the activation step with the change. |
| 2 | The plan told the existing bootstrap to create the new directory below the deployment directory. | The deployment directory permitted entry only from the service account. Ordinary users must write below the new directory, so the creation step could not set the mode, and the derived path stayed empty for every user. | Prove entry and write permission on each parent for the account that creates the directory and for the account that writes below it. |

## Results & Parameters

### Configuration

```yaml
check_1: active executable and activation verb named
check_2: value renderer and start-time reader named
check_3: writable parent proven for the creating account and the writing account
plan_gate: reject the plan when any check has no answer
```

### Expected Output

- The plan names the step that makes the change active, or states that the behavior is
  not active in deployment.
- The plan states the mode and the owner of each created directory, and the account that
  creates it.
- No acceptance criterion depends on a step that the plan does not name.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A multi-deployment open-source gateway | Planning round for a per-user storage root derived from the resolved deployment context | The source reading found a start-time read of the deployment context and a service-only deployment directory. The revised plan added the activation step and the writable-parent proof. See [notes](serving-root-derivation-activity-check.notes.md). |

## References

- [Related: verify the deployed composition delivers its contract](pr-review-deployed-composition-error-contract.md)
- [Related: verify the deployed version can reach the runbook goal](deployed-version-runbook-goal-feasibility.md)
- [Related: a disk edit alone never reaches a running process](live-hotfix-content-addressed-identity-rotation.md)