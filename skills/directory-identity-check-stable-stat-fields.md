---
name: directory-identity-check-stable-stat-fields
license: BSD-3-Clause
description: "Compare only stable stat fields when a same-object identity check protects a directory resolution. Use when (1) a fail-closed root or path resolution must stay correct while other processes create, replace, or remove entries in its tree; (2) a long-running process revalidates a directory and stops after days with a changed-during-resolution error while every deployed input is identical; (3) you write a deterministic regression test for the race and a file create+unlink pair can silently restore every sampled metadata field."
category: architecture
date: 2026-10-23
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - same-object-check
  - stat
  - directory-identity
  - race-condition
  - concurrent-writers
  - fail-closed
  - inode
  - mtime
  - nlink
  - coarse-timestamp
  - deterministic-test
---

# Directory Identity Check with Stable Stat Fields

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-23 |
| **Objective** | Keep a fail-closed same-object guard on a directory correct while concurrent writers add and remove entries below it. |
| **Outcome** | Successful as diagnosis and design rule. The defect was proven from production failure evidence; the corrected comparison is proven by a deterministic boundary test that fails before the correction and passes after it. Deployment of the correction at the source incident is outside this entry. |
| **Verification** | verified-local - the production failure shape is documented in notes; the defect and the correction are proven by a deterministic regression test on live production code paths at the incident site; the corrected comparison is not yet deployed there. |

## When to Use

- You design or review a same-object check on a directory: a process resolves a root or path and then proves, usually by comparing `fstat` on an open descriptor with `stat` on the path, that nothing swapped the object between resolve and use.
- The directory tree receives legitimate concurrent writes: heartbeats, status files, rendered documents, or rolling replacement of entries. Waiters that fail closed on any difference convert those benign writes into fatal errors.
- A long-running process dies rarely (days between events) with a resolution mismatch error, and every declared input (specification, paths, principals) is identical across the failure. The event time correlates with a writer's flush inside the tree.
- You write a regression test for this race and want it deterministic: no sleeps, no threads, and no dependence on wall-clock timing.

Do not use this entry for identity material that different hosts must compute identically. That intent has its own entry, `cross-host-identity-divergence-volatile-hash-inputs`. The distinction: cross-host divergence comes from mount-instance metadata that differs between clients; this entry covers a same-host check that compares one object with itself over time, where `st_dev` and `st_ino` are the stable ground truth.

## Verified Workflow

### Quick Reference

```text
A same-object identity check on a directory MUST compare only fields
that change when the object itself changes:
  - st_dev, st_ino    identify the filesystem object
  - st_mode           object type and permission bits
  - st_uid, st_gid    ownership, when ownership is part of the contract
Such a check MUST NOT compare fields that change on ordinary writes
below the checked directory:
  - st_mtime, st_mtime_ns, st_ctime, st_ctime_ns   updated by any
    create, rename, or unlink inside the directory
  - st_size                                       directory entry count
                                                  can change it
  - st_nlink                                      subdirectory add or
                                                  remove changes it
Equality of the stable set proves "same object". The volatile fields
measure recent write activity, which is not an identity change.
```

### Suggested Approach

