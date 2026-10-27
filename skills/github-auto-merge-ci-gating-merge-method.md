---
name: github-auto-merge-ci-gating-merge-method
description: >-
  Diagnose why a GitHub pull request does not merge when checks, reviews, merge methods,
  rulesets, classic protection, labels, signatures, or queue ownership disagree. Use before
  arming auto-merge or admitting a reviewed head to a repository-owned merge queue, when
  protocol ceremonies remain while a merge is already armed, or when a decorative state
  label may be mistaken for a merge gate.
category: ci-cd
date: 2026-07-30
version: "2.3.0"
user-invocable: false
verification: verified-ci
license: BSD-3-Clause
tags: [auto-merge, github, ci-cd, merge-method, required-checks, rulesets, review-threads, current-head-checks, merge-queue, toctou, armed-merge-race, ceremony-ordering, label-gating]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/github-auto-merge-ci-gating-merge-method.history"
history-cleanup-date: "2026-09-20"
---

# GitHub Auto-Merge: CI Gating, Branch Protection, and Merge Method

**Supporting cases:** [notes](./github-auto-merge-ci-gating-merge-method.notes.md)

**Superseded content:** [history](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/github-auto-merge-ci-gating-merge-method.history)

## Overview

`mergeable`, `mergeStateStatus`, check conclusions, review decisions, auto-merge state, and
branch policy answer different questions. Diagnose the current PR head across all layers before
changing state. Merge authority is separate from review approval: an exact GO can authorize a
review verdict without authorizing an actor to arm, disable, adopt, or replace auto-merge.

The general diagnostics and several blocker patterns are `verified-ci`. Queue interlock and some
repository-specific policy transitions are `verified-local`; their boundaries are in the notes.

## When to Use

- A PR is `CLEAN`/mergeable and checks look green, but auto-merge does not fire.
- A merge command rejects `--rebase` or `--squash`, or the repository allows one method only.
- A direct merge call is rejected with `Repository rule violations found` because the base
  branch requires the merge queue.
- A PR queued for merge shows a null `autoMergeRequest` and looks unarmed.
- A batch merge command reports success, but no PR reached the queue.
- A list response and a single-PR read report different merge state for the same PR.
- Required contexts never post, appear twice, or show an old failure beside a newer success.
- `mergeStateStatus=BLOCKED` with green CI and unresolved review threads may remain.
- Rulesets and classic branch protection impose a stricter union than either UI view suggests.
- A new required workflow creates a bootstrap deadlock because the required context does not yet
  exist on the target branch.
- Commit identity/signing, DCO, or PR-vs-issue labels keep a policy gate red.
- A shared queue encounters an auto-merge request it does not own.
- The latest branch is clean locally but merge-result CI fails after main drifts.
- Auto-merge is already armed, protocol ceremonies (a final review record, thread resolution) remain, and you must order them.
- A decorative state label shows a non-mergeable verdict while the armed merge stays pending, and you must decide whether that label gates the merge.

## Verified Workflow

1. **Capture the reviewed head.** Record PR state, head OID, base, labels, review decision,
   `mergeable`, `mergeStateStatus`, `autoMergeRequest`, and the repository merge-method flags.
2. **Inspect current-head checks.** Query check runs for the recorded OID and group by exact name.
   Compare only the latest completed run per required context. A status rollup may retain stale
   failures or cancelled duplicates.
3. **Resolve the policy union.** Inspect both repository rulesets and classic branch protection:
   required contexts, strict/current-head behavior, approval counts, dismissal rules, signed
   commits, conversation resolution, and allowed merge methods. The stricter applicable rule wins.
4. **Check non-CI blockers.** List unresolved review threads, missing human approvals, draft state,
   merge conflicts, required labels, commit signature/DCO failures, and required environments.
5. **Distinguish missing from failing.** If a required context never runs because of events or
   path filters, waiting cannot fix it. Correct the workflow/check-name contract or stage a safe
   policy transition after the context exists on the target branch.
6. **Respect ownership.** If another actor has an auto-merge request, a shared queue must not
   enable, disable, adopt, replace, or poll it as its own. GitHub exposes no conditional disable
   token that proves ownership across a race.
7. **Revalidate immediately before mutation.** Require `OPEN`, the expected head OID, unchanged
   policy, current checks, and any queue interlock. Apply state only within explicit authority.
