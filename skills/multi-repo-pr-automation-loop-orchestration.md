---
name: multi-repo-pr-automation-loop-orchestration
description: "Run and diagnose PR automation across repositories without false success, scope leakage, stale-report fixes, or branch races. Use for organization sweeps, explicit issue/PR targets, sequential merge ordering, direct-PR terminalization, blocked-check classification, and reconciliation of automation reports with live GitHub state."
category: ci-cd
date: 2026-07-24
version: "2.0.0"
license: BSD-3-Clause
verification: verified-local
user-invocable: false
history: multi-repo-pr-automation-loop-orchestration.history
tags: [multi-repo, pr-automation, github, orchestration, live-state, scope, merge-queue]
---

# Multi-Repo PR Automation Loop Orchestration

## Overview

An automation summary is not proof that a remote PR changed or merged. Correct orchestration binds
every numeric target to one repository, keeps work sequential within a repository, observes terminal
GitHub state before branch operations, and reconciles local checkpoints with live PR heads and
checks.

Detailed campaigns and project-specific evidence are in
[`multi-repo-pr-automation-loop-orchestration.notes.md`](multi-repo-pr-automation-loop-orchestration.notes.md).
The complete prior source is in
[`multi-repo-pr-automation-loop-orchestration.history`](multi-repo-pr-automation-loop-orchestration.history).

## When to Use

- A loop skips PRs, silently no-ops, reports success with open failures, or never arms auto-merge.
- Work spans three or more repositories but merges in each repository share one advancing base.
- An organization source is combined with repository-local issue or PR numbers.
- A direct PR may already be merged/closed or its head branch may have been deleted.
- `BLOCKED` could mean pending checks or a stable review/protection gate.
- A completed sweep report is old enough that its state or root-cause claims may have drifted.
- Historical failed attempts make a later successful logical item appear red.

## Verified Workflow

### 1. Discover safely and bind numeric identity

Enumerate unarchived repositories dynamically and reject an empty result as a discovery failure,
not “nothing to do.” Use paginated APIs for completion gates:

```bash
gh repo list <org> --json name,isArchived
gh api --paginate '/repos/<owner>/<repo>/pulls?state=open&per_page=100'
```

Issue and PR numbers are repository-local. A direct `--issues N` or `--prs N` request requires
exactly one explicit repository. Reject zero or multiple repositories before organization
materialization or API discovery. Resolve a per-target-repository GitHub accessor at the boundary;
never let direct scopes fall back to the current working repository.

### 2. Reconcile stale inputs with live state

Before planning a report-prescribed action, query each named PR at its current head:

```bash
gh pr view <pr> --repo <owner>/<repo> \
  --json state,headRefOid,mergeStateStatus,statusCheckRollup,autoMergeRequest
gh run view <run> --repo <owner>/<repo> --log-failed
```

Read any report-named file at the PR ref and fetch the latest failing log. A still-failing PR does
not prove the report’s diagnosis. Verify every “already merged” scope reduction with a per-PR state
loop. Query the target repository’s live protection/ruleset before attributing `BLOCKED` to review.

Classify `BLOCKED` only after required-check inspection:

- failing required checks: CI work;
- pending required checks: keep polling;
- zero failing and zero pending: stable review/protection gate; leave armed and return without a CI
  fix.

### 3. Drive one PR honestly

For a disposable automation worktree, synchronize to `origin/<head>`, record pre-agent HEAD, run the
agent, and require a changed post-agent HEAD before pushing. Push with explicit
`HEAD:<head-branch>` and preserve that refspec on any force-with-lease retry. Agent completion alone
is not evidence of a commit.

After a fix, re-run check → arm → terminal wait once. Poll with bounded exponential backoff and
distinguish `MERGED`, `CLOSED`, `FAILING`, `DIRTY`, `BLOCKED`, and `TIMEOUT`. An open PR with
`autoMergeRequest` is armed/pending, not failed. A `DIRTY` PR enters the explicit rebase/conflict
path. A session-ID collision gets bounded retries then a fresh ID; it is not a terminal condition.

