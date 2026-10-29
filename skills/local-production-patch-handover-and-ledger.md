---
name: local-production-patch-handover-and-ledger
license: BSD-3-Clause
description: "Hand a denied production change to the owner as a ready script, and keep a ledger of every local patch. Use when: (1) the owner authorizes local modifications to a live system and the permission layer still denies an agent write to the installed tree, the public client tree or the database, (2) several local patches and manual database writes exist and each needs a main-branch fix, (3) an owner runs a command with the shell prefix and the result shows the wrong account or path."
category: tooling
date: 2026-10-29
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [local-patch, handover, permission-denied, ledger, evidence, idempotent-script, shell-prefix]
---

# Hand Over a Denied Production Change and Keep a Patch Ledger

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Make an authorized local production change possible when the agent cannot write it, and make sure that every local change gets a main-branch fix. |
| **Outcome** | Operational. Eight patches, a fulfiller loop and several database writes were delivered as scripts that the owner ran. A tracking issue listed each change with its fix issue. |

An owner can authorize a change that the agent's permission layer still denies.
Do not work around the denial. Do the rest of the work, then give the owner one
ready, safe command.

## When to Use

- The permission layer denies a write to a live tree, a published client tree
  or the production database, and the owner has said that local changes are fine.
- More than two local patches exist.
- The owner ran a command with the shell prefix and it checked the wrong place.

## Verified Workflow

### Quick Reference

```text
Script: idempotent, anchor-checked, dry run first, sha256 before and after per file,
        exit non-zero on any anchor mismatch, no secrets in output.
Hand over: one command, what it changes, what it does NOT change, what I do after.
Ledger: one tracking issue; one row per patch, script, service and database write,
        each linked to the issue that owns the main fix.
```

### Suggested Approach

1. File the issue for the defect first, with possible solutions. The owner rule
   "patch locally, fix on main" needs an issue per patch.
2. Write the patch as a script under a working directory with evidence output.
   The script checks that each anchor text occurs exactly once, skips a file that
   is already patched, and writes the checksums before and after.
3. For files with mode 444, make the file writable for the in-place write and
   restore the mode in a `finally` block. A failed first run must write nothing.
4. For database writes, add a dry-run flag that opens a transaction, prints the
   planned rows and rolls back. Run it first and show the output.
5. Hand over with the exact command, the reload method that the owner required
   (for example a blue/green handoff), and the next verification step.
6. The shell prefix in the agent session runs as the session account. A command
   that edits another account's home must run in that account's terminal.
7. Keep a ledger issue: patches (file, change, fix issue), scripts and services
   that exist only on the host, and database writes. Close it when every row has
   a merged fix and the host runs a release that contains it.
8. After a denial, continue independent work and report the denial without
   rewording the same action.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Retry the denied write with another tool | Not tried; the denial text forbids a workaround | A workaround would defeat the permission intent | Hand over a script instead |
| First patch run on a read-only tree | Wrote the file in place | The tree was mode 444 and the run stopped with a permission error | Make the file writable for the write and restore the mode |
| Owner ran the repair through the shell prefix | `mv` of a file in a user's home | The command ran as the agent account | State which account must run each command |

## Results & Parameters

### Configuration

```yaml
patch_script:
  anchors: "exactly one occurrence each"
  idempotent: true
  evidence: "sha256 before and after"
  file_mode: "chmod u+w for the write; restore afterwards"
database_script:
  dry_run: "transaction rolled back"
  output: "usernames and counts only"
```

### Expected Output

Each script prints `patched <before> -> <after>` or `already patched`, exits 0,
and the ledger issue lists the change.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A scheduler-managed model-serving deployment | Production bring-up, 2026-10 | The permission layer denied installed-tree and database writes; the owner ran each prepared script. |

## References

- [harness-protected-file-edit-block-silently-defeats-precommit-deliverable](harness-protected-file-edit-block-silently-defeats-precommit-deliverable.md) — a protected-file block can defeat a deliverable
