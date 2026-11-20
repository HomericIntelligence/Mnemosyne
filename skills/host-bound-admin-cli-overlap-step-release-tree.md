---
name: host-bound-admin-cli-overlap-step-release-tree
description: "Run an admin CLI whose service listens on a local socket of another cluster node. Use when: (1) the CLI reports the socket is refused and the service heartbeat names a different host, (2) ssh to that host is blocked, (3) the service rejects the request with a context mismatch, (4) a mutating call returns an unconfirmed reply. Launch the CLI as an overlapping scheduler step inside the service job, use the CLI from the release tree the service runs, and never retry an unconfirmed mutation."
category: tooling
date: 2026-11-20
version: "1.0.0"
user-invocable: false
tags: [slurm, srun, overlap, admin-cli, operator, unix-socket, audit-log, mutating-request, release-tree]
---

# Host-Bound Admin CLI: Overlap Step and Release Tree

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-20 |
| **Objective** | Run a mutating admin command (reset a breaker, set a pool size) against a service that accepts requests only on a node-local socket. |
| **Outcome** | Operational. The command reached the service from another node, and each failure had a distinct cause and fix. |

## When to Use

- The CLI prints "socket refused" and a heartbeat file names the node that owns the service.
- The CLI offers a host-selection flag, but the flag only picks a socket path on the current node. It does not forward the call.
- ssh to the service node fails (for example host-key verification) and you must not change ssh trust.
- The service accepts the connection and then rejects the request with a context or version mismatch.
- A mutating call ends with "outcome not confirmed".

## Verified Workflow

1. Find the service node from the heartbeat or the diagnostic. Find the service's scheduler job on that node.
2. Run the CLI as an overlapping step inside that job: `srun --jobid=<job> --overlap --mem=0 -c1 -N1 -n1 --time=5 <cli> ...`. A short test first (`hostname`) proves the step starts and the node is right.
3. Size the step explicitly. Without `--mem=0 -c1` the step can wait without limit or fail with "Unable to create step ... already completing" while the job is still RUNNING. A wall-clock `timeout` around such a call gives exit 143 and no output. That result is not a service failure (see the queued-srun timeout lesson).
4. Take the CLI from the release tree that the running service uses. Read the service process command line on its node (`/proc/<pid>/cmdline`) to find the tree. A CLI from a development checkout can carry a different registered context and be rejected as "context does not match". A rejected request changes nothing.
5. Check target names against the service's registry before you mutate. List the registered pools or models from the release data and the service state directory. A near-miss name fails with a missing-file error, and a name with no breaker state answers "nothing was reset". Ask the owner when no registered name matches. Do not guess a nearby name.
6. If the reply says the outcome is not confirmed, do not retry. Find the request ID in the service audit log and read the `phase` and `ok` fields of every entry near that time. A `completed` handshake entry is not the action. A later `rejected` entry means the action did not run.
7. After a successful call, state the accepted value and the convergence delay. Read the live state again before you claim the final result.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Ran the CLI from the local checkout on another node. | Socket refused; the heartbeat named a different node. | The host flag selects a path only. Run on the service node. |
| Attempt 2 | `ssh` to the service node. | Host-key verification failed. | Do not alter ssh trust. Use a step in the service job. |
| Attempt 3 | `srun --overlap` with no step sizing, wrapped in `timeout`. | Hung, then "Unable to create step". | Add `--mem=0 -c1 --time`, and test with `hostname`. |
| Attempt 4 | Used the development-checkout CLI for the mutation. | Context mismatch; the audit log showed a rejected request. | Use the CLI from the release tree that the service runs. |
| Attempt 5 | Guessed a model name from a job name. | "No blocked breaker" or a missing cookbook file. | Verify names against the registry first. |

## Results & Parameters

| Item | Rule |
| ----- | ----- |
| Step form | `srun --jobid=<service job> --overlap --mem=0 -c1 -N1 -n1 --time=5 <release-tree cli> <command>` |
| CLI source | The tree named in the service process command line. |
| Unconfirmed mutation | Never retry. Read the audit log by request ID first. |
| Zero-size request | Setting a pool size to 0 is accepted for a registered name. Report it as "desired=0", not as "drained". |
