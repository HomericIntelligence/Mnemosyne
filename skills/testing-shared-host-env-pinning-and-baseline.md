---
name: testing-shared-host-env-pinning-and-baseline
description: "Run a permission-sensitive repository test suite reliably on an unmanaged shared host and attribute failures correctly. Use when: (1) a suite fails in a shared login shell while hosted CI is green, (2) mode- or ACL-checking tests fail with Errno 95 or 0775-versus-0755 mismatches, (3) a one-shot tool opener shows the suite green while direct runs stay red, (4) pre-commit and other spawned hooks cannot resolve the repository's own tool binaries, (5) a required commit gate runs that suite and cannot pass on this host for any change, (6) the change that would repair the gate is itself blocked by the gate, or (7) one checkout of the repository is green where a sibling checkout is red on the same host."
category: testing
date: 2026-10-09
version: "1.2.0"
user-invocable: false
tags: [shared-host, environment-pinning, umask, tmpdir, xattr, path, uv, pre-commit, test-baseline, pre-existing-failures, phantom-failures, pytest, hpc, multi-session, scratch-worktree, commit-gate, structural-block, self-unblocking-gate, cross-checkout-identity, virtualenv-base-interpreter, environment-divergence, test-attribution]
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
- A required commit gate runs the suite and fails for every change on this host, so no commit can be created.
- The change that would repair the gate is itself blocked by that gate.
- One checkout of the repository is green where a sibling checkout is red, and you are about to name test order, a missing fixture, or your change as the cause.
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
| One checkout green, a sibling checkout red at the same commit | Each checkout has its own environment, and the newer one used a different base interpreter | Compare the resolved base interpreter and its mode in both checkouts |

### When the gate is the suite and no pin reaches it

`umask`, `TMPDIR`, and `PATH` fix **created** trees and **resolved** binaries. Four cases survive every pin. Recognize them and stop searching the pin list.

**1. The inspected file already exists and is group-writable.** A permission guard that checks a pre-existing executable does not care how new files are created. Probe the target itself:

```bash
stat -c '%a %n' "$(readlink -f "$(command -v python3)")"
# 775 <path>   -> no umask change reaches this. The mode already exists on disk.
```

If the suite passes `sys.executable` or another host-owned path into the guard, the only repairs are host-side (`chmod g-w` on that file) or test-side (make the seam explicit: pin a trusted path, or skip with an explicit reason). Do not weaken the guard.

**2. The guard runs inside a required gate.** When a pre-commit hook executes the suite, the hook is the gate. A gate that cannot pass on this host blocks every commit, for every change, including the change that would fix it. Diagnose it once:

```bash
umask 022                       # does the lock-file class clear?
git -c core.hooksPath=/dev/null commit --dry-run   # NO. never use this to land a commit
```

Read the last hook output, name the branch above, and stop. Do not re-run the gate hoping for a different result: each attempt is one full suite, and none can pass.

**3. The change that repairs the gate is blocked by the gate.** This looks impossible and is not. A pre-commit hook runs against the **working tree**, not against `HEAD`. So once the repair is staged, the hook sees the repaired code and the commit succeeds even while `HEAD` is still red. Stage the repair and commit it. If the repair is a test-only change, it still unblocks itself the same way.

**4. The checkout itself no longer matches the index-recorded modes.** A worktree or clone created under a permissive creation `umask` (`0002`) lands every tracked file group-writable (`0775`/`0664`) while the object database records `0755`/`0644`. A gate that maps reviewed programs or fixtures by exact mode then fails on many paths at once, and `git status` can list phantom mode-only modifications. A session harness can create the checkout before the session pin exists, so the pin alone cannot prevent this case. Normalize the tree to the recorded modes; the repair touches the filesystem only:

```bash
git ls-files -s | awk '$1=="100755"{print $4}' | while IFS= read -r f; do chmod 0755 "$f"; done
git ls-files -s | awk '$1=="100644"{print $4}' | while IFS= read -r f; do chmod 0644 "$f"; done
```

Recreating the worktree under `umask 022` also produces the recorded modes. Do not commit the drifted modes and do not weaken a reviewed-mode map.

Never weaken the guard to get past the gate. The gate failing on a correct guard is the signal to fix the seam, not to remove the check.

Then hold the pin constant. Every validation command in the session runs under the same `umask`/`TMPDIR`/`PATH`, and the PR body records the pin so the evidence is reproducible.

Establish the baseline before attribution. Run the same test subset under the same pinned environment on a detached scratch worktree at clean `origin/main`, and count pre-existing failures. Only the delta over that count belongs to the change; repair the delta, never the phantom set. Use a scratch worktree for this — in a multi-session repository the `stash` namespace is repo-global across worktrees, so a stash hop can apply a concurrent session's content to your tree.

