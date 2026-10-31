# Notes: reconcile-before-retry-mutation-status-loss

## Incident evidence

An agent delegated an automated repository-cleanup command (merged-branch removal plus worktree
audit) through a required wrapper. The wrapper's contract forbids parsing or replacing the
delegated output, and the terminal exit status is the only accepted completion signal. The agent
shell displayed the run, but the output was truncated mid-stream: the last visible line was an
in-progress message, and the exit-status line was never observed.

The agent did not re-run immediately. It reconciled the repository with read-only checks:

```bash
git status --short                                  # clean tree
git rev-list --left-right --count main...origin/main  # 0/0, synced
git worktree prune -vn                              # no stale metadata candidates
git branch --merged main | grep -v main             # one branch, marked checked-out
git worktree list                                   # metadata consistent for all entries
```

Classification: consistent. Merged branches that were not checked out in a worktree were gone
(the first run had deleted them); the one remaining merged branch was checked out in a live
worktree, which the tool's safeguards intentionally skip. No stale worktree metadata remained.

Because the tool is guarded (it refuses closed on a dirty tree and skips items that are already
correct), repetition preserves work. One bounded re-invocation produced the terminal status:
exit 0, with the tool's own no-failures completion message. Total: one unknown result, one
reconciliation, one re-invocation, terminal status observed.

## Why the classification mattered

- Had the tree shown pending removals, the safe path would still have been a single re-run,
  because this tool's guards make repetition work-preserving.
- Had the battery contradicted both outcomes (for example, half-removed refs plus failing
  invariants), the correct action would have been to stop and report, not to retry.
- For a command without guards or idempotence (for example, a raw scripted delete), only the
  consistent-complete branch permits closure; every other branch stops for a human decision.

## Generic reconciliation batteries

Git-oriented mutations:

```bash
git status --short
git rev-list --left-right --count HEAD...@{upstream}
git worktree prune -vn
git branch --merged HEAD
```

Other domains:

- Prefer the tool's own dry-run or status mode; a supported dry run is the cheapest probe.
- Prefer an idempotent read endpoint (for example, an object inventory or a state listing) over
  parsing a partial mutation log.
- Check domain invariants that a completed run must satisfy (counts, presence or absence of
  named objects) rather than inferring from log completeness.

## Traps that this rule prevents

- Harness truncation hides execution, not commands: the process ran even where the display cut
  off.
- A refusal on the second run is not evidence that the first run failed; guarded tools refuse on
  completed or invalid preconditions.
- "It probably worked" is not a terminal status. Either observe the status (one bounded
  re-invocation) or record it as unobserved with reconciliation evidence.

## Post-version evidence: runtime restarts during an ordered write sequence

During a knowledge-corpus amend delivery in a hosted agent fleet, the runtime restarted six times
across an ordered sequence of five file edits, validation, a signed commit, a push, and a
pull-request create. After each restart a per-step sentinel battery classified state before any
re-application:

```bash
git rev-parse --abbrev-ref HEAD              # correct staging branch
git status --porcelain                       # which files carry writes
grep -c '<unique string per edit>' <file>    # per-edit applied (1) vs pending (0)
```

Each edit whose sentinel was absent re-applied cleanly; each already-applied edit would have
failed closed on its exact-match anchor. The final corpus validator passed on the full corpus and
the privacy scan passed, proving no step was dropped or applied twice.

The pull-request create returned HTTP 502. The existence battery for that step is artifact
discovery (list pull requests for the staging branch, or search by title): an unverified blind
retry can create a duplicate, because create endpoints are not guarded. One bounded retry after a
short wait succeeded with no duplicate.

A worktree-preparation helper also refused to create the staging branch because a stale, fully
merged branch already owned the exact name. Recovery: verify the existing branch's ancestry
(`git merge-base --is-ancestor <branch> <default>` showed it fully merged), leave it untouched,
and stage the work on a slug-suffixed branch name. Do not delete or reset the foreign branch.
