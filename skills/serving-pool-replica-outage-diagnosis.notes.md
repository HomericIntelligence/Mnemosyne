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

## Startup-failure evidence (2026-11-07)

A later session on a production GPU serving fleet saw two pools whose replicas never registered.
Each case had a deterministic cause that repeated on every submission.

- Missing mount source. Every replica of one large pool ended FAILED after about seven
  minutes. The first error in the lowest-rank log was a container-runtime mount failure:
  the launch spec bind-mounted three runtime overlay directories, and the overlay root on the
  new lane was empty. The pool failure breaker tripped after three identical failures. The
  original overlays still existed under an older team path. A checksum-verified copy into the
  lane's overlay root, plus a breaker reset, let the next replica start and serve a real
  completion after a load time of about forty minutes.
- Engine argument conflicts. One pool failed three times in a row with a different error each
  time: the prefill backend needed an fp8 cache type; the decode backend needed a bf16 cache
  type on this platform; a third backend did not support the cookbook's index setting. Each
  run took between four and thirteen minutes, because the engine verified the checkpoint before
  it checked flag combinations. The session fell back to the one combination that matched a
  benchmark row.
- The supervisor summary line "rank 0 exited first with status 137" appeared in each failure.
  It reports the kill of the remaining processes, and the cause was in the rank log above it.
- A waiting job's rendered launch spec (`scontrol write batch_script`) showed the flags and
  mounts before it used a node.

## Amendment record (1.1.0)

- Disposition `amend`, version 1.0.0 to 1.1.0, on the same canonical entry.
- New decision value: the startup-failure branch (first error of the lowest-rank log, missing
  mount source, engine argument conflict, breaker reset after the fix, one-replica proof) and
  one failed attempt (one flag change per resubmission).
- Duplicate search: no open pull request changed this entry; the corpus has no other entry for
  container mount sources or engine argument conflicts.

## Distributed-startup and validator-parity evidence (2026-11-12)

A later multi-node validation effort moved several maintained recipe variants to one engine
image. The active recipe contained an explicit opt-in for checkpoint-supplied custom loader
code. Three inactive qualification recipes for the same loader omitted the corresponding recipe
field and engine argument. Their inactive routing status did not remove that launch requirement.

The shared canary log ended with a distributed rendezvous timeout of about ten minutes. That
timeout initially hid the useful ordering evidence. Per-node logs showed an earlier model-loader
refusal to execute checkpoint-supplied custom code without the opt-in. The affected rank exited
before it opened its rendezvous endpoint; its peers then waited until the timeout. Parallelism
differences were not the primary cause.

The validation scripts also constructed a launch command from only part of each recipe. They
omitted some per-cluster arguments and environment values, so a canary could test a configuration
that differed from production. The repair derived global and per-cluster arguments, environment,
served name, port, and topology from the recipe and wrote one engine log per node. The loader
opt-in repair covered every maintained variant with the same requirement.

Focused recipe, rendering, validation, and image-capability test suites passed after the repair.
Complete live revalidation of the final scripts had not run when this lesson was captured: the
jobs waited for shared scheduler capacity. The evidence therefore supports the causal diagnosis,
the recipe corrections, and the validator-contract correction. It does not claim a successful
final boot matrix.

Decision value beyond the earlier startup branch:

- A distributed rendezvous timeout is not a root-cause classification. Search all node or rank
  logs for an earlier initialization failure before investigating topology or fabric.
- The lowest-numbered rank is not necessarily the first failing rank. Per-node logs and causal
  ordering replace that shortcut.
- A canary must consume the same complete declarative launch contract as production. Do not
  infer production behavior from a hand-copied subset of its arguments and environment.
- Audit maintained inactive qualification variants when a loader requirement changes. Routing
  status does not change what the engine needs to load the checkpoint.

## Amendment record (1.2.0)

- Disposition `amend`, version 1.1.0 to 1.2.0, on the same canonical entry.
- New decision value: earliest-error causality across distributed ranks, custom-loader opt-in
  classification, recipe-derived canary parity, and coverage of maintained inactive variants.
- Delivery base: `ae987be0b6739bf340e2080dcf7e183895d355d1` of the knowledge repository.
- Duplicate search: no open pull request changed this canonical entry. Open candidates covered
  inert engine flag families and service-down triage; neither covers distributed rank causality
  or recipe-derived validator inputs.
