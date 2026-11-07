---
name: stale-plan-already-resolved
license: BSD-3-Clause
description: "Check whether current source already satisfies a stale issue, plan, log finding, review finding, or pull-request premise — including at a workflow resume under a durable approval state, on an open PR head that a sibling session rewrote, on an outdated review thread, and inside a multi-item issue where a merged change delivered only some items or only some severity sites; avoid redundant fixes and close tracked work only within authorized scope."
category: ci-cd
date: 2026-06-14
version: "1.9.0"
user-invocable: false
verification: verified-ci
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/stale-plan-already-resolved.history"
history-cleanup-date: "2026-09-20"
---
## Overview

| Field | Value |
| ------- | ------- |
| **Problem** | A point-in-time artifact (plan, LOG, error report, CI failure, audit finding) was captured when main was in state A, but main is now in state B (already fixed or changed further by intervening merges) |
| **Key insight** | Verify the defect on CURRENT `origin/<default>` before applying a plan, fixing a finding, or making outward records. Any captured artifact can go stale after other merges, and decide a multi-item issue per item and per severity site |
| **Impact** | Prevents unnecessary changes and incorrect "fixes" that would revert progress or ship a no-op for an already-fixed bug |
| **Context** | Issue #4280: a plan said to change a test glob, but the code already used it. Also: a log named 4 root causes and 2 were already fixed (PR #1148). Also: a relaunched worker's approved plan was eclipsed by a split delivery lane (create-targets present, modify-sites deleted); stop with zero writes. Also: a gate-downgrade issue named four checks; one merged change delivered two, and the other two still exited non-zero, so the plan split per item and per severity site |
| **Verification** | verified-ci |
| **History** | [changelog](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/stale-plan-already-resolved.history) |

## When to Use

1. An issue's implementation plan references specific line numbers but the diff shows different content
2. A plan says "change X to Y" but X is not present — a broader/different change is already there
3. A follow-up issue references a prior fix and the code may have evolved
4. The plan was written weeks ago and many PRs have merged since
5. CI pattern change issues where the pattern may have been updated as part of a broader consolidation
6. An issue cites exact line numbers or a code snippet that does not appear anywhere in the current files — the issue likely predates a merged fix that already removed or moved the target
7. A captured log, error report, or audit output drives the work, and time passed or other PRs merged since it was produced — it reflects main at capture time, not now
8. Before implementing a fix found in ANY captured artifact (log, error report, CI failure, audit finding), you have not yet confirmed the defect still exists on current `origin/main`
9. A coordinator or supervisor relaunches an interrupted or split worker with a continue instruction and a plan that was approved on an earlier date. The approval state (plan marker, durable `state:*-go` label, or journal) survived the interruption, but the repository moved farther
10. A durable approval label or a completed earlier review gives apparent authority to implement. The label attests the review result at its time; it does not attest that the work remains
11. You are about to create an issue, edit a tracker or epic, or publish a defect claim premised on an inventory captured earlier in a long session on a shared, fast-moving default branch
12. Parallel workers own overlapping fix clusters in the same repository, and hours pass between your failure analysis and your next delivery boundary
13. A scoped task brief premises an open pull request state, for example a rebase-only brief that states the PR is conflicting or dirty against the default branch. The brief is a snapshot: the PR head may have moved after the brief was written
14. A review workflow hands you an unresolved review thread, often `isOutdated`, and the prompt expects a fix. The finding was captured at an older head. A later fix already landed, and the thread stayed unresolved because no publisher resolved it
15. You already wrote, tested, committed, and pushed the change for a task that started from a recorded base. The push or pull-request creation fails with a conflict, or the new pull request opens `CONFLICTING`/`DIRTY`. The delivery boundary is the last point where a later merge can eclipse the work
16. A user asks for a behavior change ("make X the default", "load Y dynamically") and pastes tool output that names the version they ran, or your own checkout lags and your last fetch partly failed. The default branch may already have the behavior
17. You plan an issue that names several checks, files, or behaviors to change together. A merged change can implement only part of it, and a title search hides the rest. Decide per named item before you plan any of them
18. The request is about the severity of an outcome (fail, warn, ignore, skip, remove), and a captured reference shows a value from one older revision. Severity can differ even when the symbol still exists

## Verified Workflow

### 0. Resume and durable-approval gate: verify delivery and site evidence before any publication

When a relaunch instruction or a durable approval state is the reason the work started, measure
the current repository before any review publication or code write:

