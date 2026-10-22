# Notes: Slurm Account and Partition Discovery

## Provenance

Source evidence: an interactive shell session on 2026-10-22 against one
production multi-partition Slurm cluster with slurmdbd accounting enabled.
The main skill records the generalized rules. These notes record supporting
detail that did not fit the main entry.

All cluster-specific identifiers stay out of both files:

- cluster name
- partition names (explicitly excluded at the requester's direction)
- account names
- QOS names
- user names
- hostnames and paths
- node counts, CPU counts, and memory sizes

Replace every `<placeholder>` in the commands below with the value for the
target cluster.

## Extended command reference

### Which account pays for a job

```bash
# Live job, controller record:
scontrol show job <id> | grep -E "Account=|Partition=|QOS="

# Historical job, accounting database:
sacct -j <id> -X -o JobID,User,Account,Partition,State%20,Elapsed,ExitCode

# All jobs of one account in a window:
sacct -S <date> -E <date> -X -A <account> -o JobID,User,State%20,Elapsed

# Jobs that run or wait now:
squeue -o "%.18i %.20u %.20a %.20P %.10T"
```

### Partition inventory and limits

```bash
# Exact partition set; '*' marks the default partition:
sinfo -h -o "%P" | sort -u

# Capacity detail; deduplicate before you count nodes:
sinfo -h -o "%P %T %D %C" | sort -u

# Limits for one partition; read AllowQos, AllowAccounts, AllowGroups:
scontrol show partition <partition>
```

### User access

```bash
# Associations for the current user:
sacctmgr show assoc where user=$USER

# Associations for one account, including its members:
sacctmgr show assoc where account=<account>

# QOS limits:
sacctmgr show qos

# QOS with fields for submission checks:
sacctmgr show qos format=Name,MaxWall,MaxTRES,Priority
```

### Confirm that accounting exists

```bash
scontrol show config | grep -i accounting
```

Look for `JobAcctGatherType` set to a value other than `jobacct_gather/none`
and for `AccountingStorageType` set to `accounting_storage/slurmdbd`.
When both are missing, `sacct` cannot deliver history. Use `squeue` and
`scontrol show job` for live answers, and state the history limit.

## Additional decision rules

- Multiple partitions can reference the same nodes. Node counts from one
  `sinfo` view do not sum to the cluster size.
- A user can hold several associations for the same account with different
  partitions or QOS entries. Read every row of `sacctmgr show assoc`, not
  only the first.
- The `*` suffix in `sinfo` output marks the default partition; strip it
  before you use the name in a query.
- The account field in job output records the charge target at submit time,
  not the project the owner works on most often. Do not back-fill missing
  accounts from user affiliation.
- Historic queries honor `-E <date>` (end of window); use both `-S` and `-E`
  for invoices or audits so the window is exact.

## Session observations kept for context

- Default `sinfo` output on the test cluster showed one row per partition,
  node-state, and account grouping. An observer read duplicates as extra
  partitions. `sinfo -h -o "%P" | sort -u` reduced the output to the exact
  set of four partitions.
- `sacct`, `sinfo`, and `sacctmgr` all answered on the first attempt; the
  cluster had full accounting and the querying identity had read access.
- One account name in the environment matched a tool name. This collision is
  cosmetic only and does not affect queries.
