---
name: ci-failure-triage-and-diagnosis
description: "Canonical workflow for triaging CI failures: log analysis, core dump capture, subprocess hang diagnosis, container forensics, libKGEN/JIT crash retrieval, GHA-only vs cross-environment failures, PR-specific vs systemic failure separation. Use when: (1) a CI run failed and you need to identify the root cause, (2) deciding whether a failure is PR-induced or pre-existing, (3) capturing core dumps from container environments, (4) reproducing a GHA-only crash locally, (5) GraphQL/REST rate-limited CI monitoring."
category: ci-cd
date: 2026-06-20
version: "2.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
history: ci-failure-triage-and-diagnosis.history
tags: [ci-failure, triage, log-analysis, core-dump, forensics, gdb, podman, mojo, libkgen, github-actions, rate-limit, subprocess, signal, cpu-survey, workflow-dispatch]
---

# CI Failure Triage and Diagnosis

## Overview

Use evidence from the failing run to separate a PR regression, broken main, transient failure,
missing required context, environment-specific crash, and hung subprocess. The workflow is
`verified-local`; individual CI-confirmed cases and the unverified downstream hardening proposal
are indexed in [the notes](ci-failure-triage-and-diagnosis.notes.md).

## When to Use

- A CI run failed, a report links a run but claims detailed logs are unavailable, or a proposed
  fix was formed without reading `--log-failed`.
- Several unrelated PRs fail in the same job/file, or main may already be broken.
- A PR is `BLOCKED` with no failed check because a required context never posted.
- A containerized JIT crash leaves no core, or a crash appears only on GitHub-hosted CPUs.
- A parallel runner hangs, ignores shutdown, or corrupts the caller's terminal.
- Diagnostic API loops approach rate limits, debug instrumentation should be opt-in, or a stale
  lockfile failure needs a current-SHA rerun.

Do not use a stale issue narrative as the source of truth. Reconcile the run's workflow snapshot,
action versions, current main, and repository dependency declarations before proposing a fix.

## Verified Workflow

### Quick Reference

```bash
# Read the real failure before hypothesizing.
gh run view <RUN_ID> --repo <org>/<repo>
gh run view --job=<JOB_ID> --repo <org>/<repo> --log-failed

# Check current main and whether the fix already landed.
git log -S '<fix string>' --oneline -- .github/workflows/<workflow>
gh run list --repo <org>/<repo> --workflow=<workflow> --branch main --limit 5 \
  --json conclusion,status,name,createdAt

# Distinguish transient from reproducible failure.
gh run rerun <RUN_ID> --failed --repo <org>/<repo>
gh run watch <RUN_ID> --repo <org>/<repo>

# Budget batch diagnostics.
gh api rate_limit --jq '.resources.core | "used:\(.used)/\(.limit) resets:\(.reset|todate)"'
```

### 1. Establish the failing evidence

1. List the run, identify the failing job and step, then fetch that job's `--log-failed` output.
2. Read the error literally. Exit 127 or `command not found` means the recipe may never have run;
   first identify the missing interpreter, tool, or shell function.
3. Record action versions from the run log. A different version on current main proves the run's
   workflow snapshot is stale.
4. Search current history for the suspected fix and inspect the latest main runs. If recent main
   runs are green, document the already-landed fix instead of inventing another.
5. Confirm every proposed verification command exists in the dependency manifest or is installed
   by the same workflow step. Do not cite an unavailable `pixi run <tool>` command.

The log retrieval and current-main checks were exercised locally. Any implementation inferred
from them remains unverified until its own tests or CI run succeed.

### 2. Classify ownership and recurrence

Check main before rebasing downstream branches. When unrelated PRs fail at the same job/file/line,
confirm the file is on main and absent from each PR diff; fix main once, then rebase downstream.
Do not scatter suppressions across the affected PRs. After force-updating a downstream branch,
re-arm its auto-merge request because the force update clears it.

For a red run, rerun only failed jobs. A pass is evidence of a transient failure; a repeated,
same-signature failure is reproducible. Empty commits are unreliable with concurrency
deduplication; use `gh run rerun --failed`.

For `BLOCKED` with no failure, compare required and posted contexts:

```bash
gh api repos/<org>/<repo>/branches/main/protection/required_status_checks \
  --jq '.contexts[]' | sort > /tmp/required.txt
gh pr view <PR> --repo <org>/<repo> --json statusCheckRollup \
  --jq '.statusCheckRollup[].name' | sort -u > /tmp/present.txt
comm -23 /tmp/required.txt /tmp/present.txt
```

A whole-job `if:` or excluding `paths:` filter can prevent a required context from posting. Keep
the required job running and skip work at step level, or provide an aggregator that always posts.

### 3. Classify OOM and JIT crashes

Exit code 137 is not decisive: both OOM and an in-process signal handler can produce it. Prefer
log signatures:

