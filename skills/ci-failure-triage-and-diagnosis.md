---
name: ci-failure-triage-and-diagnosis
description: "Diagnose CI failures from run logs and revision-specific workflows. Distinguish source defects, missing required contexts, infrastructure failures, stale runs, rerun identity rejections, and runs that merge conflicts suppressed."
category: ci-cd
date: 2026-10-15
version: "2.5.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
tags: [ci-failure, triage, log-analysis, core-dump, forensics, gdb, podman, mojo, libkgen, github-actions, rate-limit, subprocess, signal, cpu-survey, workflow-dispatch, merge-conflict]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/ci-failure-triage-and-diagnosis.history"
history-cleanup-date: "2026-09-20"
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
- A push to a PR branch produced no `pull_request` runs at that head at all: the rollup and the
  per-head `actions/runs` list are empty rather than red.
- A containerized JIT crash leaves no core, or a crash appears only on GitHub-hosted CPUs.
- A root-cause claim quotes log lines that were not verified against the bare job log, or a
  quoted failure line cannot be found again in the log that it was attributed to.
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

# Verify quoted text against the bare job log before attributing it.
gh api repos/<org>/<repo>/actions/jobs/<JOB_ID>/logs > job.log
grep -c '<token>' job.log  # the count must be above 0 before attribution

# Check current main and whether the fix already landed.
git log -S '<fix string>' --oneline -- .github/workflows/<workflow>
gh run list --repo <org>/<repo> --workflow=<workflow> --branch main --limit 5 \
  --json conclusion,status,name,createdAt

# Distinguish transient from reproducible failure.
gh run rerun <RUN_ID> --failed --repo <org>/<repo>
gh run watch <RUN_ID> --repo <org>/<repo>

# Recover when the rerun rejects attempt-bound producer outputs.
gh run rerun <RUN_ID> --repo <org>/<repo>

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
6. Verify quoted log text against the bare job log before it grounds a root cause. Filtered or
   decorated views, such as pipelines over `gh run view --log`, composed greps, and truncated
   previews, can surface text that is not job-log content. A match in such a view is not
   evidence of log content. Fetch the bare log through the authenticated API into a file, count
   occurrences of the quoted token, and quote only text that appears there, with line context:

   ```bash
   gh api repos/<org>/<repo>/actions/jobs/<JOB_ID>/logs > job.log
   grep -c '<token>' job.log
   ```

   The failure signature is a hypothesis that dissolves at bare-log inspection: the token has
   zero occurrences. Discard the ghost, read the true failed assertion from the bare log, and
   correct every report or dispatch that consumed the quoted text.

The log retrieval and current-main checks were exercised locally. Any implementation inferred
from them remains unverified until its own tests or CI run succeed.

### 2. Classify ownership and recurrence

Check main before changing downstream branches. When unrelated PRs fail at the same job/file/line,
confirm the file is on main and absent from each PR diff; fix main once. An active downstream task
may rebase only when that main fix is required to complete the task. A completed, non-conflicting PR
stays unchanged for CI/CD integration. Do not scatter suppressions across the affected PRs. After a
permitted force update, re-arm its auto-merge request because the force update clears it.

Before a retry, compare the run's source SHA with the source that needs validation.
A rerun retains its original source. It does not test a later repair commit.
For a red run on the intended source, rerun only failed jobs. A pass is evidence of a transient failure; a repeated,
same-signature failure is reproducible. Empty commits are unreliable with concurrency
deduplication; use `gh run rerun --failed`.

A failed-job rerun reuses the outputs of jobs that succeeded in the earlier attempt. When a
producer job stamps its output with run-attempt identity, such as `run_id` plus `run_attempt`,
and a consumer job validates that identity before it starts its work, the rerun fails
deterministically: the producer output still names the old attempt while the consumer runs under
the new one. The signature is a previously green job that aborts seconds into the rerun with a
configuration or identity error that the original attempt did not show. Further `--failed`
reruns keep failing by construction. Use a full rerun (`gh run rerun <RUN_ID>`) so the producer
regenerates its output for the current attempt and the consumer identity check aligns again.

For `BLOCKED` with no failure, compare required and posted contexts at the exact PR head.
Inspect both legacy branch protection and the rulesets that apply to the target branch:

```bash
gh api repos/<org>/<repo>/branches/main/protection/required_status_checks \
  --jq '.contexts[]'
gh api repos/<org>/<repo>/rules/branches/main \
  --jq '.[] | select(.type == "required_status_checks") | .parameters.required_status_checks[].context'
gh pr view <PR> --repo <org>/<repo> --json statusCheckRollup \
  --jq '.statusCheckRollup[] | (.name // .context)'
```

A legacy protection response of `Branch not protected` does not prove that no ruleset applies.
An authorization error or unavailable response is not an empty required-check list.
Check the expected integration identity as well as the context name when the rule binds both.

