---
name: db-lock-pool-exhaustion-idle-service-stall
license: BSD-3-Clause
description: "Find and fix the cause when a network service stops answering for minutes while its CPU is idle, because every database connection waits on a lock that one long transaction holds. Use when: (1) the health route and all other routes time out together, (2) the process is idle, not busy, (3) the proxy in front returns 499 and 504, (4) the service recovers without a code change, (5) derived aggregates are rebuilt inside a request."
category: debugging
date: 2026-11-25
version: "1.0.0"
user-invocable: false
verification: verified-live
tags: [deployed-version-lag, postgres, advisory-lock, connection-pool, pool-exhaustion, lock-timeout, statement-timeout, query-plan, seq-scan, health-probe, background-worker, rollup, outage-diagnosis, pg-locks]
---

# Idle Service Stall From A Database Lock And An Exhausted Pool

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-25 |
| **Objective** | Decide, with evidence taken before any restart, why a service that is idle gives no answer. Then remove the cause so one slow transaction cannot stop every route. |
| **Outcome** | Operational. A live stall was traced to one transaction that held an advisory lock while three other requests waited on the same key. These four requests were the whole connection pool. |
| **Verification** | verified-live on a production service. Names, hosts, paths and counts are generalized. The exact plan of the stuck statement was not readable, so the plan finding comes from the same statement on a real id. |

## When to Use

- Every route, including the health route, times out at the same time. The process is up and its CPU is near zero.
- The proxy in front returns many 499 (client gave up) and 504 (upstream timed out) answers. The service log has no line for the stall.
- Senders report read timeouts and keep their data for retry. After a recovery the backlog replays and no data is lost.
- The service uses a small database pool (a few connections) and a transaction-scoped advisory lock (`pg_advisory_xact_lock`) to order two writers.
- A request rebuilds derived rows (rollups, aggregates) from a very large table inside the same transaction as its lock.
- You must review a change that adds a lock, a pool, or a rebuild to a request path.

## Verified Workflow

### Quick Reference

```bash
# 1. Is the process waiting, not working? (thread wait channel, CPU, sockets)
for t in /proc/<pid>/task/*; do echo "$(cat $t/comm) $(cat $t/wchan)"; done | sort | uniq -c
ss -tn 'sport = :<port>' | awk 'NR>1{c[$1]++}END{for(k in c)print k,c[k]}'   # many CLOSE-WAIT = clients gave up

# 2. Who holds the lock, who waits (a read-only session; pg_locks is visible to every role)
psql "$DSN" -Atc "select pid, granted, classid, objid from pg_locks where locktype='advisory' order by granted desc"
# One granted row and N not granted rows on the same key, with N+1 = pool size, is the stall.

# 3. Is the running build older than the fix? (release of the live interpreter, then ancestry of the fix commit)
<venv>/bin/python -c "import <package>, pathlib; print(pathlib.Path(<package>.__file__).resolve())"
git merge-base --is-ancestor <fix-commit> <deployed-revision> && echo has-fix || echo predates-fix

# 4. What does the holder run? Needs the service role, in a read-only session.
PGOPTIONS="-c default_transaction_read_only=on -c statement_timeout=15000" \
psql "$SERVICE_DSN" -x -c "select pid, state, wait_event_type, wait_event,
  now()-xact_start as xact_age, left(query,400) from pg_stat_activity
  where usename = current_user and pid <> pg_backend_pid() order by xact_start"
```

### Suggested Approach

