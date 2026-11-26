---
name: slurm-explicit-grant-placement-for-shared-work
license: BSD-3-Clause
description: "Charge shared-capacity Slurm work to the intended grant by setting account, Quality-of-Service (QOS), and partition from an owner-controlled cluster record. Use when: (1) a job or fleet must charge a shared grant, (2) donors or submitters have a different default association, (3) a shared command must not inherit the submitter's scheduler default, or (4) a cluster profile supplies placement defaults."
category: tooling
date: 2026-11-26
version: "1.0.0"
user-invocable: false
tags: ["slurm", "sbatch", "sacctmgr", "scontrol", "account", "qos", "partition", "placement", "shared-capacity", "cluster-profile"]
---

# Explicit Grant Placement for Shared Slurm Work

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-26 |
| **Objective** | Make shared-capacity jobs charge the owner-selected grant, not the submitter's Slurm default association. |
| **Outcome** | Successful. A shared command now reads a complete placement from a cluster profile. Tests cover the default, an explicit override, an absent record, a partial record, and a malformed record. |

## When to Use

Use this skill when one of these conditions applies:

- A job or fleet must charge a specific shared grant, such as donated capacity, a shared pool, or service work.
- The submitter can have a different default account or QOS, such as a personal, project, or legacy association.
- A command must work for many users without each user passing the placement.
- An owner-controlled cluster profile is the source of placement values.

## Verified Workflow

### Quick Reference

```bash
# 1. Find the submitter default and the allowed sets.
sacctmgr -nP show assoc where user="$USER" format=Account,Partition,QOS%60,DefaultAccount,DefaultQOS
scontrol show partition <partition> | grep -E 'AllowAccounts|AllowQos|Default'

# 2. Prove that a complete triple is admissible. This creates no job.
sbatch --test-only --account=<grant-account> --qos=<grant-qos> --partition=<partition> -t 1 --wrap true

# 3. Verify the charged values after submission.
scontrol show job <job-id> | grep -E 'Account=|Partition=|QOS='
```

Applicability:

- Step 1 needs accounting rights. Without them, read `scontrol show partition` and ask the owner for the association.
- Step 2 is safe. The scheduler validates the request and creates no allocation.
- Step 3 answers for live jobs. Use `sacct` for completed jobs.

### Suggested Approach

1. Name the charge owner. Decide which grant pays for the work. Do not use the submitter's default as the answer.
2. Read the owner record. Put `account`, `qos`, and `partition` in one owner-controlled cluster profile record. Keep the record optional. A cluster without one keeps the submitter default.
3. Require a complete triple. If the record is present, reject it unless all three values are set. A partial record can pair one owner value with a submitter default and create an invalid or wrong charge.
4. Resolve every placement from the record. Pass all three values to every submission. Do not omit one value and rely on ambient `SBATCH_*` variables or the scheduler default.
5. Keep explicit flags on top. A caller override wins per field. Document that the account and QOS are one scheduler pair and should be overridden together.
6. Fail closed on a present-but-invalid record. Fall back only when the record is absent. A silent fallback recreates the defect.
7. Verify. Run `sbatch --test-only`. Then read the queued or running job record. Confirm the account, QOS, and partition.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Inherit the submitter default | Omitted `--account`, `--qos`, and `--partition` and let the scheduler choose | The scheduler used the submitter association and charged a different grant with a small cap. The job waited at the cap or consumed the wrong budget. | Set the triple explicitly from the owner record. |
| Override only the account | Passed `--account` and kept the profile QOS | The account and QOS pair was invalid or mixed two sources. | Treat the account and QOS as one pair. Select both from the same record or pass a matched pair. |
| Treat an invalid record as absent | Caught all profile errors and used the fallback | The command restored the submitter default with no warning. | Fail closed on a present-but-invalid record. Fall back only on absence. |
| Hardcode the grant in the command | Put the account name in the CLI default | The command broke other clusters and mixed policy with code. | Keep placement in the cluster profile. Keep the command cluster-neutral. |

## Results & Parameters

### Configuration

```yaml
# Optional owner-controlled record in the cluster profile.
shared_work_placement:
  account: <shared-grant-account>
  qos: <shared-grant-qos>
  partition: <partition>
```

Rules:

- Absent record: use the submitter default.
- Present record: require all three fields.
- Invalid record: stop the command before submission.
- Explicit CLI flag: wins over the record.

### Expected Output

- The submission arguments and the batch script contain the explicit account, QOS, and partition.
- Ambient scheduler variables cannot choose the placement.
- A cluster without the record behaves as before.
- An invalid record stops the command before it submits.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Shared-capacity Slurm service | Production cluster with multiple account grants. A shared command changed from the submitter default to a profile record. | Behavior tests cover the default, an explicit override, an absent record, a partial record, and a malformed record. Identifiers are generalized. |

## References

- [sbatch(1) — batch submission and `--test-only`](https://slurm.schedmd.com/sbatch.html)
- [sacctmgr(1) — associations and QOS limits](https://slurm.schedmd.com/sacctmgr.html)
- [scontrol(1) — job and partition records](https://slurm.schedmd.com/scontrol.html)
- [Slurm account and partition discovery](slurm-account-partition-discovery.md) — commands that answer account and partition questions
- [Slurm multi-account capacity evaluation](slurm-multi-account-capacity-evaluation.md) — one account and one QOS per job