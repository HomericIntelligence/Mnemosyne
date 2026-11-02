---
name: duplicate-implementation-first-merge-wins
description: "Close out a superseded implementation lane when a duplicate pull request for the same issue merges first. Use when two lanes implement one issue in parallel and your lane waits on a coordination decision or runs final validation while the competing pull request is still open: a terminal review verdict, an exclusive merge-gate label, and armed auto-merge do not reserve the outcome. The first merge finishes the race."
category: tooling
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-local
license: BSD-3-Clause
tags:
  - agent-coordination
  - duplicate-pr
  - supersession
  - merge-race
  - decision-hold
  - teardown
  - automerge-staleness
---

# Duplicate Implementation: The First Merge Finishes the Race

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-11-01 |
| **Objective** | Drive an issue with a sealed decision record to merge on one implementation lane while a duplicate lane for the same issue existed. The local lane held a terminal review GO, the exclusive merge-gate label, armed auto-merge, and a green rebased head. A precedence question for the duplicate was posted on the coordination channel and unanswered. |
| **Outcome** | The duplicate lane merged during the local lane's final validation window and closed the issue. A substance audit confirmed main implements the issue's decision record. The superseded lane closed its pull request with a pointer, deleted the remote and local branch, removed the worktree, posted the final disposition, and stopped. Zero code actions were needed after the supersession. |
| **Verification** | verified-local — issue closure state, the merged pull request's check rollup, the on-main audit (symbol greps, template checks, cookbook and schema checks, docs presence), and every teardown command were executed. |

## When to Use

- You claimed an issue on the coordination channel and a second, duplicate
  implementation lane appeared: another pull request names the same issue.
- You posted a precedence question (`[DECISION-NEEDED]` or equivalent) and
  hold your own lane, or you continue final validation (rebase, local
  suites, force-push, CI wait) while the duplicate pull request stays open.
- Your lane carries a terminal review verdict, an exclusive merge-gate
  label, or armed auto-merge, and you are tempted to treat the issue as
  reserved for your lane.
- The competing pull request merged. You must now choose between rebasing
  into the result, arguing precedence after the fact, or closing out.

## Verified Workflow

### Quick Reference

```bash
# ANTICIPATE — during every wait window (decision-hold, rebase, CI wait),
# poll the competing lane, not only your own CI. One forge read per turn
# is cheap; a merge detected an hour late is expensive.
gh pr view <other-pr> --json state,mergedAt --jq '{state,mergedAt}'
gh issue view <issue> --json state,closedAt,stateReason

# AUDIT — when the other lane merged first, verify main against the
# issue's decision record in substance. Never audit by diff against
# your branch: a different implementation of the same record still
# completes the record.
git fetch origin main
git grep -n "<removed-field>" origin/main -- <config> <schema> <cookbooks>   # zero hits = removed
git grep -c "<removed-function>" origin/main -- <module>; echo rc=$?        # rc=1 = gone
gh pr view <other-pr> --json statusCheckRollup \
  --jq '[.statusCheckRollup[].conclusion] | group_by(.) | map({(.[0]): length}) | add'

# TEARDOWN — close with a pointer, then remove your lane's artifacts.
# Capture evidence outside the worktree BEFORE removing it.
gh pr close <your-pr> --comment "Superseded: <issue> landed via <other-pr>; final disposition on the coordination channel."
git push origin --delete <your-branch>
git worktree remove <worktree-path>
git branch -D <your-branch>
# Post the final disposition on the coordination channel, report, stop.
```

### Detailed Steps

1. **Anticipate during every wait window.** A decision-hold pauses only
   your lane. Operators and the duplicate lane keep moving, and a merge is
   a legitimate way to answer a precedence question. Poll the duplicate
   pull request's state in every turn where you wait for anything — an
   answer, a rebase result, or a CI run. Treat the competing lane's
   mergeability (green checks, labels, armed auto-merge) as the live
   signal, ahead of any posted reply.
2. **Surface the race risk before long validation windows.** When a
   duplicate exists and you are about to spend time on a rebase or a full
   CI cycle, state on the coordination channel which lane should land and
   that the other will stand down. An unanswered precedence question plus
   two merge-ready lanes is the exact setup for a wasted validation cycle.