1. **Save evidence first.** Copy the proxy and service logs and take the snapshots above before any restart or backend termination. A restart clears the lock and the proof. Do not end a backend or restart without the owner's approval.
2. **Show that the service waits.** Idle CPU, threads in `ep_poll` or a futex, and a listen backlog of zero mean the event loop is free. The wait is on the database, not on the loop.
3. **Compare the running build with the fixed source.** A statement that runs longer than the command timeout already in the source proves that the deployed build is older than that timeout. Then the first action is to deploy the current source, not to write the timeout again. Read the release of the live interpreter and test whether the fix commit is an ancestor of it.
4. **Count the pool.** If the granted holder plus the waiters equal the pool maximum, new requests wait on pool acquire, so the health route fails too.
5. **Read the holder.** A read-only role shows "insufficient privilege" for the query of another role. Use the service role in a read-only session, with authorization. `wait_event = DataFileRead` with a transaction age of minutes points at a large scan.
6. **Map the lock key.** An advisory key splits into `classid` (high 32 bits) and `objid` (low 32 bits). Compare it with `hashtextextended(<candidate>, 0)` for each candidate string at every lock call site. Search all call sites, not only one. The holder has not committed, so its rows may not exist yet.
7. **Check the plan of the holder.** Run `EXPLAIN` (not `ANALYZE`) on the same statement with a real id. A range join of a huge table against a `DISTINCT` subquery that produces the time windows can be estimated badly and planned as a full scan. One bounded window per statement uses the time index and takes milliseconds.
8. **Fix the design, not only the timeout:**
   - Run the rebuild outside the request, in one serial background worker with a queue that drops duplicate keys and never gives up a key because others are ahead of it.
   - Replace one bounded window in each short transaction. The delete and the new rows commit together, so a reader sees old rows or new rows.
   - Set `lock_timeout` for that transaction with `set_config('lock_timeout', ..., true)`. A window that times out keeps its old rows and is tried again in a later round.
   - Set a pool acquire timeout and a command timeout. Answer a typed 503 so senders retry from their buffer.
   - Give the health route and the background worker each their own connection. A full request pool cannot hide the probe, and a slow rebuild cannot take a request connection.
9. **Make the next stall visible.** Log each slow lock wait with its key, route and pool use. Alert when an advisory lock has waited without being granted for more than a minute, and save a lock and socket snapshot with the alert. A first-seen time kept in the alert state is enough, because `pg_locks` has no wait time.
10. **Prove the fix.** The proxy shows only 200 answers, the freshest derived row advances every minute, and no lock waits longer than a minute.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Service log | Read the service log for the cause. | The service wrote nothing during the stall. | Read `pg_locks` and the proxy log. Add slow-lock logging. |
| Read-only role | Read the holder's query with the read-only role. | The role cannot see queries of other roles. | Use the service role in a read-only session, with authorization. |
| Key match on committed ids | Matched the lock key against the recent batch ids in the data. | The holder had not committed, and the key came from a different lock call site. | List every lock call site and hash each candidate string. |
| Busy-loop theory | Looked for a blocked event loop or a CPU spike. | The loop was idle. All four connections waited on the database. | Idle CPU with a full small pool points to a lock, not to compute. |
| Code fix first | Planned to add a command timeout after a statement ran 13 minutes. | The timeout was already in the source. The deployed build was older. | Compare the running build with the source before you write code. |
| Timeouts only | Considered only a command timeout. | A timeout cancels the slow rebuild, but the same rebuild starts again and fails again. | Bound the work to one window and move it out of the request. |

## Results & Parameters

### Configuration

```yaml
request_pool: {min: 1, max: 4, acquire_timeout_s: 10, command_timeout_s: 60}
health_pool: {max: 1}
rebuild_pool: {max: 1}          # one serial worker, key queue with duplicates dropped
rebuild:
  lock_timeout_ms: 5000          # per window transaction, local to the transaction
  rounds: 5
  retry_seconds: 30              # only the failed windows are tried again
alert:
  ungranted_advisory_lock_age_s: 60
```

### Expected Output

- Before: a stall of 10 to 30 minutes. One statement ran 13 minutes on a table of about 170 million rows. Three requests waited on its lock.
- After: one window takes about 2 ms on the same table (index scan), requests do not wait on a rebuild, and the health route answers while the request pool is full.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A usage-ingest service behind a reverse proxy | Dashboard rollups stopped updating. A first-batch rebuild ran inside the request under a per-batch advisory lock. | Fixed with a per-window background rebuild, lock and command timeouts, separate health and rebuild connections, and a lock-wait alert. |

## References

- [Shared-filesystem hang diagnosis from inside the allocation](shared-fs-hang-diagnosis-from-allocation.md) — the same "accepts connections, gives no answer" symptom with a different cause. Rule that cause out first.
