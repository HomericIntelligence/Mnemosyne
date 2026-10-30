---
name: dirty-worktree-batch-pr-shipping
description: >-
  Turn a batch of dirty or uncommitted worktrees (automation lanes, stale checkouts, interrupted
  sessions) across one or several repositories into pushed branches and open PRs, or into skips
  with recorded evidence. Use when the user asks to "create PRs for the dirty trees", during
  cleanup after a wide lint/triage pass, or when lane worktrees hold work that has no branch head
  on a remote.
category: tooling
date: 2026-10-14
version: "1.0.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
tags: [git, worktree, dirty, uncommitted, batch-pr, novelty-gate, coherence-gate, mid-merge,
  shared-checkout, pr-policy, closes-line, split-issue, merge-tree, hash-object,
  content-constraint, reconciliation]
---

# Dirty Worktree Batch PR Shipping

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-14 |
| **Objective** | Ship every dirty worktree that holds unique work as a PR, and skip the rest with evidence. Do not push junk, do not interfere with active lanes, and do not break repo PR policy. |
| **Outcome** | Operational. One run over three repositories: 5 PRs opened and pushed (#3458 merged same day; #2489, #3403, #3404, draft #3402), 7 trees skipped with recorded evidence, zero policy-gate failures after one body-format repair round. |

Case evidence is indexed in
[`dirty-worktree-batch-pr-shipping.notes.md`](dirty-worktree-batch-pr-shipping.notes.md).

## When to Use

- The user asks to turn "the dirty trees", leftover lanes, or uncommitted session work into PRs.
- A cleanup pass (for example a tidy run) reports dirty worktrees whose branch content is
  already on trunk.
- Worktrees from another actor (automation pipeline, codex campaign, older session) show staged,
  unstaged, or untracked changes and it is not clear whether the work shipped elsewhere.
- A batch spans more than one repository, so PR and issue lookups need a pinned repository each.
- An earlier batch attempt was interrupted (server restart, agent abort) and must resume without
  duplicating commits or PRs.

## Verified Workflow

### Quick Reference

Per worktree, in this order. A `NO` at any gate moves the tree to the skip list with evidence.

```text
1. STATE     git status (full output)          mid-merge or foreign-actor merge?  -> skip, do not conclude it
2. PIN       query PR/issue against a literal  wrong repo? [] on a repo that must -> do not trust the empty set
             --repo <org>/<name>               exist?
3. NOVEL     hash worktree file vs             content already on trunk?           -> skip (superseded)
             git show origin/main:<path>
4. COHERE    per-artifact gate (table below)   red PR predictable?                 -> skip or fix first
5. SCREEN    grep the diff for boundary terms  term found but forbidden?           -> skip
6. SHIP      commit -s, push, gh pr create     body has a standalone Closes #N     -> fix body; use a split
             with policy-exact body            line, no trailing punctuation?         issue for partial scope
```

### 1. Enumerate and reconcile before you touch anything

List every worktree of every in-scope repository and its porcelain state. Treat these as
verification probes, not as authority to mutate:

```bash
for wt in $(git -C <repo> worktree list --porcelain | awk '/^worktree /{print $2}'); do
  git -C "$wt" status --porcelain | head -5
  git -C "$wt" status | head -3      # mid-merge and staged/unstaged need the full banner
done
```

A worktree in the middle of a merge (`All conflicts fixed but you are still merging`, staged
paths that add up to a full merge delta) belongs to the actor that started the merge. Record it
and move on. Concluding another actor's merge resolution can ship reviewed work you never saw,
and the open PR on that branch absorbs your guess.

If an earlier batch attempt was interrupted, reconcile before you retry:

- open PRs per candidate head branch (`gh pr list --head <branch> --repo <org>/<name>`);
- remote branch SHAs (`git ls-remote --heads origin <branch>`) — a pushed remote head without
  the dirty files committed locally means the remote predates the dirty work;
- residual dirty state per tree (prove whether the previous attempt committed).

Only then continue. This probe set makes a repeated batch safe: pushes are idempotent, PR
creation against an existing head fails visibly instead of duplicating.

### 2. Bind lookups to the literal repository

In a multi-repo batch, never resolve `<org>/<name>` through a shell call that runs in a
different repository. `gh repo view` (and `gh pr list` without `--repo`) answers for the current
directory's repository and fails **empty**, which looks identical to "no PR exists".

```bash
gh pr list --repo OrgA/RepoA --head <branch> --state all --json number,state,title
gh pr view <n> --repo OrgA/RepoA --json number,state,headRefName,mergedAt
gh issue view <n> --repo OrgA/RepoA --json number,title,state
```

### 3. Novelty gate: prove the content is not already on trunk

Squash merges make ancestry useless; compare content, file by file. This also covers files that
were never committed:

```bash
# modified file: identical to trunk?       -> skip
[ "$(git hash-object <wt>/<path>)" = \
  "$(git -C <repo> show origin/main:<path> | git hash-object --stdin)" ]

# deleted file: still present on trunk?    -> deletion is novel; already gone? -> skip
git -C <repo> cat-file -e origin/main:<path>

# untracked file: absent on trunk?         -> novel; present? -> align before shipping
git -C <repo> cat-file -e origin/main:<path>
```

A branch whose PR already merged can still hold a *novel uncommitted delta*. Ship that delta on a
fresh branch cut from `origin/main`, not on the spent branch, when the spent branch identity is
ambiguous. For a leftover commit unique to a branch whose PR merged, simulate the landing before
you open a PR:

```bash
git merge-tree --write-tree --merge-base=<novel-commit>^ origin/main <novel-commit>
```

A conflict here predicts an unmergeable PR: stop, and report the commit SHA as a manual port.

### 4. Coherence gates per artifact type

Novel content is not necessarily shippable content. Gate by artifact:

| Artifact | Gate before shipping | Predictable red PR if skipped |
| --- | --- | --- |
| untracked test file | import targets exist on current trunk; expected-content snapshots execute clean against current trunk | stale snapshot tables drift: recorded run had 11 missing / 10 unexpected keys |
| new module | `py_compile`, plus the repo linters the pre-commit hook would run | style/type failures CI would catch seconds later |
| ADR / numbered doc | number unique on trunk and the repo index (README) ships in the same PR | docs gate enforces unique numbers and index sync |
| staged tree prepared by another actor | ship exactly the staged set; check that nothing unstaged or untracked sneaks in | mixing prepared work with strays changes the intent |
| diff whose dependencies are untracked strays next to the dirty set | resolve or include them deliberately | recorded: tracked-only diff imported an untracked stub (`NotImplementedError`) — an instant broken PR |
| dirty state on a shared main checkout | do **not** edit in place; extract the diff as a patch, apply with `git apply --3way` onto a fresh worktree from `origin/main` | another actor can switch the shared checkout's branch mid-batch (recorded) |
| untracked build/session dirs (`build/`, `.opencode/`) | exclude always | junk in the PR, or leaked session config |

Before a PR for work that follows up a merged PR, query the merged PR and its issue. The issue
can already be closed by a later parallel fix; the "novel" leftover is then an obsolete draft
whose delta would revert merged work.

### 5. Content-constraint screen

When the user or the ecosystem forbids a boundary term (example: no PR into repos B/C may
reference project A), grep the exact bytes you would push, not the file list:

```bash
git diff HEAD | grep -ci <term>      # or: git diff --cached | grep -ci <term>  for staged trees
```

Apply it to prepared trees too. A removal campaign *about* the forbidden term still references
it. Skip and report; do not launder it into a different title.

### 6. Ship with policy-exact PR metadata

Commit with `git commit -s` (repo convention here: signed commits). Push, then open the PR with
a body the repo's policy gate accepts **byte-exactly**:

- Hephaestus-class gates require a line matching `^Closes #[0-9]+$`: literal `Closes`, capital C,
  alone on its line. A trailing period fails the anchor. A `Refs #N` line does not satisfy it.
- Partial scope needs a valid close target that does not lie: file a narrow split issue that
  names exactly the delivered slice, cite the parent with `Refs #N`, and put `Closes #<split>`
  on its own line. Opening the PR as a draft is honest when the slice is partial. Never point
  `Closes` at a bug the diff does not fix, or at a parent issue that a later PR already closed —
  the merge would close stale or wrong scope.
- Body edits re-trigger the policy check; a repair round is cheap. Verify the *latest* run's
  result — status rollups mix attempts from older runs.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | Batch PR lookup via `--repo $(gh repo view --json nameWithOwner -q .nameWithOwner)` so one loop covered several repos | The substitution ran in the knowledge repo, so comet-org queries silently became Mnemosyne queries and returned false `[]`; only a separate `gh pr view` GraphQL error exposed the wrong org | In a multi-repo batch, pin `--repo` to a literal `<org>/<name>` per target; treat a successful empty result as untrusted when the repo was derived, not stated |
| 2 | PR bodies written naturally: no `Closes` line on two, `Closes #3306.` (trailing period) on the third | The `pr-policy` job failed all three with `PR body must contain a line matching ^Closes #N$ ... literal "Closes", capital C, on its own line` | Policy text is regex-anchored bytes, not prose intent; a trailing period fails the anchor. Repair by `gh pr edit` with the exact line; edits re-trigger the check |
| 3 | Ship the tracked-only dirty diff from a stale main checkout (`admin.py` + `test-tiers.yaml`) | The diff imported `comet.cli.validation`, an untracked WIP stub whose every command raised `NotImplementedError`; both registered test files were untracked too. The PR would fail on import | A dirty set's dependencies can live in untracked strays beside it. Check what the diff references beyond the dirty set; ship the feature whole or skip |
| 4 | Ship three untracked files including `docs/adr/0040-...md` as prepared | Trunk already holds ADR `0040` for a different topic; the repo docs gate enforces unique ADR numbers and README↔disk index sync, and the README entry was not in the set | ADR and numbered-doc artifacts carry repo-level uniqueness and index invariants; renumber to the next free number and ship the index update in the same PR |
| 5 | Re-ship an untracked test with its 2026-07 expected-scope table onto current trunk | Executing the snapshot logic against pristine `origin/main` showed drift: 11 expected keys absent, 10 unexpected keys (trunk gained the `pr_review` stage) | Expected-content snapshots rot against a moving trunk; execute the table against current trunk and refresh it before proposing the PR |
| 6 | Resume an interrupted batch by re-running the whole agent from scratch | The earlier attempt had already staged a file in a shared checkout, and remote branches existed at old SHAs with their dirty work never committed — an un-reconciled retry risks duplicate PRs and wrong assumptions | Reconcile first: open PRs per head branch, remote SHA presence, residual dirty state. Pushes are idempotent; PR creation into an existing head fails visibly. Only then rerun the missing items |

## Results & Parameters

### Configuration

The gate order and the probe set copy directly from Quick Reference and sections 1–6. The
failure-prediction table in section 4 is the reusable unit: extend it when a new artifact type
survives novelty but predictably fails CI or policy.

### Expected Output

Per worktree, one of two recorded verdicts:

- `SHIPPED: <PR-url>` — branch pushed, PR opened, policy gates green on the latest run; or
- `SKIP: <reason, evidence>` — with the exact probe result (hash match set, `merge-tree`
  conflict, snapshot drift counts, forbidden-term count, mid-merge banner, wrong-org lookup).

A completed batch reports zero trees in an unknown state, plus any shared-checkout mutation a
foreign actor performed mid-batch.

### Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Mnemosyne | PR #3458 merged 2026-10-13 (skill v2.2.0 from a tidy-flagged dirty worktree) | [notes.md](dirty-worktree-batch-pr-shipping.notes.md) |
| comet (third-party org) | PR #2489 open (dead-CI deletion); 1 skip (untracked stub deps); 1 mid-merge non-interference | [notes.md](dirty-worktree-batch-pr-shipping.notes.md) |
| Hephaestus | PRs #3403, #3404 open, #3402 draft; skips with evidence: superseded leftover, snapshot drift, ADR collision, post-merge-refactor conflict, comet-boundary screen | [notes.md](dirty-worktree-batch-pr-shipping.notes.md) |

## References

- [git-branch-state-triage-and-recovery](git-branch-state-triage-and-recovery.md) — branch-level classification this batch gate feeds from.
- [ci-failure-triage-and-diagnosis](ci-failure-triage-and-diagnosis.md) — `git merge-tree` conflict isolation.
- [ci-cd-github-code-quality-findings-no-api](ci-cd-github-code-quality-findings-no-api.md) — tracking-issue remedy for a missing `Closes #N` line.
- [tooling-stage-only-your-own-files-in-shared-worktree](tooling-stage-only-your-own-files-in-shared-worktree.md) — staging discipline in shared worktrees.
- [checkout-other-ref-silent-file-clobber](checkout-other-ref-silent-file-clobber.md) — read content with `git show`, never checkout, in shared checkouts.
