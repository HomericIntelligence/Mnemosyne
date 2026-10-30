---
name: rm-permission-denied-owner-readonly-repair
description: "Finish a partially failed bulk deletion: owner-owned read-only files (0444) and search-only directories (0555) make rm -rf fail with 'Permission denied'. Use when: (1) rm -rf of your own scratch, cache, or run trees reports 'cannot remove ... Permission denied' although you own the entries, (2) container test fixtures, package caches, or model-hub caches left read-only modes behind, or (3) a keep-filter protected live directories on the first pass but a later unfiltered pass deleted them."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [filesystem, permissions, chmod, rm, cleanup, shared-storage, network-filesystem]
---

# Repair a Bulk Delete That Fails With Permission Denied

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-10-30 |
| **Objective** | Delete large owner-owned trees on a shared filesystem when plain `rm -rf` stops on read-only entries, and keep protective filters intact across every deletion pass. |
| **Outcome** | Successful. After a scoped mode repair, about 39 GB of compiler temps and scratch directories and a multi-terabyte set of archived run trees were deleted. The verified archive copy and the newest run generation stayed intact. |

## When to Use

- `rm -rf` on entries you own fails with `rm: cannot remove '...': Permission denied`.
- The failed entries are mode `0444` files or `0555` directories, typical after container test runs, model-hub or package caches, or backup tools that set read-only modes.
- A cleanup chain stopped at its first failure, so later independent deletion steps never ran.
- A keep-filter, by age or by name, protected live directories on the first pass, and a later unfiltered pass removed them.

## Verified Workflow

### Quick Reference

```bash
# Repair modes in scope, then delete. Use the same keep-filter in both passes.
find ROOT -mindepth 1 -maxdepth 1 ! -name 'KEEP-*' -exec chmod -R u+rwX {} +
find ROOT -mindepth 1 -maxdepth 1 ! -name 'KEEP-*' -exec rm -rf {} +
```

### Suggested Approach

1. **Classify the denial.** Run `ls -ld` on one failing file and its parent directory. An owner-owned file with mode `r--r--r--`, or a parent with mode `dr-xr-xr-x`, means a mode repair is enough. If the owner is a different user, for example root inside a container, `chmod` fails too; remove the entries through that container or host instead.
2. **Repair modes in scope.** Run `chmod -R u+rwX <subtree>`. Capital `X` adds execute or search permission only where some user already has it, so data files stay non-executable. Keep the repair inside the affected subtree: recursive metadata writes can overload weak NAS servers, and a broad recursive chmod over mixed-ownership trees widens access.
3. **Re-run the deletion without chaining independent steps.** Run each independent deletion as its own command, or join them with `;`. A `cmd1 && cmd2` chain stops at the first nonzero exit, and the remaining cleanup silently does not run.
4. **Apply every keep-filter to every pass.** Directories modified within the last day can belong to live jobs. Give the first pass, the mode-repair pass, and each delete pass the same `! -name 'KEEP-*'` or `-mmin +1440` expression. Do not finish with an unfiltered glob.
5. **Verify completion.** Count the remaining entries and confirm the keep targets exist: `find ROOT -mindepth 1 -maxdepth 1 | wc -l`, then list the keep matches.

For irreplaceable data, archive and verify before any deletion. See
[slurm-shared-storage-artifact-relocation](slurm-shared-storage-artifact-relocation.md) and
[backup-before-state-mutation](backup-before-state-mutation.md). This skill starts where that verified copy already exists.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| 1 | Plain `rm -rf` over mixed cleanup trees | `rm` skipped entries with read-only modes and exited nonzero, so some trees stayed behind | Repair modes with `chmod -R u+rwX`, then delete again |
| 2 | Chained independent deletions with `&&` | The first `Permission denied` exit stopped the chain; later independent steps never ran | Run independent destructive steps separately; collect failures, repair, and re-run |
| 3 | Age-filtered first pass, then a final unfiltered glob delete | The glob deleted three recent scratch directories that the filter had kept; live jobs may have used them | Put the keep-filter in every pass, including the last one |

## Results & Parameters

### Configuration

| Parameter | Value | Why |
| --------- | ----- | --- |
| Mode repair | `chmod -R u+rwX` | Owner write everywhere; execute or search permission only where it already exists |
| Keep-filter | `! -name 'KEEP-*'`, `-mmin +1440` | Name or age guard; use the same expression in every pass |
| Scope | One subtree per command | Avoids weak-server metadata overload and mixed-ownership widening |

### Expected Output

- The delete commands exit 0 after the mode repair.
- A re-list of the target directory shows only the keep-filter matches.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Parallel shared-filesystem cleanup session | Deleted compiler temps, scratch directories, and archived run trees after mode repair | See [notes](../skills/rm-permission-denied-owner-readonly-repair.notes.md) |

## References

- [slurm-shared-storage-artifact-relocation](slurm-shared-storage-artifact-relocation.md) — verified copy before source retirement
- [backup-before-state-mutation](backup-before-state-mutation.md) — snapshot gate for irreversible mutations
- [nfs-server-oom-recursive-metadata-ops](nfs-server-oom-recursive-metadata-ops.md) — why recursive metadata writes need a narrow scope
- [container-ci-uid-permissions-rootless](container-ci-uid-permissions-rootless.md) — why broad recursive chmod over mixed ownership is unsafe
- [tooling-wipe-claude-code-session-secrets](tooling-wipe-claude-code-session-secrets.md) — removal of foreign-owned temp dirs through the owning container