1. **Separate identity from activity.** `st_dev` and `st_ino` change only when the object is replaced. `st_mode`, `st_uid`, and `st_gid` change only on permission or ownership mutations, which are identity-relevant for a trust boundary. The volatile class (`st_mtime*`, `st_ctime*`, `st_size`, `st_nlink` on a directory) changes on writes completely below the checked object that leave its identity intact. Compare identity; treat activity as logging material only.
2. **Treat volatile-field equality as a fatal-false-positive generator.** A guard that compares volatile fields needs a writer flush to fall between the two stat calls. That window is sub-millisecond, so the event is rare: normal test runs and even soak days do not hit it, then a healthy production component dies. Rarity is a property of the window size, not evidence that the comparison is safe.
3. **Keep the fail-closed posture for the stable class.** Removing volatile fields does not weaken the guard: an attacker or a bug that replaces the directory changes its inode; a permission or ownership change shows in the stable class. The guard still fails closed on every real identity change.
4. **Test at the stat boundary, not at the clock.** Introduce a seam at the point where the guard reads the descriptor and the path (usually one helper). In the test, run the directory mutation between the two reads through that seam. This makes the race deterministic on any filesystem and any scheduler.
5. **Make the injected churn guaranteed-visible.** Use a mutation that must change observable directory metadata: creating and keeping an empty subdirectory increments the parent's `st_nlink` on typical filesystems and also sets `st_mtime` and `st_ctime`. A file create+unlink pair inside the directory is not reliable: name reuse can restore every sampled field, and coarse timestamp granularity can make `st_mtime` identical, so the test samples equal metadata before and after the "mutation" and proves nothing.
6. **Prove both arms of the guard in the test.** The benign-churn case must pass after the correction. The true-replacement case (a different inode at the same path) must still fail closed. A correction that passes the first arm and loses the second is a hole, not a fix.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Volatile-field equality as the guard | Include resolved-path strings plus volatile stat fields (mtime with nanosecond precision, among others) in the comparison between an open descriptor and the freshly read path. | Any sibling write inside the tree updates the directory's volatile fields. Over weeks, a timed heartbeat flushed inside the resolve-to-use window and killed a healthy replica of a serving pool. | Compare identity, not activity. `st_dev` and `st_ino` are the identity; everything else is reporting. |
| File create+unlink as deterministic test churn | In the regression test, create a temporary file in the target directory and unlink it between the two stat reads, as the minimal benign write. | On filesystems with coarse timestamp granularity, and with the name released for reuse, the directory's sampled metadata (mtime, ctime, size, nlink) can be identical before and after the pair. The "racy" test then runs the guard with equal data and silently proves nothing. | Test-side churn must be observable in the compared data, not only in the write syscall count. A kept subdirectory changes parent `st_nlink` on typical filesystems and cannot be undone by coarse timestamps. |

## Results & Parameters

### Configuration

```yaml
same_object_directory_check:
  compare:
    - st_dev      # filesystem identity
    - st_ino      # object identity within the filesystem
    - st_mode     # type and permission bits
    - st_uid      # include when ownership is part of the trust contract
    - st_gid
  do_not_compare:
    - st_mtime / st_mtime_ns
    - st_ctime / st_ctime_ns
    - st_size     # directory entry count can change it
    - st_nlink    # subdirectory churn changes it without an identity change
regression_test:
  injection_point: between the descriptor read and the path read at the guard seam
  benign_churn: created-and-kept empty subdirectory inside the target directory
  forbidden_churn: file create+unlink (can restore every sampled field)
  required_arms:
    - benign churn passes after the correction
    - true replacement (new inode at the same path) still fails closed
```

### Expected Output

- The guard ignores heartbeat, status, and render writes below the directory and stays armed for real inode replacement and for permission or ownership changes.
- The regression test fails on the volatile-field implementation before the correction and passes on the stable-field implementation, deterministically and on filesystems of any timestamp granularity.
- No more changed-during-resolution kills under concurrent writers; when such a kill does occur, the evidence now points to a real replacement instead of write noise.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private shared-cluster deployment (identifiers withheld) | Fail-closed binding of a long-running registrar component to its deployment root, racing a periodic heartbeat writer into the same tree | Failure shape, window analysis, and test evidence in [notes.md](directory-identity-check-stable-stat-fields.notes.md). |

## References

- Different scope, do not merge: `cross-host-identity-divergence-volatile-hash-inputs` removes volatile mount-instance fields from identity material that many hosts compute. This entry keeps `st_dev` and `st_ino` as the stable ground truth for a same-host same-object check.
- POSIX `stat(2)` manual page on the host for field definitions and update rules.
