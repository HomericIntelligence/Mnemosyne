---
name: tooling-plan-artifact-delivery-nogo
description: "A plan-producing turn followed by a /learn-or-summary step can post the WRONG artifact to the reviewer: the harness pipes your post-work reviewer-bullet SUMMARY into the issue AS THE PLAN BODY, the reviewer sees only bullets, grades it F ('risk memo, not a plan'), and NOGOs — a false NOGO caused by artifact-delivery, not design. Use when: (1) a planning step is chained with a /learn, /retrospective, or summary step and the plan lands in the wrong channel, (2) a reviewer NOGO'd a plan that reads as 3-5 bullets / a risk register with no full sections, (3) you are re-planning after a NOGO and must decide whether to emit a diff or the whole plan, (4) you see the #693 R0/R1 NOGO-exhaustion failure mode where the plan body is empty/bulletized, (5) you need to reason about which OUTPUT goes to which CHANNEL when one turn produces both a plan artifact and a reviewer summary."
category: tooling
date: 2026-07-05
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - plan-artifact-delivery
  - nogo-recovery
  - summary-vs-plan-channel
  - reviewer-bullets
  - false-nogo
  - re-plan-full-not-diff
  - harness-pipeline
  - planning
  - 693-nogo-exhaustion
---

# Tooling: The Plan-Artifact-Delivery NOGO (summary overwrote the plan)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-05 |
| **Objective** | Capture a NON-design NOGO failure mode: a plan graded F not because the design was wrong but because the WRONG artifact reached the reviewer — the harness posted the post-work reviewer-bullet SUMMARY to the issue as the PLAN BODY |
| **Outcome** | Diagnosed on ProjectHephaestus issue #1858: R0 plan NOGO'd (graded F, "this is a risk memo, not a plan"); root cause was artifact delivery, not design; re-planned to GO by re-emitting the FULL plan as the turn's final message. Plan-only — the fix is a delivery discipline, not executed code |
| **Verification** | unverified — this is a workflow/discipline lesson observed once (#1858) and reasoned from the #693 NOGO-exhaustion prior; the discipline itself was not put through a controlled A/B and no CI validates it |

## When to Use

- A **planning step is immediately followed by a `/learn`, `/retrospective`, or summary
  step** in the same harness turn, and the plan that reaches the reviewer is a handful of
  bullets rather than the full document you wrote.
- A reviewer **NOGO'd a plan that reads as 3-5 bullets or a bare risk register** with no
  Overview / approach / step sections — the review complaint is "this is a risk memo, not
  a plan," "where is the actual plan," or "empty plan body."
- You are **re-planning after a NOGO** and are tempted to post only a diff / delta ("here's
  what I changed") rather than the whole plan.
- You recognize the **#693 R0/R1 NOGO-exhaustion pattern**: rounds burned on a plan whose
  BODY never actually carried the full plan.
- You need to reason about **which output goes to which channel** when a single turn
  produces BOTH a plan artifact (for the reviewer/issue) AND a short reviewer-bullet
  summary (the post-`/learn` recap). They are different outputs to different channels.

**Trigger phrasing in a review comment:** "this is not a plan," "risk memo not a plan,"
"empty plan," "where are the steps," "graded F for missing plan body," "NOGO" on a plan
you know was complete when you wrote it.

## Verified Workflow

> **Proposed / unverified — this is a "Proposed Workflow."** This workflow has not been
> validated end-to-end. It is a delivery-discipline hypothesis drawn from a single observed
> instance (ProjectHephaestus #1858) plus the #693 NOGO-exhaustion prior. No controlled
> experiment was run and no CI enforces it. Treat as a hypothesis until a re-plan round
> confirms the discipline flips a false-NOGO to GO. (The heading is kept as
> `## Verified Workflow` only to satisfy the marketplace schema; the content is proposed.)

### Quick Reference

Before submitting a plan for review — the three-line self-check:

```text
1. Is the message the harness will POST the full plan, or my post-work summary?
2. Does the posted body contain the plan's SECTIONS, or only 3-5 bullets?
3. On a re-plan: did I re-emit ALL sections, or only the delta?
```

If any answer is "summary / bullets / delta," STOP and re-emit the full plan as the turn's
final, posted message before submitting.

### The failure mode (why a sound plan gets an F)

When a plan-producing step is chained with a summary/`/learn` step, some harnesses take the
turn's FINAL message as the artifact to post. If your final message is the short
**reviewer-bullet summary** (the 3-5 bullets a post-`/learn` recap emits), that summary —
not your plan — becomes the ISSUE/PR body the reviewer grades. The reviewer sees only
bullets, correctly judges "this is a risk memo, not a plan," and NOGOs. The design was
never the problem; the **artifact delivery** was. This is a false NOGO.

### The discipline

1. **The FINAL message of a planning turn must BE the full plan.** When a planning step is
   followed by a `/learn` or summary step, ensure the plan artifact — all sections
   (Overview, approach, steps, risks, test plan) — is the message the harness posts to the
   reviewer. Do NOT let the post-work reviewer-bullet summary be the final/posted message.
2. **Separate the two outputs by channel, explicitly.** The full PLAN goes to the
   reviewer/issue body. The short SUMMARY (the reviewer bullets, the `/learn` recap) goes
   to its own recap channel. They are DIFFERENT outputs; never let the summary OVERWRITE
   the plan artifact. If the tooling emits both, order them so the plan is what lands as the
   body, or post them to distinct sinks.
3. **On a re-plan after NOGO, re-emit the WHOLE plan — not a diff.** A NOGO round re-posts
   the body; if you post only "here's what changed," the reviewer again sees a fragment and
   re-NOGOs (the #693 exhaustion loop). Re-emit every section, with the changed parts folded
   in, so the posted body is a complete standalone plan each round.
4. **Before treating a NOGO as a design failure, check the delivered artifact.** If the
   review says "not a plan / risk memo / empty," read what actually landed in the issue/PR
   body. If it is your summary rather than your plan, the fix is delivery, not redesign —
   re-emit the full plan and resubmit. Do not spend the next round redesigning a plan that
   was never actually shown to the reviewer.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Let the post-`/learn` reviewer-bullet summary be the turn's final message | Chained a planning step with a summary/`/learn` step and ended the turn on the 3-5 reviewer bullets | The harness posted the SUMMARY to the issue as the PLAN body; the reviewer saw only bullets, graded it F ("risk memo, not a plan"), NOGO — a false NOGO caused by artifact delivery, not design | The FINAL message of a planning turn must BE the full plan; the summary and the plan are different outputs to different channels — never let the summary overwrite the plan artifact |
| Re-post only a diff on the re-plan | After the NOGO, posted "here is what I changed" instead of the whole plan | A NOGO round re-posts the BODY; a diff-only body is again a fragment, so the reviewer re-NOGOs — the #693 R0/R1 NOGO-exhaustion loop | On a re-plan after NOGO, re-emit the FULL plan (every section) with changes folded in, not a delta |
| Assume a NOGO means the design is wrong | Started redesigning the approach after the "not a plan" NOGO | The design was fine; the wrong artifact (the summary) had been delivered — redesigning wasted a round on a plan the reviewer never saw | Before treating a NOGO as a design failure, READ the delivered issue/PR body; if it's the summary not the plan, the fix is delivery (re-emit the plan), not redesign |

## Results & Parameters

- **Instance**: ProjectHephaestus issue #1858 (shared-cache repo-key lock planning). R0
  plan graded **F / NOGO** — reviewer saw only the post-`/learn` reviewer bullets, not the
  plan. Re-planned to **GO** by re-emitting the FULL plan (all sections) as the turn's final
  posted message.
- **Related prior**: the #693 R0/R1 NOGO-exhaustion failure mode (rounds burned on a plan
  whose body never carried the full plan).
- **Status**: `unverified` / discipline-only. No code, no CI. This is a delivery-channel
  discipline for plan-producing turns chained with `/learn`/summary steps.
- **Companion skills**: `architecture-metaclass-threadlocal-thread-safety` (the #1858 fix
  DESIGN whose R0 plan hit this NOGO) and `architecture-executable-convention-guard-pattern`
  (its NOGO→GO tightening sub-pattern) capture the design-side re-plan lessons; THIS skill
  captures the orthogonal artifact-DELIVERY lesson, which is a distinct search surface.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectHephaestus | Issue #1858 — R0 plan NOGO (graded F) caused by summary posted as plan body; re-planned to GO by re-emitting the full plan | Plan-only; unverified, discipline lesson (no PR, no CI) |
