---
name: github-auto-merge-ci-gating-merge-method
description: >-
  Diagnose why a GitHub pull request does not merge when checks, reviews, merge methods,
  rulesets, classic protection, labels, signatures, or queue ownership disagree. Use before
  arming auto-merge or admitting a reviewed head to a repository-owned merge queue, when a
  merge command with an explicit method is rejected because the queue owns the method, when
  protocol ceremonies remain while a merge is already armed, when a decorative state
  label may be mistaken for a merge gate, when a label-gated workflow keeps failing
  after the label changed, when every check is green but the merge state stays
  `BLOCKED` because a checkless rule such as `required_signatures` rejects an
  unverified commit, or when a reviewer must decide whether to set the GO label
  after a required check was claimed as a success before that check ran.
category: ci-cd
date: 2026-07-30
version: "2.8.0"
user-invocable: false
verification: verified-ci
license: BSD-3-Clause
tags: [auto-merge, github, ci-cd, merge-method, required-checks, rulesets, review-threads, current-head-checks, merge-queue, toctou, armed-merge-race, ceremony-ordering, label-gating, cancelled-leg, checkless-rule, required-signatures, commit-verification, claim-before-check, verdict-time-check-state, stale-check-claim]
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
- Every check is green and the PR is mergeable, but the state stays `BLOCKED` or `UNKNOWN` because
  a checkless rule such as `required_signatures` fails on an unverified commit and emits no check
  run to point at.
- Rulesets and classic branch protection impose a stricter union than either UI view suggests.
- A new required workflow creates a bootstrap deadlock because the required context does not yet
  exist on the target branch.
- Commit identity/signing, DCO, or PR-vs-issue labels keep a policy gate red.
- A shared queue encounters an auto-merge request it does not own.
- The latest branch is clean locally but merge-result CI fails after main drifts.
- A required aggregate check fails because one upstream matrix leg was cancelled at a job or
  workflow timeout, while every other leg passed and auto-merge stays armed.
- Auto-merge is already armed, protocol ceremonies (a final review record, thread resolution) remain, and you must order them.
- A decorative state label shows a non-mergeable verdict while the armed merge stays pending, and you must decide whether that label gates the merge.
- A verdict comment reports a required check as a success, but that run started after the comment, and the GO label decision depends on which result is real.

## Verified Workflow

1. **Capture the reviewed head.** Record PR state, head OID, base, labels, review decision,
   `mergeable`, `mergeStateStatus`, `autoMergeRequest`, and the repository merge-method flags.
2. **Inspect current-head checks.** Query check runs for the recorded OID and group by exact name.
   Compare only the latest completed run per required context. A status rollup may retain stale
   failures or cancelled duplicates.
3. **Resolve the policy union.** Inspect both repository rulesets and classic branch protection:
   required contexts, strict/current-head behavior, approval counts, dismissal rules, signed
   commits, conversation resolution, and allowed merge methods. The stricter applicable rule wins.
   Classify each rule as **check-emitting** or **checkless**. A checkless rule has no context and
   emits no check run, so no rollup or check query can show that it is unsatisfied.
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
conversation resolution is required. A thread blocks merge even with a passing review verdict and
green checks. The acting agent owns the closure and needs no owner approval: verify each finding
against the current head, reply with one line of evidence (the fixing commit, or the reason the
finding no longer applies), and resolve the thread; then refresh because merge state may briefly
become `UNKNOWN`.

A permission-classifier denial of an action is not a repository rule that a human must approve it.
Do not bypass the denial and do not invent an approval requirement. Retry only through the normal
authorized path, and read the repository and user instructions to learn what is really required.

### Merge-method and check rules

- Detect allowed methods from repository settings; never hardcode a personal preference.
- A required check is identified by its exact posted name, not workflow filename or guessed job ID.
- `strict_required_status_checks_policy=false` can allow a prior-SHA success; if current-head
  validation is intended, require the strict/current-head policy explicitly.
- When a check is rerun, select the newest run for the PR head by timestamp/ID. Do not call a stale
  red entry an active failure.
- If CI tests the synthetic merge result, reproduce by integrating current main and running the
  exact job command. A clean branch-only run is not equivalent.

### Cancelled-leg blocker on an armed merge

