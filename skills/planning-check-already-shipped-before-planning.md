---
name: planning-check-already-shipped-before-planning
description: "Use before planning follow-up, extraction, migration, or closeout work whose issue cites paths, counts, tests, or future-state acceptance criteria. Verify origin/main and every local worktree before assuming work remains; map each criterion to a command; establish the provenance of red tests before calling them unrelated; and emit a forward-looking closeout plan when implementation already exists. Split sibling-repository changes into their own PRs and reconcile every repeated count from one measured source."
category: architecture
date: 2026-06-19
version: "2.0.0"
user-invocable: false
license: BSD-3-Clause
history: planning-check-already-shipped-before-planning.history
verification: verified-local
tags: [planning, already-shipped, stale-premise, extraction, migration, provenance, closeout, cross-repo, acceptance-criteria, replan]
---

# Planning: Check If Already Shipped Before Writing a Plan

## Overview

An issue describes a past snapshot, not necessarily the current tree. Before designing work, prove
whether the requested behavior is absent, already merged, or present as uncommitted work in another
worktree. A shipped implementation changes the deliverable from reimplementation to a
forward-looking verification-and-closeout plan; it does not eliminate the need for a plan.

The operational rules are retained here. Session transcripts and case-specific counts are in
[the notes](./planning-check-already-shipped-before-planning.notes.md); the exact superseded skill is
in [history](./planning-check-already-shipped-before-planning.history). Verification remains
`verified-local`: the provenance and investigation commands were exercised, while cited downstream
plans and sibling-repository CI retain their documented evidence limits.

## When to Use

- An issue requests an extraction, migration, decomposition, consolidation, or follow-up filed
  before recent merges.
- It cites exact paths, line/method counts, or acceptance criteria phrased as future work.
- A target module already exists, the source directory is absent, or the named symbol moved.
- `git status` or `git worktree list` reveals sibling work that `git log` cannot see.
- A reviewer rejects a plan as a retrospective status note or as relying on false provenance.
- Tests are red and someone proposes dismissing them as unrelated or from another branch.
- A plan touches `../OtherRepo/` or claims another repository's CI is green.
- The same count appears in multiple sections, or the issue's estimate differs from disk.
- A long-running check tempts the author to emit an empty or placeholder plan artifact.

## Verified Workflow

### Quick Reference

```bash
# Synchronize and inventory all possible sources of truth.
git fetch origin
git status --short
git worktree list
git log --oneline -20 origin/main

# Measure and locate rather than trusting issue prose.
wc -l path/to/file.py
grep -cE '^\s+(async )?def ' path/to/file.py
grep -rn '<SymbolOrBehavior>' --include='*.py' .

# Prove whether an artifact and its wiring belong to HEAD or local WIP.
git cat-file -e HEAD:path/to/test.cpp
git status --short path/to/test.cpp path/to/CMakeLists.txt
git show HEAD:path/to/CMakeLists.txt | grep '<test-name>'

# Verify a merged closing PR and the actual main-branch content.
gh pr list --state all --search '<issue-number> in:body' \
  --json number,state,mergedAt,url
git show origin/main:path/to/file | grep '<acceptance-marker>'
```

### 1. Freeze the evidence boundary

Record `git rev-parse origin/main`, the issue update time, repository status, and worktree list.
Search open and merged PRs by issue number and key symbols. A local branch name or a GitHub issue's
open state does not establish that work remains. Re-fetch before making the final determination.

Inspect every worktree. `git log` cannot reveal an uncommitted implementation in a sibling checkout.
For each candidate, compare status, branch, base, and the relevant paths. Never overwrite or absorb
uncommitted work while performing this read-only investigation.

### 2. Test the issue premise cheaply

Run existence, absence, and symbol searches before a full build:

```bash
find <target>/src -type f -name '*.<ext>'
test ! -d <source>/src/<moved-dir>
grep -rl '<MovedSymbol>' <source> <target>
git diff --stat origin/main...HEAD
```

Measure cited LOC, methods, files, and generated artifacts directly. Store each measurement once and
reuse it throughout the plan. If the issue estimate differs, state both the estimate and the current
measurement; do not silently mix them.

### 3. Map acceptance criteria to evidence

Create a table with one row per acceptance criterion: current observation, exact command, expected
result, evidence boundary, and remaining action. Build and run the actual suite needed by “CI passes”;
file presence alone proves only structure. Account for feature guards such as `#ifdef`, optional
dependencies, test labels, and generated code. A green subset is not full-suite evidence.

