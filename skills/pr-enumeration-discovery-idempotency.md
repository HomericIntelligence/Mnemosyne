---
name: pr-enumeration-discovery-idempotency
description: "Use when GitHub list commands silently truncate, bot PRs lack issue-closing links, automation creates duplicate PRs, bulk status discovery times out, planner and implementer skip semantics diverge, merged closing PRs leave zombie issues, soft-fail gh wrappers omit timeout/OS errors, or a stale local branch appears to contain already-merged work. Paginate exhaustive discovery, separate bulk identity from per-PR status, deduplicate by stable issue keys, verify merged state against fetched refs, and guard every creation phase."
category: ci-cd
date: 2026-06-15
version: "2.0.0"
user-invocable: false
license: BSD-3-Clause
history: pr-enumeration-discovery-idempotency.history
verification: verified-ci
tags: [github, pagination, pull-requests, idempotency, dependabot, discovery, merge-state, subprocess, zombie-issue, stale-branch]
---

# PR Enumeration, Discovery, and Idempotency

## Overview

Reliable PR automation separates exhaustive identity discovery, per-PR status lookup, and mutation.
It never treats a CLI default limit, branch naming convention, or issue state as complete evidence.
Every phase that can create work repeats the same idempotency gate.

This skill remains `verified-ci`. The reusable interfaces and failure modes are retained here;
project-specific incidents are indexed in
[the notes](./pr-enumeration-discovery-idempotency.notes.md), and the exact superseded content is in
[history](./pr-enumeration-discovery-idempotency.history).

## When to Use

- `gh pr list`, `gh issue list`, or `gh label list` returns exactly a suspicious default-sized set.
- “All PRs” logic uses a finite `--limit` or attempts unsupported `gh pr list --paginate`.
- Dependabot/Renovate PRs lack `Closes #N` and disappear from issue-keyed automation.
- A driver opens duplicate PRs or reconstructs a branch that already has a remote PR.
- A 50+ PR query requesting `statusCheckRollup` times out or returns an empty queue on error.
- BEHIND/BLOCKED PRs are classified as test failures instead of rebase candidates.
- A helper promises `[]`/`{}` on any lookup failure but a timeout or missing `gh` aborts the run.
- The planner spends work on an issue the implementer later skips due to an open PR.
- An issue remains open after a closing PR merged, or an operator receives a stale issue list.
- A guessed `<issue>-auto-impl` branch differs from the PR's real head or has a revert-shaped diff.

## Verified Workflow

### Quick Reference

```bash
# Exhaustive REST enumeration; follow Link headers and choose fields locally.
gh api --paginate 'repos/<owner>/<repo>/pulls?state=open&per_page=100' \
  --jq '.[] | {number,title,user:.user.login,user_type:.user.type,head:.head.ref}'

# Lightweight bulk identity list, then query expensive status per PR.
gh pr list --state open --limit 1000 --json number,title,headRefName
gh pr view <number> --json state,mergeStateStatus,statusCheckRollup,headRefName

# Resolve the actual branch; never derive it from the issue number.
gh pr view <number> --json headRefName --jq .headRefName

# Search open and merged closing PRs before planning or creating.
gh pr list --state all --search '<issue> in:body' \
  --json number,state,mergedAt,headRefName,url

# Verify API merge state against the remote and main content.
git fetch origin
git branch -r --contains <merge-or-head-sha>
git show origin/main:path/to/file
```

### 1. Enumerate without silent truncation

`gh <noun> list` defaults to a finite number of rows; `--limit` is still a cap. Use a sufficiently
large explicit cap only when the domain has a documented maximum and truncation is detectable. For
true exhaustive discovery, call `gh api --paginate` with `per_page=100` and deduplicate stable IDs.
Do not assume list subcommands accept `--paginate`.

For GraphQL, follow `pageInfo.hasNextPage`/`endCursor`. Record page and unique-row counts; repeated
cursors or duplicate IDs should fail rather than loop forever.

### 2. Union issue-linked and bot-authored PRs

Issue-driven discovery finds human PRs with closing references but misses dependency bots. Perform a
second paginated sweep and identify bots using API `user.type == "Bot"`, not a login suffix. Map each
bot update to a synthetic stable issue key derived from ecosystem plus normalized dependency identity,
then union it with issue-number keys. Keep the PR number as the value; key and value are not
interchangeable.

Deduplicate deterministically. If two open PRs claim one key, surface a conflict for operator review;
silently selecting newest or smallest can mutate the wrong branch.

### 3. Guard every mutation chokepoint

Before planning, implementation, branch creation, and `gh pr create`, call the same
`find_pr_for_issue(issue)` contract. A guard only in the implementer still wastes planner work. Search
all open PRs by closing reference and synthetic key, and check local/remote branch ownership.

Immediately before create, repeat the query because another actor may have opened a PR after the
initial discovery. If one exists, attach to or report it; do not overwrite its branch. A creation API
failure is not proof that no PR was created—re-query before retrying.

### 4. Keep bulk discovery light and fail loudly

