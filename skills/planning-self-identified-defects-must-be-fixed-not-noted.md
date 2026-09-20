---
name: planning-self-identified-defects-must-be-fixed-not-noted
license: BSD-3-Clause
description: "Correct self-identified plan defects when caveats leave inaccurate values, paths, or unsupported claims in actionable sections."
category: architecture
date: 2026-07-02
version: "1.1.0"
user-invocable: false
verification: unverified
tags:
  - planning
  - plan-verdict
  - self-identified-defect
  - addendum-not-fix
  - transparency-not-correctness
  - blocked-vs-fabricated
  - reviewer-nogo
  - fix-or-block
  - meta-rule
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/planning-self-identified-defects-must-be-fixed-not-noted.history"
history-cleanup-date: "2026-09-20"
---

# Planning: Correct Self-Identified Defects

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-02 |
| **Objective** | Prevent the anti-pattern where a planning agent flags its own plan's defects (fabricated content, unverified assumptions, wrong arithmetic) in a "Learnings" or "Known Issues" addendum while leaving the defective content in the plan body, producing a plan that is guaranteed to be NOGO'd by any competent reviewer. |
| **Outcome** | PLAN ONLY — captured on the R1 revision cycle of ProjectOdyssey issue #5527, where the R0 plan included a "Learnings captured during planning" section that identified F1/F2/F3/F4 defects (wrong tensor arithmetic, guessed file paths, illustrative loss values, unverified compat wrapper) but LEFT the defective content in the plan body. The reviewer NOGO'd R0 specifically because the self-identified defects were left in place. R1 replaced the fabricated content with placeholder tokens plus render-script structural gates. This skill documents the meta-rule. |
| **Verification** | unverified |

## When to Use

