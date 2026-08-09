---
name: automation-event-log-retention-concurrency-safe-bounded-lifecycle
description: "Design bounded lifecycle management for local diagnostic event logs without turning them into restart state. Use when: (1) timestamp-and-PID JSONL logs accumulate without bounds, (2) concurrent pipeline runs must never prune one another's active logs, (3) age and count limits need independent operator disable switches, (4) dry-run cleanup must reflect lock contention, or (5) cleanup failures must be observable but must not change the pipeline result."
category: architecture
date: 2026-08-06
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - automation
  - diagnostic-logs
  - event-logs
  - jsonl
  - retention
  - age-limit
  - count-limit
  - file-lock
  - advisory-lock
  - concurrency
  - dry-run
  - best-effort-cleanup
---

# Concurrency-Safe Bounded Lifecycle for Diagnostic Event Logs

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-06 |
| **Objective** | Bound local diagnostic JSONL growth by age and count while protecting logs written by concurrent pipeline runs. |
| **Outcome** | Proposed architecture and behavior-first test matrix captured; implementation and CI validation are pending. |
| **Verification** | unverified — derived from a reviewed implementation design, not an executed change |

The load-bearing boundary is that event logs remain best-effort diagnostics. They are not a
journal, checkpoint, replay source, or restart authority. The outer application wrapper owns
log creation, active-file protection, and cleanup; the coordinator or worker that emits records
only appends them best-effort.

## When to Use

- A long-running automation process creates one timestamped JSONL event log per invocation and
  the directory grows without a lifecycle policy.
- Multiple processes may run concurrently, so a cleanup pass must distinguish inactive logs from
  files still being written without relying on PID liveness checks.
- Operators need conservative defaults plus independent rollback switches for age and count
  retention.
- A dry run must preview only files that a real cleanup could lock and remove.
- Diagnostic cleanup must warn on failures but must never change routing, checkpoint authority,
  or the application's exit code.
- Filenames are a narrow application-owned namespace, while the surrounding directory may
  contain unrelated files, malformed names, directories, or symlinks.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until
> focused tests, the full relevant test suite, and CI confirm the behavior.
>
> **Validator compatibility:** Mnemosyne's current validator requires the literal
> `## Verified Workflow` section even for `unverified` skills. The canonical proposed steps are
> therefore repeated under that heading below; they remain unverified.

## Verified Workflow

> **Warning:** This is a proposed workflow, not a verified one. Implementation and CI validation
> are pending.

### Quick Reference

```python
DEFAULT_RETENTION_DAYS = 30
DEFAULT_RETENTION_COUNT = 100

with event_log_lifecycle(
    event_log_path,
    retention_days=DEFAULT_RETENTION_DAYS,
    retention_count=DEFAULT_RETENTION_COUNT,
    dry_run=dry_run,
):
    return run_pipeline(config)
```

```text
candidate name: pipeline-events-YYYYMMDDTHHMMSSZ-<positive-pid>.jsonl
age policy:     delete recognized inactive logs strictly older than the cutoff
count policy:   after age cleanup, remove oldest inactive logs until total <= cap
zero value:     disable only that limit
failure policy: warn, preserve files, continue the pipeline unchanged
```

### Detailed Steps

1. **Keep lifecycle ownership outside the record writer.** Let the composition root or CLI
   wrapper choose the per-run path and wrap the complete pipeline dispatch in one lifecycle
   context. Keep the coordinator's event-record method append-only and best-effort. This makes
   retention a local resource concern rather than a new persistence authority.

2. **Expose two validated, independent limits.** Use a non-negative integer parser for an age
   limit and a count limit. Conservative starting defaults are 30 days and 100 recognized logs.
   Define `0` as disabling only the corresponding limit; event logging itself stays enabled.

3. **Recognize a deliberately narrow filename language.** Use a full-match regular expression
   such as:

   ```python
   re.compile(
       r"pipeline-events-(?P<timestamp>\d{8}T\d{6}Z)-"
       r"(?P<pid>[1-9]\d*)\.jsonl"
   )
   ```

   Parse the timestamp as UTC and reject impossible calendar values. Admit only regular,
   non-symlink files. Ignore malformed names, zero or signed PIDs, directories, symlinks, and
   unrelated files. Do not parse JSON: a partially written, correctly named inactive log is
   still an application-owned log.

4. **Hold the current file's activity lock for the entire run.** Acquire the existing
   cross-process file lock on the current event-log path with non-blocking, exclusive-required
   semantics before cleanup starts, and release it only after pipeline dispatch exits. If the
   platform cannot provide a real exclusive lock, or acquisition otherwise fails, warn and skip
   all cleanup while still running the pipeline.

5. **Serialize cleanup passes separately.** Use one persistent directory-scoped sentinel lock so
   concurrent cleaners cannot make decisions from the same stale inventory. Acquire it
   non-blockingly; contention or lock failure means this cleanup pass is skipped with a warning.
   The sentinel name must not match the event-log filename grammar.

6. **Lock each deletion candidate non-blockingly.** A candidate lock conflict means the file is
   active, so preserve it and continue. Require real exclusive locking for candidate deletion;
   never degrade a non-idempotent unlink operation to an unlocked path. Re-check that the path is
   still a recognized regular non-symlink after locking before previewing or unlinking it.

7. **Apply age before count.** Sort recognized logs oldest-first by the validated UTC timestamp
   in the name. First attempt to remove inactive logs strictly older than `now - retention_days`;
   a log exactly at the cutoff remains. Then, from the remaining recognized inventory, attempt
   oldest-first inactive removals until the total recognized count is at or below the configured
   cap. Count active logs in the total, but never remove them. Concurrent runs may therefore keep
   the directory temporarily above the cap.

