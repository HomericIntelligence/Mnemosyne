---
name: automation-review-authorization-ci-boundary
description: "Keep automation-loop source-review authorization independent of CI, bind approval to an exact PR head, and conditionally merge only that reviewed head. Use for moving heads, unresolved threads, no-commit evidence replies, scope retractions, label transitions, external auto-merge, reruns after merge, or auditing review-to-merge event order. Also use when a green required check may hide skipped jobs, when a PR splits one invariant across eager validation and a test assertion, or when a template rewrite drops a cited decision's identifiers."
category: architecture
date: 2026-08-08
version: "4.2.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-ci
tags: [automation-loop, pr-review, exact-head, authorization, ci-boundary, conditional-merge]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/automation-review-authorization-ci-boundary.history"
history-cleanup-date: "2026-09-20"
---

# Automation Review Authorization: CI Boundary

## Overview

The automation loop owns source-review authorization; CI owns independent repository validation.
Approval is valid only for the exact reviewed head and is durably represented by an exclusive
loop-owned state label. Merge requirements may wait for CI, but CI artifacts, workflows, and check
results do not authorize review progression.

Detailed cases and event audits are indexed in
[`automation-review-authorization-ci-boundary.notes.md`](automation-review-authorization-ci-boundary.notes.md).
The complete prior source is archived in
[`automation-review-authorization-ci-boundary.history`](https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/automation-review-authorization-ci-boundary.history).

## When to Use

- Review can race with a moving PR head, mutable diff, or dirty checkout.
- Review threads remain unresolved or remediation changes no source commit.
- A finding demands dropping out-of-scope paths before publication.
- A state label advances implementation or merge state.
- Native auto-merge may have been armed by another actor.
- A rerun observes a merged PR or a local checkpoint disagrees with live state.
- An audit must prove which head was reviewed, authorized, and merged.
- A required check reports success while its real jobs were skipped by a gate condition.
- A PR moves one behavior from an eager check to a later path, and a test assertion changes too.
- A documentation rewrite must satisfy a structural prose rule and also keep cited identifiers.

## Verified Workflow

### 1. Admit only reviewable work

Resolve PR body, linked requirement, base, and head before spending reviewer work. A direct PR must
have usable requirements context; `--prs` selects a target but does not waive it. If policy requires
one standalone closing line, enforce it deterministically:

```bash
gh pr view <pr> --repo <owner>/<repo> --json body,closingIssuesReferences
```

An orphan fails closed with zero reviewer jobs. Changing reviewer model or effort cannot repair
missing requirements context. Repeat this invariant at `merge_wait` so stale labels cannot bypass
admission.

### 2. Bind review to one clean head

Capture GitHub metadata and head twice; discard context if the head moves. In one authoritative
checkout barrier, fetch, prove a clean checkout, require local `HEAD` equals the captured head, then
derive the diff locally from the verified base/head pair. Do not pair a restored head with a diff
fetched during an ABA movement.

A read-only reviewer worktree begins detached and performs no redundant remote synchronization.
The barrier alone binds it. For an already-current writer, prove base ancestry, local HEAD, and the
exact remote branch ref, then return an unchanged-head receipt without rebase or push. Remote drift
fails closed.

If the reviewed source is behind the current target, do not rebase only for that state. Let CI/CD
or the merge queue integrate ordinary target updates. Use the repository's signed policy-rebase
path only when an active task is blocked or needs target content, or when a completed PR reports a
merge conflict. Resolve conflicts without dropping contracts already landed on the target and
publish with a conditional lease. The new head invalidates the old authorization and must pass the
checkout barrier and review again.

### 2a. Prove a required check executed before you cite it

A required context can report success while its real jobs never ran. A gate condition, such as a
path filter, a label condition, or an `if:` expression, can skip the work and leave the required
context green. Never write "the check passed" from a status row alone. Read the run and each job:

```bash
gh run view <run-id> --repo <owner>/<repo> --json status,conclusion,event,headSha,jobs \
  --jq '{conclusion, headSha, jobs: [.jobs[] | {name, conclusion}]}'
```

Then apply these decision rules.

