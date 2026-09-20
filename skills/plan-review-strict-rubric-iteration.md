---
name: plan-review-strict-rubric-iteration
license: BSD-3-Clause
description: "Improve implementation plans with relevant engineering principles and actionable review findings. Use for design tradeoffs, incomplete handoffs, and revisions that need another review."
category: architecture
date: 2026-06-11
version: "1.2.0"
user-invocable: false
verification: verified-local
tags: [plan-review, architecture, github-issues, design-docs, rubric]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/e98a4da5d67f0766bc6b4bfaed1ab399fca90e9f/skills/plan-review-strict-rubric-iteration.history"
history-cleanup-date: "2026-09-19"
---

# Iterative Plan Review with Strict Rubric

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-11 |
| **Objective** | Improve implementation plans through relevant design principles, actionable findings, and review proportionate to unresolved risks |
| **Outcome** | Successfully reviewed 6 interrelated issues across 4 rounds — 3 plans approved at round 2, 3 needed revision and were approved at round 3 |
| **Verification** | verified-local |

## When to Use

- Reviewing implementation plans for GitHub issues before coding begins
- An epic has multiple interrelated child issues that need coordinated plan approval
- A plan has material risks or missing decisions that review could clarify
- You want to apply software engineering principles as concrete review criteria
- You need iterative refinement: write plan → review → fix findings → re-review

## Verified Workflow

> **Warning:** This workflow has been validated locally. Treat as a hypothesis until CI confirms.

### Quick Reference

```bash
# Fetch issue body
gh issue view {issue_number} --repo {owner}/{repo} --json title,body

# Post review as comment
gh issue comment {issue_number} --repo {owner}/{repo} --body-file /tmp/review{issue}.md

# Post revised plan as comment
gh issue comment {issue_number} --repo {owner}/{repo} --body-file /tmp/plan{issue}v{n}.md
```

### Detailed Steps

#### Phase 1: Prepare the Rubric

1. Select the relevant principle-based questions; use them to guide judgment:
   - **P1 KISS**: Is the solution as simple as possible?
   - **P2 YAGNI**: Is everything in the plan required by the issue?
   - **P3 TDD**: Are tests named and defined before implementation?
   - **P4 DRY**: Is there code reuse from existing codebase?
   - **P5 SOLID/SRP/OCP/DIP**: Single responsibility, open-closed, dependency inversion
   - **P6 Modularity**: Clean module boundaries and interfaces
   - **P7 POLA**: Intuitive behavior, no surprising side effects

2. Define stage-specific dimensions:
   - Requirements alignment: every AC mapped to concrete steps
   - Plan completeness: setup, implementation, test, rollback steps named
   - Concreteness: real file paths, function signatures, module paths
   - Risk surface: no destructive ops, no scope creep
   - Verification plan: copy-paste-run commands
   - Stage handoff: implementer has everything needed

3. Assess the evidence and tradeoffs directly. Avoid default-failure grading or a score threshold unless an external consumer requires it.

#### Phase 2: First Review Round

1. Fetch all issue bodies and titles via `gh issue view`
2. When independent review is useful and available, provide the reviewer with:
   - The issue requirements (acceptance criteria)
   - The proposed plan
   - The strict rubric dimensions
   - A request for actionable findings, reasons, and verification limits
3. Use a GO/NOGO format only if the consuming workflow requires it.
4. Publish review comments when authorized; otherwise keep the review local.

#### Phase 3: Revision Loop

1. For each issue with material findings:
   - Extract specific, actionable findings from the review
   - Revise the plan to address those findings, locally or through available delegation
   - Bump the plan version (v1 → v2 → v3...)
   - Update the canonical plan when publication is authorized
2. Re-review ONLY the revised plans (not the GO plans)
3. Re-review when revisions or unresolved material findings justify it. Continue authorized implementation once its decisions are sufficiently clear; avoid rounds that add no useful evidence.

#### Phase 4: Final Compilation

1. Compile comprehensive task descriptions for each issue:
   - Full final plan with code snippets
   - Review history summary (how findings were resolved per round)
2. Deliver the complete handoff through the authorized channel and continue implementation if it is part of the task.

