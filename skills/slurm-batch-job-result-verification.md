---
name: slurm-batch-job-result-verification
description: "Verify a completed Slurm batch job's payload result before recording a measurement or continuing a pipeline. Use when: (1) sacct reports COMPLETED with exit code 0 for a job whose payload ran inside a wrapper script, (2) the wrapper's later statements can succeed and mask a payload failure, (3) result artifacts or a payload exit record are required before any downstream conclusion, (4) automation polls scheduler state as its only success signal."
category: tooling
date: 2026-10-25
version: "1.0.0"
user-invocable: false
tags:
  - slurm
  - batch-scheduler
  - payload-verification
  - result-artifacts
  - exit-code
  - automation
---

# Slurm Batch Job Result Verification

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-25 |
| **Objective** | Treat a scheduler terminal state as an availability signal only, and decide job success from payload-level evidence: an explicit payload exit record plus the expected result artifacts. |
| **Outcome** | Operational. Benchmark jobs whose payload aborted still showed COMPLETED with exit code 0 in sacct; only the missing payload exit record and the missing result artifacts revealed the false success. |

## When to Use

- A wrapper script (an sbatch batch script, an `srun` wrapper, or a submission harness), not the payload itself, produces the exit code that Slurm records.
- `sacct`, `squeue`, or a job API reports State COMPLETED and ExitCode 0:0, and you are about to record measurements or treat outputs as produced.
- A wrapper combines strict-mode shell options (`set -u`, `set -e`) with statements that still let the script finish successfully after the payload dies.
- Automation drives a sweep of jobs and polls only scheduler fields before consuming outputs.

## Verified Workflow

### Quick Reference

```bash
sacct -j <id> --format=JobID,State,ExitCode        # scheduler availability signal only
grep -h "SRUN_EXIT=" results/<id>*.out             # payload-level exit record (required)
ls results/<id>/single-summary.txt results/<id>/load-summary.txt   # required artifacts
# per-variant success = payload exit record 0 AND every required artifact present and parseable
```

### Suggested Approach

1. Treat scheduler State/ExitCode as "the batch script reached its last statement", never as "the payload succeeded". Slurm records the wrapper's exit code.
2. Require an explicit payload exit record from the wrapper's final statements (for example an `SRUN_EXIT=<n>` line emitted after a hard-exit trap). No exit record means no success claim.
3. Enumerate the required result artifacts per job variant before the sweep, then check each artifact exists, is nonempty, and parses.
4. Make the per-variant pass condition: payload exit record 0 AND all required artifacts valid. Fail a variant on either check even when the scheduler shows success.
5. When the check catches a false success, repair the wrapper (guarded expansions such as `${VAR:-}`, strict-mode awareness, and a final status echo that cannot mask the payload), resubmit, and re-apply the same artifact checks.
6. For jobs owned by another account, apply the same artifact-gating rule under the readable-evidence limits of the foreign-artifact skill.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust sacct State/ExitCode as the success signal | Classified sweep jobs with COMPLETED 0:0 as measured runs | A strict-mode variable-expansion abort killed the payload, but the wrapper's final statements still completed, so Slurm recorded success for the whole variant group | The wrapper exit path, not the payload, produces the scheduler exit code; verify payload exit records and artifacts |
| Inspect only job stdout for failure | Read job output files for crash text | No crash text appeared, because strict-mode abort messages did not reach the job log that was checked | Absence of crash text is not presence of results; require the artifacts |

## Results & Parameters

### Configuration

```yaml
scheduler_report:
  role: availability-signal-only        # State COMPLETED / ExitCode 0:0
payload_success_requires:
  - explicit payload exit record (for example SRUN_EXIT=0 from the final wrapper statement)
  - every required result artifact present, nonempty, and parseable
mask_patterns:
  - wrapper final statements that exit 0 after a payload abort (echoes, cleanup)
  - strict-mode aborts during payload expansion while the wrapper continues
sweep_pass_condition: payload-exit-record-0 AND all-required-artifacts-valid
```

### Expected Output

- Each job variant is classified from payload evidence: success requires a payload exit record of 0 plus valid artifacts.
- False successes are re-classified before any measurement is recorded, compared, or reported.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A private compute-cluster benchmark sweep | One wrapper-harness variant set across two submissions | Generalized identifiers; details in [notes.md](../skills/slurm-batch-job-result-verification.notes.md) |

## References

- [Slurm sacct documentation](https://slurm.schedmd.com/sacct.html)
- [slurm-wrap-shell-contract.md](slurm-wrap-shell-contract.md)
- [slurm-foreign-job-artifact-gate.md](slurm-foreign-job-artifact-gate.md)
