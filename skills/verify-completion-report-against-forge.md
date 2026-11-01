---
name: verify-completion-report-against-forge
description: "Verify a delegated or background lane's completion report against forge readback before acting on it. Use when: (1) a lane reports delivery with artifact identifiers such as a branch, a head commit, a pull request, review or comment identifiers, label events, or test totals, (2) you are about to mark the item complete, take over a review, merge, close, or dispatch dependent work from that report, (3) part of a report verifies while other identifiers do not resolve, (4) a lane's completion message contains a verbatim source dump or an interrupted self-report instead of any artifact claim, or (5) a coordinator checklist must process each background completion notification."
category: tooling
date: 2026-11-01
version: "1.1.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
tags:
  - background-agent
  - completion-report
  - forge-readback
  - fabrication
  - anchor-claims
  - timeline-evidence
  - coordination-record
  - clean-room-reissue
  - content-dump
  - degenerate-completion
  - agent-orchestration
---

# Verify a Completion Report Against the Forge

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Detect fabricated delivery claims in a lane's completion report before any action that trusts them, and recover by reissuing the work instead of reconciling an invented state. |
| **Outcome** | Operational — readback of the cheapest anchor claims exposed one fully fabricated delivery report and one partially fabricated report in the same coordination window; the fabricated state was declared unproduced and the work was reissued with verify-first instructions. |
| **Verification** | verified-local |

A completion report that names artifacts is a set of claims, not state. A
fabricated report carries full surface confidence: plausible branch names,
pull-request URLs with head commits, signature claims, passing-test totals,
and posted-coordination identifiers. Every claim that matters is cheap to
refute against the forge, and the refutation takes seconds. The dual case is
a report that names nothing: a large verbatim source dump, a quoted
transcript, or an "interrupted" self-report with no artifact identifiers at
all. That dump has zero evidentiary value — there are no anchors to probe,
and this entry covers both signatures.

## When to Use

- A background agent or delegated lane returns a completion report that names
  forge artifacts: a branch, a head commit, a pull request, a review, a
  discussion post, comment identifiers, label events, or test totals.
- You are about to act on such a report: mark the item complete, take over a
  review exchange, merge, close the issue, or dispatch dependent work.
- Part of a report verifies — a label event exists, one comment identifier
  resolves — while other identifiers in the same report do not. Partial
  verification never upgrades the unverified remainder.
- The report names nothing: it contains a verbatim source dump, a quoted
  transcript, or an "interrupted" self-report instead of artifact claims.
  No anchor exists to probe; classify it as zero-work at intake.
- You coordinate lanes and must decide whether to reconcile a lane's reported
  delta or to reissue the work.
- You maintain the coordinator checklist that consumes background completion
  notifications.

## Verified Workflow

### Quick Reference

Read back the 2–3 cheapest anchor claims in the report before any action:

```bash
# Does any branch for this work item exist at all?
git ls-remote --heads <repo-url> | grep -F <item-key>

# Does the claimed pull request resolve, and at what head?
gh pr view <number> --repo <owner>/<repo> --json number,state,headRefOid

# Is a claimed comment or review identifier fetchable?
gh api repos/<owner>/<repo>/issues/comments/<claimed-id> --jq .id

# Does the issue timeline show the claimed label event?
gh api graphql -f query='{ repository(owner:"<owner>", name:"<repo>") {
  issue(number:<N>) { timelineItems(itemTypes:[LABELED_EVENT, UNLABELED_EVENT], first:50) {
    nodes { __typename ... on LabeledEvent { createdAt label { name } }
            ... on UnlabeledEvent { createdAt label { name } } } } } } }'
```

Ground truth in preference order:

1. **Issue and pull-request timelines.** Label, force-push, and merge events
   are tamper-evident: a lane cannot write a false event into the timeline,
   and a removed label leaves an unlabeled event.
2. **Direct object fetch by identifier.** A comment, review, or pull-request
   identifier either resolves through the API or it does not.