### Plan Artifact Boundaries

Aim for a plan with enough detail to implement and a structure that is easy to review.
Maintain one canonical, standalone plan artifact and make all review rounds refer to
that artifact rather than reproducing it.

1. **Prefer precise prose to illustrative code.** Include a fenced snippet only
   when prose cannot unambiguously express a public contract, a non-obvious
   algorithm, or a test assertion. A snippet that merely restates a named edit or
   repeats code already present in the canonical plan adds review surface without
   adding evidence.
2. **Prefer findings over repeated diffs in plan-review responses.** State the
   finding, its effect, and a suggested plan-level correction. The
   next canonical plan revision incorporates the correction; it does not need a
   second copy in the review comment.
3. **Keep revision history out of the implementation handoff.** When a planning
   thread becomes too large to review, preserve only the latest complete plan in
   the authorized handoff. Preserve historical discussion unless its removal is
   authorized and consistent with repository policy. Request another review when material decisions
   changed; shortening the document alone need not reset its status. Never retain a partial amendment or a review as the canonical plan.
4. **Improve artifact quality where it helps.** Simplify repeated code, pasted
   diffs, or redundant snippets that obscure a decision. Continue independent
   implementation when the affected design choices are already clear.

### Orchestration Pattern

```
Round 1: Review all 6 plans in parallel → 3 GO, 3 NOGO
Round 2: Revise 3 NOGO plans in parallel → re-review → all GO
Round 3: Review revised plans → all GO
Round 4: Fix minor findings → post final task descriptions
```

**Key insight:** Launch reviews in parallel for speed. Only re-review plans that changed.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Inheriting prior reviews as plans | Code-reviewer-mimo-pro confused prior review text as the plan | Agent treated the review verdict text as the plan artifact | Always clearly label the PLAN artifact and instruct agents to never treat review text as the plan |
| Spawning all agents in single JSON string | Tool call with JSON string instead of parsed object | Invalid parameters error | Use proper spawn_agents format with agents array |
| Single round review | Reviewing plans once without iteration | Plans had major findings that needed revision | Re-review material revisions; choose rounds from unresolved findings |
| Repeated code and review diffs | Reposted large snippets in the plan and then repeated them in review/amendment comments | The canonical handoff became hard to navigate and reviewers spent rounds comparing duplicate artifacts rather than the decision | Keep one canonical plan; use prose-first planning and reference corrections from reviews instead of reposting diffs |

## Results & Parameters

### Rubric Template

```
## 🔍 Plan Review (Round N — Strict Rubric)

**Verdict: GO|NOGO**

### Requirements Alignment
<mapping of each AC to plan steps>

### Grade: A|B|C|D|F
<critical/major/minor finding counts>

### P1-P7
<per-principle findings>

### Prior Findings Resolution
<for round N-1: how each finding from round N-1 was addressed>
```

### Optional Verdict Format

When a consuming workflow expects GO/NOGO, use its required format. Otherwise,
a concise assessment with actionable findings is sufficient. The source workflow used:
```
Verdict: GO — Plan is sound and ready to implement.
Verdict: NOGO — Plan needs changes before implementation (explain what in the review above).
```

### Typical Round Budget

| Phase | Agent Spawns | Time |
|-------|-------------|------|
| Round 1 review | N code-reviewer-mimo-pro (parallel) | ~2 min |
| Round 1 results | Post N reviews via basher | ~1 min |
| Round 2 revision | M basher agents for NOGO plans | ~2 min |
| Round 2 review | M code-reviewer-mimo-pro (parallel) | ~2 min |
| Final compilation | N basher agents for task descriptions | ~2 min |

## Verified On

| Project | Context | Details |
|---------|---------|--------|
| example-org/inference-service | Epic #81 — 6 interrelated GitHub issues for CPU endpoint manager | Reviewed 6 plans across 4 rounds; 3 plans needed 1 revision cycle; all plans eventually passed |
| isolated automation planning run | Oversized canonical plans and repeated review artifacts were compacted to one body-level plan before a clean NOGO re-review | Verified operational cleanup and plan-state reset |