```bash
# Freeze the current tip read-only; never diff against a remembered base.
git fetch origin main && git rev-parse origin/main

# Site check: each symbol or file the plan modifies must still exist.
git grep -l '<cited symbol>' origin/main -- <plan scopes>

# Create-target check: an artifact the plan will create must not already exist.
git show origin/main:<path>

# Delivery search and end-goal check.
gh pr list --state merged --search '<issue number or plan artifact name>'
gh pr checks <latest merged delivery PR>
```

Decision rule: the plan's create-targets already exist on `origin/main`, its modify-targets were
deleted by later merges, and merged PRs or a green terminal-gate sequence carry the issue's
objective — then the plan is eclipsed. Make zero writes: do not implement, and do not publish a
review verdict over the stale plan. Report the stop disposition that the task authorizes (for
example PARKED) with the delivery evidence.

### 0a. Post-push duplicate gate: search the delivery lane before you resolve a conflict

A base commit that is still an ancestor of the default branch does not prove the work is absent.
When the push reports a conflict, or the new pull request opens `CONFLICTING`, measure the range
between the plan base and the current default tip before any rebase:

```bash
git fetch origin <default>
git merge-base --is-ancestor <plan-base> origin/<default>   # true says nothing about the work
git log --oneline <plan-base>..origin/<default>
git log --oneline --grep '<issue number>' origin/<default>  # the delivery commit, if it exists
git show <delivery-commit> --stat
```

Decision rule: a commit on the default branch that names the task and changes the same files is a
prior delivery, not a conflict to solve. Compare your result with that commit, then make zero
writes: rebase nothing, push nothing, do not merge a duplicate. Close your duplicate pull request
with a comment that names the delivery commit, and delete only your own branch. A correct but
duplicate change costs review time and can revert later behavior. An ancestor merge base only
shows the base is old; it is not evidence that the work is unfinished.

### 0b. Open-PR premise gate: measure the PR head before a premise-scoped rewrite

When the assignment targets an open pull request and premises its state — for example a
rebase-only brief that states the PR is conflicting or dirty against the default branch —
the delivery lane may be that same PR. A sibling session can already have rebased its head
while the brief was in transit. A merged-PR search and a main-tree site check cannot see a
delivery that lives on the open PR's rewritten head. Measure the PR head before any rebase
or push:

```bash
git fetch origin <default-branch> <pr-branch>

# Ancestry: does the head already contain the current default tip?
git merge-base --is-ancestor origin/<default-branch> origin/<pr-branch>
git rev-list --count origin/<pr-branch>..origin/<default-branch>   # 0 = nothing to rebase onto

# Mergeability: provider status plus a local merge test (the provider value can lag)
gh pr view <pr-number> --json mergeable,mergeStateStatus
git merge-tree --write-tree origin/<default-branch> origin/<pr-branch> >/dev/null 2>&1 \
  && echo MERGE_CLEAN || echo MERGE_CONFLICTS

# Provenance: did a sibling move the head or report the task complete?
gh api repos/<org>/<repo>/issues/<pr-number>/events \
  --jq '[.[] | select(.event == "head_ref_force_pushed") | {created_at}]'
```

Decision rule: the head already contains the current default tip, the merge is clean, and a
sibling session reported the task complete at that head — then the premise is eclipsed. Make
zero writes: do not re-run the rebase, re-push, or post a duplicate completion comment. A
rebase of identical content still produces a new head SHA, breaks any head-bound approval, and
restarts the review gate.

Verification level: this subsection is `verified-live` from one session (see the notes). The
rest of this entry keeps its `verified-ci` claim.

### 0c. A requester's installed copy and a failed fetch: compare versions before you file

A request for a behavior change can describe an old install, and your own checkout can lag the
default branch. Run these checks before you open an issue, write a plan, or start an agent:

1. Fetch the default branch and require exit code 0. A fetch that reports "did not send all
   necessary objects" or a bad ref can still move some refs. Compare the local tip with
   `git ls-remote origin <default>`. If they differ, treat every absence claim as unverified.