- Privacy review: model and project identifiers, issue and job identifiers, infrastructure
  paths, hostnames, and exact operational identifiers are omitted. No secret, credential,
  regulated record, or erasure-requested material appears in the selected current or prior
  content inspected at the delivery base.

## Amendment record (1.5.0)

- Disposition `amend`, version 1.4.0 to 1.5.0, on the same canonical entry.
- Trigger: a multi-node replica launch ended in an unhandled distributed-initialization error.
  The error message named a diagnostic flag, and the per-rank logs did not contain the
  underlying cause.
- Decision value added: add the named flag to one isolated development launch only; read the
  first underlying cause from the verbose trace; keep the flag out of the production recipe
  and out of the fix; re-stage the development lane from clean fixed source before using it
  as proof.
- Supporting evidence: the verbose trace named a missing shared library used for topology
  resolution. A direct host-file mount was refused as an unapproved mount source. A read-only
  copy staged under an approved artifact root resolved the failure. The clean fix carried only
  the artifact mount and the loader path.
- Delivery base: `71dbe93d2d375236feaca6760e53e37e9bb3bb44` of the knowledge repository.
- Duplicate search: no open pull request changed this canonical entry. The nearest entries
  covered startup-failure classification from existing per-rank logs and canary parity with
  the production recipe; neither covered instrumenting one isolated lane when the error itself
  names the missing diagnostic flag.
- Privacy review: project names, model names, node names, job identifiers, internal paths,
  hostnames, and issue numbers are omitted. The library class and the artifact-root rule are
  described generically. No secret, credential, regulated record, or erasure-requested material
  appears in the selected current or prior content inspected at the delivery base.

## Requeue-versus-preemption evidence (2026-11-23)

Three multi-node replicas of one serving pool left RUNNING and returned to PENDING
under the same job IDs at the same second. The current records showed `PENDING`,
`Reason=Priority`, `Restarts=2`, `RunTime=00:00:00`, and `PreemptTime=None`.
`scontrol show job` and `sacct` without `--duplicates` showed only the reset
record. The service logs were not readable to the operator.

`sacct --duplicates` showed that each prior incarnation ended `PREEMPTED` at
the same second that several one-node jobs in a higher-tier partition started.
The two partitions covered the same full node set and differed in priority tier.
The jobs that started on the freed nodes were in the low-tier partition and
started about one minute after the preemption. They were occupants, not
preemptors. The controller log was root-only, so the exact preemptor identity
was not available. The start-time match and the partition tier comparison
established the preemption wave.

The first analysis classified the event as an explicit requeue. It used only the
current record and the victims' partition. That classification was wrong.
`sacct --duplicates` and the cross-partition start-time comparison corrected it.

## Amendment record (1.6.0)

- Disposition `amend`, version 1.5.0 to 1.6.0, on the same canonical entry.
- Trigger: a running job returned to PENDING under the same job ID, and the
  current record hid the prior terminal state.
- Decision value added: read each prior incarnation with `sacct --duplicates`
  before you classify the cause; a prior `PREEMPTED` state is direct evidence of
  scheduler preemption; compare every partition that shares the node set, because
  a higher-tier preemptor can be in a different partition; the jobs that start on
  the freed nodes later are occupants, not preemptors.
- Supporting evidence: three serving replicas returned to PENDING at the same
  second. Their prior incarnations ended `PREEMPTED` when higher-tier jobs
  started. The later occupants were in the low tier and started about one minute
  later. The service logs were not readable. See the section above.
- Delivery base: `b832e3a8b86af5ee31d0186f4f1ceda9fb321807` of the knowledge repository.
- Duplicate search: no open pull request changed this canonical entry. The nearest
  merged entries covered drain-versus-completion classification and preemptible
  capacity accounting; neither covered the hidden prior incarnation or the
  cross-partition preemptor check.
- Privacy review: project names, model names, node names, job identifiers, account
  names, user names, internal paths, and hostnames are omitted. The counts and
  scheduler fields are described generically. No secret, credential, regulated
  record, or erasure-requested material appears in the selected current or prior
  content inspected at the delivery base.
