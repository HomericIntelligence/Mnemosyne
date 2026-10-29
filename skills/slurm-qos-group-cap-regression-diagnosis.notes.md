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