Read repository wrappers before adding arguments. In the cited Python case, `pixi run mypy` already
targeted the whole tree, so adding paths created duplicate modules; ad-hoc pytest subsets needed
`--no-cov` to avoid interpreting an aggregate coverage gate as a test failure. These flags are
repository-specific, but verifying the wrapper's argv contract is mandatory.

When work is already present, test the current tree and, when relevant, `origin/main`. Distinguish:

- **merged:** present at immutable `origin/main` SHA;
- **local WIP:** present only as tracked/untracked changes in a worktree;
- **partially shipped:** structural criterion passes but runtime/integration criterion does not;
- **not shipped:** requested artifact and equivalent behavior are absent.

### 4. Establish provenance before disposing of failures

A failing test is not “someone else's branch” merely because its source file is untracked. Inspect
the test, build wiring, generated registrations, and configuration separately. An untracked test
whose `CMakeLists.txt` entry is a modified local line is current-tree WIP and can affect the real
build. A correct scope conclusion supported by a false provenance claim is still a planning defect.

Use `git cat-file -e HEAD:<path>` for tracked-at-HEAD status, `git status --short <paths>` for `??`
versus `M`, and `git show HEAD:<wiring>` to compare committed wiring. Then either include the failure,
exclude the WIP from the deliverable without discarding it, or route a real pre-existing defect to a
separate issue with evidence.

### 5. Reframe shipped work as a forward-looking plan

Do not submit a retrospective list of what already happened. Plan remaining actions with named
actors and gates, for example:

1. Re-verify the immutable base and every criterion.
2. Correct documentation, ADR/index attribution, stale issue language, or missing tests.
3. Run the scoped and repository-required checks.
4. Publish evidence and close or update the issue only after gates pass.

Run gates yourself; “reviewer will verify” is a stage handoff, not a plan. Emit the complete artifact
from the evidence available at the deadline. If a long job is pending, mark that row pending and
provide the rest; an empty placeholder is not a plan.

### 6. Preserve repository and PR boundaries

A change in `../OtherRepo/` requires a branch and PR in that repository. A local build of the sibling
does not prove its hosted CI; use `gh pr checks --repo <owner>/<other> <pr>`. Keep red local WIP out
of a closeout/docs commit, run the labels that cover the deliverable, and route unrelated defects
without claiming they are green.

### 7. Final consistency audit

Immediately before publishing, re-fetch and re-run the cheap checks because another PR may have
merged during planning. Reconcile all counts, paths, SHAs, issue/PR states, and test totals. Ensure
every “already shipped,” “unrelated,” and “CI passes” statement names its precise evidence boundary.
If code comments attribute work to an ADR, open the ADR itself; comments are not provenance proof.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Trust the issue snapshot | Planned against cited paths and counts | Later merges had moved or completed the work | Measure current disk and `origin/main` first |
| Search only commit history | Concluded no fix existed from `git log` | Uncommitted sibling-worktree changes were invisible | Inventory worktrees and status |
| Submit a status note | Listed what had already shipped | It contained no actor-owned future steps or gates | Reframe as verification-and-closeout |
| Emit a placeholder | Withheld the plan while a background test ran | The required artifact was empty at handoff | Publish complete known evidence and mark the one pending gate |
| Dismiss red tests by assumption | Called an untracked test foreign WIP | Modified committed wiring made it part of the current build | Prove source and wiring provenance independently |
| Bundle sibling-repository work | Edited `../OtherRepo/` from the current PR | A branch cannot deliver changes to another repository | Create a separate PR and verify its hosted checks |
| Repeat remembered counts | Different sections used different totals | Reviewers could not tell which snapshot was authoritative | Measure once and reconcile everywhere |

## Results & Parameters

| Decision | Required evidence |
| --- | --- |
| Work is merged | Immutable `origin/main` SHA plus source/behavior check |
| Work is local only | Worktree path, branch, and `git status --short` |
| Migration is complete | Destination present, source absent, residual-symbol search, build/tests |
| Failure is unrelated | HEAD/local provenance plus a separately routed owner/issue |
| Cross-repo CI is green | `gh pr checks` in that repository |
| Count is authoritative | One runnable command and one recorded result reused throughout |
| Closeout is ready | All mapped criteria and repository-required checks pass |

## Verified On

- 2026-06-19 through the 2026-07 amendments: provenance, worktree, and extraction-premise
  investigations were exercised locally (`verified-local`).
- Individual case outcomes and limitations are indexed in
  [the notes](./planning-check-already-shipped-before-planning.notes.md).

## Companions

- [Case notes](./planning-check-already-shipped-before-planning.notes.md)
- [Version history and exact superseded snapshot](./planning-check-already-shipped-before-planning.history)
