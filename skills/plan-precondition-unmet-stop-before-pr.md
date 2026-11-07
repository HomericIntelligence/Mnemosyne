---
name: plan-precondition-unmet-stop-before-pr
description: "Stop before you open a pull request when an approved plan turns out to be an operator procedure with no code change, or when the artifact it modifies does not exist yet. Use at implementation start, after you read an approved plan and before you commit, to separate a missing precondition from a missing capability so you report the difference and do not manufacture scope. Also use when the plan's pass rule lists the expected fields of a generated record and you must learn offline whether the real function still produces exactly those fields."
category: tooling
date: 2026-11-01
version: "1.1.0"
user-invocable: false
tags:
  - approved-plan
  - precondition
  - blocked-work
  - decision-needed
  - no-circular-justification
  - scope-discipline
  - operational-procedure
  - pass-rule-verification
  - computed-record-fields
---

# Stop Before a PR When a Plan's Preconditions Are Unmet

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Decide at implementation start whether an approved plan can produce a pull request, and report a genuine block instead of fabricating one. |
| **Outcome** | Operational. The rule separated a missing artifact from a missing capability, produced a precise block report, and prevented an empty pull request. |

An approved plan is authorization for its own steps. It is not evidence that
those steps can run now. Approved plans are written before the work starts, so
they can name artifacts that do not exist yet and steps that no session can
perform. Read the plan for two things before you change any file: does it
contain a step that changes this repository, and does each input that step
needs exist?

## When to Use

- You are told to implement an approved plan and open a pull request.
- The plan's steps are administrative, release, or operator commands that act on a named artifact such as a release draft, a manifest, or a deployment root.
- The plan says the work happens at a future point, such as after a cut, a release, or another issue's merge.
- You must report a block and you want the report to name the real cause.

## Verified Workflow

### Quick Reference

```bash
# 1. Does the plan edit this repository at all?
grep -niE "no code change|code changes \(none\)|out of scope" <plan-file>

# 2. Does the artifact every step depends on exist right now?
test -s "<draft-or-manifest-path>" || echo "precondition unmet: artifact absent"

# 3. Is the capability absent, or only the artifact?
<probe the protected surface> || echo "capability probe: denied"
```

Treat a hit on the first command as a stop signal. Treat an absent artifact as
a reason to report the block, not a reason to create a stand-in.

### Suggested Approach

1. **Classify the plan before you touch a file.** Read the objective, the
   out-of-scope list, and every acceptance criterion. If no step edits tracked
   files, the plan is an operational procedure. A branch from that plan holds
   no change, so a pull request would be empty or invented. State this plainly
   and do not invent a code step to justify the branch.

2. **Name the load-bearing input and test that it exists.** Most operational
   plans depend on one artifact: a draft, a manifest, a staged image, a
   permission. Find it in the plan text, then check it with a read-only
   command. Use `test -s`, `ls`, a tag lookup, or a search of the tree. A plan
   that says "after the draft is created" is not executable while the draft is
   absent, even though the plan is approved.

3. **Probe the capability separately from the artifact.** An access denial
   proves a missing capability. A missing file proves a missing precondition.
   These are different findings with different owners. Do not report one as
   the other. Confirm a denial with one direct read-only probe and record its
   exact message and timestamp.

4. **Check that the plan's own citations still hold.** Approved plans carry
   `file:line` references and constants. Verify the load-bearing ones: the
   digest or value the steps use, and the file that holds the mechanism. Note
   that documentation reorganizations move or delete cited paths while the
   code paths stay valid. Record stale citations so the operator can correct
   them, but do not treat a stale doc reference as a block when the mechanism
   is intact.

5. **Use the existing test as the positive evidence.** When the plan reuses a
   function, run the tests for that function. A passing suite proves the
   mechanism the operator will use works, and it shows no new test is needed.
   That is useful evidence to hand over and it is not a code change.

6. **Re-derive the plan's pass rule with the real function, not from the
   plan text.** A pass rule that lists the fields a generated record may
   change is a prediction. Run the product's own generator, if its inputs
   are readable, against the last published artifact and the current source
   tree. Diff the two records. If a field appears or changes that the pass
   rule does not list, report it as a plan defect. Do not widen the rule
   yourself and do not assume the added field is unwanted: the renderer may
   compare it at launch. Put the measured table in the block report and ask
   whether the operator should accept the new fields or a plan revision
   should update the rule.

7. **Reconcile conflicting plan comments explicitly.** If several comments
   change the plan, use the latest only when it says it revises the earlier
   one. When the latest comment neither revises nor withdraws the plan but
   describes different commands, report the conflict and both readings. Do not
   pick a winner by recency alone.

8. **Report the block once, then stop.** Put the classification, the absent
   artifact, the denial probe, the verified evidence, the pass-rule diff, and
   the stale citations in one comment. Offer concrete options so the owner can
   choose: defer to the real execution point, revise the plan, or name a
   different deliverable. This is a report, not a request for one field.
   Finish the turn.

9. **Confirm the negative state.** Prove you made no write: the working tree
   is clean, no commit was created, no branch was pushed, and no approval
   label was set. Report the head identifier so the reader can confirm nothing
   moved.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| N/A | The direct approach was successful. Read-only classification and a single block report needed no repair. | N/A | No change was necessary. |

## Results & Parameters

### Configuration

```yaml
# What to record for a block report
block_kind: missing_precondition | missing_capability | conflicting_plan | plan_pass_rule_mismatch
load_bearing_input: "<path or artifact the plan modifies>"
input_exists: false
probe_command: "<read-only check>"
probe_result: "<exact message>"
plan_edits_repository: false
verified_evidence:
  - "<test suite that proves the reused mechanism works>"
  - "<constants that still match the tree>"
pass_rule_check:
  generator: "<function the operator command calls>"
  inputs:
    - "<last published artifact, read-only>"
    - "<current source tree>"
  declared_fields: ["<fields the plan's pass rule allows to change>"]
  measured_fields: ["<fields that actually changed>"]
  undeclared_fields: ["<fields that changed but the rule does not list>"]
stale_citations: []
```

### Expected Output

- One classification: operational procedure, or code change.
- One existence result for the load-bearing input.
- One capability probe result with its exact message.
- One pass-rule result: the fields the rule allows, the fields that actually change, and the undeclared fields.
- One clarification comment with concrete options for the owner.
- A clean working tree with no commit, no push, and no label change.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| Not applicable | General tooling rule. Repository-specific evidence is withheld. | Worked on one approved operational plan whose draft artifact did not exist. |
| Not applicable | General tooling rule. Repository-specific evidence is withheld. | A second approved operational plan declared that only derived identity fields may change. The real generator also added three provenance fields, because a source change added the values. The report named the mismatch and asked for either acceptance or a plan revision. See [notes](plan-precondition-unmet-stop-before-pr.notes.md). |

## References

- [Blocked Probe: Pinned Evidence Substitution](blocked-probe-pinned-evidence-substitution.md) — use when a substitute path can still settle the facts; this entry covers the case where none can.
- [Verify Issue Premise Before Implementing](verify-issue-premise-against-code-before-planning.md) — check the premise before planning; this entry checks executability at implementation start.
- [Live Hotfix Content-Addressed Identity Rotation](live-hotfix-content-addressed-identity-rotation.md) — computes new digests with the system's own functions for a live write; step 6 of this entry uses the same function to test a plan's pass rule before any write.