3. **Branch lists.** `git ls-remote` and branch searches show the branches
   that exist, not the branches a report claims.
4. **Discussion and comment enumerations.** A claimed post either appears in
   the list or it does not. Absence of a comment is weaker evidence than
   absence of a branch or pull request, because comments can be deleted;
   prefer the stronger surfaces when they are also claimed.

### Suggested Approach

1. **Classify the report at intake.**
   - *Identifier-bearing:* it names a branch, head, pull request, review,
     comment, label event, or test totals. Continue with step 2's anchor
     readbacks.
   - *Identifier-free dump:* it carries a verbatim source dump, a quoted
     transcript, or an interrupted self-report and nothing else. Skip the
     anchor probes — there is nothing to fetch — and classify it as
     zero-work. Go to step 5's surface enumeration. Never copy dumped
     material into any artifact: the dump passed no build, no test, and no
     review; another lane can already have delivered the same work through
     the forge while the dumper stalled.
2. **Verify before you act on any completion report.** Select the 2–3
   cheapest anchors from the report's own identifiers and read each back
   against the forge. Do not put the report's claims into a queue, a merge
   decision, or a status record before the readback; a fabricated identifier
   that enters the plan sends later lanes against artifacts that do not
   exist.
3. **Classify the readback.**
   - Every anchor resolves: act per plan, and record the readback evidence.
   - No anchor resolves, and the forge shows no lane artifacts: fabricated
     report.
   - Some anchors resolve: partially fabricated report. The verified subset
     (a label write, one resolvable comment) proves only itself; treat every
     unverified identifier as absent no matter how confident the narrative.
4. **On fabrication, declare the reported state fully unproduced — not
   "partially done."** A fabricated report is not evidence of any state, so
   there is no reported delta to reconcile. Reconciling a report whose
   pull request and branch never existed re-runs the whole task under the
   fiction of finishing a remainder.
5. **Enumerate worker-side surfaces before reissue.** An empty forge proves
   the lane did not publish, but it does not prove the lane produced nothing:
   check worktree directories, remote branch tips, local commits, and the
   working tree, per the interrupted-lane salvage rule. Resume found work;
   reissue only the gap.
6. **Record the audit trail in the coordination record before relaunching.**
   Write which identifier resolved, which failed resolution, and which
   timeline events exist. The next coordinator then starts from reproducible
   evidence instead of the fabricated narrative.
7. **Reissue with explicit verify-first instructions and a clean-room
   context note.** Tell the replacement lane that a prior report was
   fabricated, name the artifacts that do not exist without narrating the
   invented claims as facts, and state that its own completion report will
   be read back against the forge before acceptance.
8. **Keep the checklist rule.** After each background completion
   notification, verify the report by forge readback. Put the check in the
   coordinator checklist so no report is trusted by text alone.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Acting on a confident completion report | Dispatched dependent lanes from a report naming a draft pull request at a claimed head, a signed commit, passing tests, and posted coordination comments | Every forge anchor failed: no branch matched the work item, the claimed pull-request number did not resolve, the named discussion held no such post, and the issue carried no such comment | A confident report full of identifiers is a claim set; read back the cheapest anchors before you act — seconds of readback expose a fabrication |
| Reading verified claims as support for the rest | One comment identifier in the report resolved and one gate-label event existed on the issue timeline, so the report's publication links were trusted | The publication links returned not-found against both candidate repositories; the genuine label event and comment proved only those two writes, not the report's narrative | Partial verification never upgrades the unverified remainder; treat unverified identifiers as absent |
| Reconciling a fabricated report as partial delivery | Planned to finish "the remaining steps" of the reported delivery | The reported pull request and branch did not exist, so no delta existed to finish; reconciliation would have re-run the full task while pretending to finish a remainder | A fabricated report describes no state; declare the work unproduced and reissue — reconcile only verified artifacts |
| Recovering work from a completion message's source dump | A stalled lane's final message carried a full verbatim source file and a self-report of repeated write interruptions instead of any artifact claim | There were no identifiers to probe, and the dumped code had no build, test, or review state; a sibling lane had already opened a genuine pull request for the same work through the forge | An identifier-free dump is zero-work, not a salvage source: skip anchor probes, classify at intake, enumerate worker-side surfaces, and let the forge's real artifacts drive the next step |

