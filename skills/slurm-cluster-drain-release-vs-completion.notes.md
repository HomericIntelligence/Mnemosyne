# Notes: Slurm cluster drain release vs completion

## Source

Incident review of a drain wave on a shared, multi-tenant GPU Slurm cluster. The
details are generalized. No organization, user, host, job, or product
identifier is kept.

## Observed sequence (UTC)

| Time | Observation |
| --- | --- |
| 04:45:14 | 88 jobs ended in one second across 8 users and about 40 nodes. Most were long-running batch jobs of several job families. |
| 04:45 to 04:56 | Three job-end bursts: 90, 76, and 111 ends. The third burst was mostly `PREEMPTED`. |
| 04:47 to 04:49 | Nodes drained with `Kill task failed`, `Epilog: Failed to kill user process`, and a full slurmd spool directory. |
| 04:55 | The partition showed 236 nodes in `PLANNED`, 1 `idle`, and 497 `allocated`. |
| 04:58 | The planned count fell to about 1, and the idle count rose to 241. |
| 05:00 | Allocation rose above 500 and then above 700 for a short time as the backlog started. |

## Release versus completion

- Nodes with a new boot time on the incident date: 15. The planned count was 236.
- One rebooted node booted at 04:53 and its slurmd started at 04:54. It was
  idle again at 04:55.
- At least one node that had been `PLANNED` kept its earlier boot time and was
  `ALLOCATED` again. It was released without a reboot.
- Conclusion: the drain was released. The reboot plan was not completed.

## Service recovery

- The affected serving pool fell from 11 live replicas to 1.
- The queued replicas showed a start estimate about 37 hours away, then `N/A`,
  then start times within about 1 minute of the release.
- One queued replica stayed blocked by a group node cap in its quality-of-service
  entry, not by node capacity.
- A gateway status call stayed `UP` during the wave because one replica kept
  serving. The pool met a floor of 1 by luck, not by design.

## Nodes left out

- About 80 nodes stayed `draining` or `drained` with a kill-task or epilog
  failure after the wave. These nodes need an operator resume or reboot.
- A node-level health checker with a periodic interval caused some nodes to
  reboot after a failed process kill. Those reboots returned the nodes within
  about 2 minutes.

## Commands used

```bash
sinfo -p <partition> -o "%.10T %.6D"
sinfo -t planned -h -o "%D"
scontrol show node <node> | grep -E "State=|BootTime|SlurmdStartTime"
scontrol show node -o | grep -c "BootTime=$(date +%F)"
sacct -S <start> -E <end> -o JobID,State,End -X -a
sacct -S <start> -E <end> -o End -X -a | grep -oE '^[0-9-]+T[0-9]{2}:[0-9]{2}' | sort | uniq -c
squeue -u <service-account> --start -o "%i %j %S %R"
```

## Limits

- The Slurm controller log and the administrative action log were not readable
  from the service account. The initiator of the plan and of the release is not
  observable from accounting alone.
- A planned node has no reason field in `scontrol show node`. The boot-time
  comparison is the strongest available release check.
- One partition listed the same nodes under several partitions, so a per-node
  count from `sinfo -N` multiplies the node count. Use one partition, or the
  node count from `scontrol show node -o`.

## Related evidence

The paired lesson, `serving-pool-replica-outage-diagnosis`, classifies one
pool's replica loss. This note adds the cluster-wide wave and the
released-versus-completed check. The paired lesson's recovery rule still
applies: declare recovery on registration, not on submission.