8. **Verify the mutation.** Read back the auto-merge request or merge result, confirm the expected
   method/head, and continue monitoring current-head gates. On a queue-protected base, a null
   `autoMergeRequest` does not mean the arm failed; check `mergeQueueEntry` instead.

### Read-only snapshot

```bash
gh pr view <PR> --json state,isDraft,headRefOid,baseRefName,mergeable,mergeStateStatus,reviewDecision,autoMergeRequest,labels,statusCheckRollup
gh api repos/<OWNER>/<REPO> --jq '{allow_squash_merge,allow_merge_commit,allow_rebase_merge,allow_auto_merge}'
gh api repos/<OWNER>/<REPO>/rulesets
gh api repos/<OWNER>/<REPO>/branches/<BASE>/protection
gh api repos/<OWNER>/<REPO>/commits/<HEAD>/check-runs
```

List review threads via GraphQL and treat every unresolved, non-outdated thread as a blocker when
conversation resolution is required. Reply with the fixing commit/evidence before resolving a
thread; then refresh because merge state may briefly become `UNKNOWN`.

### Merge-method and check rules

- Detect allowed methods from repository settings; never hardcode a personal preference.
- A required check is identified by its exact posted name, not workflow filename or guessed job ID.
- `strict_required_status_checks_policy=false` can allow a prior-SHA success; if current-head
  validation is intended, require the strict/current-head policy explicitly.
- When a check is rerun, select the newest run for the PR head by timestamp/ID. Do not call a stale
  red entry an active failure.
- If CI tests the synthetic merge result, reproduce by integrating current main and running the
  exact job command. A clean branch-only run is not equivalent.

### Queue ownership and direct review

GitHub's enable-auto-merge mutation can include an expected head, but disable-auto-merge has no
equivalent ownership nonce. Reading `autoMergeRequest` later cannot prove which actor owns it.
Therefore a shared queue fails closed whenever `autoMergeRequest` is non-null. It may perform a
separately authorized conditional normal merge against the reviewed head, but must not disturb
the external request.

An exact review GO establishes the requested verdict on the reviewed OID. Before any merge action,
separately prove merge authority, current head identity, required checks, human review count, and
queue/auto-merge ownership.

### Repository-forced queue admission

On a queue-protected base, direct merge mutations are structurally rejected. The REST
`PUT /repos/<OWNER>/<REPO>/pulls/<N>/merge` call returns HTTP 405 with
`Repository rule violations found: Changes must be made through the merge queue`. Use
`gh pr merge <N>`: the CLI detects the queue policy and enqueues the PR. Its output
`The merge strategy for <BASE> is set by the merge queue` is informational, not an error.
A repeated `gh pr merge <N>` prints `already queued to merge`; use it as the enqueued-state
signal. Poll `gh api repos/<OWNER>/<REPO>/pulls/<N>` until `merged_at` is non-null, and
treat the merge-group run for the base as the merge validation evidence.

Verify the admission through `mergeQueueEntry`, not `autoMergeRequest`:

```bash
gh api graphql -f query='
query($n:Int!){repository(owner:"<OWNER>",name:"<REPO>"){
  pullRequest(number:$n){mergeStateStatus mergeQueueEntry{state position}}}}' -F n=<PR>
```

GitHub leaves `autoMergeRequest` null for a PR that a queue owns. A null value therefore looks
like a failed arm. A `mergeQueueEntry` with a state and position proves the admission. Use
`--auto` alone. The queue supplies the method, so a method flag adds only the informational
strategy message. The flag is `--auto`; `--auto-merge` is rejected as an unknown flag. Read merge
state per PR with `gh pr view`. A list response can report `BLOCKED` for a PR that a single-PR
read reports as `CLEAN`.

### Ordering against an armed merge

An armed auto-merge fires as soon as the last gate clears. It does not wait for
remaining protocol steps. When ceremonies remain:

- Deliver each remaining record before you clear the final gate. For example,
  publish the terminal review before you resolve the last foreign thread.
- Or disarm, complete the ceremonies, and re-arm.
- Do not schedule ceremony work after the gate that the armed merge watches.

Treat decorative state labels as non-gating unless a ruleset or protection rule
requires them. An armed merge does not wait for them, and their presence or
absence does not block the merge. Only labels that policy requires are blockers
(see the PR-vs-issue label blocker below). Check the policy union before you
read any label as a gate.

