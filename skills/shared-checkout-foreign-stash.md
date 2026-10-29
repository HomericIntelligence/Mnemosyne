---
name: shared-checkout-foreign-stash
license: BSD-3-Clause
description: "Protect foreign stashes in a shared git checkout; inspect stash identity before any pop, apply, drop, or clear."
category: tooling
date: 2026-10-26
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [git-stash, shared-checkout, multi-agent, foreign-state, recovery, pop, drop, clear]
---

# Shared Checkout Foreign Stash

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-26 |
| **Objective** | Stop agents from treating the top entry of `git stash list` in a shared checkout as their own |
| **Outcome** | Successful — foreign stash preserved, own work recovered without loss |
| **Verification** | verified-local |

## When to Use

- More than one agent, session, or lane works in the same git checkout.
- A workflow step wants to run `git stash pop`, `git stash apply`, `git stash drop`, or `git stash clear`.
- A stash entry appears that no current lane created.
- A cleanup step considers stashes as residue.

## Core Rule

The stash stack is shared mutable state. The top entry does not belong to the caller by default.
Never run a destructive stash command on an entry whose owner, message, and content were not
verified first. Other lanes lose work silently when a foreign stash is popped or dropped.

## Verified Workflow

### Quick Reference

```bash
git stash list                     # read every message and date
git stash show -p stash@{N}        # inspect content before any action
git stash apply stash@{N}          # own entry only; prefer apply over pop
# drop only after the applied result is confirmed on disk
```

### Steps

1. List before any action: `git stash list`. Read every entry's message and date.
2. Identify ownership. Stash messages carry the branch and commit they were made from. Match them
   against the current lane's branch and expected base.
3. Inspect content before acting: `git stash show -p stash@{N}`. Confirm the diff is the expected
   one. Unknown content means foreign.
4. If the entry is foreign, stop. Do not pop, apply, drop, or clear it. Record its index and
   message in the lane ledger, and route the decision to the owner or coordinator.
5. If the entry is verified as the lane's own, prefer `git stash apply` over `pop`; drop only
   after the applied result is confirmed on disk.
6. If own work is missing and the stack order changed, suspect that another lane popped the wrong
   entry. Recover from the stash reflog: `git fsck --unreachable` plus
   `git stash list` history on clones that still hold the objects, or restore from a salvage
   archive taken before the incident.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Pop the top entry by position | Assumed the newest entry is the caller's own | Foreign changes entered a dirty tree and the foreign lane lost its stash | Verify message and diff first |
| `git stash clear` as cleanup | Treated all entries as residue | Every lane's stashed work is destroyed at once | Never clear in a shared checkout; drop only verified-own entries one at a time |
| Drop after apply without read-back | Assumed apply succeeded cleanly | Partial application or a conflict leaves a destroyed-only copy | Confirm the tree state, then drop |
| Treat a foreign stash as a blocker | Deleted it to unblock the lane | Permanent loss of another lane's uncommitted work | Park, record, escalate |

## Results & Parameters

A multi-lane run shared one git checkout. A cleanup step near the end found stash entries it had
not created. Position-based handling would have destroyed work belonging to a parallel lane. The
lane instead listed, inspected, and classified each entry, preserved the foreign one untouched,
and completed its own recovery from a verified-own entry plus on-disk salvage. No foreign state
was modified. The full timeline is in the lane ledger for the run.