Do not request `statusCheckRollup` for the entire queue when it triggers gateway timeouts. Fetch
number/title/head in bulk, then query status per PR with bounded concurrency and retries. Cache only
within the current snapshot.

A failed bulk query must raise or return an explicit error state, never `[]`: empty means “repository
has no matching PRs,” not “GitHub was unavailable.” For a deliberately soft-fail single lookup whose
documented contract is empty-on-failure, catch the complete subprocess boundary:

```python
except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError, ValueError):
    return {}
```

Include `ValueError` only when parsing is inside that boundary. Log enough context to distinguish
timeout, missing binary, command failure, and malformed JSON. Do not reuse a soft-fail contract for
the top-level queue discovery.

### 5. Classify state for routing

Use check conclusions for test health and `mergeStateStatus` for branch/ruleset health. A BEHIND or
BLOCKED PR is not automatically failing; route it to rebase/update or policy handling. Treat UNKNOWN
as indeterminate and refresh rather than green. Preserve distinctions among pending, failing,
behind, blocked, conflict, approved, and mergeable.

In the cited bulk synchronizer, a red MERGEABLE PR was treated as PR-specific failure only when
`mergeStateStatus == CLEAN`; every other red mergeable state was stale and routed to refresh/rebase.
Adopt that exact rule only when the repository state machine has the same semantics, but never
collapse branch staleness into test failure.

Avoid requesting expensive rollups until after identity pagination. This keeps a single pathological
PR from turning the whole queue into a silent no-op.

### 6. Verify merged state and close zombie issues

`gh pr view` reporting MERGED proves the API record, not that a local clone or remote tracking ref is
current. Fetch before reading `origin/main`, then verify the expected path/content or containing
commit. Before working any issue from a saved list, re-run `gh issue view`; a parallel merge may have
closed it.

Search merged PRs as well as open ones. When an unambiguously closing PR is merged and the issue is
still open, verify its content on `origin/main`, then close the zombie issue with a link to that PR.
Do not reimplement it.

### 7. Reject stale or guessed branches

Resolve `headRefName` from the PR API. Compare local, remote, and PR head SHAs before pushing. A local
issue-named branch with a large revert-shaped diff against current main is likely based before the
real merge. An `add/add` cherry-pick conflict on the target file is evidence that main already has the
work; abort the reuse path and inspect main instead of resolving by replacement.

### 8. Acceptance checks

1. Fixture data spanning multiple pages returns every unique PR exactly once.
2. Bot and issue-linked passes union without key/value confusion.
3. Timeout, command error, missing binary, and malformed JSON exercise the declared hard/soft policy.
4. Planner and implementer skip the same existing open or merged work.
5. Creation retry re-queries and cannot create a second PR.
6. BEHIND/BLOCKED routes separately from failing checks.
7. MERGED claims are verified after fetch against `origin/main`.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Trust defaults | Used `gh pr list` with no limit | Rows after the default cap vanished silently | Paginate the API for exhaustive discovery |
| Raise the cap | Used a large finite `--limit` as “all” | Growth can exceed any guessed cap | Detect bounds or use cursor/page iteration |
| One heavy query | Requested status rollups for 50+ PRs | Gateway timeout erased the queue | Enumerate identities first, fetch status per PR |
| Return empty on error | Converted top-level gh failure to `[]` | Automation treated outage as no work | Use explicit error state for required discovery |
| Catch one exception | Handled only `CalledProcessError` | timeout, missing executable, or bad JSON escaped | Match the documented subprocess boundary |
| Guard only creation | Planner still processed existing PRs | Skip semantics differed by phase | Reuse one guard before planning and implementation |
| Search only open PRs | Missed already-merged closing PRs | Zombie issues were reimplemented | Search all states and verify main |
| Guess branch names | Derived `<issue>-auto-impl` | Real PR heads differed; stale branches reverted main | Read `headRefName` and compare SHAs |

## Results & Parameters

| Parameter | Invariant |
| --- | --- |
| REST page size | `per_page=100`, follow all pages |
| Exhaustive identity | Stable PR/issue IDs, deduplicated |
| Bot discriminator | API `user.type == "Bot"` |
| Status strategy | Lightweight bulk list, bounded per-PR detail |
| Required-discovery error | Explicit failure, never empty-success |
| Soft lookup failures | command error, timeout, OS error, parse error as applicable |
| Mutation guard | Repeat before every planning/create chokepoint |
| Branch source | API `headRefName`, never a naming convention |
| Merge proof | API state plus fetched remote/main content |

## Verified On

- 2026-06-15 through the 2026-07 amendments: pagination, idempotency, state routing, planner
  skip-gating, and zombie-issue behaviors were exercised in CI-backed cases.
- Case references and precise evidence are in
  [the notes](./pr-enumeration-discovery-idempotency.notes.md).

## Companions

- [Case notes](./pr-enumeration-discovery-idempotency.notes.md)
- [Version history and exact superseded snapshot](./pr-enumeration-discovery-idempotency.history)