### Common blockers

- **Unresolved threads:** all checks green but conversation-resolution policy blocks merge.
- **PR-vs-issue label:** policy reads pull-request labels; applying the same label to the linked
  issue does not satisfy it.
- **Signature/DCO:** author, committer, signing key, and trailer policy disagree; verify the commit,
  not only local configuration.
- **Bootstrap:** a PR cannot satisfy a newly required context that is not emitted by the target
  branch. Land the workflow first, observe the exact context, then require it.
- **Advisory gate:** move advisory diagnostics outside the required aggregate rather than weakening
  the required gate's meaning.
- **Truncated automation:** an empty review-thread result is not success unless logs reached the
  tool's explicit analysis-complete marker.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Treat `mergeable=true` as merge-ready | Treat `mergeable=true` as merge-ready | Policy, review, checks, or threads may still block | Inspect every layer on the current head |
| Trust the status rollup at face value | Trust the status rollup at face value | It can contain stale and duplicate runs | Group exact names and select latest per head |
| Wait for a required check that never triggers | Wait for a required check that never triggers | No check event will ever post | Repair event/path/name wiring or stage policy |
| Hardcode `--rebase` or `--squash` | Hardcode `--rebase` or `--squash` | Repository settings can forbid it | Detect allowed merge methods first |
| Resolve a review thread without a reply | Resolve a review thread without a reply | Evidence and reviewer context are lost | Reply with the fix, then resolve and refresh |
| Put the GO label on the linked issue | Put the GO label on the linked issue | PR policy reads PR labels | Mutate and verify the pull request label |
| Disable an external auto-merge request | Disable an external auto-merge request | No conditional disable proves ownership | Shared queue fails closed and stands down |
| Direct merge on a queue-only base | Called the REST merge mutation against a merge-queue repository | The repository rule rejects every direct merge method with HTTP 405 | `gh pr merge <N>` detects the queue policy and enqueues; confirm with `already queued` |
| Read a queued PR as unarmed | Armed auto-merge, read back `autoMergeRequest`, saw null, and re-armed | A queue-owned PR leaves `autoMergeRequest` null by design | Verify with `mergeQueueEntry` state and position, not `autoMergeRequest` |
| Batch-arm with the wrong flag | Looped `gh pr merge --auto-merge` and piped the output | `--auto-merge` is not a flag; the piped error hid every failed call | Use `--auto` and confirm each PR reached the queue |
| Call empty review output clean | Call empty review output clean | The tool may have truncated before analysis | Require its completion marker |
| Clear the final gate before the terminal record | Resolved the last foreign thread while the terminal review publication still pended under an armed merge | The armed merge fired within minutes of the gate clearing and landed before the ceremony completed | Deliver remaining records before the final gate clears, or disarm and re-arm |
| Read a decorative state label as a merge gate | Expected a non-mergeable state label to hold an armed merge | The label was not policy-required; the armed merge stayed pending and ignored it | Check the policy union for label requirements; gate on reviews, threads, and checks |

## Results & Parameters

| Parameter | Rule |
| --- | --- |
| Identity | Repository, PR number, base, and reviewed head OID |
| Check selection | Exact required name; newest run on current head |
| Protection | Union of applicable rulesets and classic protection |
| Review | Required count plus unresolved-thread policy |
| Merge method | One enabled by target repository settings |
| Auto-merge ownership | Non-null external request makes shared queue stand down |
| Queued-PR readback | `autoMergeRequest` null is expected under queue ownership; use `mergeQueueEntry` |
| Arming flag | `--auto` only; the queue sets the method and `--auto-merge` is invalid |
| Mutation precondition | PR open, head unchanged, gates current, authority explicit |
| Bootstrap ordering | Emit context on target branch before requiring it |
| Ceremony ordering | Deliver remaining records before the final gate clears, or disarm and re-arm |
| Label gating | Only policy-required labels block; decorative state labels do not |
| Verification | Read back request/result and continue current-head monitoring |

The successful outcome is either a precisely identified blocker with a safe remediation, an
auto-merge request armed by its authorized sole owner, or a conditional merge/queue admission tied
to the reviewed OID. Project-specific state machines and command transcripts are in the notes.