| Signal | Disposition |
| --- | --- |
| `Killed`, OOM-killer, address-space or `mmap` failure without libKGEN | Treat as OOM |
| `libKGENCompilerRTShared.so+0x...` without OOM evidence | Treat as a separate JIT crash |
| Mixed or unknown signature | Escalate; neither auto-revert nor auto-ship |

If a container crash leaves an empty core directory, set `/proc/sys/kernel/core_pattern` to a path
visible in the crashing process's mount namespace, such as the container-side bind mount:

```bash
echo '/workspace/crash-bundle/cores/core.%p.%e.%t' \
  | sudo tee /proc/sys/kernel/core_pattern
```

When a user-space libKGEN handler consumes SIGILL/SIGABRT before the kernel dumps, run the inferior
through `pixi run -- gdb`, register `gdb.events.stop`, and accept only `gdb.SignalEvent`. Handle
SIGILL, SIGABRT, SIGSEGV, SIGBUS, and SIGFPE; write `128 + signal` to a temporary exit file because
`--return-child-result` is unreliable in batch mode. Symbolicate inside the container where both
the binary and bind-mounted core paths resolve.

For a GitHub-hosted-only SIGILL, compare repeated runs across CPU families and record model name,
CPUID flags, image digest, iteration count, and exit-code histogram. Do not conclude that missing
AVX-512 flags alone are causal: virtualization may mask CPUID while code generation uses another
CPU identity signal.

### 4. Make expensive diagnostics opt-in

Gate gdb/core capture behind a boolean `workflow_dispatch` input with `default: false`. Set the
derived switch at job-level so every relevant step sees it, and guard against inputs on other
events:

```yaml
env:
  MOJO_TEST_UNDER_GDB: >-
    ${{ (github.event_name == 'workflow_dispatch' && inputs.enable_gdb_cores) && '1' || '0' }}
```

Trigger it explicitly with:

```bash
gh workflow run <workflow>.yml -f enable_gdb_cores=true --ref <branch>
```

### 5. Keep subprocess orchestration interruptible

Replace indefinite completion waits with `wait(pending, timeout=2.0,
return_when=FIRST_COMPLETED)`, checking the shutdown event after every timeout. A completed future
may use `future.result(timeout=0)`. Poll `proc.communicate(timeout=2.0)` and subtract from the total
timeout; on shutdown, kill the process group and raise the shutdown exception.

Use `stdin=subprocess.DEVNULL` for noninteractive children. Restore the terminal only when stdin is
a TTY. Never register SIGTSTP as an ordinary graceful-shutdown signal, and never call
`threading.Event.wait()` without a timeout in the coordinator.

### 6. Preserve API and rerun budgets

Prefer one `gh pr list --json ...` over a per-PR `gh pr view` loop. Stop bulk log retrieval below
500 remaining core calls and stop nonessential API use below 100. For a stale lockfile, regenerate
with the repository package manager, commit the lockfile, push, then rerun the failed run tied to
the current head SHA.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Hypothesis before log retrieval | Diagnosed workflow internals from an issue narrative | The failing recipe never ran; `--log-failed` showed exit 127 | Fetch the failing job log first |
| Host-path core capture | Put the runner CWD in `core_pattern` | The path did not exist in the crashing container namespace | Use the container-visible bind path |
| Bare gdb and `hook-stop` | Ran host gdb and dumped on every stop | Environment paths were absent and exit-stop is not a live signal stop | Use `pixi run -- gdb` plus `SignalEvent` |
| Exit 137 as OOM proof | Classified every 137 as OOM | A JIT signal handler produced the same code | Combine exit code with log signatures |
| Per-PR suppression | Patched identical failures on each branch | The defective file came from main | Fix main once, then rebase |
| Blocking futures | Used `as_completed()` and unbounded waits | Shutdown could not be observed while nothing completed | Poll at two-second intervals |
| Always-on debug capture | Defaulted gdb collection to true | Every PR paid the diagnostic cost | Use an opt-in dispatch input |

## Results & Parameters

| Parameter | Recommended value or rule |
| --- | --- |
| Failing evidence | `gh run view --job=<JOB_ID> --log-failed` before diagnosis |
| Recurrence | One failed-job rerun; repeated same signature is reproducible |
| Shutdown poll interval | `2.0` seconds |
| gdb signals | SIGILL, SIGABRT, SIGSEGV, SIGBUS, SIGFPE |
| Debug input | Boolean, `default: false`, dispatch-only |
| API reserve | Stop bulk logs below 500; nonessential calls below 100 |
| CPU survey | Same image/reproducer, repeated runs, model/flags/exit histogram |

## Companions

- [Case evidence and detailed verification](ci-failure-triage-and-diagnosis.notes.md)
- [Version history and superseded content](ci-failure-triage-and-diagnosis.history)