Define completion by the delta: green branch runs under the pin, baseline count reproduced and quoted, and hosted checks observed. See [notes](testing-shared-host-env-pinning-and-baseline.notes.md) for the measured counts and probe details.

### When two checkouts disagree, compare environment identity first

A test result from one checkout is not evidence about another checkout of the same repository. This rule holds when both checkouts have the same commit, the same host, and the same time.

A tool that builds a virtual environment for a new worktree takes the first interpreter that it finds. That interpreter is often not the one that the existing environment uses. The two checkouts then run different binaries with different permissions. A guard that checks the interpreter reaches opposite verdicts in the two checkouts.

Compare the base interpreter in each checkout before you name the code, test order, or a fixture as the cause. Resolve the link before you compare. A guard inspects the target, not the link.

```bash
for v in <checkout-a>/.venv <checkout-b>/.venv; do
  printf '%s ' "$v"; stat -c '%a' "$(readlink -f "$v/bin/python3")"
done
# 755 <checkout-a>/.venv   -> private base; the trust guard accepts it
# 775 <checkout-b>/.venv   -> group-writable base; the trust guard rejects it
```

An equal commit and an equal host with different verdicts mean that the environments differ. Test order is not the cause.

Build the divergent environment against the interpreter that the trusted checkout uses:

```bash
uv sync --python <path-to-a-private-mode-interpreter>
```

Run both checkouts again. A difference that disappears was environmental. Only a failure that survives an equal environment identity belongs to the change.

Do not weaken a guard to correct this. The guard is right. The environment that it inspected was not the one you assumed.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Treat all local failures as change-caused | Ran the suite under the default login environment and started attribution | Mode/ACL and xattr failures were environment-only; none traced to the change | Pin the environment and count a clean-HEAD baseline before any attribution |
| Trust a green one-shot opener over red direct runs | One context used `uv run`-style opening, the other direct execution | The two contexts resolved different `PATH`/dependency sources; collected-set sizes also differed | Align the execution context before believing any green/red split |
| Baseline with a different `PATH` than the branch run | Comparison produced false "regression" counts from environment skew | Use byte-identical environment for baseline and branch runs |
| `git stash` hop for a dirty-tree baseline | A stash push/pop in a multi-session repository | The stash namespace is repo-global across worktrees; a pop applied a concurrent session's stash | Use a detached scratch worktree at verified `origin/main` instead |
| Re-run a structurally failing commit gate hoping it passes | Ran the hook three times after its failures were already attributed to host permissions | Every attempt costs a full suite run and none can pass. The repetitions also raised host load, so each attempt took far longer than the first | Diagnose the gate once, name the branch, and stop. Report the block instead of retrying it |
| Overlap your own full-suite runs while a gate is slow | Several independent suites launched together after the first hook attempt was slow | Host load reached roughly half the core count. Each later attempt inherited the contention, and the two concurrent writers made attribution noisy | Bound concurrent suites. One gate attempt at a time, and one validation owner per worktree |
| Escalate a host-environment failure before checking the existing rule | Filed a tracking issue for a mode-mismatch failure class | The pin set in this entry already names the cause and the fix. The issue restated a known rule | Search the existing rule before escalating. Extend it when the new case is not covered; do not duplicate it |
| Name test order as the cause of a difference between two checkouts | Bisected the order, and every step reproduced the failure, so the split looked like shared state | Both halves of the bisect ran in the same environment. The isolation run that passed ran in the other checkout | Compare the environment identity of both checkouts before you name order, pollution, or a fixture |

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
- A structurally blocked gate is reported once with its measured cause, not retried.
- A repair that unblocks its own gate commits cleanly, because the hook sees the working tree.
- A difference between two checkouts disappears after both checkouts use an equal environment identity.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| LLM360/Comet | Implementation validation on a shared HPC host, 2026-10-08/09 | 15 pre-existing failures under the login environment; 59/59 and 61/61 green under the pin; two independent parallel sessions reproduced the same phantom set and same recovery. See [notes](testing-shared-host-env-pinning-and-baseline.notes.md). |

## References

- [Hephaestus loop on an unconfigured host](hephaestus-loop-unconfigured-host-operation.md) — adjacent host bring-up runbook for the same class of unmanaged cluster machines.
- [Recover stashed work after a concurrent branch reset](tooling-git-recover-stashed-work-after-concurrent-branch-reset.md) — companion shared-checkout stash guidance (recovery direction).
- [Stage only your own files in a shared worktree](tooling-stage-only-your-own-files-in-shared-worktree.md) — companion shared-worktree discipline (staging direction).