Distinguish an absent workflow run from a failed, cancelled, queued, or skipped job in an existing run.
An aggregate cannot report when its parent workflow never starts.
Inspect the workflow at the event revision, its event and path filters, and the PR event history.
Consider event-time merge conflicts, workflow admission, and credential-trigger restrictions as hypotheses, not established causes.
Current mergeability does not prove that the PR had no conflict when the event occurred.
Successful push or `pull_request_target` runs do not prove that a `pull_request` workflow started.
If the evidence cannot identify the cause, report that limit instead of declaring a lost event.

A confirmation bundle can convert the merge-conflict hypothesis into an established cause: the
per-head `gh api repos/<org>/<repo>/actions/runs?head_sha=<SHA>` list is empty while other heads
carry runs; `gh pr view <PR> --json mergeable,mergeStateStatus` reports the conflict state at
the same head; `git merge-tree --write-tree <base> <head>` reproduces the conflict and names the
files; and a conflict-resolving push that preserves the PR delta is immediately followed by the
complete run wave for the new head. GitHub does not start `pull_request` workflows while a pull
request has merge conflicts, so no run exists to rerun or dispatch for the old head. For this
confirmed case the supported, authorized trigger is the conflict-resolving push itself: resolve
the isolated files, repush on the updated base, and then verify with `gh pr checks <PR>` that the
new head carries the full wave. Carry prior review evidence forward by tree identity: an
unchanged tree keeps its verdicts, and a tree changed by conflict resolution gets fresh review of
that delta.

Select a supported, authorized trigger for an absent run and verify the resulting source identity.
Do not rerun an older head as evidence for a newer head. Do not manufacture a passing status.
Do not change to privileged PR execution merely to force a trigger.
For a confirmed path-filter problem, preserve the required context while limiting the applicable work.
Do not assume that an administrator merge option overrides a ruleset. Verify actor authority and report a rejected attempt accurately.

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
| Legacy protection only | Treated an absent legacy protection rule as no required checks | A ruleset still required the missing aggregate | Inspect both rule sources before selecting recovery |
| Host-path core capture | Put the runner CWD in `core_pattern` | The path did not exist in the crashing container namespace | Use the container-visible bind path |
| Bare gdb and `hook-stop` | Ran host gdb and dumped on every stop | Environment paths were absent and exit-stop is not a live signal stop | Use `pixi run -- gdb` plus `SignalEvent` |
| Exit 137 as OOM proof | Classified every 137 as OOM | A JIT signal handler produced the same code | Combine exit code with log signatures |
| Per-PR suppression | Patched identical failures on each branch | The defective file came from main | Fix main once; rebase only an active task that needs the fix or a PR with a reported conflict |
| Blocking futures | Used `as_completed()` and unbounded waits | Shutdown could not be observed while nothing completed | Poll at two-second intervals |
| Always-on debug capture | Defaulted gdb collection to true | Every PR paid the diagnostic cost | Use an opt-in dispatch input |
| Failed-job rerun on an attempt-bound producer | Re-ran only the failed shard after a matrix flake | The producer output pinned the earlier attempt, so rerun consumers rejected the identity and exited at startup | Detect attempt-bound producer/consumer validation; switch to a full rerun |
| Re-trigger an absent run | Looked for a run to rerun or dispatch for a head whose PR had merge conflicts | GitHub never created runs for that head, so there was nothing to rerun and a dispatch would test the wrong source | Establish the conflict with the empty per-head run list, `mergeStateStatus`, and `git merge-tree`; resolve, repush, and verify the new head's wave |
| Decorated-view match as evidence | Cited a failure line from a filtered or decorated log view as the root cause in a report and a fix dispatch | The bare job log contained zero occurrences of the quoted text; the ghost hypothesis and the dispatch built on it were wrong | Verify quoted lines in the bare authenticated log before attribution; record the view type with each quote |

## Results & Parameters

| Parameter | Recommended value or rule |
| --- | --- |
| Failing evidence | `gh run view --job=<JOB_ID> --log-failed` before diagnosis |
| Quote verification | Bare-log fetch plus an occurrence count above 0 for each quoted token |
| Recurrence | One failed-job rerun; repeated same signature is reproducible |
| Attempt-bound producer rerun | Full `gh run rerun <RUN_ID>`; repeated `--failed` reruns stay misaligned |
| Conflict-suppressed runs | Resolve conflicts, repush on the updated base, verify the new head's full wave; carry reviews by tree identity |
| Shutdown poll interval | `2.0` seconds |
| gdb signals | SIGILL, SIGABRT, SIGSEGV, SIGBUS, SIGFPE |
| Debug input | Boolean, `default: false`, dispatch-only |
| API reserve | Stop bulk logs below 500; nonessential calls below 100 |
| CPU survey | Same image/reproducer, repeated runs, model/flags/exit histogram |

## Companions

- [Case evidence and detailed verification](ci-failure-triage-and-diagnosis.notes.md)
- [Version history and superseded content](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/ci-failure-triage-and-diagnosis.history)
