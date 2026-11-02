# Notes: Slurm QOS Group-Cap Regression Diagnosis

Supporting evidence for the main entry. All cluster-specific identifiers are
generalized per the privacy policy.

## Source session

- Date: 2026-10-27, one interactive diagnosis session on a production
  multi-tenant Slurm cluster with an accounting database.
- Trigger: a request to bring up one serving node of a model fleet; the node
  job and four sibling fleet jobs stood pending with `QOSGrpNodeLimit`, and
  the largest pending job also showed `QOSGrpGRES`.

## Measured evidence

### Live cap

```
$ sacctmgr -nP show qos <fleet-qos> format=name,maxnodesperuser,maxtresperuser,grptres
<fleet-qos>|||gres/gpu=32,node=4|
```

- `MaxNodesPerUser` and `MaxTRESPerUser` were empty; `GrpTRES` was the
  binding limit: four nodes, 32 GPUs.
- A sibling deployment QOS in the same table showed the identical
  `gres/gpu=32,node=4` values. The fleet budget record for the affected
  account named the same QOS with `GrpNodes=10` and `gres/gpu=80`.

### Running usage over the live cap

- Seven running jobs of the fleet QOS held seven GPU nodes (56 GPUs).
- One further fleet job, a CPU-only gateway service, held one more node with
  no GPU allocation. Against a `GrpTRES` node count, that node also counted.
- Total: eight nodes and 56 GPUs against a cap of four nodes and 32 GPUs.
- The scheduler left all of these jobs running. It refused only new jobs.

### Change-time bound

- Start times of the over-limit running jobs spread over roughly two hours
  the same morning. The latest start gave the lower bound: the cap changed
  after that job started, that is, inside the same day, before the session.
- Later the same day, one healthy serving job was cancelled from outside:
  accounting showed `CANCELLED` with exit code `0:15` and the step record
  `CANCELLED ... DUE to SIGNAL Terminated`; the server log showed successful
  request handling until the signal. This is consistent with a capacity trim
  of an over-limit fleet. The session recorded it as consistent evidence,
  not as proof of intent.
- `sacctmgr show events` listed only the cluster registration event. No QOS
  edit history was available to the session identity.

### Change-shape observation

- Both `GrpTRES` fields fell by the same factor: ten nodes to four, and 80
  GPUs to 32, which is eight GPUs per node in both states.
- The affected QOS and the sibling deployment QOS carried identical values
  after the change. Both observations support a scripted resize or copied
  values rather than a single-field edit. The session recorded the shape as
  evidence, with no administrator confirmation available.

## Restoration prepared, not applied

- The session prepared `sacctmgr modify qos <fleet-qos> set
  grptres=node=10,gres/gpu=80` for a scheduler administrator and did not run
  it: the session identity lacked QOS modification rights, and the operator
  decision was deferred. The main entry records restoration as a prepared
  hand-off, not as a verified fix.
- Residual queue after restoration: fleet demand was 14 nodes against the
  restored cap of ten, so pending jobs would still queue after the cap
  returned. State this expectation in the hand-off.

## Duplicate-search record

- Corpus search terms: `qos`, `grptres`, `grpnode`, `scheduler limit`,
  `pending job`, `QOSGrp`, `group limit`, `node budget`.
- Closest entries inspected in full: `slurm-account-partition-discovery`
  (discovery of accounts, partitions, and QOS grants; no cap-regression
  rule), `serving-pool-replica-outage-diagnosis` (classification of dead
  replicas; different failure mode), `slurm-walltime-expiry-outage-diagnosis`
  (job disappearance at time limit; different trigger).
- No entry covered the pending-with-grandfathered-usage failure mode, so the
  selected disposition was `create`.

## At-limit saturation evidence (2026-10-30)

A later session on the same fleet QOS hit the opposite branch: the cap was
intact, and the running usage stood exactly at it.

- Live cap unchanged: four nodes and 32 GPUs, `MaxNodesPerUser` and
  `MaxTRESPerUser` still empty, `GrpTRES` still the binding limit.
- Running usage exactly at the cap: one CPU-only gateway service node, one
  two-node replica pool, and one one-node replica pool. Total four nodes and
  24 of 32 GPUs. The node count was exhausted while GPU headroom remained,
  so the binding dimension was the node count, not the GPU count.
- A model-replica pool pended with `QOSGrpNodeLimit`. Its protected floor was
  one packed node: two replicas of one model on one host, four GPUs and
  roughly 700 GiB of memory per replica.
- Repeated opener jobs did allocate on hosts that already served the account,
  twice on the gateway's node. Each partial placement was cancelled about two
  minutes after allocation. The serving coordinator's cohort-fit guard ran
  the check before the cohort was complete, found the host short, cancelled
  the packed cohort, and quarantined the host for this pool.
- The coordinator's drift log recorded each failure as a `packed-placement`
  record with the comparison `host_fits_cohort`: the expected cohort need as
  CPU, memory, and GPU counts; the observed free and short amounts per
  resource; and the resolution `free the host or exclude it from the pool;
  the packed cohort is cancelled`. In the measured failures the hosts often
  had enough free GPUs but were short on CPU or memory, so visible free GPUs
  never proved placement.
- The next pending job carried an `ExcNodeList` that named exactly the hosts
  the guard had quarantined. The pending pool therefore refused hosts that
  the scheduler's free-GPU view showed as available.
- Floor arithmetic against the cap: gateway 1 + two-node replica pool 2 +
  one-node replica pool 1 + packed pool 1 = 5 nodes against a cap of 4. No
  placement policy could satisfy the floors. The remedies were a cap raise,
  a floor reduction or retirement of another pool, or a full-cohort
  co-location on one host, which the other tenants' allocations ruled out.
  The session reported the deficit and the three remedies and left the
  operator decision open.

## Amendment record

- Disposition `amend`, version 1.0.0 to 1.1.0, on the same canonical entry.
- New decision value: the at-limit saturation branch, the node-count
  co-location rule, the coordinator quarantine and exclude-list mechanism,
  and the floor-arithmetic check.
- Duplicate search: no open pull request touched this entry or added an
  entry with the same intent at delivery time.
