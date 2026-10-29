---
name: gate-bypass-enumerate-every-enforcement-path
license: BSD-3-Clause
description: "Find every code path that enforces a gate before you bypass it, using the blocked state that the system records, not only the error text. Use when: (1) an owner authorizes a temporary bypass of a qualification, acceptance or policy gate on a live service, (2) the first bypass patch removes the error but the work item stays blocked, (3) a status record shows a blocked flag or a missing-requirement list after the action path passes."
category: debugging
date: 2026-10-29
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [gate, bypass, enforcement-path, blocked-state, status-record, local-patch, restart-cost]
---

# Enumerate Every Enforcement Path Before a Gate Bypass

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Bypass a gate once, completely, so that a live service needs one restart cycle and not several. |
| **Outcome** | Operational. A qualification gate enforced the same requirement in an action path and in a status-marking path. The first patch cleared the action error. Every work item stayed blocked until the second patch. |

A gate often has two kinds of enforcement. The action path raises when the
operator starts the work. The status path marks the work item as blocked and
blocks follow-on actions such as recycling. A patch of one path leaves the other
in force. Each extra patch costs a restart of the process that loaded the code.

## When to Use

- An owner authorizes a temporary bypass of a gate on a running service.
- The error text disappeared, but the status record still shows `blocked: true`
  or a missing-requirement list.
- You plan a local patch of an installed tree and each reload is expensive.

## Verified Workflow

### Quick Reference

```bash
# 1. Find the gate's predicate and every caller, not only the raising function.
grep -rn "<gate predicate name>\|<missing-list function>" src/
# 2. Read what the status record exposes; each key names a second path.
cat <work item>/status.json     # blocked, error, <requirement>_missing, recycling.blocked
```

### Suggested Approach

1. Name the requirement in the error text, then search for its predicate and its
   "missing list" helper. Both can feed different consumers.
2. Read the status record of one blocked work item. A key such as a blocked
   flag, a missing-requirement list or a blocked-recycling reason shows a path
   that the action error does not reveal.
3. List all callers of the predicate: the action path, the supervisor or
   reconcile loop, the recycle path and the validation tool.
4. Patch all of them in one script with before and after checksums and an
   idempotent anchor check. Record the patch in the issue that owns the main fix.
5. Reload once. Verify with the status record, not with the absence of the
   error: the blocked flag is false and the work item reaches a scheduled state.
6. Prefer the main fix that removes the gate or makes it advisory. Do not keep
   two enforcement paths with different rules.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Patch only the raising function | Made the action-path check return at once | The reconcile loop still marked every work item blocked through a separate missing-list helper; nothing started | Search for the helper that builds the missing list, not only the function that raises |
| Trust the clean command output | Declared the bypass done when the start command succeeded | The command only recorded the desired state; the supervisor refused to act on it | Verify with the status record and the scheduler, not the command exit code |

## Results & Parameters

### Configuration

```yaml
verification:
  status_record: "blocked is false; the missing-requirement list is empty"
  scheduler: "replica allocations appear within one reconcile interval"
patch:
  idempotent: true
  evidence: "sha256 before and after for each file"
  reload: "once, after all enforcement paths are patched"
```

### Expected Output

One reload clears the gate: the status record has no blocked flag and the
scheduler shows new allocations within one reconcile interval.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A scheduler-managed model-serving deployment | Production bring-up, 2026-10 | The bypass needed two patches and two restart cycles because the status path was found second. |

## References

- [serving-pool-replica-outage-diagnosis](serving-pool-replica-outage-diagnosis.md) — verify recovery with scheduler state
