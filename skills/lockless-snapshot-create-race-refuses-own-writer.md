---
name: lockless-snapshot-create-race-refuses-own-writer
description: "Repair an intermittent failure where concurrent writers refuse each other's first-created directory. Use when a lockless scope takes a state snapshot, an existence check compares the path to that snapshot, and a create by another thread lands between the snapshot and the check."
category: debugging
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - race-condition
  - check-then-act
  - stale-snapshot
  - concurrency
  - flaky-test
  - permission-error
  - fail-closed
  - idempotent-create
  - shared-filesystem
  - test-isolation
---

# A Lockless Snapshot Makes Concurrent First Creates Refuse Each Other

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-11-01 |
| **Objective** | Find why a concurrency test fails intermittently and a single malformed record blocks unrelated work. |
| **Outcome** | A scope that takes no file lock read a whole-directory trust snapshot, then compared a target path against that snapshot. Two writers both saw the target directory absent. Both created it. The loser then compared the directory, which now existed, to its own older snapshot, did not find it there, and refused it as untrusted. The same scope also raised on any single drifted entry, so one bad entry refused every unrelated operation. |

## When to Use

- A concurrency test fails intermittently with a permission or ownership refusal that names a directory the test itself just created.
- A scope reads a snapshot of a directory tree, then makes an existence or membership decision about one path under that tree.
- The scope takes no file lock, and two writers can create the same directory at the same time.
- A single malformed or drifted entry causes every unrelated entry to fail.

Do not use this for a case where the refusal is correct: a foreign-owned path that existed before the snapshot must still be refused. Read the snapshot semantics before you change the check.

## Verified Workflow

### Quick Reference

```python
# Before: a directory created after the snapshot is not IN the snapshot,
# so a concurrent first create is refused as untrusted.
existed = target.exists()
trusted = scan_tree(root)              # the snapshot; no lock is held
if existed and name not in trusted:
    raise PermissionRefused(target)
ensure_directory(target)
```

```python
# After: the snapshot decides only for paths that it could have observed,
# and the create path validates the directory that the create landed on.
existed = target.exists()
trusted = scan_tree(root)
if existed and name not in trusted:
    raise PermissionRefused(target)
ensure_directory(target)
if not existed:
    later = scan_tree(root)            # validate what actually landed
    if name not in later:
        raise PermissionRefused(target)
```

### Suggested Approach

1. Reproduce the failure and capture the state at the raise, not at the end of the test. Attach a trace hook that runs on exception, and print the fields that the check compares.
2. Compare those fields. A path that is absent from the snapshot, present with the correct mode and owner, and created after the snapshot started is a concurrent first create. It is not a foreign path.
3. Decide what the snapshot can prove. It can prove that a path existed and was not trusted. It cannot prove that a path was untrusted when the path did not exist during the scan. Use the second fact only for the first branch.
4. Keep the refusal for the first branch unchanged. Do not weaken the check for a path that the snapshot could observe.
5. Validate the created path after the create, so a directory that appeared between the snapshot and the create is still checked before any write publishes into it.
6. Separate per-entry refusal from whole-tree refusal. A scan that returns a trusted set must exclude a drifted entry and continue. Let each caller refuse the one entry it needs. Do not raise from the scan, because that refuses every sibling.
7. Prove the change with a test that fails without it. Create the directory between the snapshot and the create with a foreign owner, and assert the refusal plus no published write. Then assert that an unrelated entry still succeeds.
8. Run the concurrency test many times in sequence to confirm the removal of the intermittent failure.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | Run the failing test in isolation | It passed every time | A concurrency failure that needs a scheduler interleave is not evidence of a fixed test when a single run passes |
| 2 | Treat the intermittent test as the defect | The failing case only showed the shared helper's own refusal message | Read the raise message first. It named the helper, not the test |
| 3 | Patch the first scan the test could reach with a monkeypatch | The module imported the name directly, so the patch had no effect | Confirm that the patch target is the name the caller resolves |
| 4 | Make the new test pass by matching the message that the ensure step raised | The ensure step refused the directory with or without the fix, so the test proved nothing | A regression test must fail because of the missing change, not because of a pre-existing guard |

## Results & Parameters

- Symptom signature: the refusal names a directory with the correct owner and mode, and the directory is newer than the snapshot call.
- Fix shape: the pre-create check keeps the snapshot; the post-create check re-scans only when the path did not exist before.
- Scan shape: return a trusted set and exclude drifted entries. Do not raise from the scan.
- Verification: verified-local. The intermittent test passed eight sequential runs after the fix. The new race test fails with a different message without the change and passes with it.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| Internal service repository | A concurrent pool-load command and its supervisor shared one lockless directory-trust scope | The fix removed an intermittent failure in a concurrent-load test and a whole-deployment refusal from one drifted entry |

## References

- [related-skill](./architecture-shared-cache-repo-key-lock-vs-threadlocal.md) covers in-memory shared state that needs a lock or a per-key lock.
- [related-skill](./fix-flaky-glob-ordering.md) covers a different flaky cause: filesystem ordering.