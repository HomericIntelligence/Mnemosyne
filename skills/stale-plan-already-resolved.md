---
name: stale-plan-already-resolved
license: BSD-3-Clause
description: "Check whether current source already satisfies a stale issue, plan, or log finding — including at a workflow resume under a durable approval state; avoid redundant fixes and close tracked work only within authorized scope."
category: ci-cd
date: 2026-06-14
version: "1.4.0"
user-invocable: false
verification: verified-ci
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/stale-plan-already-resolved.history"
history-cleanup-date: "2026-09-20"
---
## Overview

| Field | Value |
| ------- | ------- |
| **Problem** | A point-in-time artifact (plan, LOG, error report, CI failure, audit finding) was captured when main was in state A, but main is now in state B (already fixed or changed further by intervening merges) |
| **Key insight** | Always verify the defect still reproduces on CURRENT `origin/<default>` before applying a plan, fixing a finding, or making outward records (issues, tracker edits, defect claims) that premise the defect — any captured artifact can become stale after other PRs merge |
| **Impact** | Prevents unnecessary changes and incorrect "fixes" that would revert progress or ship a no-op for an already-fixed bug |
| **Context** | Issue #4280: plan said change `test_*_layers.mojo` → `test_*_layers*.mojo`, but code already used `test_*.mojo`. Also: a 2588-line `output.log` named 4 root causes — 2 were already fixed on current main (PR #1148, `learn_claude_timeout`). Also: a relaunched worker's approved plan was eclipsed by a split delivery lane (create-targets present on main, modify-sites deleted); stop with zero writes |
| **Verification** | verified-ci |
| **History** | [changelog](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/stale-plan-already-resolved.history) |

## When to Use

1. An issue's implementation plan references specific line numbers but the diff shows different content
2. A plan says "change X to Y" but X is not present — a broader/different change is already there
3. A follow-up issue references a prior fix (e.g., "follow-up from #3458") and the code may have evolved
4. The plan was written weeks ago and many PRs have merged since
5. CI pattern change issues where the pattern may have been updated as part of a broader consolidation
6. An issue cites exact line numbers or a code snippet that does not appear anywhere in the current files — the issue likely predates a merged fix that already removed or moved the target
7. A captured log / `output.log` drives the work and time has passed (or other PRs merged) since the log was produced — the log reflects main at capture time, not now
8. Before implementing a fix found in ANY captured artifact (log, error report, CI failure, audit finding), you have not yet confirmed the defect still exists on current `origin/main`
9. A coordinator or supervisor relaunches an interrupted or split worker with a continue instruction and a plan that was approved on an earlier date. The approval state (plan marker, durable `state:*-go` label, or journal) survived the interruption, but the repository moved farther
10. A durable approval label or a completed earlier review gives apparent authority to implement. The label attests the review result at its time; it does not attest that the work remains
11. You are about to create an issue, edit a tracker or epic, or publish a defect claim premised on an inventory captured earlier in a long session on a shared, fast-moving default branch
12. Parallel workers own overlapping fix clusters in the same repository, and hours pass between your failure analysis and your next delivery boundary

## Verified Workflow

### 0. Resume and durable-approval gate: verify delivery and site evidence before any publication

When a relaunch instruction or a durable approval state is the reason the work started, measure
the current repository before any review publication or code write:

```bash
# Freeze the current tip read-only; never diff against a remembered base.
git fetch origin main
git rev-parse origin/main

# Site check: each symbol or file the plan modifies must still exist.
git grep -l '<cited symbol>' origin/main -- <plan scopes>
# A plan whose modify-targets were deleted cannot execute.

# Create-target check: an artifact the plan will create must not already exist with its contract.
git show origin/main:<path>

# Delivery search: find the lane that already delivered the work.
gh pr list --state merged --search '<issue number or plan artifact name>'

# End-goal check: verify the terminal outcome the issue defines
# (a merged delivery sequence, plus its required gates).
gh pr checks <latest merged delivery PR>
```

Decision rule: the plan's create-targets already exist on `origin/main`, its modify-targets were
deleted by later merges, and merged PRs or a green terminal-gate sequence carry the issue's
objective — then the plan is eclipsed. Make zero writes: do not implement, and do not publish a
review verdict over the stale plan. A verdict that binds deleted or previously delivered sites is
invalid evidence. Report the stop disposition that the task authorizes (for example PARKED) with
the delivery evidence.