2. Read the artifact version on the fetched default branch (version constant, changelog, or the
   file's log). Read the version the requester ran (a banner or version line in pasted output).
3. Choose the outcome:

| Finding | Action |
| ---- | ---- |
| Default branch has the behavior and the requester's version is older | Do not file or implement. Tell the requester to update. Name the commit and version |
| Default branch lacks the behavior | Plan and implement |
| Default branch has part of it | Plan only the remaining delta. Name the covered part |

4. When you delegate, tell the agent to check the fetched default branch first. It stops with
   "no change" and its evidence when the behavior exists. That costs one comment. An agent that
   implements anyway costs a duplicate pull request.
5. If a duplicate issue already exists, close it with the commit and version as evidence.

### 0d. An issue with several named items: decide per item, and check severity per site

An issue body is not one premise. It often names several checks, files, or behaviors to change
together, and a merged change can implement only some of them. A title search then finds the
delivery and hides the rest. Decide each named item against current source. A request to change
severity ("warn instead of fail", "log and continue", "remove") has a second dimension: one file
can hold both a delivered warn site and a site that still exits non-zero.

```bash
git fetch origin <default-branch> && git log -1 --oneline origin/<default-branch>

# 1. One row per named item: does the file, symbol, or record still exist?
git grep -n '<item>' origin/<default-branch> -- <paths>

# 2. Severity per row: classify each site that still exists.
git grep -n -A3 'raise\|return 1\|SystemExit\|require(' origin/<default-branch> -- <path>
grep -n 'WARNING' <path>            # an existing warn path shows a delivered downgrade

# 3. Attribution per row: which commit or PR delivered the item?
git log -S '<decision wording the delivered change added>' --oneline origin/<default-branch> -- <path>

# 4. Re-verify the delivered rows as guards; plan only the residual rows.
```

| Row finding | Action |
| --- | --- |
| Site removed by a merged change | Report it as done; cite the commit |
| Site exists and every outcome is already warn-and-continue | Report it as done; do not re-apply it |
| Site exists and a comparator or gate still exits non-zero | Plan this residual row |
| One file mixes warn sites and fail sites | Classify each site, because the residual is usually the fail sites |
| A captured reference shows a value from an older revision | Re-read the outcome on the current tip; the captured value does not bind |

Decision rule: a title search that finds a merged delivery does not make the issue complete.
Split the issue per named item, decide each item, plan only the rows that still fail, and add a
guard assertion for each delivered row so that the downgrade stays. Report the mixed state item
by item: a single "resolved" verdict leaves live work, and a plan that repeats the delivered
rows either produces no diff or reverts the downgrade.

Verification level: this subsection is `verified-live` from one planning session (see the
notes). The rest of this entry keeps its `verified-ci` claim.

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


```bash
git log -S "<exact line or snippet the issue quotes>" -- '<globs from the issue>'
# → surfaces the commit and PR that already removed or changed the line.
```

If `git log -S` shows the string was already removed by a merged commit, the issue's cited
line numbers are stale and the requested change is already done. Keep the original quote and
the resolved commit in the issue close-out comment.

### 5. Re-verify each finding against CURRENT origin/main (logs & captured artifacts)

A captured log reflects `origin/main` at the time of capture. Between capture and your fix
session, other PRs may have fixed the defect. Before implementing ANY fix from a log, error
report, CI failure, or audit finding, re-confirm it on current main:

```bash
git show origin/main:<file> | grep -n "<buggy snippet from the log>"   # empty => code changed
```

For an external-facing or command-driven bug, re-run the exact failing command. A command that
now succeeds means the bug is already fixed. Inspect side effects before you reuse a command
from an old log.

Only the findings that still reproduce on current main warrant a fix. Scope the rest down or
drop them.

### 5a. Re-verify a review finding before you edit for it

A review thread is another captured artifact. Check the finding against the current head
before you write code:

```bash
HEAD_SHA="$(git rev-parse HEAD)"   # the branch checkout, not the default tip
git log --oneline -S "<snippet the finding names>" -- <path>
# The fix commit in this range means the defect is gone; the thread is stale.
sed -n '<start>,<end>p' <path>     # quote the lines that close each requested item
```

Run the tests that cover the fixed behavior as evidence. Do not re-edit a fixed file or push an
empty commit to close a thread. Answer with the current line numbers, not lines from the old head.

### 5c. State the decisive outcome before you edit (required)

After step 5 or 5a, pick one of these two states and record it:

| State | Evidence | Action |
| ---- | ---- | ---- |
| **Change required** | At least one item still fails on the current head | Edit, test, commit, and push |
| **No readable defect** | Every item is already fixed, answered by recorded approval, or covered by the documented contract | Do not edit or commit. Post the evidence and complete the authorized records |

"No readable defect" does not mean the task stops. Resolve the threads, post the report, and
complete the evidence record; that work changes no source file. Do not invent a "minimal" change
to create activity: a cosmetic edit to a fixed file breaks the head-bound approval for no benefit.

#### 5c.1 Review-thread records: resolve on proof, not on a new commit

A review-finding workflow commonly expects one commit per fix. The "No readable defect" state
needs no commit, but its records are still required:

- Resolve an already-fixed thread with the closing commit, the current file:line of each item,
  and the test names. Do not answer with opinion.
- Keep a thread open when its work needs a product decision or remains blocked.
- Report `commits: none` and keep the head. A head change restarts CI and voids the approval.

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
  already fixed with the resolving commit, revert the tracker edit, and keep only the clusters
  that still reproduce on the current tip.
- No match and the defect still reproduces: proceed with the planned mutation.

A prepared patch is cheap to discard; tracker records are not. Outward mutations need the
freshest premise because they cannot be quietly rebased away. For the post-interruption
salvage decision, use the companion `shared-repo-interruption-yield-to-peer-pr`.

### 6. Determine if the issue's goal is already satisfied

Ask whether the current state **achieves the same objective** as the planned change.

| Plan objective | Current state | Action |
| ---------------- | --------------- | -------- |
| `test_*_layers*.mojo` (match part files) | `test_*.mojo` (even broader, also matches part files) | Goal already met — add clarifying comment only |
| Remove explicit filenames | Already using wildcard | Goal already met — document only |

### 7. Apply the minimal appropriate change

Pick the action based on whether **any file** still needs to change:

| Situation | Correct action |
| ----------- | ---------------- |
| Functional fix already exists, but a comment/doc would clarify current intent | Update the comment/doc, then create a comment-only PR with `Closes #<issue>` |
| Goal is fully met AND no comment/doc change belongs in any file (the change is genuinely zero-diff) | Close the issue directly — **no PR** |
| The finding arrived as a review thread, and no source file needs a change | Do not edit. Resolve the thread with the proof from step 5c.1, and post the report |

A clarifying comment is a narrow case: change the comment only when the current wording
misleads a future reader about why the broad pattern or the delivered outcome is correct.

When there is genuinely **nothing to change**, avoid an empty PR. Report the satisfying
evidence; when issue cleanup is authorized, close the issue with the commit that already did
the work:

```bash
gh issue close <N> --reason completed \
  --comment "Already resolved by <PR> (commit <sha>), which changed this behavior on <date>.
The lines cited in this issue predate that merge. No code change is needed."
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
- If the record is a review thread: create no PR from a no-change finding. Resolve the thread
  and report `commits: none`. The thread is the record, and the review workflow already holds
  it.

## Results & Parameters

| Parameter | Value |
| ----------- | ------- |
| Key diagnostic | `grep -n "<pattern from plan>" <file>` — if empty, plan is stale |
| Decisive diagnostic | `git log -S "<exact phrase from issue>" -- '<glob>'` — finds the commit/PR that already made the change |
| Live re-verify (logs) | `git show origin/main:<file> \| grep "<snippet>"` + re-run the exact failing command; if it now succeeds, the bug is already fixed |
| Correct change scope | Comment-only update when the functional fix already exists; zero change when nothing needs editing |
| Close when zero diff | `gh issue close <N> --reason completed --comment "<cites the PR/commit>"` — no PR |
| Site and boundary gates | Pre-write premises: resume, open PR head, installed copy, multi-item split. Boundary points: before issue filing, tracker edits, and defect claims; after long validation runs; before push; after any restart |
| Delivery-boundary stop | A merged commit on the same files ⇒ close the duplicate unmerged and delete only your branch |
| Multi-item split | One row per named item, one severity reading per site; plan the residual rows and guard the delivered ones |
| Mixed-state report | Report done rows with their commit and residual rows with their exit path; one "resolved" verdict hides live work |
| Per-gate commands and parameters | See the notes for the copy-ready command table |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Applying plan verbatim | Would have narrowed a working broad glob back to a specific one | That is a regression of delivered behavior | Read the actual file before applying a plan "before → after" |
| Skipping verification | Assumed the plan's "before" state was current | The cited line held different content | Verify anchors (line numbers, patterns) before touching anything |
| Treating as no-op | Issue already resolved, do nothing | Issue remains open; no PR closes it | Even when goal is met, create a PR with a comment clarification to formally close |
| Assuming a PR is always needed to close the issue | Planning a comment-only PR even though no file needed any change | There was literally no diff to make — a PR would be empty | When the goal is fully met and no clarifying comment belongs in any file, close the issue directly with `gh issue close --reason completed --comment` |
| Took the log's findings at face value | Planned fixes for all 4 root causes in a captured log | 2 were already fixed; the fixes would have been redundant or reverted progress | Re-verify each finding against current `origin/main` before implementing |
| Assumed the log is current main | Treated a captured log as the live state | A log is a point-in-time snapshot; merges changed main before the fix session | A log reflects capture time only; re-confirm the defect now |
| Trusted a durable approval label as current authority | Started protocol re-review and implementation on a relaunched worker because the durable label proved the plan was once approved | Every plan-cited site had been restructured or deleted by a later delivery lane; a published verdict would have bound deleted code | A durable label attests review-time state only; re-run site evidence on the current default branch first |
| Treated a continue instruction as fresh requirements | Assumed a relaunch means the saved plan is the remaining work | The instruction reloads the task and its authority, not repository state | The issue and current main define remaining work, not the saved plan |
| Filed tracker records from the analysis snapshot | Created repair issues and an epic edit from a failure inventory captured hours earlier | Parallel workers had merged fixes for every cluster; the records were obsolete on creation | Re-anchor the premise before every outward mutation, not only before code delivery |
| One re-check per session | Re-verified the inventory once and treated it as valid for the session | The default branch advanced during the session, including fixes for the analyzed failures | A premise check expires; re-run it at each delivery boundary |
| Checked only the code artifact | Re-fetched before the fix PR but filed issues and edited the tracker from the decayed analysis | The discardable artifact got the fresh check; the hard-to-retract records did not | Give outward mutations the freshest premise: they cannot be quietly rebased away |
| Editing a review finding from its body text | A review workflow asked for fixes on nine unresolved threads | Eight were already fixed by two merged commits on the same head; no publisher had resolved the threads | Check the current head before you edit; resolve on proof when no change is needed |
| Resolved a pull-request conflict by rebasing a finished implementation | The new pull request opened `CONFLICTING` although the plan base was a default-branch ancestor | The default branch already carried a merged commit for the same task on the same files; the rebase would have duplicated it | Run step 0a before any rebase: search the base-to-tip range, then close your duplicate unmerged |
| Empty commit to satisfy a fix-per-thread contract | Review workflows often expect one commit per accepted finding | The commits existed. An empty one would move the head and restart review for no change | Zero-diff is a valid outcome. Never move a head to show activity |
| Filed from a stale checkout | Opened a feature issue and started an agent for behavior the default branch already had; the requester pasted an older banner and the last fetch partly failed | The checkout lagged and the partial fetch left the default branch stale | Compare versions against a clean fetch before you file |
| Trusted a title-level delivery search for a multi-item issue | Read that one merged change named the issue, then planned the whole issue body or reported it complete | The merged change delivered only part of the named items, and one item was partially delivered: a warn site existed beside a site that still exited non-zero | Split the issue per named item and read severity per site (step 0d); plan only the residual rows and guard the delivered ones |

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectOdyssey | Issue #4280 (follow-up from #3458) | [notes.md](../references/notes.md) |
| ProjectHephaestus | Issue #422 — CHANGELOG criterion already removed by PR #357 (commit 76b46c9) | Closed directly as completed; no PR (zero diff) |
| ProjectHephaestus | 2026-06-14 output.log 4-RC analysis; 2 of 4 already fixed, caught via live re-verify | PRs #1353-#1356 |
| Internal CI-gate repository | 2026-10 relaunched single-issue worker; durable plan eclipsed by a split delivery lane | stop report, zero writes; [notes](./stale-plan-already-resolved.notes.md) |
| External repository (unnamed) | 2026-10 release-train session: 4 analyzed failure clusters were fixed by parallel workers mid-session; 2 repair issues + 1 tracker edit filed on the decayed premise needed close-out; the pre-push boundary check prevented a duplicate PR | [notes](./stale-plan-already-resolved.notes.md) |
| Internal CI-gate repository | 2026-10-31 rebase-only brief on an open PR; the head was already rebased onto the current default tip by sibling sessions | zero-write stop with measured evidence; [notes](./stale-plan-already-resolved.notes.md) |
| Internal promotion PR | 2026-11 review round: 8 required findings already fixed on the same head by 2 merged commits, and 1 approval recorded | zero-diff resolution, `commits: none`; [notes](./stale-plan-already-resolved.notes.md) |
