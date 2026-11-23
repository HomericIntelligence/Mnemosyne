---
name: slurm-queued-srun-timeout-false-failure
description: "Run a validation command on a busy Slurm partition without a false result. Use when: (1) a command is wrapped as `timeout N srun ...` and exits 143 or prints nothing, (2) srun reports 'queued and waiting for resources' and your wall-clock limit expires, (3) a job queue holds many pending jobs and you need a test result from a compute node, (4) the estimated start of your pending job is hours or days away and a review, merge, or hand-off waits for the test result."
category: tooling
date: 2026-11-04
version: "1.2.0"
user-invocable: false
tags: ["slurm", "srun", "sbatch", "timeout", "queue-wait", "validation", "ci-gate", "unverified-results"]
---

# Slurm Queued srun Timeout False Failure

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-04 |
| **Objective** | Get a real validation result from a busy Slurm partition. |
| **Outcome** | Operational. A batch submission with an output file replaced the timed `srun` call. |

## When to Use

- A command has the form `timeout N srun ...` and exits with code 143 (SIGTERM).
- `srun` prints "queued and waiting for resources" and no payload output.
- The partition has many pending jobs, so the queue wait can be longer than your limit.
- An agent or script ran a check and the result looks like a pass, but the payload never started.
- A batch job shows `COMPLETED` but its output file is missing or empty on the submit host.
- The estimated start of a pending job (`squeue --start`) is hours or days away, and a review, a merge, or a hand-off waits for that result.

## Verified Workflow

### Quick Reference

The `timeout` limit counts the queue wait, not only the run time. Submit with `sbatch` and read the output file:

```bash
sbatch --parsable -p <PARTITION> -A <ACCOUNT> --qos=<QOS> -t <RUN_MINUTES> \
  -o <OUT_DIR>/check.out <OUT_DIR>/check.sh
squeue -h -j <JOBID> -o "%T"      # PENDING, RUNNING, or empty when done
```

### Suggested Approach

1. Check the queue first: `squeue -h -p <PARTITION> -t PD | wc -l`. A long list means a long wait.
2. Put the payload in a script. Set the Slurm time limit (`-t`) for the run time only.
3. Write job output to a file in a job-specific directory that the submit host can read. Do not use a shared temporary directory. Do not leave the output path or a redirect inside the script under a node-local `/tmp`: the job then completes, the submit host sees no file, and a resubmission costs a second queue wait. Check the `-o` path and any `TMPDIR` or log redirect on shared storage before the first submit.
4. Run the submission in the background or poll `squeue`. Do not put a wall-clock `timeout` around the submit step.
5. Treat a result as valid only when the output file contains the payload's own pass or fail line. A killed or pending job is "not run", not a pass and not a failure.
6. If the same check also runs in CI, you can cancel the batch job after CI passes (`scancel <JOBID>`). Keep CI as the proof.

If you must use `srun`, give it no outer `timeout`. Use `srun --immediate=<SECONDS>` to fail fast when no resources are free, and accept that this means "not run".

### When the wait is hours or days

A batch submission fixes the false result but not the delay. When `squeue --start` shows a start time far beyond the useful window, change the evidence source instead of waiting:

1. Submit at most one short job for each question, with a small `-t`, early, and only once. Many agents that each queue a job make a long list of pending jobs that all start late and run for nothing.
2. Cancel your own pending jobs (`scancel <JOBID>`) as soon as you decide not to wait. Do not leave them to start days later. Cancel only job IDs that you submitted. Leave other users' jobs and the jobs of other agents alone.
3. Continue the work that does not need the result: read the diff, check the contract by reading the code, run linters and import checks on the login or build host if the site policy allows it.
4. Use the required CI as the test gate. Start it by the repository's own trigger (for example the label that CI waits for), and gate the merge on it. Bind the merge to the exact head that was reviewed, so a later push cannot merge on an old result.
5. Report each local test claim by its true state: `not run`, `author-reported, unconfirmed`, or `run by me, with the command and the result`. Do not copy a number from a hand-off report into a verdict as if you had observed it. A review based on reading is a valid GO only if its text says that it did not run the tests and names CI as the gate.
6. If CI fails after the merge is armed, treat it as new evidence and diagnose that failure. Do not merge around it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | `timeout 300 srun ... python check` | The job waited in the queue, so `timeout` sent SIGTERM (exit 143) before the payload started. | The outer limit includes the queue wait. |
| 2 | An inline script that only parsed YAML and printed file names | It did not load the real validator, so a success would not prove the change was valid. | A check must run the code that enforces the rule. |
| 3 | Restarting `srun` in the background after a session restart | The background process ended with the session, and the job stayed in the queue. | A job tied to a client session is lost with it. A batch job is not. |
| 4 | Each reviewer and each writer queued a test job and waited for it | The estimated starts were days away. Reviews stalled, and the jobs would have started later and run for nothing. | Decide early not to wait, cancel your own pending jobs, and move the proof to the required CI. |
| 5 | Wrote "N tests passed" in a review from a hand-off report | The writer's own run had also never started. The number had no observer. | State the true source of each test claim. |
| 6 | Several writers each submitted a test job with its output under a node-local `/tmp` | The jobs completed, but the submit host had no output file. Each writer submitted a second job and waited again. | A completed job with no readable output is an output-path error, not a test result. Fix the path on shared storage, then resubmit once. |

## Results & Parameters

### Configuration

```bash
#!/bin/bash
#SBATCH -p <PARTITION>
#SBATCH -A <ACCOUNT>
#SBATCH --qos=<QOS>
#SBATCH -t 30
#SBATCH -o <OUT_DIR>/check.out
umask 022
cd <WORKTREE>
<test command>
```

### Expected Output

- `sbatch` prints a job ID at once, whatever the queue length.
- The output file has the payload result when the job runs.
- `squeue` shows PENDING until the job starts.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Inference-service repository | Config change validated while the CPU partition had about 70 pending jobs | Two timed `srun` attempts never ran. The batch submission waited in the queue, and CI gave the passing result first. |
| Control-plane repository | Many review and writer agents ran in one session while the CPU partition had about 90 pending jobs | Pending jobs showed estimated starts of days. The coordinator cancelled its own jobs, reviewers read the code and reported "tests not run", and merges waited on the required CI at the reviewed head. |

## References

- [slurm-batch-job-result-verification](slurm-batch-job-result-verification.md)
- [slurm-wrap-shell-contract](slurm-wrap-shell-contract.md)
