# Notes: Slurm Multi-Account Capacity Evaluation

## Provenance

Source evidence: an interactive shell session on 2026-10-30 against one
production multi-partition Slurm cluster with slurmdbd accounting enabled. The
session planned a capacity experiment: it asked whether jobs could run on
"any" preemptible placement and whether one job could name several account
placements at once. The main skill records the generalized rules. These notes
record the evidence shapes that did not fit the main entry.

All cluster-specific identifiers stay out of both files:

- cluster name;
- partition, account, QOS, and user names;
- hostnames and paths; and
- node counts, CPU counts, and memory sizes.

Replace every `<placeholder>` in the transcripts below with the value for the
target cluster.

## Session evidence pattern

Probe transcript shapes, with identifiers replaced:

```text
$ sbatch --test-only --account=<a1>,<a2> --qos=<q> --partition=<p> -t 1 --wrap true
allocation failure: Invalid account or account/partition combination specified

$ sbatch --test-only --account=<a> --qos=<q1>,<q2> --partition=<p> -t 1 --wrap true
allocation failure: Invalid qos specification

$ sbatch --test-only --account=<a> --qos=<q> --partition=<p>,<p> -t 1 --wrap true
sbatch: Job <id> to start at <time> using 2 processors on nodes <node> in partition <p>
# Accepted; --test-only creates no job.

$ sbatch --test-only --account=<a2> --qos=<q> --partition=<p> -t 1 --wrap true
sbatch: Job <id> to start at <time> using 2 processors on nodes <node> in partition <p>
# A second account, single placement: also accepted.

$ sacctmgr show assoc where account=<a1> format=account,partition,qos -nP
<a1>||<q-self>,<q-exclusive>,<q-shared>
<a1>|<user>||<q-self>,<q-exclusive>,<q-shared>
# Empty partition column: a cluster-wide grant.

$ sacctmgr -nP show qos <q-shared> format=Name,Flags,MaxTRES,MaxTRESPerUser,GrpTRES,MaxJobsPerUser
<q-shared>|||||
# No caps: a shared fair-share pool.

$ scontrol show partition <p-shared> | grep -E 'AllowQos|PreemptMode|PriorityTier'
AllowAccounts=ALL AllowQos=<q-shared>,<q-ci> ... PreemptMode=REQUEUE ... PriorityTier=<lower>
```

Reading: two project accounts carried the shared preemptible QOS as a
cluster-wide grant; the shared QOS had no caps; a third account lacked that
QOS entirely, and an earlier incident recorded the bare refusal for exactly
that missing association. The per-partition CPU totals for the GPU partitions
were identical, so those partitions span one node set.

## Boundary with related skills

- [Slurm account and partition discovery](slurm-account-partition-discovery.md)
  selects the authoritative command for an access question. This skill adds
  the decision rules that apply to the answers: the arity rule, the access
  product, and the capacity-parity check.
- [Slurm QOS group-cap regression diagnosis](slurm-qos-group-cap-regression-diagnosis.md)
  treats a changed group cap. This skill treats the no-cap comparison case.
