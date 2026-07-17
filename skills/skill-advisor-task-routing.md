---
name: skill-advisor-task-routing
description: "Route a task to the appropriate procedural skill before starting substantive work. Use when: (1) beginning any non-trivial task, (2) unsure whether a process, execution, or completion skill applies, (3) tempted to skip workflow checks because the task 'seems simple'"
category: tooling
date: 2026-07-16
version: "1.0.0"
user-invocable: false
tags: [workflow, routing, process, skills]
---

# Skill Advisor: Task Routing

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-16 |
| **Objective** | Decision tree for routing a task to the right procedural skill before work begins |
| **Outcome** | Operational — migrated from the Athena `skill-advisor` skill into standard knowledge |

## When to Use

**Core principle:** check for a relevant skill BEFORE beginning any substantive work. If there is even a 1% chance a skill applies, invoke it.

Knowledge first, then process: search the knowledge backend (advise) for prior lessons before routing to a procedural skill. Failure to prepare the required knowledge backend is blocking.

## Verified Workflow

### Decision Tree

```text
What are you about to do?
│
├─ Implementing a new feature or fixing a bug?
│   └─ → test-driven-development (BEFORE writing any code)
│
├─ Debugging an unexpected failure, bug, or error?
│   └─ → systematic-debugging (BEFORE proposing fixes)
│
├─ About to claim work is "done", "passing", or "fixed"?
│   └─ → verification evidence audit (BEFORE making any success claims)
│
├─ Starting a complex or ambiguous feature from scratch?
│   └─ → brainstorm (BEFORE writing any code or plan)
│
├─ Needing an isolated workspace for a new branch?
│   └─ → git-worktrees
│       (skip if using myrmidon-swarm — it handles isolation automatically)
│
├─ Implementation complete, ready to merge or create PR?
│   └─ → finish-branch delivery workflow (AFTER verification)
│
├─ Completed a major task and want quality assurance?
│   └─ → code-review before merge (uses an independent reviewer when available)
│
└─ Received code review feedback to act on?
    └─ → evaluate each comment with evidence, then request an independent recheck
```

### Skill Priority

When multiple skills could apply:

1. **Process skills first** (brainstorm, systematic-debugging) — determine HOW to approach
2. **Execution skills second** (test-driven-development, git-worktrees) — guide execution
3. **Completion skills last** (verification, finish-branch, code-review) — gate closure

Example: "Fix this bug" → systematic-debugging first, then test-driven-development for the fix.

Example: "Build new feature" → brainstorm first, then test-driven-development for implementation.

### When to Skip

- You are a subagent dispatched by an orchestrator with a specific task — follow your task prompt directly.
- You were explicitly told "just do X" without workflow overhead.
- The task is truly trivial (typo fix, single-line rename).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| "Just a simple question" | Skipping the check for questions | Questions become tasks | Check anyway |
| "I already know the approach" | Working from memory of a skill | Skills evolve | Check the current version |
| "Skill is overkill" | Ad-hoc approach to a "simple" task | Simple things become complex | Use the skill |
| "I'll check after exploring" | Exploring first, routing later | Skills tell you HOW to explore | Check first |

## Results & Parameters

### Expected Output

The selected skill (or explicit skip justification) stated before substantive work begins.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Athena | Shipped as the `skill-advisor` plugin skill; exercised across HomericIntelligence repositories | Migrated 2026-07-16 |

## References

- Related: [advise-before-planning.md](advise-before-planning.md), [verification-evidence-audit.md](verification-evidence-audit.md), [finish-branch-delivery-workflow.md](finish-branch-delivery-workflow.md)
- Adapted from [obra/superpowers](https://github.com/obra/superpowers) under the MIT License. Copyright (c) 2025 Jesse Vincent.