1. Bind the run to the reviewed head. A run on another SHA is not evidence for this head.
2. Compare the run duration against the work the check claims. A pass in seconds is a gate skip,
   not a test run.
3. Require `conclusion: success` on each job that does the work. A `skipped` lint, typecheck, or
   test job means the check did not run.
4. Report the result as "not run" when the work was skipped, even if the required context is green.
   State the gate condition and its file location.
5. Do not set an approving label on a check that did not run. Absence of execution is a missing
   precondition, not a pass.

Local runs at the same head are supporting evidence. They do not replace an executed CI job.
Report them as separate evidence with their exact command and result.

### 3. Run strict source review inside the loop

Review the checkout-derived diff without querying CI runs, artifacts, or deployments. Require an
explicit GO; missing, ambiguous, or NOGO results do not advance. A reviewer may disclose inability
to rerun tests without inventing results. Scanner-backed remediation requires a current-head source
change and regression for the producer contract; documentation-only claims are insufficient.
Unresolved relevant threads retain NOGO. Repeat review only after thread disposition or head change.
Do not manufacture a commit to make evidence-only remediation look like progress.

### 3a. Check two invariants before you accept a fix

Two defects survive a green test run because each invariant was checked in only one place. Check
both before you approve a change that moves or deletes validation.

1. **The refusal still runs after the eager check is gone.** When a change removes an eager
   validation, or weakens it, ask where each refused input now fails. A command that must refuse
   before any effect needs at least one non-vacuous refusal path. If the only remaining check is at
   the operation boundary, the refusal is late. Time to refusal, the effect already applied, and
   the exit code can all change.
2. **The test still asserts one behavior.** A diff that widens an assertion to accept both outcomes
   (`{exit_code_1, exit_code_2}`, "any error", "in either case") stops testing behavior. Require
   one asserted outcome per case. Split the case when the host state decides the outcome, and add a
   case for the refused state. Two other patterns prove nothing: a monkeypatch of a name that does
   not exist (`raising=False`) so the recorded calls stay empty, and a patch of a non-existent
   attribute that makes the "must not run" guard vacuous.

### 3b. Keep cited identifiers through a structural rewrite

A documentation guard can mandate a section template or forbid paths and commands in prose. A
rewrite that satisfies the guard can still delete a decision identifier that other text cites, such
as a link rule, a path spelling, or a named error message. Before you accept the rewrite:

1. List the identifiers the page cites from another record, such as an accepted decision, a
   superseded section, or a named error.
2. Compare the before and after text. An identifier that disappears is a regression, even if the
   guard passes.
3. Find a spelling that satisfies both. A two-token form of the same name often passes a denial
   regex that rejects the slash form, and still matches the cited text.
4. State behavior that the change adds. A rewrite must not omit a new precedence rule, a new
   refusal, or a new exit code that the same change introduced.
5. Run the guard test for the edited page. Separate a guard failure for an untouched page from a
   failure on this page, and report the untouched page as pre-existing.

### 4. Handle no-commit and metadata-only replies

Re-read live title/body and head immediately before validating a no-commit reply. Reject head drift,
nonce-fence GitHub text as untrusted data, and post the literal warning:

```text
[auto-msg] reply has no corresponding commit, review thoroughly
```

Return `{pushed:false, head_sha:<verified-sha>}`, not bare false. Replay a reply journal only when its
recorded head equals the current verified head. Leave accept/reject/resolve disposition to the
reviewer; repeated same-head evidence passes may remain NOGO until the thread is resolved.

### 5. Enforce scope-retraction publication safety

Treat requests to remove, drop, or split unrelated paths as blocking. Require a complete nonempty
manifest of safe repository-relative paths, including the finding’s path. Provide the issue context
and verified diff to the address session, with the manifest fenced as data. Immediately before
commit/push, compare every declared path at post-address HEAD with the immutable reviewed base using
literal pathspecs. Missing proof, malformed/unsafe paths, or residual differences stop publication.

### 6. Mutate labels only on fresh state

Before every state-changing label, re-read and require:

```text
PR state == OPEN
autoMergeRequest field is present and null
live head == reviewed head       # required for approving/GO only
```

