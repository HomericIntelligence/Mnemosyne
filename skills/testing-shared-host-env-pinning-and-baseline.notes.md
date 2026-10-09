# Notes: Shared-Host Test Environment Pinning and Failure Baseline

Supporting evidence for `testing-shared-host-env-pinning-and-baseline.md`. Host paths,
usernames, and job identifiers are omitted; substitute site values.

## Host facts (probed 2026-10-08)

| Probe | Result |
| ----- | ------ |
| Login-shell `umask` on the shared compute/login host | `0002` (group-write on created trees) |
| Site scratch filesystem under the default job/local `TMPDIR` | `listxattr`/`setxattr` unsupported → `OSError: [Errno 95]` in ACL-checking tests |
| `/tmp` on the same host | xattrs supported |
| Repository tool binaries (`pre-commit`, linters) location | Repository virtual environment only; not on the login PATH |
| `uv run`-style one-shot opener | Rebuilds the execution `PATH`; results diverge from direct runs that reuse an exported `PATH` |

## Measured effect of the pin

| Run context | Environment | Result |
| ----------- | ----------- | ------ |
| Branch suite, login defaults | umask `0002`, scratch `TMPDIR` | 15 failures in permission/ACL-sensitive tests |
| Branch suite, pinned | umask `022`, `TMPDIR=/tmp`, repo env `PATH` | 59/59 passed; 61/61 after the final commit |
| Clean-HEAD baseline, pinned, same subset | same | Baseline failures reproduced and counted; the change's delta was zero environment failures |
| Hosted PR checks | — | Green throughout |

Two independent parallel sessions on the same host produced the same phantom set and the
same recovery, confirming environment causation rather than a code defect or a flaky suite.

## Skew observed between tool contexts

- A one-shot opener reported a green suite while direct runs in the exported-`PATH` shell were
  still red, and collected-set sizes differed (truncated versus full collection). Aligning
  `PATH` and the run directory made the contexts agree.
- Plain `git commit` from an unactivated login shell aborted inside the hook with a
  tool-resolution error; `PATH="$PWD/.venv/bin:$PATH" git commit ...` succeeded with hooks
  running.

## Why the baseline rule uses a scratch worktree

In a repository with concurrent sessions, `git stash` entries live in one repo-global
namespace shared by every worktree. A `stash pop` after a failed push applied another
session's stash (`stash@{0}` authored hours earlier on a different branch), and clean-merge
files landed silently in the worktree. A detached worktree from verified `origin/main`
(`git worktree add --detach <path> origin/main`) carries no such coupling and gives a
citable baseline commit for the PR record.
