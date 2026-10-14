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

## Second host measurement (2026-10-13)

Same class, second site, reached through a commit gate rather than a manual suite run.

| Probe | Result |
| ----- | ------ |
| Filesystem type under the default work root | `fuseblk` |
| `umask` | `0002` |
| Mode of a fresh file, `umask 0002` | `664` — group-write set |
| Mode of a fresh file, `umask 0022` | `644` — clear |
| Mode of a fresh file, `umask 0077` | `600` — clear |
| Mode of the resolved interpreter | `775` — group-write set on a pre-existing file |

The first table resolves a question the pin set alone could not. A FUSE work root
**honours the umask**; it does not force the group-write bit. Two independent
verification runs disagreed on this — one measured the lock failures clearing under
`umask 0022`, the other measured a fresh file as group-writable under the default
umask. A direct three-way probe settled it in favour of the first reading.

Measure the mechanism instead of inheriting either claim. Three `stat` calls under
different umasks cost less than one full-suite retry.

## The two blockers, separated

| Blocker | Created by | Cleared by `umask 022` |
| --- | --- | --- |
| Writer-lock files rejected for group-write | The process umask, at creation time | Yes |
| Attachment-program rejected for group-write | An existing file's mode on disk | No |

22 failures in the first class, 15 failures and 26 errors in the second. Only the
first is a pin problem. Reporting them as one "umask" cause sends the next reader
after a fix that cannot work.

## Gate observations

- Two unrelated changes on two branches were blocked by the same required hook in the
  same session. Neither touched a module in the failing files. The hook runs the suite,
  so one host-environment class blocked all commits.
- The lock class is what a test-only repair addresses, and a pre-commit hook evaluates
  the **working tree**. A staged test repair therefore unblocks its own gate even while
  the committed tree is still red. The apparent deadlock is not one.
- Hook runtimes degraded across attempts: the first took minutes, later attempts took
  far longer because concurrent suites from several sessions had saturated the host.
  Nothing about the gate changed between those attempts.

In a repository with concurrent sessions, `git stash` entries live in one repo-global
namespace shared by every worktree. A `stash pop` after a failed push applied another
session's stash (`stash@{0}` authored hours earlier on a different branch), and clean-merge
files landed silently in the worktree. A detached worktree from verified `origin/main`
(`git worktree add --detach <path> origin/main`) carries no such coupling and gives a
citable baseline commit for the PR record.