8. **Make dry-run use the real eligibility checks.** Scan, parse, stat, and acquire cleanup and
   candidate locks just as a real cleanup would. Replace `unlink()` with an informational
   `[dry-run] would remove <path>` message. This prevents a preview from claiming that an active
   or malformed file would be deleted.

9. **Contain every cleanup failure.** Directory iteration, lock acquisition, metadata reads, and
   per-file unlink can all fail. Emit warnings with enough path context to diagnose the failure,
   continue with other candidates where safe, and preserve the pipeline's original return value
   or exception. Cleanup is never allowed to become routing authority.

10. **Drive the implementation with deterministic filesystem tests.** Freeze `now`, create
    timestamped files in a temporary directory, and cover exact age cutoff, oldest-first count,
    combined policies, malformed and unrelated entries, symlinks, active-lock contention,
    temporary cap excess, dry-run previews, per-file failure continuation, directory/current-lock
    failure, and both limits set to zero. Patch the lifecycle at CLI-dispatch unit seams so parser
    and wiring tests do not touch repository state.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Delete by broad glob or suffix | Considered treating every `pipeline-events-*.jsonl` or every `.jsonl` sibling as owned | Broad patterns admit malformed, unrelated, directory, or symlink entries and expand the destructive scope | Use full-match naming, UTC validation, positive PID validation, and regular non-symlink checks |
| Treat PID liveness as active-log authority | Considered using the PID embedded in the filename to decide whether a writer still exists | PIDs are reusable, process visibility can be restricted, and liveness does not prove ownership of a particular open file | Make a held advisory lock the cooperative activity signal; keep PID only as namespace data |
| Run cleanup inside the coordinator's append method | Considered coupling pruning to record emission | It mixes lifecycle policy with best-effort append behavior, repeats cleanup work, and risks turning diagnostics into coordinator state | Keep creation/protection/cleanup in the outer wrapper and appends in the coordinator |
| Delete candidates without requiring exclusive locking | Considered allowing the file-lock helper's portable no-op fallback | A no-op is acceptable for idempotent coordination but unsafe for unlinking a file another process may be writing | Require a real exclusive lock; unavailable locking means preserve files and warn |
| Enforce count without including active logs | Considered counting only currently deletable candidates | The reported cap would no longer describe the recognized directory inventory and could hide sustained concurrent growth | Count all recognized logs, skip active ones, and explicitly permit temporary cap excess |
| Preview from names alone | Considered logging all age/count matches during dry-run without candidate locking | The preview would claim active logs are removable and would not exercise real scan/stat/lock failure paths | Dry-run should follow the same eligibility and locking path, stopping immediately before unlink |
| Let cleanup exceptions escape | Considered treating retention failure like a pipeline failure | These logs are diagnostic only; changing routing or exit status would accidentally promote cleanup into operational authority | Warn, preserve data, continue safely, and leave the pipeline result untouched |

These are rejected design alternatives from the planning session, not failures observed in an
executed implementation.

## Results & Parameters

### Proposed Configuration

| Parameter | Proposed default | Semantics |
| --------- | ---------------- | --------- |
| `retention_days` | `30` | Delete recognized inactive logs strictly older than the UTC cutoff; `0` disables age cleanup |
| `retention_count` | `100` | After age cleanup, attempt oldest-first inactive deletions until total recognized logs are within the cap; `0` disables the cap |
| `dry_run` | inherited from the application | Report eligible removals without unlinking |
| Current-log lock | non-blocking, exclusive required | Held across cleanup and the complete pipeline run |
| Cleanup lock | non-blocking, exclusive required | Serializes cleaners; contention skips this pass |
| Candidate lock | non-blocking, exclusive required | Contention classifies the candidate as active and preserves it |

### Invariants

```text
diagnostic event log != journal != checkpoint != restart authority
recognized candidate = exact name + valid UTC timestamp + positive PID + regular non-symlink
deletion eligibility = recognized + inactive exclusive lock + selected by age/count policy
cleanup failure = warning + preservation + unchanged pipeline outcome
```

### Proposed Verification Matrix

| Behavior | Evidence to require |
| -------- | ------------------- |
| Age cutoff | Older file removed; exact-cutoff file retained |
| Count cap | Oldest inactive files removed first |
| Combined limits | Age removals occur before count calculation/removal |
| Namespace safety | Malformed names, invalid timestamps/PIDs, unrelated entries, directories, and symlinks remain |
| Active protection | A log locked by another lifecycle is not previewed or unlinked |
| Temporary excess | Active logs can keep the recognized total above the cap without unsafe deletion |
| Dry-run | `[dry-run] would remove ...` is logged and every file remains |
| Failure isolation | Scan, lock, stat, and unlink failures warn without changing pipeline completion |
| Disable switches | Both limits at zero produce no retention deletion |

No runtime result is claimed here. The expected outcome is bounded inactive-log growth under
cooperating processes while active files and unrelated directory contents remain untouched.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | Proposed lifecycle for default pipeline JSONL event logs, 2026-08-06 | [Planning notes](./automation-event-log-retention-concurrency-safe-bounded-lifecycle.notes.md); implementation, local tests, and CI pending |

## Related Skills

- [Automation Pipeline Observability and Dry-Run](automation-pipeline-observability-and-dryrun.md)
- [Git Worktree Parallel Execution Lifecycle](git-worktree-parallel-execution-lifecycle.md)
- [Automation Log Path Helper Planning Risks](automation-log-path-helper-planning-risks.md)
