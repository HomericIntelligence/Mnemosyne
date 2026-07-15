---
name: plan-review-strict-rubric-iteration
description: "Iterative multi-round plan review with strict rubric applying 7 software engineering principles (KISS, YAGNI, TDD, DRY, SOLID, Modularity, POLA). Use when: (1) reviewing implementation plans for GitHub issues, (2) design docs need GO/NOGO gating, (3) plans must evolve through multiple review rounds until all findings are resolved."
category: architecture
date: 2026-06-11
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [plan-review, architecture, github-issues, design-docs, rubric]
---

# Iterative Plan Review with Strict Rubric

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-11 |
| **Objective** | Review implementation plans for GitHub issues using a strict, principle-based rubric with GO/NOGO verdicts, iterating through multiple rounds until all plans pass |
| **Outcome** | Successfully reviewed 6 interrelated issues across 4 rounds — 3 plans approved at round 2, 3 needed revision and were approved at round 3 |
| **Verification** | verified-local |

## When to Use

- Reviewing implementation plans for GitHub issues before coding begins
- An epic has multiple interrelated child issues that need coordinated plan approval
- Plans must pass a quality gate (GO/NOGO) before implementation
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

1. Define 7 principle-based dimensions:
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

3. Define grading: every dimension starts at F; A must be earned. Default is F.

#### Phase 2: First Review Round

1. Fetch all issue bodies and titles via `gh issue view`
2. Spawn one `code-reviewer-mimo-pro` per issue with:
   - The issue requirements (acceptance criteria)
   - The proposed plan
   - The strict rubric dimensions
   - Instruction to output EXACTLY ONE verdict line: `Verdict: GO` or `Verdict: NOGO`
3. Collect verdicts: binary GO/NOGO gate
4. Post review comments to each issue

#### Phase 3: Revision Loop

1. For each NOGO issue:
   - Extract specific, actionable findings from the review
   - Spawn a sub-agent to write a revised plan fixing those findings
   - Bump the plan version (v1 → v2 → v3...)
   - Post the revised plan as a new issue comment
2. Re-review ONLY the revised plans (not the GO plans)
3. Repeat until all plans are GO

#### Phase 4: Final Compilation

1. Compile comprehensive task descriptions for each issue:
   - Full final plan with code snippets
   - Review history summary (how findings were resolved per round)
2. Post as final issue comments

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
| Single round review | Reviewing plans once without iteration | Plans had major findings that needed revision | Always plan for at least 2 review rounds |

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

### Verdict Contract

The review MUST end with EXACTLY ONE of:
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