- You are drafting a "Learnings captured during planning" / "Known Gaps" / "Caveats" / "Assumptions" section in your OWN plan document (not another person's plan; a caveats section calling out load-bearing risks is fine; a caveats section calling out defects YOU introduced and did not fix is not).
- A reviewer has NOGO'd a plan you authored with a list of concrete defects, and your revision plan involves "adding a note explaining the defect" rather than fixing or blocking on it.
- You catch yourself writing prose of the form "these numbers are illustrative; the executor must replace them before creating the PR" — this is exactly the pattern this skill warns against; the illustrative content plus hedge is worse than either alone.
- A plan depends on an API, path, value, or helper behavior that has not yet been verified.
- Any planning session where the deliverable is "a plan a reviewer will approve or NOGO" — reviewers evaluate the plan body, not the confession addendum; a self-identified defect is a defect.

## Verified Workflow

> **Warning:** This section is a **Proposed Workflow**, not a verified one. It was
> *not* executed end-to-end: no reviewer has independently confirmed that plans
> written this way avoid NOGO. The rule was inferred from a single R0→R1 NOGO
> cycle on ProjectOdyssey #5527. Test the rule against your own reviewer's
> feedback loop before treating it as universal.

### Quick Reference

Correct inaccurate claims in the section that a reader will act on. If evidence is missing,
use a clear placeholder, remove the unsupported assertion, or describe the assumption and
how it will be checked. Continue work that does not depend on that missing input.

### Suggested Approach

1. Identify the specific inaccurate value, path, calculation, or behavior claim.
2. Inspect available source and correct the claim where possible. A separate caveat does
   not make an incorrect actionable instruction correct.
3. If evidence comes from later work, describe its source and use a clearly marked
   placeholder. For a report generator, consider a check that prevents unresolved
   placeholders from being published as real results.
4. Separate an uncertain design assumption from a known defect. An assumption can support
   continued work when its consequences and fallback are clear; fabricated evidence cannot.
5. Keep the missing input local to the affected step. Continue independent implementation,
   investigation, or review. Seek user input only for a material unresolved decision or
   an action outside current authorization.
6. In review, suggest the concrete correction and its effect on dependent work. Use an
   existing GO/NOGO protocol only when the active workflow actually requires one; do not
   invent a new approval round for every self-review finding.

The recorded case used render-time placeholder checks. That is one useful mechanism for
preventing fabricated evidence, not a required plan format or a reason to stop the whole task.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | ProjectOdyssey #5527 R0 plan: include fabricated tensor arithmetic and guessed file paths in the plan body, add a "Learnings captured during planning" section flagging F1/F2/F3/F4 as self-identified defects, submit the plan for review. | Reviewer NOGO'd on the exact defects the planner self-flagged. The addendum did not shield the plan body; it advertised the plan body's flaws. The revision cycle cost a full R1 round-trip that would have been unnecessary if R0 had either fixed or blocked on the flagged items. | Self-identified defects are grounds for internal revision BEFORE submitting, not for adding a caveat AFTER writing the defective content. Correct the actionable content or identify the affected dependency; continue independent work. |
| Attempt 2 | Same R0 plan: include an "illustrative" loss log block inline with a hedging note ("the executor will overwrite these before creating the PR"). | The hedging note is a conditional gate — it depends on the executor reading and honoring it. Reviewers may skim the hedge and treat the numbers as real; executors may skip the hedge and ship the illustrative values. Silent enforcement is not enforcement. | Replace illustrative content + hedge with a `<<TOKEN>>` placeholder + a render-time structural gate that fails when the token is unresolved. See `planning-pr-body-extract-sibling-artifact-at-runtime` §Structural gates. |
| Attempt 3 | Same R0 plan: assert `just precommit` will pass without `SKIP=mojo-format` based on a claim about a compat wrapper the planner had not read; call out the unread status of the wrapper in the "Learnings" section. | The claim is load-bearing (the plan's PR-open step depends on it); calling out that the claim is unverified while still making the claim is the same anti-pattern in a different domain. Reviewer NOGO'd on the unverified assumption. | Either read the wrapper (verify) or hedge the claim explicitly with a documented fallback (see `planning-pr-open-load-bearing-assumption-hygiene`). Distinguish a labeled assumption from a verified behavior claim. |

## Results & Parameters

### Suggested Configuration

Record the affected claim, its evidence source, the correction or remaining uncertainty,
and the work that depends on it. Use a placeholder check when a generated report could
otherwise present missing evidence as a real result.

### Expected Output

- The actionable plan text reflects known corrections.
- Missing evidence is visible at the point of use.
- Independent work continues while a dependency is resolved.
- The final report separates completed results, assumptions, and unresolved inputs.

The historical case below supports the defect-correction lesson. It does not establish
that one format eliminates all future review cycles.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectOdyssey | Issue #5527 R0→R1 revision cycle (2026-07-02) — R0 shipped self-flagged defects; R0 was NOGO'd; R1 replaced flagged content with placeholder + gate. Meta-rule extracted from the delta. Not applied end-to-end beyond this cycle. | See ProjectOdyssey issue #5527 planning comments (R0 verdict, R1 verdict). |

## References

- [planning-pr-body-extract-sibling-artifact-at-runtime](planning-pr-body-extract-sibling-artifact-at-runtime.md) — domain-specific fix for sibling-artifact content: use placeholder + structural gate instead of illustrative content + hedge.
- [planning-pr-body-numeric-claims-source-derived](planning-pr-body-numeric-claims-source-derived.md) — domain-specific fix for numeric claims: derive from source at execute time; never fabricate.
- [planning-pr-open-file-scope-via-git-diff](planning-pr-open-file-scope-via-git-diff.md) — domain-specific fix for file-path claims: derive from `git diff --name-only`; never guess.
- [planning-pr-open-load-bearing-assumption-hygiene](planning-pr-open-load-bearing-assumption-hygiene.md) — domain-specific fix for load-bearing assumptions: probe or hedge with fallback; never assert un-probed.
