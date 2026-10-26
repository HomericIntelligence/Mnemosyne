---
name: debugging-dangling-symlink-file-exists-no-such-file
description: "Diagnose and recover when one path reports EEXIST (File exists) on mkdir but ENOENT (No such file or directory) on access. Use when: (1) a tool crashes at startup with ENOENT on mkdir of a log/state/data path whose parent exists, (2) mkdir of a path says File exists while ls of the same path says No such file or directory, (3) mkdir -p fails with ENOENT although the parent directory exists, (4) a tool data directory was symlinked to scratch space and broke after a reboot, cleanup, or reimage."
category: debugging
date: 2026-10-25
version: "1.0.0"
verification: verified-local
user-invocable: false
tags: [symlink, dangling-symlink, enoent, eexist, mkdir, filesystem, startup-crash, xdg, opencode, diagnosis]
---

# Dangling symlink: contradictory "File exists" vs "No such file or directory"

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-25 |
| **Objective** | Diagnose a tool crash that reports ENOENT on a path whose parent directory exists, and recover without reinstalling the tool. |
| **Outcome** | Root cause identified as a dangling symlink mid-path; the EEXIST-on-mkdir plus ENOENT-on-access contradiction is its diagnostic signature. Recovery is a one-command fix: recreate the symlink target or remove the link. Verified by live reproduction on OpenCode 2.1.3 including a valid-target control case. |
| **Trigger signature** | The same path yields `File exists` (EEXIST) and `No such file or directory` (ENOENT) depending on the operation. |

## When to Use

- A program fails at startup or runtime with `ENOENT: no such file or directory` on a path whose parent directory you can list.
- `mkdir <path>` reports `File exists` while `ls <path>` or `mkdir <path>/child` reports `No such file or directory` for the **same** path.
- `mkdir -p <path>/child` fails with ENOENT even though `-p` normally creates missing parents.
- The tool's data or state directory was previously symlinked to scratch space (for example `/var/tmp/$USER/...` or `/scratch/...`) and the tool broke after a reboot, a tmp-cleaner run, or a node reimage.

Verified trigger case: OpenCode 2.x crashes on every command with
`PlatformError: NotFound: FileSystem.makeDirectory ($XDG_DATA_HOME/opencode/log)`
when `$XDG_DATA_HOME/opencode` (typically `~/.local/share/opencode`) is a dangling symlink.

Do **not** use this workflow when ENOENT occurs on a path with no symlink component (a plain
missing directory, where `mkdir -p` succeeds), or when the error is EACCES (a permissions
problem with a different recovery).

## Verified Workflow

### Quick Reference

```bash
# 1. Confirm a mid-path component is a dangling symlink: the link exists, its target does not.
ls -la <parent-dir>            # shows: <name> -> /some/target
stat <path>                    # ENOENT: link resolves to nothing
readlink -m <path>             # prints the resolved target that must be created or abandoned
find <parent-dir> -maxdepth 2 -xtype l   # list broken symlinks directly

# 2. Recover with exactly ONE of:
mkdir -p "$(readlink -m <path>)"   # create the target tree; keeps the indirection
rm <path>                          # remove the link only (rm on a symlink never removes the target)

# 3. Re-run the failing command. The tool recreates what it needs inside the now-valid path.
```

### Decision rule

The EEXIST-plus-ENOENT contradiction on one path is the diagnostic signature of a dangling
symlink in the path chain:

- `mkdir <link>` -> EEXIST: existence checks use lstat, and the symlink entry itself exists.
- `operation <link>/child` -> ENOENT: name resolution follows the link into a nonexistent target.
- `mkdir -p <link>/child` -> ENOENT: `-p` stops at the "existing" link component, then fails
  descending through it. Recursive mkdir cannot create through a dangling symlink.

Corollaries:

- The contradiction is not a race condition, not a filesystem bug, and not (by itself) a defect
  in the failing tool. Do not reinstall the tool; fix the path chain.