Do not skip an existing open PR merely to avoid clobbering it. Synchronize its worktree, enter the
review/remediation loop, and advance only after the terminal implementation-state label is present.
An early return before review/labeling leaves a green PR permanently unarmed. Conversely, never
commit a synthetic blocker file just to force agent engagement; report the blocker as state.

### 4. Terminalize direct PRs before branch adoption

Use one helper before head lookup, worktree adoption, CI routing, or implementation routing:

```text
state MERGED or truthy mergedAt -> PASS
state CLOSED                    -> FAIL
missing/open state              -> continue normal routing
```

GitHub may delete a merged head branch. Branch work after terminal state converts a successful
external result into a false local failure. Compute summaries, exit codes, and preserved-worktree
guidance from the latest effective logical item; filter stale and nonexistent entries.

### 5. Preserve requested scope

For an `--issues`-scoped run, discovery, bot-PR inclusion, arming, and the done gate must all use the
selected PR set. Repository-wide discovery remains valid only for an unscoped backlog sweep. Test
this by poisoning ambient/current-repo helper functions and asserting every queued item retains its
explicit repository.

### 6. Order merges and verify outcomes

Parallelize across independent repositories. Within one repository, merge oldest/lowest dependency
first, rescan after each base advance, and cap each pass. Use the repository’s allowed merge method:

```bash
gh api repos/<owner>/<repo> --jq '{allow_squash_merge,allow_rebase_merge,allow_auto_merge}'
gh pr merge <pr> --repo <owner>/<repo> --auto --squash
```

Do not infer successful arming. Query `autoMergeRequest`, head SHA, checks, and final state. If a
local process was interrupted after a live merge, pair the GitHub merge proof with a dry-run that
reclassifies the item as terminal PASS.

### 7. Report reality, not banners

For every claimed push, verify the remote head changed inside the run window. For every “driven”
repository, compare the summary with the live paginated open-PR set. Decompose failures into real
crashes, no-new-commit, architectural discovery gaps, and noisy done gates. Report a
reality-versus-claim table rather than copying the driver banner.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Bare push | Used `git push origin HEAD` | Could update a stray branch | Push `HEAD:<expected-head>` explicitly |
| Agent-return proof | Treated session return as work | Resume may produce no commit | Compare pre/post HEAD |
| Open-is-failed | Failed every open PR | Armed queue entries are legitimately pending | Inspect auto-merge and terminal states |
| Eager blocked exit | Exited on every `BLOCKED` | Pending checks also appear blocked | Require zero failing and zero pending checks |
| Org numeric scope | Used repo-local number across an org | Number may resolve in wrong repo | Require exactly one explicit repository |
| Post-merge adoption | Continued a merged direct PR | Deleted branch lookup failed after success | Terminalize before branch lookup |
| Parallel same-base merge | Merged siblings concurrently | Each merge invalidated the rest | Serialize within repo; parallelize across repos |
| Stale diagnosis | Trusted report-prescribed cause | Fix existed or cause was wrong | Read current head and latest failed log |
| Historical status | Counted every prior attempt | Superseded failure poisoned final state | Summarize latest logical item only |
| Substring dedup | Searched issue text by substring | `#4` matched `#44` | Parse exact closing-keyword references |

## Results & Parameters

```text
organization and explicit repository set
direct issue/PR targets and scope-validation result
PR number, expected head branch, pre/post/remote head SHA
required checks: failing, pending, completed
merge state, auto-merge state, terminal outcome
allowed merge methods and per-repo ordering
poll deadline/backoff and retry budget
latest logical item and preserved-worktree state
summary claim versus live GitHub evidence
```

## Verified On

- ProjectHephaestus driver hardening, scoped runs, target-repo accessors, blocked early exit, and
  direct-PR terminalization through 2026-07-24.
- Cross-repository sweeps verified local and in CI as classified in the notes; compaction preserves
  `verified-local` without upgrading pending or plan-only cases.
