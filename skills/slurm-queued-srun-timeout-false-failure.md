---
name: slurm-queued-srun-timeout-false-failure
description: "Run a validation command on a busy Slurm partition without a false result. Use when: (1) a command is wrapped as `timeout N srun ...` and exits 143 or prints nothing, (2) srun reports 'queued and waiting for resources' and your wall-clock limit expires, (3) a job queue holds many pending jobs and you need a test result from a compute node."
category: tooling
date: 2026-11-04
version: "1.0.0"
user-invocable: false
tags: ["slurm", "srun", "sbatch", "timeout", "queue-wait", "validation"]
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
3. Write job output to a file in a job-specific directory. Do not use a shared temporary directory.
4. Run the submission in the background or poll `squeue`. Do not put a wall-clock `timeout` around the submit step.
5. Treat a result as valid only when the output file contains the payload's own pass or fail line. A killed or pending job is "not run", not a pass and not a failure.
6. If the same check also runs in CI, you can cancel the batch job after CI passes (`scancel <JOBID>`). Keep CI as the proof.

If you must use `srun`, give it no outer `timeout`. Use `srun --immediate=<SECONDS>` to fail fast when no resources are free, and accept that this means "not run".

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | `timeout 300 srun ... python check` | The job waited in the queue, so `timeout` sent SIGTERM (exit 143) before the payload started. | The outer limit includes the queue wait. |
| 2 | An inline script that only parsed YAML and printed file names | It did not load the real validator, so a success would not prove the change was valid. | A check must run the code that enforces the rule. |
| 3 | Restarting `srun` in the background after a session restart | The background process ended with the session, and the job stayed in the queue. | A job tied to a client session is lost with it. A batch job is not. |

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

## References

- [slurm-batch-job-result-verification](slurm-batch-job-result-verification.md)
- [slurm-wrap-shell-contract](slurm-wrap-shell-contract.md)
