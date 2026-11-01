---
name: testing-removed-exclusion-stale-concurrency-test
license: BSD-3-Clause
description: "Find and rewrite tests that assert the exclusion a removed file lock provided, before or after the lock-free change merges. Use when a change deletes `fcntl.flock`/`lockf` or another mutual-exclusion primitive from a guard, when a deletion issue mandates single-writer plus atomic publish instead of locks, when a concurrency test that passed on the base commit fails only at the change head through an event that is already set, when a merge gate stayed green because the test file sits in a nightly or otherwise unselected tier, or when a leaf-level bisect attributes a post-merge failure to the lock-removal commit so you can choose between restoring exclusion and rewriting the assertion."
category: testing
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-merge
tags:
  - lock-removal
  - flock
  - mutual-exclusion
  - stale-assertion
  - concurrency-test
  - leaf-bisect
  - tier-selection
  - nightly-only-gate
  - post-merge-regression
  - single-writer
---

# Testing Removed Exclusion Stale Concurrency Test

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Repair a test that depends on the mutual exclusion of a removed file lock, and detect the same dependency before a lock-removal change merges. |
| **Outcome** | Successful. The failure was attributed to one commit, the stale assertion was identified, and an operator decision on the replacement contract was recorded. |

A test that proves exclusion does two things without saying so. It starts a
second writer. Then it asserts that the writer cannot make progress while the
first one holds the guard, usually with a bounded wait on an event. When a
change deletes the underlying `flock`, `lockf`, or equivalent lock, the second
writer proceeds, the event is set early, and the assertion fails. The failure
is deterministic, not flaky, because the race the test relied on no longer
exists.

The failure is easy to miss at merge time. Such tests often live in a tier the
pull-request gate does not select, and they pass on the pre-change base. A
merge gate can stay green while the merged tree is red on that test.

## When to Use

Use this skill when one or more of these conditions apply:

- A change removes a lock primitive from a guard function, and call sites keep
  a `mode="exclusive"` and a `mode="shared"` argument that used to select the
  lock.
- A concurrency test passes on the base commit and fails at the change head,
  with a message like `assert not done.wait(0.1)` and `where True = wait(...)`.
- The test file is unchanged by the branch, so the change in behavior comes
  only from the source edit.
- The change merged with a green gate, and a local full run is red on one
  test that no pull-request shard selected.
- You must decide between restoring exclusion and rewriting the test, and the
  deletion issue states a policy such as "no file locks; use a single writer".

## Verified Workflow

### Quick Reference

```bash
# 1. Does the test depend on the base, or on the branch?
git worktree add --detach /dev/shm/cmp-base <base-sha>   # outside the repo
ln -s <repo>/.venv /dev/shm/cmp-base/.venv
(cd /dev/shm/cmp-base && uv run --locked --extra dev pytest "<test-id>" -q --no-cov -p no:randomly)

# 2. Rerun several times at the change head: deterministic is not flaky.
for i in 1 2 3 4 5 6; do uv run --locked --extra dev pytest "<test-id>" -q --no-cov -p no:randomly | tail -1; done

# 3. Attribute to a non-merge commit.
git log --oneline --no-merges <base>..<head>

# 4. Is the test selected by the pull-request gate?
grep -n "<test-file>" tests/test-tiers.yaml
```

### Suggested Approach

1. **Classify before you fix.** Run the test at the base commit and at the
   change head. Six runs at the head distinguishes a deterministic failure from
   a flaky one. If the test file is unchanged by the branch, the source edit is
   the only candidate cause.
2. **Attribute with a leaf bisect.** Build a scratch worktree at the base
   commit outside the repository, symlink the existing virtual environment, and
   check out single non-merge commits from the branch in order. Record pass or
   fail for each. Merge commits and squash history can hide the responsible
   commit.
3. **Read what the removed code did.** Compare the pre-change guard to the
   post-change guard. The removed block usually shows `LOCK_EX` for
   `exclusive`, `LOCK_SH` for `shared`, and a path predicate that already
   skipped the lock on shared storage. The test almost always depends on the
   `exclusive` half.
4. **Check tier selection.** Search the tier inventory for the test file. A
   module under a nightly list or a suite-only runner is not part of the merge
   gate. Say so explicitly, because it explains why the gate was green.
5. **Choose the contract with the owner, not alone.** Two repairs exist:
   restore exclusion for the case the test needs, or keep the code lock-free
   and rewrite the test. The second option weakens a safety property that
   other call sites may rely on for compare-then-write sequences. When an issue
   or an owner states a policy, follow it. When neither does, record a
   decision request with the call sites that need serialization.
6. **Rewrite to the guarantees that remain.** Remove the assertion that the
   second writer is blocked. Keep assertions that still hold: the durable
   pointer is unchanged, the operation ends with its own preflight error, and
   the target artifact is not published. Add a short comment that names the
   removed mechanism so a future reader does not reintroduce the wait.
7. **Run the file, then the tier it lives in.** A focused pass is not proof.
   Run the whole module and the tier command that owns it, with the same
   environment the gate uses.

Keep the write bounded. Change the test that pins the removed exclusion, and
the source only when the chosen contract restores behavior.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | ---------------- | --------------- | --------------- |
| Treat as flaky | Reran the failing test a few times and planned a rerun strategy | Six consecutive failures showed a deterministic contract change, not a race | Count runs first; a stable failure points to a removed mechanism |
| Blame the latest commit | Assumed a recent fix commit caused the failure | The responsible commit was an earlier "slice" commit in a long series; the latest commit only exposed it in a full run | Bisect non-merge commits, do not infer from position in the log |
| Trust the green gate | Accepted the passing pull-request checks as evidence the test still held | The module sat in a nightly tier that the gate never selected | Cross-check the tier inventory for every test that asserts a removed mechanism |
| Weaken silently | Considered changing the test without recording why the guarantee disappeared | The test guarded a compare-then-write sequence at several call sites | Record the decision or the operator ruling with the test change |

## Results & Parameters

### Configuration

```yaml
# Settings used to reproduce and classify
tmpdir: /dev/shm/private-tmp          # outside any group-writable parent
pytest_args: ["-q", "--no-cov", "-p", "no:randomly"]
runs_for_determinism: 6
scratch_worktree: outside the repository, with a symlinked virtual environment
```

### Expected Output

- Base run: `1 passed`.
- Head runs: `1 failed` in each of six runs, with an assertion on a bounded
  wait that is already satisfied.
- Bisect: the first failure appears at the commit that removes the lock call.
- Tier lookup: the test file is absent from the pull-request module list.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| A Python service on shared storage | A lock-removal series merged with a green gate; one concurrency test in a nightly module failed deterministically on the merged tree and passed on the base | Bisect and evidence details in [notes](testing-removed-exclusion-stale-concurrency-test.notes.md) |

## References

- [ci-test-partition-new-modules](ci-test-partition-new-modules.md) — tier
  inventory that decides whether a module runs in the merge gate
- [testing-deterministic-clock-vs-thread-sleep-classification](testing-deterministic-clock-vs-thread-sleep-classification.md) —
  classifying timing assertions, the nearest neighbor for wait-based tests
- [testing-retired-lever-inertness-guard](testing-retired-lever-inertness-guard.md) —
  proving a retired mechanism cannot return
- [testing-authority-subtraction-surrogate-repoint](testing-authority-subtraction-surrogate-repoint.md) —
  the sibling repair when a removal breaks a test through a registration check