A required aggregate check can fail because one upstream matrix leg was cancelled, not because
content broke. The signature: every completed leg is green, one leg is `cancelled`, and the
aggregate failure message names the cancelled leg (for example `required job did not succeed:
<leg> ('cancelled')`). The usual cause is a job or workflow timeout after a runner hang.

Classify before you act:

1. List the tests the cancelled leg owns. If none of them touch the change surface, the cancel
   is probably environmental.
2. Read the same leg's duration on a recent green run at a nearby head. A leg that completes in
   minutes there did not hang for hours because of a change outside its surface.
3. If both checks agree, rerun only the failed and cancelled jobs:
   `gh run rerun <run-id> --failed`. An armed auto-merge fires when the leg returns green.
4. If the leg owns changed tests or the comparator is inconclusive, treat the failure as real
   and debug the hang as a content problem.

Do not rebase, push, or disable the armed request to clear this blocker: none of them repairs
a cancelled leg, and a push discards the reviewed head.

### Label-gated workflow after a label change

A workflow gate that reads `github.event.pull_request.labels` is satisfied or refused from the
event payload, not from live label state. Two consequences:

- A re-run replays the original payload. `gh run rerun <run-id> --failed` after a label change
  reports the old decision again. The gate fails again with the previous label set in its `env`.
- The label event itself starts a fresh run with the current labels. Read that run as the evidence.

Classify a label-gate failure before you touch content:

1. Read the failing step's `env` block in the log. If it lists the superseded label set, the gate
   rejected the past state. It is not a content regression.
2. Select the run whose `created_at` is after the label mutation for the same head OID. Require a
   success in that run, not in a re-run of an older one.
3. Arm auto-merge after that success. Do not push, rebase, or edit the label to force a new event.

A draft pull request cannot receive the state label, so a gate that needs the label does not start. Mark the pull request ready first.

CI checks out the pull request head, not a merge with the base. If the base branch merged a new CI script after the branch point, the head lacks that script and lint fails. Merge the base branch into the head. That push moves the head and voids an earlier GO, so review the new head again.

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

`gh pr merge --squash` on a queue-protected base without `--auto` prints
`The merge strategy for <BASE> is set by the merge queue` and exits with a non-zero status. That
message is the queue signal for the direct form too. Do not read the non-zero exit as a policy
failure, and do not try another method flag. Repeat the command with `--auto`. The second call
prints `already queued to merge` when the first call changed nothing, and the PR state stays
`OPEN` until the queue merges it.

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

### Checkless rules block without a red check

A ruleset can require a property that GitHub evaluates itself and never reports as a check
context. `required_signatures` is the common case: the rule carries no `parameters` and no
context, and it fails the merge on every commit whose signature the forge cannot verify.

The symptom is a merge state that stays `BLOCKED` or `UNKNOWN` while every check conclusion is
`SUCCESS`. Do not treat that combination as a flaky rollup or a pending mergeability
calculation. Check the two properties directly:

```bash
# A checkless rule has null parameters and no context.
gh api repos/<OWNER>/<REPO>/rules/branches/<BASE> \
  --jq '.[] | select(.type=="required_signatures") | .parameters'
# Confirm no check run represents the rule.
gh api repos/<OWNER>/<REPO>/commits/<HEAD>/check-runs \
  --jq '[.check_runs[].name] | map(select(test("sig|sign";"i")))'
# Verify the commit itself, not the local signing configuration.
gh api repos/<OWNER>/<REPO>/commits/<HEAD> --jq '.commit.verification'
```

An empty `parameters`, an empty name match, and `verified: false` together identify the blocker.
Repair is a signed rewrite of the head; re-signing does not change file content. Do not wait for
a check to turn green, because no check exists to turn green.

### Common blockers

- **Unresolved threads:** all checks green but conversation-resolution policy blocks merge.
- **PR-vs-issue label:** policy reads pull-request labels; applying the same label to the linked
  issue does not satisfy it.
- **Signature/DCO:** author, committer, signing key, and trailer policy disagree; verify the commit,
  not only local configuration.
- **Checkless signature rule:** `required_signatures` blocks an unverified commit with no check
  run and no context. A fully green rollup does not satisfy it.