### 1. Read the plan carefully for specific anchors

Look for references to:

- Specific line numbers (`line 234`)
- Specific patterns that should exist (`pattern: "test_*_layers.mojo"`)
- "Current state" described in the plan

```bash
# Issue plan said: "line 234: change test_*_layers.mojo → test_*_layers*.mojo"
```

### 2. Verify current file state against the plan's "before"

```bash
# Check if the "before" state from the plan still exists
grep -n "test_\*_layers\.mojo" .github/workflows/comprehensive-tests.yml
# If no output → the plan's "before" state is gone; something already changed it
```

### 3. Check what's actually there now

```bash
# Read the relevant section to understand current state
grep -A3 '"Models"' .github/workflows/comprehensive-tests.yml
```

### 4. Find the commit/PR that already made the change (decisive diagnostic)

When the plan's "before" state is gone, `git log -S` pinpoints exactly which commit removed
or changed it. Search for the **exact phrase or code snippet quoted in the issue**:

```bash
# git log -S finds commits that ADDED or REMOVED the given string
git log -S "<exact phrase or snippet from the issue>" -- '<glob>'
```

Real example — issue #422 asked to remove a `CHANGELOG.md or equivalent release notes`
criterion line from four `repo-analyze*/SKILL.md` files:

```bash
git log -S "CHANGELOG.md or equivalent release notes" -- 'skills/repo-analyze*/SKILL.md'
# → surfaces commit 76b46c9 (PR #357, "chore: remove CHANGELOG.md and changelog tooling")
#   which already removed the line ecosystem-wide weeks before the issue was actioned.
```

If `git log -S` shows the string was already removed by a merged commit, the issue's cited
line numbers are stale and the requested change is already done.

### 5. Re-verify each finding against CURRENT origin/main (logs & captured artifacts)

A captured log reflects `origin/main` AT THE TIME THE LOG WAS PRODUCED. Between capture and
your fix session, other PRs may have merged and already fixed the defect. Before implementing
ANY fix found in a log / error report / CI failure / audit finding, re-confirm it reproduces
on current main:

```bash
# (a) Confirm the buggy code still exists on the live tip — NOT just in the log
git show origin/main:<file> | grep -n "<buggy snippet from the log>"
# If no output → the code changed since the log; the defect may already be fixed.
```

For an external-facing or command-driven bug, use a safe authorized reproduction when
needed. Inspect side effects before reusing a command from an old log:

```bash
# Re-run the exact command the log shows failing. If it now SUCCEEDS, the bug is already fixed.
gh api graphql -f query='query($owner:String!,$name:String!){...}' -F owner=ORG -F name=REPO
# → returns valid JSON (no UNKNOWN_CHAR) ⇒ already fixed (PR #1148 passes owner/name as -F vars)

# Then run the OLD broken form to confirm it WAS the prior cause:
gh api graphql -f query='query{...inlined ${owner}...}'   # → reproduces the UNKNOWN_CHAR error
```

