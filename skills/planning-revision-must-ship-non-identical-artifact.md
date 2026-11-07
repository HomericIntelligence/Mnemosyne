---
name: planning-revision-must-ship-non-identical-artifact
description: "Revise a rejected plan, design, or review artifact so the new revision is not byte-identical to the one already rejected, and so it recites none of that revision's stale premises. Use when a prior review reports that several rounds saw an unchanged artifact, when a revision instruction asks for a plan-level restructure but the regenerated text can stay the same, when a regeneration path re-emits the retained text, and when a cited evidence anchor may have moved between revisions."
category: architecture
date: 2026-11-07
version: "1.0.0"
user-invocable: false
license: BSD-3-Clause
verification: verified-local
tags: [plan-revision, re-plan, nogo-response, identical-artifact, stale-premise, premise-recheck, evidence-anchor, retention, regeneration, revision-label]
---

# Planning: A Revision Must Ship a Non-Identical, Re-Verified Artifact

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-11-07 |
| **Objective** | Stop a re-plan round from spending a review round on text that no finding can change, and stop a revised artifact from reciting the premises that the prior review already rejected. |
| **Outcome** | Operational rule set stated as deterministic pre-publication checks. |
| **Verification** | verified-local: the checks were executed against one retained plan artifact and its review history; no revision package was published. |

A revision label is bookkeeping. A reviewer decides from the artifact text. When the text does not change, the review can only repeat the prior disposition. This rule is the plan-revision counterpart of a premise check: the reviewer has already converted each finding into a claim about the tree, and the revised artifact must show that the claim now holds.

## When to Use

- A prior review reports that the artifact is unchanged across consecutive rounds, or that no prior finding was addressed.
- The revision instruction names a structural change, but the regeneration path can still emit the retained text.
- The retained text contains an evidence claim of the form "X is absent", "X is new", or "X names N items", and merges can land between rounds.
- A consumer reads the artifact mechanically, such as a body-extraction pattern or a machine-checked table row.
- A deeper rule already covers part of the problem: use this entry for the artifact-identity question only. Use a premise-verification entry for how to prove one claim, and a post-review verification entry for how to prove one implementation detail.

## Verified Workflow

### Quick Reference

```text
Before you publish a revision of a rejected artifact:
1. diff    compare the new text with the retained revision; an empty diff means do not publish.
2. restate re-read every prior blocking finding and mark how the new text answers it.
3. rebind  re-run each build-time evidence claim at the current default-branch head.
4. preserve name every retained behavior with the file:line of its consumer.
5. reclean remove claims about deleted or relocated anchors that were never verified at the new head.
6. spot    spot-check a mechanically consumed surface (an extraction pattern, a checked table) in the new text.
```

### Steps

1. **Diff the artifact against the retained revision first.** A revision that differs only in a label or a version stamp is still the rejected artifact. Change at least one substantive claim, scope statement, or evidence citation. If you cannot name the substantive change, you have not revised.
2. **Restate each blocking finding in one line and cite where the new text answers it.** A finding with no answer becomes an unanswered finding, and the next review repeats it.
3. **Re-bind every build-time evidence claim.** An artifact records the tree at authoring time. Check each cited path, symbol, and count at the current head. Record the head in the artifact or the change summary. A claim that a file is absent or a feature is new is the most perishable claim class: verify it before you keep it.
4. **Name the retained behaviors and their consumers.** When the existing artifact already delivers part of the requirement, state each retained behavior with the `file:line` of its consumer. This prevents a restructure from silently dropping verified work, and it tells the reviewer that the removal or change is deliberate.
5. **Remove dead anchors.** A cited runbook, inventory file, or gate that a later change deleted must not survive in the revision, in a rollback note, or in a documentation target. Retarget the change to the page or module that owns the subject now.
6. **Spot-check the mechanically consumed surface.** If a test or a script parses the artifact or its companion, run the parser against the new text before publication. A new section can break a fixed-shape reader even when the prose is correct.

### Decision table

| Observation | Action |
| --- | --- |
| New text equals the retained text except for a label | Do not publish; make a substantive change or report a blocker |
| A finding is answered nowhere in the new text | Add the answer or withdraw the finding with evidence |
| An "absent" or "new" claim fails at the head | Rewrite the claim and its consequence |
| A retained behavior has no named consumer | Find the consumer, or remove the behavior with evidence |
| A cited anchor no longer exists | Retarget or drop the claim |
| The consumer parser fails on the new text | Repair the text, not the consumer, unless the consumer is also in scope |

### If a step is unavailable

- No local checkout at the current head: state the limit in the artifact and keep the prior citation with its authoring commit.
- A consumer cannot run locally: record the parser contract and request the gate result from the pipeline that owns it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Answer a NOGO by regenerating the same plan text | The revision was recorded as a new revision, and the body was reproduced from the retained artifact | The reviewer graded the body, which was identical, and returned the same disposition for a third round | Diff the text first; a label is not a revision |
| Ask for a structural change without changing the emitted text | The instruction named a restructure, but the retained body still satisfied the format | The structural request was invisible to the reviewer | Convert a structural instruction into a checkable text delta, such as a removed section, a changed scope row, or a new named consumer |
| Keep a build-time "file is absent" claim into an older-base revision | The claim was true when the artifact was written and false at the head | The reviewer verified the head and rejected the whole evidence basis | Treat "absent" and "new" claims as the first class to re-check |
| Restructure a change that the base already delivered | A greenfield plan was written against a base that already had the script | The reviewer reported that the plan would regress merged behavior | Name each retained behavior with its consumer before you plan a replacement |

## Results & Parameters

- Revision check: `git diff` shows the change in one line when both revisions are saved; an empty result blocks publication.
- Head pin: record the default-branch commit that the evidence claims were verified against.
- Consumer spot-check: run the repository's own parser or checked-table test against the new text, not a hand inspection.
- Finding ledger: one line per prior blocking finding, with the answering location or a withdrawal reason.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| Issue-planning exchange | A plan stayed unchanged across three consecutive reviews while a restructure was requested, and its evidence claim that the subject script was new was stale at the head | verified-local: the diff, the re-bound claim, the deleted-anchor sweep, and a mechanically consumed documentation surface were all checked; no revision package was published |