- **Bootstrap:** a PR cannot satisfy a newly required context that is not emitted by the target
  branch. Land the workflow first, observe the exact context, then require it.
- **Advisory gate:** move advisory diagnostics outside the required aggregate rather than weakening
  the required gate's meaning.
- **Truncated automation:** an empty review-thread result is not success unless logs reached the
  tool's explicit analysis-complete marker.
- **Cancelled matrix leg:** an upstream leg cancelled at a timeout fails the required aggregate
  although content is green. Classify leg ownership and comparator timing, then rerun failed
  jobs only.
- **Stale label payload:** a label-gated workflow fails or passes from the payload labels of its
  triggering event. A re-run replays the old label set. Require a success from the run that the
  label event started on the same head.
- **Claim before check:** a verdict comment can report a required check as a success while that
  run has not started. The claim then describes no result. Read the check results before you
  accept the claim or act on the label. Compare the run `created_at` with the comment `createdAt`.
  A run that started after the comment cannot support it. When the result is a failure, record
  that failure in the verdict comment. When a prior lane already set the GO label against a
  verdict that is not a clean GO, or against checks that did not pass at that head, report the
  unmet conditions to the owner. Do not remove the label unless the task authorizes removal.

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
| Read a green rollup as "nothing left blocks" | Saw 24 `SUCCESS` conclusions with no failing context and concluded the merge state was stale | The blocker was `required_signatures`, a checkless rule with null parameters. No check run existed to fail, so the rollup was correct and irrelevant | Enumerate the ruleset rules and classify each as check-emitting or checkless before you trust a green rollup |
| Re-enqueue without changing the head | Called `gh pr merge --auto` again on the same unverified head | The queue refused admission and the command exited without a message, so a retry only masked the cause | When enqueue is silently refused on a green PR, verify the commit signature rather than re-arming |
| Call empty review output clean | Call empty review output clean | The tool may have truncated before analysis | Require its completion marker |
| Debug content for a red required check | Read the armed merge's failing required check as a content regression and started a diff investigation | The aggregate check failed only because one matrix leg hung to the workflow timeout and was cancelled; the leg owned no changed tests and ran in minutes at nearby heads | Match the gate message's cancelled leg to the change surface and a comparator run; rerun failed jobs only |
| Clear the final gate before the terminal record | Resolved the last foreign thread while the terminal review publication still pended under an armed merge | The armed merge fired within minutes of the gate clearing and landed before the ceremony completed | Deliver remaining records before the final gate clears, or disarm and re-arm |
| Read a decorative state label as a merge gate | Expected a non-mergeable state label to hold an armed merge | The label was not policy-required; the armed merge stayed pending and ignored it | Check the policy union for label requirements; gate on reviews, threads, and checks |
| Re-run to clear a label gate | Applied the required label, then ran `gh run rerun <run-id> --failed` on the pre-label run | A re-run replays the original event payload, so the gate step read the superseded label set from `env` and failed again | Read the run whose `created_at` follows the label mutation; require its success and leave the re-run out of the evidence |
| Accept a verdict's check claim of success | A reviewer comment reported `Required check: success` and a lane set the GO label. The check run started after the comment and concluded `failure` | The claim had no result behind it. Two lanes reviewed one head, so the GO decision rested on a claim, not on the check result | Read the check results at the head, compare their `created_at` with the comment `createdAt`, and state the real result. Report unmet label conditions to the owner |

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
| Cancelled-leg recovery | Classify by leg ownership plus comparator timing; rerun failed jobs only; do not push or rebase |
| Label gating | Only policy-required labels block; decorative state labels do not |
| Label-event evidence | Use the run created after the label mutation on the same head; a re-run replays the old payload |
| Verdict check claim | Accept a required-check result only from a run whose `created_at` precedes the verdict comment; a later run cannot support the claim |
| Label authority | Set the GO label only on a clean GO with passing required checks at the reviewed head; report an unmet condition instead of removing a foreign label |
| Verification | Read back request/result and continue current-head monitoring |

The successful outcome is either a precisely identified blocker with a safe remediation, an
auto-merge request armed by its authorized sole owner, or a conditional merge/queue admission tied
to the reviewed OID. Project-specific state machines and command transcripts are in the notes.