Only the findings that still reproduce on current main warrant a fix. In the 2026-06-14
session, 2 of 4 log-found bugs were already fixed (the `UNKNOWN_CHAR` GraphQL crash by
PR #1148; the planner-learnings 120s timeout replaced by `learn_claude_timeout()` = 7200s), so
their fixes were scoped down to the durable hardening only. The other 2 (armed-DIRTY
swallowed, green-BLOCKED threads not addressed) were confirmed still present before implementing.

### 5b. Re-anchor at each outward-mutation boundary on fast shared trains (verified-live)

A premise check expires. On a shared repository whose default branch advances during your
session — for example, a release train with parallel fix workers — a defect inventory
captured hours earlier can name defects that peers already fixed and merged. Re-verify the
premise immediately before each outward mutation:

- before creating an issue or editing a tracker/epic that premises the defect;
- before a review or PR-body defect claim;
- after a long validation run, and before `git push`; and
- after any session or tool restart (the restart itself is a mandatory re-anchor point).

```bash
git fetch origin <default-branch> --quiet
BASE="$(git merge-base HEAD origin/<default-branch>)"   # your analysis base
git log --oneline "$BASE"..origin/<default-branch> -- <paths-your-fixes-touch>
git log --oneline "$BASE"..origin/<default-branch> | grep -iE "<failing-node-or-failure-signature>"
gh search prs --repo <org>/<repo> "<failure signature>" --state all --limit 10
gh search issues --repo <org>/<repo> "<failure signature>" --state all --limit 10
```

Outcomes:

- A matching merged commit or PR retires that cluster: discard the prepared patch, do not
  open the PR, and do not file the issue.
- Records already filed on a decayed premise get close-out hygiene: close the record as
  already fixed with the resolving commit/PR reference, revert the tracker edit, and keep
  only the clusters whose failure still reproduces on the current tip. Re-run the failing
  node before any delivery claim.
- No match and the defect still reproduces: proceed with the planned mutation.

Cost asymmetry drives the rule: a prepared patch is cheap to discard; tracker records are
not — outward mutations need the freshest premise because they cannot be quietly rebased
away. For the post-interruption salvage decision itself, use the companion
`shared-repo-interruption-yield-to-peer-pr`.

### 6. Determine if the issue's goal is already satisfied

The key question: does the current state **achieve the same objective** as the planned change?

| Plan objective | Current state | Action |
| ---------------- | --------------- | -------- |
| `test_*_layers*.mojo` (match part files) | `test_*.mojo` (even broader, also matches part files) | Goal already met — add clarifying comment only |
| Add explicit filenames | Wildcard already present | Goal already met — no change needed |
| Remove explicit filenames | Already using wildcard | Goal already met — document only |

### 7. Apply the minimal appropriate change

Pick the action based on whether **any file** still needs to change:

| Situation | Correct action |
| ----------- | ---------------- |
| Functional fix already exists, but a comment/doc would clarify current intent | Update the comment/doc, then create a comment-only PR with `Closes #<issue>` |
| Goal is fully met AND no comment/doc change belongs in any file (the change is genuinely zero-diff) | Close the issue directly — **no PR** |

When a clarifying comment IS warranted:

```diff
- # test_googlenet_layers.mojo split into 3 parts (≤8 tests each)
+ # test_*.mojo glob auto-discovers all model tests including _partN split files
+ # (e.g., test_googlenet_layers_part1.mojo) without requiring manual CI updates.
```

When there is genuinely **nothing to change** — no functional change and no comment/doc
edit belongs anywhere — avoid an empty PR. Report the satisfying evidence; when issue
cleanup is authorized, close it with the commit/PR that already did the work:

```bash
gh issue close <N> --reason completed \
  --comment "Already resolved by PR #357 (commit 76b46c9, 'chore: remove CHANGELOG.md
and changelog tooling'), which removed this line ecosystem-wide on 2026-05-07. The line
numbers in this issue predate that merge. Section 10 already covers release management
generically. No code change needed."
```

### 8. Verify with the project's validation command

```bash
python3 scripts/validate_test_coverage.py
# Must exit 0 before committing — only when a file actually changed
```

### 9. Close the issue

- If a file changed: create the PR with `Closes #<issue>` (even a pure comment update) so
  the issue closes on merge and the already-correct state is documented.
- If nothing changed: the `gh issue close --reason completed --comment` from step 6 already
  closed it — no PR exists or is needed.

## Results & Parameters

| Parameter | Value |
| ----------- | ------- |
| Key diagnostic | `grep -n "<pattern from plan>" <file>` — if empty, plan is stale |
| Decisive diagnostic | `git log -S "<exact phrase from issue>" -- '<glob>'` — finds the commit/PR that already made the change |
| Live re-verify (logs) | `git show origin/main:<file> \| grep "<snippet>"` + re-run the exact failing command — if it now succeeds, the bug is already fixed |
| Validation command | `python3 scripts/validate_test_coverage.py` |
| Correct change scope | Comment-only update when the functional fix already exists; zero change when nothing needs editing |
| Close when zero diff | `gh issue close <N> --reason completed --comment "<cites the PR/commit>"` — no PR |
| PR label | `cleanup` |
| Resume / durable-label gate | `git rev-parse origin/main`, `git grep -l '<symbol>' origin/main -- <scopes>`, `gh pr list --state merged --search <ref>`, `gh pr checks <merged delivery PR>` |
| Plan eclipsed (create-targets exist, modify-sites deleted, terminal gates green) | Stop with the authorized disposition and zero writes; report the delivery evidence |
| Mutation-boundary re-anchor | `git fetch && git log --oneline <analysis-base>..origin/<default> -- <touched-paths>` + commit-subject and issue/PR search for the failing node IDs — any match retires that cluster |
| Boundary points | Before issue filing, tracker edits, and defect claims; after long validation runs; before push; after any restart |
| Decayed-premise recovery | Close obsolete records with the resolving commit/PR reference; revert tracker edits; salvage only unmatched clusters |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Applying plan verbatim | Would have changed `test_*.mojo` back to `test_*_layers*.mojo` | This would have been a regression — narrowing a working broad pattern | Always read actual file before applying a "before → after" from a plan |
| Skipping verification | Assuming plan's "before" state was current | Plan said line 234 had `test_*_layers.mojo`; actual line 283 had `test_*.mojo` | Verify anchors (line numbers, patterns) before touching anything |
| Treating as no-op | Issue already resolved, do nothing | Issue remains open; no PR closes it | Even when goal is met, create a PR with a comment clarification to formally close |
| Assuming a PR is always needed to close the issue | Planning a comment-only PR even though no file needed any change | There was literally no diff to make — a PR would be empty | When the goal is fully met and no clarifying comment belongs in any file, close the issue directly with `gh issue close --reason completed --comment` |
| Took the log's findings at face value | Planned fixes for all 4 root causes found in `output.log` | 2 were already fixed on current main (PR #1148 `-F` vars; `learn_claude_timeout()` 7200s) — would have shipped redundant no-op "fixes" / reverted progress | Re-verify each finding against current `origin/main` (`git show` + live command re-run) before implementing |
| Assumed the log == current main | Treated the captured `output.log` as the live state of main | False — a log is a point-in-time snapshot; intervening merges change main between capture and the fix session | A log reflects main AT CAPTURE TIME only; always re-confirm the defect reproduces now |
| Trusted a durable approval label as current authority | Started workflow-protocol re-review and implementation steps on a relaunched worker because the durable label proved the plan was once approved | Every plan-cited site had been restructured or deleted on current main by a later delivery lane; a published verdict would have bound deleted code, and the "fix" would have reverted delivered behavior | A durable label attests review-time state only; re-run site and delivery evidence on the current default branch before any exchange publication or write |
| Treated a continue instruction as delivering fresh requirements | Assumed a relaunch means the saved plan is still the remaining work | The instruction reloads the task and its authorization, not the repository state | Measure the current branch first; the issue and current main define remaining work, not the saved plan |
| Filed tracker records from the analysis snapshot | Created repair issues and an epic edit premised on a failure inventory captured hours earlier on a release train | Parallel workers had merged fixes for every analyzed cluster; the new records were obsolete on creation and needed close-out cleanup | Re-anchor the premise immediately before every outward mutation, not only before code delivery |
| One re-check per session | Re-verified the defect inventory once at analysis time and treated it as valid for the whole session | The default branch advanced ~30 commits during the session, including fix PRs for the exact analyzed failures | A premise check expires; re-run it at each delivery boundary |
| Checked only the code artifact | Re-fetched before opening the fix PR but filed issues and edited the tracker from the decayed analysis | The easily discarded artifact (the branch) got the fresh check; the hard-to-retract artifacts (tracker records) did not | Give outward mutations the freshest premise: they cannot be quietly rebased away |

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectOdyssey | Issue #4280 (follow-up from #3458) | [notes.md](../references/notes.md) |
| ProjectHephaestus | Issue #422 — CHANGELOG criterion already removed by PR #357 (commit 76b46c9) | Closed directly as completed; no PR (zero diff) |
| ProjectHephaestus | 2026-06-14 output.log 4-RC analysis; 2 of 4 already fixed, caught via live re-verify | PRs #1353-#1356 |
| Internal CI-gate repository | 2026-10 relaunched single-issue worker; durable plan eclipsed by a split delivery lane | stop report, zero writes; [notes](./stale-plan-already-resolved.notes.md) |
| External repository (unnamed) | 2026-10 release-train session: 4 analyzed failure clusters were fixed by parallel workers mid-session; 2 repair issues + 1 tracker edit filed on the decayed premise needed close-out; the pre-push boundary check prevented a duplicate PR | [notes](./stale-plan-already-resolved.notes.md) |