3. **Audit main in substance, not your branch by diff.** When the other
   lane merges first, verify the issue's decision record on main: removed
   fields and functions produce zero grep hits in their old homes; added
   behavior has its new names and call sites; the owning docs page exists;
   the merged pull request's check rollup is green. Residual same-named
   internal variables for derived values are a naming choice, not a
   declared-field remnant — classify them before calling drift.
4. **Evaluate your objective by outcome-bound criteria.** Completion
   criteria that name an outcome (the decision record is implemented on
   main, a closing pull request merged green, the reviews ran, cleanup is
   done) can be satisfied with a different actor. Criteria that name your
   pull request specifically cannot. Record which reading you close on,
   with the evidence either way.
5. **Tear down immediately and publish nothing on the other lane's
   artifacts.** Close your pull request with a one-paragraph pointer to
   the landed pull request and your review records. Delete the remote and
   local branch. Remove the worktree after you capture the evidence you
   still need outside it. Post the final disposition on the coordination
   channel of the work item. Do not rebase into, re-argue, or comment on
   the landed pull request: the merge is the terminal state.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Treated a terminal review GO plus the exclusive merge-gate label as reserving the issue | Continued the final validation window (rebase, local suites, force-push) while the precedence question on the duplicate stayed unanswered | The hold bound only the local lane; the duplicate merged during the window, and the freshly force-pushed head became CONFLICTING within minutes | Verdicts, labels, and armed auto-merge are lane-local state. The merge is the only finish line. Poll the competing lane every wait turn |
| Held merge-path steps for a posted precedence question with no fallback | Waited for a written reply before the final push and CI classification | The answer arrived as the merge event itself; no written reply preceded it | A precedence question can be answered by the merge. Watch the duplicate's mergeability as the live decision signal |
| Armed auto-merge (squash) early with a prepared commit message, then force-pushed a rebased head | Assumed the merge machinery tracks the branch | The forge keeps the prepared squash title and body across force-pushes; the armed body still carried pre-rebase claims (stale base, stale test counts). Harm was avoided only because the lane lost the race | After every force-push to a pull request with armed auto-merge, re-read the prepared commit message and refresh it before checks can go green |

## Results & Parameters

- **Substance audit that was executed** (all greps against the fresh
  `origin/main`): the removed configuration field had zero hits in the
  config module, the schema, and the cookbooks; the removed planner
  functions had zero hits in their old module; the submission template
  carried no node-pin directives and carried the derived-lease flags; the
  offset cookbooks matched the expected count; the owning documentation
  page existed; the merged pull request's rollup was 49 checks SUCCESS and
  0 FAILURE. Conclusion: the decision record was implemented on main in
  substance.
- **Re-resolution cost after supersession:** zero code actions. The
  closeout is close, delete branch, remove worktree, disposition post,
  report.
- **Criteria reading used for the close:** outcome-bound criteria closed
  on evidence (record on main, merge green, reviews executed, cleanup
  receipts); the one actor-bound clause (this lane's pull request merged)
  was reported as superseded by the duplicate lane's merge, with the merge
  identifier and timestamps quoted.

### Related skills

- `shared-token-agent-identity-claim-coordination` — the claim and
  decision-hold protocol this lesson assumes. This lesson adds what the
  hold does not protect: the competing lane keeps moving.
- `agents-pr-review-forked-terminal-verdict-supersession` — supersede and
  replace when two publishers fork ONE pull request's review ledger. This
  lesson covers the obverse: two intact lanes for one issue, where the
  first merge wins.
- `sibling-pr-mutually-exclusive-design-conflict` — detect hidden design
  conflicts between two open sibling pull requests while both are open.
  This lesson covers the closeout after one sibling already merged.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| A fleet-scheduler repository with a shared agent credential and a coordination discussion board | One issue with a sealed decision record, implemented in parallel by two lanes; a precedence question posted and unanswered | verified-local; the duplicate merged during the superseded lane's final validation window; the substance audit on main passed on every decision-record item; teardown executed (pull request closed with pointer, branches deleted, worktree removed); final disposition posted on the work item's coordination thread |
