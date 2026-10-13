---
name: testing-shared-host-env-pinning-and-baseline
description: "Run a permission-sensitive repository test suite reliably on an unmanaged shared host and attribute failures correctly. Use when: (1) a suite fails in a shared login shell while hosted CI is green, (2) mode- or ACL-checking tests fail with Errno 95 or 0775-versus-0755 mismatches, (3) a one-shot tool opener shows the suite green while direct runs stay red, or (4) pre-commit and other spawned hooks cannot resolve the repository's own tool binaries."
category: testing
date: 2026-10-09
version: "1.0.0"
user-invocable: false
tags: [shared-host, environment-pinning, umask, tmpdir, xattr, path, uv, pre-commit, test-baseline, pre-existing-failures, phantom-failures, pytest, hpc, multi-session, scratch-worktree]
---

# Shared-Host Test Environment Pinning and Failure Baseline

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-09 |
| **Objective** | Reproduce trusted test results on a shared, unmanaged host, and separate pre-existing environment failures from change-caused failures before any repair. |
| **Outcome** | Successful. Under one pinned environment (`umask`, `TMPDIR`, `PATH`), more than a dozen phantom local failures disappeared, every suspected regression was either pre-existing on clean HEAD or environment-only, and hosted PR checks stayed green. |

## When to Use

- A repository test suite fails in a shared login shell while hosted CI (or a package-clean run) is green.
- Mode- or ACL-checking tests fail with `PermissionError`, `OSError: [Errno 95]`, or 0775-versus-0755 style mismatches.
- A one-shot tool opener (for example `uv run`, a CI wrapper, or an IDE task) reports the suite green while direct runs in your shell stay red — or the other way around.
- `git commit` or another spawned hook aborts with a tool-resolution error even though the tool is installed in the repository environment.
- You are about to blame your change for failures you have not yet reproduced on clean HEAD.

## Verified Workflow

### Quick Reference

Pin the environment once per session, then run every validation command under it:

```bash
umask 022                            # shared hosts often default to 0002
export TMPDIR=/tmp                   # scratch filesystems can lack listxattr/setxattr
export PATH="$PWD/.venv/bin:$PATH"   # one-shot runners and spawned hooks start a different PATH

# Baseline before attribution: clean HEAD, detached scratch worktree, same pinned env.
git fetch origin
git worktree add --detach /tmp/<name>-baseline origin/main
cd /tmp/<name>-baseline && <same test subset>   # count pre-existing failures
# Only the failure delta over this count belongs to your change.
```

### Suggested Approach

Recognize the environment split first. Green hosted CI plus red local runs (or two shells on the same host disagreeing) evidence an environment difference, not a code defect. Match the symptom to the pin before rerunning anything:

| Symptom | Likely cause | Pin |
| ------- | ------------ | --- |
| `OSError: [Errno 95]` in ACL or security-check tests | `TMPDIR` filesystem has no xattr support | `export TMPDIR=/tmp` |
| Mode 0775 where the test expects 0755; permission checks fail on created trees | Login default `umask 0002` | `umask 022` |
| Suite green through a one-shot opener, red (or counts skew) in direct runs | The opener resolves a different `PATH`/dependency source | Export the repo env `PATH` explicitly, rerun both contexts identically |
| Commit aborts inside a hook with a tool-resolution or `FileNotFoundError` | Spawned shells do not inherit activation | Prefix hook commands: `PATH="$PWD/.venv/bin:$PATH" git commit ...` |

Then hold the pin constant. Every validation command in the session runs under the same `umask`/`TMPDIR`/`PATH`, and the PR body records the pin so the evidence is reproducible.

Establish the baseline before attribution. Run the same test subset under the same pinned environment on a detached scratch worktree at clean `origin/main`, and count pre-existing failures. Only the delta over that count belongs to the change; repair the delta, never the phantom set. Use a scratch worktree for this — in a multi-session repository the `stash` namespace is repo-global across worktrees, so a stash hop can apply a concurrent session's content to your tree.

Define completion by the delta: green branch runs under the pin, baseline count reproduced and quoted, and hosted checks observed. See [notes](testing-shared-host-env-pinning-and-baseline.notes.md) for the measured counts and probe details.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Treat all local failures as change-caused | Ran the suite under the default login environment and started attribution | Mode/ACL and xattr failures were environment-only; none traced to the change | Pin the environment and count a clean-HEAD baseline before any attribution |
| Trust a green one-shot opener over red direct runs | One context used `uv run`-style opening, the other direct execution | The two contexts resolved different `PATH`/dependency sources; collected-set sizes also differed | Align the execution context before believing any green/red split |
| Baseline with a different `PATH` than the branch run | Comparison produced false "regression" counts from environment skew | Use byte-identical environment for baseline and branch runs |
| `git stash` hop for a dirty-tree baseline | A stash push/pop in a multi-session repository | The stash namespace is repo-global across worktrees; a pop applied a concurrent session's stash | Use a detached scratch worktree at verified `origin/main` instead |

## Results & Parameters

### Configuration

```bash
umask 022
export TMPDIR=/tmp
export PATH="$PWD/.venv/bin:$PATH"   # substitute the repository's own tool environment
```

### Expected Output

- Phantom mode/ACL failures vanish; the local count drops to the clean-HEAD baseline count, and the branch count matches it (or improves by the intended fix delta).
- Green/red splits between one-shot openers and direct runs disappear once `PATH` is aligned.
- Hooks resolve repository binaries when invoked with the env `PATH` prefix.
- PR evidence (commands and counts) is reproducible under the documented pin.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| LLM360/Comet | Implementation validation on a shared HPC host, 2026-10-08/09 | 15 pre-existing failures under the login environment; 59/59 and 61/61 green under the pin; two independent parallel sessions reproduced the same phantom set and same recovery. See [notes](testing-shared-host-env-pinning-and-baseline.notes.md). |

## References

- [Hephaestus loop on an unconfigured host](hephaestus-loop-unconfigured-host-operation.md) — adjacent host bring-up runbook for the same class of unmanaged cluster machines.
- [Recover stashed work after a concurrent branch reset](tooling-git-recover-stashed-work-after-concurrent-branch-reset.md) — companion shared-checkout stash guidance (recovery direction).
- [Stage only your own files in a shared worktree](tooling-stage-only-your-own-files-in-shared-worktree.md) — companion shared-worktree discipline (staging direction).