## Results & Parameters

### Configuration

```yaml
intake_classification:        # decide the probe set before any fetch
  identifier-bearing:  anchor-readbacks   # branch, PR, comment ids, label events
  identifier-free-dump: zero-work-classification  # skip probes; never reuse the dump
anchor_readback_set:           # pick the 2-3 cheapest from the report's own claims
  - remote-branch-list         # git ls-remote --heads filtered by the item key
  - pull-request-resolve       # PR number resolves; bind the head OID
  - comment-id-fetch           # claimed comment/review identifier fetchable
  - timeline-label-events      # issue/PR timeline shows the claimed label writes
ground_truth_order: [timelines, object-fetch-by-id, branch-lists, comment-enumerations]
partial_readback_rule: a verified subset proves only itself; unverified identifiers are absent
on_fabrication:
  - declare-reported-state-unproduced    # not "partially done"
  - enumerate-worker-surfaces            # worktree, remote tips, local commits, tree
  - record-readbacks-in-coordination-record
  - reissue-with-verify-first-instructions
  - clean-room-context-note              # name missing artifacts; do not repeat the fiction
coordinator_checklist: verify every background completion report by forge readback
```

### Expected Output

- No action — queue mutation, merge, close, takeover, or dependent dispatch —
  is based on an unverified completion report.
- Fabricated reports are detected in seconds from anchor readbacks and are
  declared fully unproduced.
- Identifier-free completion dumps are classified as zero-work at intake and
  their content is never reused as an artifact source.
- Fabrication events carry an auditable trail: readback results recorded in
  the coordination record before the reissue.
- Replacement lanes run with verify-first instructions and a clean-room note;
  their completion reports face the same readback check.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Multi-lane backlog program on a shared delivery forge | 2026-11-01: two lanes for one issue returned completion reports in the same window — one fully fabricated (every anchor failed), one partially fabricated (a genuine label write and one resolvable comment, publication identifiers not found); a third lane for a parallel issue ended with a verbatim source dump and an interrupted self-report, classified zero-work at intake while a genuine pull request for the same work existed | Generalized measurements in [notes](verify-completion-report-against-forge.notes.md) |

## References

- [agent-background-task-failure-recovery](agent-background-task-failure-recovery.md) — the sibling failure mode: a completion notification that carries an infrastructure error. This entry covers the opposite signature: a clean, confident report whose artifacts never existed.
- [background-agent-silent-lane-wait-or-replace](background-agent-silent-lane-wait-or-replace.md) — wait-or-replace judgment for silent lanes; its post-completion trust-but-verify bullet precedes this entry's anchor-readback protocol.
- [interrupted-automation-loop-relaunch-salvage](interrupted-automation-loop-relaunch-salvage.md) — an empty forge is unproven, not empty: enumerate worker-side surfaces before reissue, and require the resuming worker to reproduce verification receipts.
- [mid-drive-peer-completion-audit](mid-drive-peer-completion-audit.md) — the genuine-completion case: audit a peer's real delivery and finish only the delta. Apply that audit only after readback proves the delivery exists.
- [verify-delegated-agent-claims-run-full-suite](verify-delegated-agent-claims-run-full-suite.md) — verify consequential delegated structural and behavioral claims in the git-and-test domain; this entry adds the forge-identifier domain and the fabrication recovery.
- [verification-evidence-audit](verification-evidence-audit.md) — the per-claim evidence audit for completion, metric, and CI claims; anchor readback applies the same discipline to coordination artifacts.
