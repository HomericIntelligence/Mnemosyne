---
name: agent-shell-inherits-scheduler-allocation
license: BSD-3-Clause
description: "Stop an automated agent shell from launching job steps inside the allocation that the shell itself runs in. Use when: (1) an agent session was started from an interactive or batch allocation, (2) a plain srun or sbatch from the agent runs on the wrong nodes or is charged to the wrong job, (3) a rule says work must not run on a given allocation, or (4) a delegated agent or a background monitor runs Slurm commands."
category: tooling
date: 2026-11-28
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - slurm
  - srun
  - sbatch
  - environment-inheritance
  - agent-session
  - allocation
  - scheduler-metadata
---

# Agent Shell Inherits Its Scheduler Allocation

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-28 |
| **Objective** | Make each Slurm step that an automated agent starts run in the allocation that the task names, and not in the allocation that hosts the agent shell. |
| **Outcome** | Successful. After the scheduler variables were cleared, steps and jobs went to the intended nodes. Earlier steps that ran with the inherited variables had run inside the host allocation. |
| **Verification** | verified-local on a shared cluster. The agent shell, its delegated agents, and its monitors all ran inside one user allocation. |

## When to Use

- The agent session starts from an interactive allocation (a terminal on a compute node) or from a batch job, so the shell has `SLURM_JOB_ID` set.
- A plain `srun` from the agent starts a step inside the host allocation. The step takes that allocation's CPUs and memory, and the accounting shows the host job.
- A rule or an owner instruction says that some work must not run on a named allocation, and the agent shell is in that allocation.
- A delegated agent or a background monitor starts Slurm commands. Each child process inherits the same variables.
- A foreground `srun` fails with step-creation errors (memory, CPU binding, or "requested node configuration is not available") that do not occur from a login node.

## Verified Workflow

### Quick Reference

Check the shell once at session start, and tell every delegated agent the result:

```bash
# Is this shell inside an allocation?
env | grep -E '^SLURM_(JOB_ID|JOBID|STEP_ID|NODELIST)=' || echo "no allocation inherited"

# Launch for a different job: clear the inherited scheduler variables first.
# Keep SLURM_CONF if the site needs it to find the controller.
env -u SLURM_JOB_ID -u SLURM_JOBID -u SLURM_STEP_ID -u SLURM_NODELIST \
    -u SLURM_NNODES -u SLURM_NTASKS -u SLURM_CPUS_ON_NODE \
    srun --account=<acct> --partition=<part> ... <command>

# Intentional step in a job you name (an admin command on a host-bound job):
env -u SLURM_JOB_ID -u SLURM_JOBID srun --jobid=<named-job> --overlap ... <command>
```

### Suggested Approach

1. At session start, detect the inherited allocation. If `SLURM_JOB_ID` is set, record the job ID and its owner as the host allocation. State in the first message of every delegated agent that the shell sits in it.
2. Treat every `srun`, `sbatch`, and `salloc` as in-allocation unless the command clears the variables or names a job with `--jobid`. A new `srun` with no `--jobid` joins the host allocation when the variables remain.
3. Clear the variables in the command itself (`env -u ...`). Do not export the change for the whole shell. A one-time change in a long shell is easy to lose, and other tools in the shell can need the variables.
4. For a step that must run in a named job, give `--jobid` and clear the other `SLURM_*` variables, so the step does not take the host job's step ID or node list.
5. Verify where a launch landed. Run `squeue -j <job> -s` or `scontrol show job <job>` after the launch. Do not trust the exit code alone.
6. If an earlier step ran with the inherited variables, report it with the job ID and time window. Do not hide it. The owner of the host allocation can then judge the effect.
7. If you cannot launch outside the host allocation (no login node, no queue access), stop and report the exact blocked command. Do not use the host allocation as a fallback for work it must not carry.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Plain srun from the agent shell | Ran `srun` for a short CPU task and trusted the node name in the output. | The step ran inside the host allocation because `SLURM_JOB_ID` was inherited. | Check `env` first. A step that works is not proof of the intended placement. |
| Rely on a prose rule | Told delegated agents "never launch on the host allocation" and did not name the variable. | Two short steps ran there anyway, because the agents had no way to see the cause. | Give each child the cause and the exact `env -u` form, not only the rule. |
| Export the unset once | Unset the variables in one shell command and assumed the next command was clean. | Each tool call can start with a fresh shell that carries the inherited variables again. | Clear them inside every launch command. |

## Results & Parameters

### Configuration

```text
Variables to clear for a launch that is not part of the host job:
  SLURM_JOB_ID  SLURM_JOBID  SLURM_STEP_ID  SLURM_NODELIST
  SLURM_NNODES  SLURM_NTASKS SLURM_CPUS_ON_NODE
Keep: SLURM_CONF (or the site's controller pointer).
```

### Expected Output

- `env | grep SLURM_JOB_ID` prints a job ID in an agent shell that runs inside an allocation, and nothing in a clean shell.
- After a clean launch, `squeue -s -j <new-job>` shows the step under the new job, and the host job shows no new step.
- A report of any earlier in-allocation step names the job ID and time window.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Shared GPU cluster, agent-run bring-up | An agent session and its delegated agents ran inside one user allocation; an owner rule forbade launches there. | Two short CPU steps ran in the host allocation before the variables were cleared. They were disclosed to the owner. |

## References

- [Step-lifetime server ownership](slurm-step-lifetime-server-ownership.md): scrubs inherited scheduler context for a server step; this entry covers the agent-session trigger.
- [Running-job content attribution](slurm-job-content-attribution.md)
