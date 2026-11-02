# Notes: Testing Removed Exclusion Stale Concurrency Test

Supporting evidence for
[testing-removed-exclusion-stale-concurrency-test.md](testing-removed-exclusion-stale-concurrency-test.md).
Identifiers are generalized. No internal paths, hostnames, or account details
are recorded.

## Measured case

One source tree removed file locks across many modules over a commit series.
Each series step was a separate non-merge commit. The final merge used a squash
commit.

Measurements:

| Step | Command shape | Result |
| --- | --- | --- |
| Base commit | single test id, `-q --no-cov -p no:randomly` | `1 passed`, repeated 2 times |
| Change head | same | `1 failed` in 6 of 6 runs |
| Head, full file | whole module | same single failure |
| Scratch base worktree | base commit, symlinked venv | `1 passed` |

The failure text was:

```text
>   assert not activation_done.wait(0.1)
E   assert not True
E    +  where True = wait(0.1)
E    +    where wait = <threading.Event at 0x...>.wait
```

The `Event` was already set when the assertion ran. The second writer had
completed, so the test measured a guarantee that no longer existed.

## Bisect result

A leaf bisect over successive non-merge commits gave a clean boundary:

| Commit position | Result |
| --- | --- |
| Preceding commit | `1 passed` |
| Candidate removal commit | `1 failed` |
| Later commits | `1 failed` |

The removal commit's message named the change directly: it dropped the lock
from a guard and kept an anchor file for descriptor validation only.

## What the removed code did

The deleted block had this shape:

```python
shared = is_shared_fs(context.root)
operation = fcntl.LOCK_EX if mode == "exclusive" else fcntl.LOCK_SH
if not shared:
    flock_bounded(fd, operation, timeout_s=ADMIN_LOCK_TIMEOUT_S)
```

The replacement kept the anchor file, took no lock, and documented "no mutual
exclusion exists between deployment mutations" as residual risk. After the
change, `is_shared_fs` had no remaining callers in the source tree.

## Why the gate stayed green

The test module was listed under the nightly tier of the tier inventory, not
the pull-request tier. The gate therefore never selected it. The merged tree
was red on that test while the gate was green.

Push runs on the default branch also failed, but on unrelated modules. So a
red default branch was not by itself proof of this regression; the specific
test had to be run.

## Alternatives considered

| Option | Content | Why it was not chosen by the driver |
| --- | --- | --- |
| Restore node-local exclusion | Reintroduce a bounded lock for the node-local case, keep shared roots lock-free | Contradicts a stated "no file locks" policy; the lock helper had already been removed from the shared module and a policy test forbids its name |
| Keep lock-free, rewrite the test | Remove the blocked-writer assertion; keep pointer-unchanged and error assertions | Chosen after the owner confirmed the policy |
| Split the work | Land the removal, schedule the guard redesign separately | Viable, but the test still fails on the default branch until the rewrite lands |

## Follow-up contract for the rewrite

The durable guarantees that survived the lock removal were:

- the active release pointer is unchanged while the target release is not fully
  activated;
- the operation ends with its own preflight error type, not with a shared lock
  error;
- the target artifact is byte-identical to its pre-operation content.

These became the replacement assertions. The blocked-writer wait was deleted,
with a comment naming the removed mechanism.

## Environment note

Local service-path checks rejected a temporary directory under a group-writable
parent. The fix was to point the test runner at a private directory on a local
tmpfs. This is a test-environment concern, unrelated to the lock removal, but
it hid the failure during earlier runs.