- Common origin: a data directory was symlinked to scratch storage to save a home-directory
  quota, and the scratch tree was later cleaned or the host reimaged, leaving the link behind.

### Detailed Steps

1. Reproduce the failure and record the exact errno and path from the tool error.
2. Try the error's implied manual fix, `mkdir <path>` and `mkdir -p <path>/child`. If mkdir
   reports `File exists` for the directory but still cannot create children, the dangling-
   symlink signature is confirmed; do not keep retrying mkdir variants.
3. Walk the chain with `ls -la` on each parent, or list broken links directly with
   `find <root> -xtype l`. Identify the dangling component and its intended target with
   `readlink -m`.
4. Decide by intent of the original indirection:
   - The indirection is still wanted: create the target with `mkdir -p "$(readlink -m <path>)"`.
   - The indirection is obsolete (scratch moved, quota rules changed): remove the link with
     `rm <path>` so the tool creates a real directory in place.
5. Re-run the tool and verify normal startup.
6. Optional isolation test for tool-vs-environment attribution: point the tool's path
   variable (for example `XDG_DATA_HOME`) at a fresh temporary directory containing only the
   suspected symlink, and run the command once. Reproduce the crash to confirm environment as
   the cause. Then recreate the symlink with an existing target as a control case: if the
   tool now works, the failure is specific to the dangling case, which is strong evidence for
   an upstream report.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Attempt 1 | `mkdir <path>/log` after the tool error named that path | Returns ENOENT: name resolution descends through the dangling link into a missing target | The path in a tool error cannot be created manually when a mid-chain component is a dangling symlink |
| Attempt 2 | `mkdir -p <path>/log` to force recursive creation | `-p` sees EEXIST on the symlink component, then ENOENT descending through it | Recursive mkdir does not resolve or repair dangling symlinks; stop retrying mkdir variants |
| Attempt 3 | `mkdir <path>` as a parent fix | Returns `File exists` although the directory "does not exist" per ls | Lstat-based checks see the symlink entry itself; the existence contradiction is the diagnosis, not noise |
| Attempt 4 | Reinstalling or upgrading the tool, or re-running the installer | Identical crash on next start; the link survives any reinstall | When the path chain is broken, repair the chain, not the installation |

## Results & Parameters

### Environment of the verified case

- Tool: OpenCode CLI, version 2.1.3, release install channel.
- OS: Linux x86_64 (kernel 5.15); shell: /bin/bash.
- Data path: `$XDG_DATA_HOME/opencode` as a symlink to a cleaned scratch tree.

### Verified behavior matrix

| Symlink target | Tool behavior | Manual mkdir behavior |
| --- | --- | --- |
| Dangling (target missing) | Startup crash: `PlatformError: NotFound: FileSystem.makeDirectory (...)`, cause `ENOENT` | `mkdir` reports EEXIST on the link, ENOENT through it |
| Existing | Normal startup; log directory created at the target | Not needed; succeeds |

### Upstream-report guidance

When the tool owns the failing mkdir, report the bug upstream with: the minimal reproduction
(dangling symlink on the data path), the valid-target control case, the contradictory mkdir
output, the workaround (recreate target or remove link), and a suggested fix (resolve the path
and create the real target, or emit an actionable error naming the link and its target).
Identifying the dangling-only boundary converts an opaque errno crash into an actionable report.
A report filed from this incident is linked in References.

## Verified On

- OpenCode 2.1.3 on Linux: deterministic crash reproduced with a clean `XDG_DATA_HOME`
  containing only a dangling symlink named `opencode`; recovery via `rm` of the link; valid-
  target control case passed (tool runs, creates its log directory at the target).
- Mechanism cross-check: manual `mkdir` and `mkdir -p` reproduce the EEXIST/ENOENT
  contradiction on the same chain, independent of the tool.

## References

- Upstream report: anomalyco/opencode issue 58212 (public): startup crash when the data
  directory is a dangling symlink.
- Companion evidence and reproduction logs: `debugging-dangling-symlink-file-exists-no-such-file.notes.md`.
