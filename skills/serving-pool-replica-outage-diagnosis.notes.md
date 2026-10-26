# Notes: Serving-Pool Simultaneous Replica Outage Diagnosis

Privacy-safe supporting evidence for `skills/serving-pool-replica-outage-diagnosis.md`.
All coordinates are generalized. No project names, model names, node names, job
identifiers, or internal paths are recorded here.

## Source incident

A production GPU model-serving fleet runs each model as a pool of engine
replicas. Each replica is a multi-node scheduler allocation. A two-tier
placement contract applies: the protected replica floor runs on a
high-priority partition and QoS owned by the serving account; surplus,
demand-driven replicas run on a preemptible low-priority partition and QoS
owned by a different account.

## Timeline shape (whole-pool loss)

- T0: replica A of the affected pool failed after three days of uptime.
- T0+2m: replica B failed after three days of uptime. The pool reported zero
  of two replicas ready.
- Both allocations showed state FAILED with a nonzero exit code.
- Each replica's engine log ended with the identical unhandled application
  exception, raised from the engine's multimodal prefill path when a request
  carried aggregated vision-encoder inputs. The second replica's log showed
  the exception more than once, which is consistent with the same request
  class being retried against the surviving capacity after the first crash.
- The scheduler did not report NODE_FAIL for either allocation. Replacement
  jobs later started on nodes of the same hardware class without incident.

## Recovery timeline shape

- T0+2m: a replacement job was submitted to the preemptible tier. It started
  almost immediately on the nodes freed by replica A and was preempted seconds
  later.
- T0+22m and T0+30m: two more preemptible-tier replacement jobs started and
  were preempted within seconds to minutes of their starts.
- The three jobs were requeued by the scheduler and then sat pending for
  about two hours. Final accounting for each showed no start time and no node
  list, while the job log files showed the earlier brief runs and the
  preemption banners. This is the requeue accounting trap.
- During the same window, a preemptible-tier replica of a second pool and a
  preemptible-tier replica of a third pool were also preempted. The event was
  a reclamation wave on the preemptible tier, not a wave of independent
  failures.
- About T0+2h04m: the pending jobs were cancelled and new floor-replica jobs
  were submitted to the protected partition and QoS. They started within one
  minute, completed engine startup, and registered with the gateway.

## Why the sibling-pool check matters

The sibling pool that serves the same model in a different precision loads the
same engine model-definition code. It stayed up only because client traffic
for the failing pool is routed by model name. One request with the poison
characteristic, sent to the sibling pool, produces the same crash there. The
engine-side correction (request validation, or splitting the aggregated
encoder inputs before the failing call) protects every pool at once.

## Duplicate-check context

Near-miss candidates in the corpus, and why they do not cover this lesson:

- `slurm-walltime-expiry-outage-diagnosis`: single-job disappearance near the
  time limit; the drain-versus-crash branch. It does not cover the
  simultaneous multi-replica trigger, the identical-exception correlation, or
  the recovery-placement audit.
- `slurm-memcg-oom-kills-cross-filesystem-copy`: SIGKILL attribution for a
  memory-cgroup event; a different signature and workflow.
- `serving-lane-zero-floor-demotion`: capacity-policy change workflow, not
  outage diagnosis.
- `cluster-endpoint-incident-reproducer-validation`: reproducer artifact
  hardening, not outage classification.
- Open pull requests at the delivery base: an unrelated batch-job
  result-verification entry and an unrelated report-metric entry. No overlap.
