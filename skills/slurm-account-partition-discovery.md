---
name: slurm-account-partition-discovery
license: BSD-3-Clause
description: "Map Slurm jobs to the accounts charged for them, list cluster partitions and their limits, and show the accounts, partitions, and Quality-of-Service (QOS) entries that a user can submit to. Use when: (1) you must find the account that a job is charged to, (2) you enumerate the partitions on a cluster, or (3) you check what a given user is allowed to submit."
category: tooling
date: 2026-10-22
version: "1.0.0"
user-invocable: false
tags: ["slurm", "squeue", "sacct", "sinfo", "scontrol", "sacctmgr", "partitions", "accounts", "qos", "cluster-discovery"]
---

# Slurm Account and Partition Discovery

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-22 |
| **Objective** | Answer account, partition, and access questions on a Slurm cluster from authoritative command output. |
| **Outcome** | Successful. Each question has one authoritative source; fallbacks cover missing accounting or missing rights. |

## When to Use

Use this skill when one of these conditions applies:

- You must find the account that a queued, running, or completed job is charged to.
- You must list the partitions on a cluster and their limits or capacity.
- You must find which accounts, partitions, or QOS entries a user can submit jobs to.
- You must explain which tool answers which question before you run cluster-wide queries.

## Verified Workflow

### Quick Reference

Select the source by job lifetime. Use custom output formats; do not parse default layouts:

```bash
# Queued and running jobs only. %a is the charged account, %P the partition.
squeue -o "%.18i %.20u %.20a %.20P %.10T %.10M"

# Completed and canceled jobs. Needs the accounting database (slurmdbd).
sacct -S <YYYY-MM-DD> -X -o JobID,JobName%30,User,Account%20,Partition%20,State%20

# One job, from the controller. No accounting database needed. Live jobs only.
scontrol show job <id> | grep -E "Account=|Partition=|QOS="

# Inside an allocation. The fastest authoritative per-job answer.
printenv SLURM_JOB_ACCOUNT SLURM_JOB_PARTITION

# The unique partition set on the cluster. Additional rows repeat per state.
sinfo -h -o "%P" | sort -u

# The accounts, partitions, and QOS entries that a user can submit to.
sacctmgr show assoc where user=$USER
```

### Suggested Approach

1. Classify the question by job lifetime before you choose a command. `squeue`
   covers pending and running jobs only. `sacct` covers completed and canceled
   jobs when accounting is configured. `scontrol show job <id>` gives one
   authoritative per-job answer from the controller without the database.
2. Use `%a` for the account and `%P` for the partition in `squeue` and `sacct`
   output formats. Set an explicit column width, such as `Account%20`, before
   you filter or parse output.
3. Derive the partition set with `sinfo -h -o "%P" | sort -u`. Default `sinfo`
   output repeats one row per partition and node-state combination, and the
   same node can serve more than one partition. A `*` suffix marks the default
   partition.
4. Read per-partition limits with `scontrol show partition <partition>`.
   `AllowQos` lists the QOS entries that can submit; `AllowAccounts` and
   `AllowGroups` list the grant scope. `Default=YES` marks the default
   partition.
5. Read user access with `sacctmgr show assoc where user=<user>`. The
   association record joins cluster, account, user, partition, and QOS. Read
   QOS limits with `sacctmgr show qos`.
6. Treat the account field as a charge attribute, not as the user's project.
   The scheduler set the account at submit time with `--account`, or from the
   user's default association. The charged value can differ from the job
   owner's usual affiliation.
7. When `sacct` returns nothing for a completed job, or a database error
   appears, check whether the collection has accounting configured. Run
   `scontrol show config | grep -i accounting`. State the limit in the
   report. Give live answers from `squeue` and `scontrol show job` instead.
8. When `sacctmgr` output is empty or returns a permissions error, the
   requesting identity lacks accounting rights. State the limit. Ask a
   privileged operator for the association, or read `scontrol show partition`
   for the partition-level grant lists as a partial substitute.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Default output as inventory | Read default `sinfo` rows as the partition inventory. | Rows repeat per partition, node-state, and account grouping. Shared nodes inflated the apparent node counts. | Use `sinfo -h -o "%P" \| sort -u` for the exact partition set. Use a custom `-o` format for capacity detail. |
| Group lookup as access proxy | Read POSIX group membership as a proxy for Slurm access. | Groups are not Slurm associations. The account and QOS grants stayed invisible. | Use `sacctmgr show assoc where user=<user>` as the authoritative source for partitions, accounts, and QOS. |
| Historical coverage check | Ran `sacct` for completed and canceled jobs on the test cluster. | No failure observed; accounting was enabled on this cluster. This row records the coverage limit, not a defect. | When `sacct` returns empty output or a database error, the cluster can lack accounting. State the limit; do not report an unverified history. |

## Results & Parameters

### Configuration

Parameters that change the answer, grouped by command:

- `squeue`: `%a` charged account; `%P` partition; `%i` job identifier; `%T`
  state; `%M` elapsed time; `%D` node count; `%R` reason or node list. Use
  `-A <account>` to filter by account and `-u <user>` to filter by user.
- `sacct`: `-S <date>` and `-E <date>` bound the window; `-X` hides batch and
  extern steps; `-j <id>` selects one job; `-A <account>` and `-u <user>`
  filter; field widths such as `State%20` prevent truncation when you parse.
- `sinfo`: `%P` partition; `%T` node state; `%D` node count; `%C` CPU
  counters (allocated/idle/other/total); `%G` generic resources (GRES). The
  default layout needs `sort -u` to deduplicate partition names.
- `scontrol show job <id>`: read `Account=`, `Partition=`, and `QOS=` from
  the controller record. One short call replaces a database query.
- `sacctmgr show assoc where user=<user>`: join fields `Cluster`, `Account`,
  `User`, `Partition`, `QOS`, `GrpTRES`. Empty output means no association,
  or a rights limit, not "no access configured."
- Environment inside an allocation: `SLURM_JOB_ACCOUNT`,
  `SLURM_JOB_PARTITION`, and `SLURM_JOB_QOS` give the charged values without
  any scheduler query.

### Expected Output

- One row per job with its account and partition, from `squeue` or `sacct`.
- The exact partition name set; a `*` suffix marks the default partition.
- Per-partition limits from `scontrol show partition`, including `AllowQos`.
- One association row per granted (account, partition, QOS) combination for
  the queried user.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Production multi-partition Slurm cluster with slurmdbd accounting | Verified live job, historical job, partition-set, and per-user association answers in an interactive shell session. | Cluster-specific identifiers were generalized per privacy policy. See [notes](slurm-account-partition-discovery.notes.md). |

## References

- [squeue(1) — view information about jobs in the scheduling queue](https://slurm.schedmd.com/squeue.html)
- [sacct(1) — display accounting data](https://slurm.schedmd.com/sacct.html)
- [sinfo(1) — view information about nodes and partitions](https://slurm.schedmd.com/sinfo.html)
- [scontrol(1) — view or modify configuration and state](https://slurm.schedmd.com/scontrol.html)
- [sacctmgr(1) — manage associations, accounts, and QOS](https://slurm.schedmd.com/sacctmgr.html)
- [Slurm foreign job artifact gate](slurm-foreign-job-artifact-gate.md) — cross-account job monitoring and artifact pinning when logs are unreadable.
