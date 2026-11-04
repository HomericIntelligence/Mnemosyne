---
name: rolled-back-transaction-replay-of-a-failing-operation
license: BSD-3-Clause
description: "Find which database statement makes an operation return a generic conflict, by replaying it inside a transaction that you roll back. Use when: (1) a service maps several constraint violations to one refusal such as conflict, (2) logs and the client show no cause, (3) you can reach the database but must not change production state, (4) a partial unique index or a foreign key may block a step that looks innocent."
category: debugging
date: 2026-10-29
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [database, transaction, rollback, savepoint, constraint, unique-index, foreign-key, diagnosis, conflict]
---

# Replay a Failing Operation in a Rolled-Back Transaction

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Name the exact statement and constraint behind a generic refusal, without a durable change. |
| **Outcome** | Operational. A key rotation returned `conflict` for two real users. Two replays, one through the real code and one statement by statement, showed three separate causes: a foreign key on a value the server did not know, a partial unique index that did not block the insert but blocked the final state change, and a catch-all that mapped all of them to the same result. Production state was identical before and after each replay. |

A service that catches `CheckViolation`, `ForeignKeyViolation` and `UniqueViolation` together and
returns one result hides which rule failed. The failing statement is often not the one that looks
guilty: a partial unique index can accept an insert and refuse a later update.

## When to Use

- The operation returns `conflict`, `refused` or a similar single outcome with no reason.
- The constraint set includes partial unique indexes, check constraints or foreign keys.
- You have read and write access to a database where a mistake is costly.

## Verified Workflow

### Quick Reference

```python
class Rollback(Exception): ...

try:
    async with conn.transaction():           # outer transaction, never committed
        result = await store.operation(...)  # the REAL code path
        print(result.outcome, await states(conn))
        raise Rollback                       # leaving the block rolls everything back
except Rollback:
    pass
print(await states(conn))                    # must equal the state before the call
```

### Suggested Approach

1. Read the state first (read-only): the rows the operation touches, with non-secret columns only
   (ids, states, flags, the scope parts of a hash, never the hash or a key).
2. Call the real operation inside an outer transaction and raise a sentinel at the end so that
   the transaction rolls back. Print the state before, inside and after. A `conflict` with an
   unchanged inside-state means the operation rolled itself back.
3. If the cause is still hidden, replay the operation's statements one by one. Wrap each statement
   in its own nested transaction (a savepoint) and print only the exception class, the SQLSTATE and
   the constraint name. A failed statement then does not poison the later ones.
4. Read the migration that defines the failing constraint, and write the rule in plain words
   (for example: "one active key per user and cluster; a pending row does not count").
5. Fix the operation for each cause, and make the service log the constraint name (no values) so a
   later failure is not silent. Run the replay again: the outcome is now a success, the state
   inside shows the intended change, and the state after is unchanged.
6. Replays take row locks for a short time and consume sequence values. Do them on one user at a
   time, and never print key material or connection strings.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Read the service log | Looked for the reason in the supervisor log | The code maps three violation types to one result and logs nothing | Reproduce the call and print the exception class and constraint name |
| Replay the insert twice in one script | A statement-by-statement replay inserted the same new key in step 1 and again in step 4 | Step 4 failed on the primary key, a false failure that my own replay caused | Remember that the transaction sees its own earlier writes; reuse no key in two steps |
| Trust the obvious blocker | Expected the unique index to block the insert | The index covers only acknowledged rows; the pending insert succeeded and the final acknowledge failed | Test each statement; the failing one can be the last |

## Results & Parameters

### Configuration

```yaml
isolation: outer transaction raised to roll back; savepoints for single statements
print: ids, states, exception class, SQLSTATE, constraint name
never_print: keys, hashes, connection strings, passwords
check: state after rollback equals state before
```

### Expected Output

One line per statement such as `3 revoke other active key OK UPDATE 1` or
`4 insert new key FAILED (UniqueViolationError, 23505, <constraint>)`, and a final line that
shows the unchanged active set.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A scheduler-managed model-serving deployment | Credential rotation on production, 2026-10 | Two users replayed; three causes found; no production change. |

## References

- [silent-service-routine-run-once-with-logging](silent-service-routine-run-once-with-logging.md) — reproduce a silent routine outside the service
