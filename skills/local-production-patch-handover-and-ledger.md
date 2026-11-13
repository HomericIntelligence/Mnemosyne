---
name: local-production-patch-handover-and-ledger
license: BSD-3-Clause
description: "Hand a denied production change to the owner as a ready script, keep a ledger of every local patch, and retire each patch at a release cut with a revert record. Use when: (1) the owner authorizes local modifications to a live system and the permission layer still denies an agent write to the installed tree, the public client tree or the database, (2) several local patches and manual database writes exist and each needs a main-branch fix, (3) an owner runs a command with the shell prefix and the result shows the wrong account or path, (4) a release cut replaces a patched deployed tree, so each active patch needs a revert record or a recorded keep decision."
category: tooling
date: 2026-10-29
version: "1.2.0"
user-invocable: false
verification: verified-local
tags: [local-patch, handover, permission-denied, ledger, evidence, idempotent-script, shell-prefix, release-cut, revert-record]
---

# Hand Over a Denied Production Change and Keep a Patch Ledger

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Make an authorized local production change possible when the agent cannot write it, make sure that every local change gets a main-branch fix, and retire each patch without a silent revert. |
| **Outcome** | Operational. Eight patches, a fulfiller loop and several database writes were delivered as scripts that the owner ran. A tracking issue listed each change with its fix issue. |

An owner can authorize a change that the agent's permission layer still denies.
Do not work around the denial. Do the rest of the work, then give the owner one
ready, safe command.

A patch that a main fix replaces stays active until the release cut replaces
the patched tree. At that cut, each active patch needs one revert record or one
recorded keep decision. A patch that is lost in a later deploy without either
record is a silent revert.

## When to Use

- The permission layer denies a write to a live tree, a published client tree
  or the production database, and the owner has said that local changes are fine.
- More than two local patches exist.
- The owner ran a command with the shell prefix and it checked the wrong place.
- A release cut replaces the patched installed tree, or a main fix for a patch
  is merged and the deployed tree still holds the local change.

## Verified Workflow

### Quick Reference

```text
Script: idempotent, anchor-checked, dry run first, sha256 before and after per file,
        exit non-zero on any anchor mismatch, no secrets in output.
Hand over: one command, what it changes, what it does NOT change, what I do after.
Ledger: one tracking issue; one row per patch, script, service and database write,
        each linked to the issue that owns the main fix.
Cut: one revert record per active patch, each with the bypass, its evidence patch,
        the before and after digest on the installed tree, and the replacing commit
        or the recorded keep decision.
```

### Suggested Approach

1. File the issue for the defect first, with possible solutions. The owner rule
   "patch locally, fix on main" needs an issue per patch.
2. Write the patch as a script under a working directory with evidence output.
   The script checks that each anchor text occurs exactly once, skips a file that
   is already patched, and writes the checksums before and after. When the script
   patches several sibling files, check each file on its own and patch only the
   files that still need it. Do not start with one "already patched" guard on a
   single file: if another person fixed that file, the guard skips the siblings
   that still have the defect. Keep one backup per file, run a dry run before the
   write, and end with a check that no file still has the bad text.
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
9. At the release cut, walk the ledger and write one revert record per active
   patch in the cut evidence directory. Name the patch, the evidence patch, the
   before and after digest on the installed tree, and the source commit that
   replaces it. A source commit is a valid replacement only if CI proved it and
   the cut tree contains it; a fix that is still an unmerged branch is not.
10. A patch that the new tree still needs stays active only with a keep decision
    in the ledger. Do not delete a patch because a fix exists somewhere.
11. Ask the cut operator to attest the record set against the installed tree.
    The evidence directory and the installed tree usually sit outside the code
    repository, so no check in the repository can confirm them.
12. Separate a workaround from a fix. A local change that is itself the correct
    behavior (for example a lock change on a network file system) needs only an
    adoption note at the cut, not a revert record. Remove hand-edited backup
    copies of a source file when the cut deploys the source version.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Retry the denied write with another tool | Not tried; the denial text forbids a workaround | A workaround would defeat the permission intent | Hand over a script instead |
| First patch run on a read-only tree | Wrote the file in place | The tree was mode 444 and the run stopped with a permission error | Make the file writable for the write and restore the mode |
| Owner ran the repair through the shell prefix | `mv` of a file in a user's home | The command ran as the agent account | State which account must run each command |
| Close the ledger when each main fix merged | Treated the merged fix as the end of the patch | The deployed tree kept the local change, and a later cut would drop it without a record | Close the ledger only when the release that contains the fix is installed, and write the revert record at that cut |
| One guard for sibling files | The script began with an "already patched" check on one file | Another person had fixed that file; the script exited with "already patched" while four siblings kept the defect | Guard and patch each file on its own, and finish with a no-bad-text check on all files |

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
revert_record:
  fields: [patch, evidence_patch, before_digest, after_digest, replacing_commit_or_keep_decision]
  location: "cut evidence directory, one record per active patch"
  attestation: "cut operator confirms the records against the installed tree"
```

### Expected Output

Each script prints `patched <before> -> <after>` or `already patched`, exits 0,
and the ledger issue lists the change. At the cut, each active patch has one
revert record or one keep decision, and no record is missing.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A scheduler-managed model-serving deployment | Production bring-up, 2026-10 | The permission layer denied installed-tree and database writes; the owner ran each prepared script. |
| A schedule-authorized release cut | Patch retirement at a release cut, 2026-10 | An operations page for a scheduled cut covered the ledger, the revert records and the operator attestation. |

## References

- [harness-protected-file-edit-block-silently-defeats-precommit-deliverable](harness-protected-file-edit-block-silently-defeats-precommit-deliverable.md) — a protected-file block can defeat a deliverable
- [gate-bypass-enumerate-every-enforcement-path](gate-bypass-enumerate-every-enforcement-path.md) — find every enforcement path before you patch a gate
- [workaround-demolition-wave-strategy](workaround-demolition-wave-strategy.md) — batched removal of obsolete workarounds after an upstream fix
