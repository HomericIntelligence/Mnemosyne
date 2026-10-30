---
name: slurm-multi-account-capacity-evaluation
license: BSD-3-Clause
description: "Evaluate whether more Slurm accounts or partitions add usable capacity before a multi-account or multi-partition experiment. Use when: (1) you ask whether one job can charge more than one account, bind more than one Quality-of-Service (QOS) record, or run on a partition list, (2) you plan to spread a job fleet across accounts, or (3) you compare the capacity that two accounts see on a shared partition."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
tags: ["slurm", "sbatch", "sacctmgr", "sinfo", "scontrol", "accounts", "qos", "partitions", "capacity", "multi-account"]
---

# Slurm Multi-Account Capacity Evaluation

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Decide, from recorded scheduler facts, whether extra accounts or partitions give more usable capacity. |
| **Outcome** | Successful. The arity errors, the access derivation, and the capacity-parity check were verified on a production cluster without creating a job. |

## When to Use

Use this skill when one of these conditions applies:

- You ask whether one job can charge more than one account, bind more than one QOS record, or run on several partitions at once.
- You plan to spread a fleet of jobs across two or more Slurm accounts.
- You compare the capacity that two accounts see on one shared partition.
- You must prove that a placement is schedulable before the scheduler creates the job.

## Verified Workflow

### Quick Reference

```bash
# Prove argument arity and admission without creating a job. --test-only
# validates the request and returns an immediate error or a start estimate.
sbatch --test-only --account=<a1>,<a2> --qos=<q> --partition=<p> -t 1 --wrap true
#   -> allocation failure: Invalid account or account/partition combination specified
sbatch --test-only --account=<a> --qos=<q1>,<q2> --partition=<p> -t 1 --wrap true
#   -> allocation failure: Invalid qos specification
sbatch --test-only --account=<a> --qos=<q> --partition=<p1>,<p2> -t 1 --wrap true
#   -> accepted; the job starts where initiation is earliest

# Access facts for one account and one partition.
sacctmgr show assoc where account=<account> format=account,partition,qos -nP
sacctmgr -nP show qos <qos> format=Name,MaxTRES,MaxTRESPerUser,GrpTRES,MaxJobsPerUser
scontrol show partition <partition> | grep -E 'AllowQos|AllowAccounts|PreemptMode|PriorityTier'

# Capacity overlap between partitions: sum the per-node CPU counters.
sinfo -h -N -p <partition> -o '%C' | awk -F/ '{a+=$1;i+=$2;o+=$3;t+=$4} END {print a"/"i"/"o"/"t}'
```

### Suggested Approach

1. Apply the arity rule before you design the experiment. One job binds exactly
   one account and exactly one QOS. Only `--partition` accepts a comma-separated
   list, and the job then starts on the listed partition that offers the
   earliest initiation (sbatch(1)). A comma list adds nothing when the tier has
   a single partition. To use two accounts, submit two jobs.
2. Derive access as a product, not from the refusal text. The placements that an
   account can use are its association QOS set joined with each partition's
   `AllowQos` list. An empty partition column in an association row is a
   cluster-wide grant, so the partition `AllowQos` then becomes the binding
   constraint. A missing association is refused with a bare
   "Invalid qos specification" that names no account, no QOS, and no partition.
   Read the association rows and `AllowQos` lists instead of the error text.
3. Check capacity parity before you expect additive capacity. When the QOS
   record shows no `GrpTRES` or `MaxTRES` caps and the per-account association
   rows show no `GrpTRES`, two accounts see identical capacity on the same
   shared partition. They differ only in charge and fair-share attribution.
4. Do not count partitions as disjoint pools. Large partitions can span the same
   node set. Identical per-partition CPU totals mean the partitions overlap
   completely, so two named partitions are not two pools of capacity. Compare
   the `sinfo` totals before you count capacity.
5. Score a preemptible tier as revocable capacity. A partition with
   `PreemptMode=REQUEUE` and a lower `PriorityTier` offers leftover capacity
   that other work can take back, regardless of the charged account.
6. Verify each claim with `--test-only`. Run the multi-value probes to record
   the arity errors, then run the single-placement probe as the passing
   control. No job is created by either probe.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Two accounts on one job | `sbatch --test-only --account=<a1>,<a2>` on a valid placement | Refused with "Invalid account or account/partition combination specified" | One job charges exactly one account; spread a fleet across separate submissions |
| Two QOS records on one job | `sbatch --test-only --qos=<q1>,<q2>` on a valid placement | Refused with "Invalid qos specification" | One job binds exactly one QOS, even when both records are individually valid |
| Read a bare refusal as a syntax error | An earlier incident treated "Invalid qos specification" on a well-formed placement as a syntax problem | The text names no account, QOS, or partition; the root cause was a missing account association | Verify the account association and the partition `AllowQos` list first; the error text carries no diagnosis |
| Assume two accounts give two slices | Compared two project accounts on one shared preemptible partition | The QOS record and both association rows carried no caps; the partition pool was identical | With no caps, accounts differ only in charge and fair-share attribution; check the cap records before you expect additive capacity |

## Results & Parameters

### Configuration

```yaml
placement_arity:
  account: exactly one per job
  qos: exactly one per job
  partition: comma-separated list allowed; earliest initiation decides (sbatch(1))
access_derivation:
  usable_placement: association QOS set joined with the partition AllowQos list
  empty_partition_column: cluster-wide grant; the partition AllowQos then binds
  refusal_text: "Invalid qos specification (names no account, no QOS, no partition)"
capacity_parity:
  check_records: [qos GrpTRES, qos MaxTRES, per-association GrpTRES]
  empty_caps_mean: identical shared capacity; difference is charge and fair share only
partition_overlap_check: per-partition sinfo CPU totals; identical totals mean one node set
preemptible_tier: PreemptMode=REQUEUE with a lower PriorityTier means revocable leftover capacity
```

### Expected Output

- A multi-value `--account` or `--qos` probe exits with an immediate client-side
  error; a comma-separated `--partition` probe parses and returns a start
  estimate.
- Association rows list the QOS records that an account can use; an empty
  partition column marks a cluster-wide grant.
- `scontrol show partition` supplies `AllowQos`, `PreemptMode`, and
  `PriorityTier` for the access and priority decision.
- Identical per-partition CPU totals confirm that two partitions share one
  node set.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Production multi-partition Slurm cluster with slurmdbd accounting | Verified both arity errors, the single-placement passing control, the association rows, the partition grants, and the uncapped QOS records live with `--test-only` probes; no jobs were created. | Cluster-specific identifiers were generalized per privacy policy. See [notes](slurm-multi-account-capacity-evaluation.notes.md). |

## References

- [sbatch(1) — submit a batch script; the partition list accepts commas and the one with earliest initiation is used; --test-only validates without submission](https://slurm.schedmd.com/sbatch.html)
- [sacctmgr(1) — associations and QOS limits](https://slurm.schedmd.com/sacctmgr.html)
- [sinfo(1) — per-partition node and CPU counters](https://slurm.schedmd.com/sinfo.html)
- [Slurm account and partition discovery](slurm-account-partition-discovery.md) — which command answers which access question
- [Slurm QOS group-cap regression diagnosis](slurm-qos-group-cap-regression-diagnosis.md) — pending reasons when a QOS group cap changes