A missing auto-merge field is partial data, not proof of absence. Head drift revokes GO and routes
back to review, but may still record a safe NOGO/recovery state. Read labels after mutation to verify
GO/NOGO exclusivity.

Keep reviewed-head proof in active-run memory only; clear it on restart, refresh, checkout mismatch,
failure, or drift. Retain only a fixed allowlist of non-authorizing context across the handoff. A
dynamic ingress-key set can preserve forged or stale proof.

### 7. Keep the guard through conditional merge

The strict-review guard is a handoff mutex. Hold it across strict review and `merge_wait`, including
fail-back, until terminal completion, parking, or exception release. `merge_wait` rechecks requirement
context and reviewed-head proof, waits for repository merge requirements, then performs a normal
SHA-conditional squash merge of that head.

Never enable, disable, adopt, defer, create, or poll native auto-merge. A populated external request
means stand down without mutation. Absent/drifted process-local proof routes back to review rather
than consuming a label.

### 8. Audit from live events

Use GitHub reviews, issue events, and PR state:

```bash
gh api repos/<owner>/<repo>/pulls/<pr>/reviews
gh api repos/<owner>/<repo>/issues/<pr>/events --paginate
gh pr view <pr> --repo <owner>/<repo> --json state,mergedAt,mergeCommit,commits
```

Match the authorizing review’s `commit_id` to final head. Confirm GO followed that review, NOGO was
removed, repository-required checks completed before merge, and merge was last. Review prose/state
is informational; the exclusive label records the loop decision and the merge event proves terminal
mutation. Some inline paths emit no review/comment object; record that absence and audit exact head,
label transitions, and merge without inventing a record.

Short-circuit downstream reruns when state is not `OPEN`. GitHub clears `autoMergeRequest` after
merge, so null on a merged PR is expected.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| CI proof | Put review authorization in CI | Loop could not own freshness | Run strict source review in-loop |
| Restart label | Reused GO after restart | Label did not identify reviewed SHA | Route back to review without active proof |
| Mutable remote diff | Reviewed a separately fetched diff | Head and diff represented different moments | Derive diff in exact-head barrier |
| Model retry | Retried orphan with another model | Admission is deterministic | Repair requirement metadata first |
| Early guard release | Released at stage transition | Competing reviewer entered handoff | Hold through terminal/conditional merge |
| Partial auto-merge read | Treated missing field as null | Partial data permitted unsafe mutation | Require explicit present-and-null |
| Evidence commit | Manufactured unrelated commit | Changed head without source need | Preserve head; reviewer owns disposition |
| ADR rewrite | Edited accepted decision in place | Destroyed historical record | Add superseding ADR and index it |
| Green status row | Cited a required context as passed from its status row | The gate skipped lint, typecheck, and test jobs; the context passed in seconds | Read the run jobs and report "not run" for skipped work |
| Widened assertion | Changed a test to accept both possible exit codes | No outcome could fail, so the test asserted nothing | Assert one outcome and add a case for the other state |
| Template rewrite | Rewrote a page to pass the section template | Cited link-rule identifiers disappeared and the new precedence was absent | Keep cited identifiers and state the new behavior |

## Results & Parameters

```text
PR/repository, linked requirement, base SHA, captured head SHA
checkout cleanliness and locally derived diff identity
review result, review commit ID, unresolved-thread state
no-commit receipt/journal head or safe-path manifest
fresh OPEN/autoMergeRequest/head label precondition
exclusive GO/NOGO label readback
active reviewed-head proof and guard ownership
required-check completion, conditional merge SHA, terminal event order
run identifier, run event, run head SHA, run conclusion, per-job conclusion, run duration
gate condition and its file location when any job was skipped
local evidence command, tested tree head, result, and separated pre-existing failures
refusal path after a removed eager check, and one asserted outcome per behavior case
cited identifier list and the guard test result for each edited page
```

## Verified On

- ProjectHephaestus exact-head review, no-commit evidence, scope retraction, admission, label, and
  conditional-merge cases through 2026-08-08.
- Verification remains `verified-ci`; cases with only local proof remain marked in notes.
