---
name: scheduler-job-inherits-submitter-environment
license: BSD-3-Clause
description: "Find why a patch has no effect on a scheduler job, or why a job dials a tunnel that exists only on the submitting host. Use when: (1) a patched release tree changes nothing in a running batch job, (2) a job logs a connection error to a loopback address that works from the login node, (3) the job imports different code than the release it names, (4) you are about to patch a service that a scheduler job started."
category: debugging
date: 2026-10-29
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [slurm, sbatch, environment, pythonpath, loopback, tunnel, import-path, patch-misses, diagnosis]
---

# A Scheduler Job Inherits the Submitter's Environment

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Make a fix reach the code and the network route that a batch job really uses. |
| **Outcome** | Operational. A gateway job, started through a service that ran on a login node, inherited that service's whole environment. It carried a source-checkout import path and a loopback database dial address for a tunnel that exists only on the login node. A patch of the installed release tree had no effect, and every database call in the job failed with a loopback connection error. Patching the code that the job really imported, and not forwarding the two variables, fixed it. |

`sbatch` exports the submitter's environment to the job by default. When a long-lived service on a
login node submits the job, the job gets that service's `PYTHONPATH`, tunnel variables and
connection settings. Two effects follow: the job can import a source checkout instead of the
release tree, and it can dial an address that is valid only on the submitting host.

## When to Use

- A patch of the installed release tree does not change the job's behavior.
- A job logs a refused connection to `127.0.0.1` or `::1` for a service that is reachable from the
  login node through a tunnel.
- After you drop a tunnel variable, the error changes from `refused` to `timeout`.

## Verified Workflow

### Quick Reference

```text
1. Print the import path and the release id at job start (names and paths, not secrets).
2. Compare the NAMES of the submitter's environment variables with the job's.
3. Loopback address in a connect error => a tunnel variable crossed over.
4. Refused turns into timeout after you drop it => the node has no route at all.
5. Fix at submission: allow-list the environment, or `unset VAR ...` on an existing line of the template.
```

### Suggested Approach

1. Before you patch, find which tree the job imports. Log the module path (`comet.__file__`-style)
   and the release id once at start. If the path is a source checkout, the release tree is not in play.
2. List the variable names that the submitting service holds and that the job inherits
   (`PYTHONPATH`, tunnel dial hosts, connection strings). Do not print values.
3. A loopback address in a connect error from a compute node means a tunnel setting crossed over.
   Drop it for that call and read the new error. A timeout instead of a refusal proves that the
   node has no route to the resource. Then the work belongs on the host that has the route, not in
   the job.
4. Fix it where the job is built: pass an explicit allow-list of variables, or add the variables to
   the template's existing `unset` line. When a test pins template line numbers, edit an existing
   line and add no new one.
5. After a patch, prove which tree runs: the job must log the release path, and the failure must be
   gone in the job's own log, not only in a manual run from the login node.
6. If a reload restarts only some processes of the job, check which of them load the changed file
   before you rely on the reload.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Patch the installed tree | Dropped the tunnel variable in the release tree and reloaded | The job imported the source checkout from the inherited `PYTHONPATH`; the log still showed the old behavior | Find the imported tree first |
| Drop the tunnel variable and expect success | Removed the loopback dial host in the job | The error became a timeout: the node has no route at all | A changed error class is evidence; move the work to the host with the route |
| Test from the login node | Ran the routine by hand with the tunnel | It worked there, which hid the job's real environment | Verify in the job's own log |

## Results & Parameters

### Configuration

```yaml
job_environment: allow-list, or unset PYTHONPATH and tunnel variables in the template
start_up_log: import path, release id, and "route: ok|unreachable (<class>)"
verify: the job log shows the release path and no loopback error
```

### Expected Output

The job logs the release tree as its import path, and its connection errors, if any, name the
real host and not a loopback address.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A scheduler-managed model-serving deployment | Gateway job, 2026-10 | The inherited environment hid a patch and caused every key request to be lost. |

## References

- [bluegreen-reload-candidate-worker-replay](bluegreen-reload-candidate-worker-replay.md) — what a reload restarts
- [git-worktree-sys-path-precedence-issue](git-worktree-sys-path-precedence-issue.md) — import path precedence in worktrees
