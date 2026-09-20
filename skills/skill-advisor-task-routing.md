---
name: skill-advisor-task-routing
license: BSD-3-Clause
description: "Select relevant procedural skills when workflows overlap, triggers conflict, or a user names a skill."
category: tooling
date: 2026-07-16
version: "1.2.0"
user-invocable: false
verification: verified-review
tags: [workflow, routing, process, skills, policy, boundary]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/e98a4da5d67f0766bc6b4bfaed1ab399fca90e9f/skills/skill-advisor-task-routing.history"
history-cleanup-date: "2026-09-19"
---

# Skill Advisor: Task Routing

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-07-16 |
| **Objective** | Select each applicable procedural skill and use it when its specified trigger occurs |
| **Outcome** | Policies stay active for all work in their scopes. Skills start at their specified boundaries. |
| **Verification** | verified-review |

A policy gives a rule for applicable work. A procedural skill gives steps for
a specified workflow phase. Policy scope and skill timing are different.

In this skill, a current skill has a trigger in the current phase. A deferred
skill is a skill for a subsequent phase.

## When to Use

- You start a task where skill selection is necessary.
- A policy is applicable to all task work, but its validation skill is for a
  subsequent workflow boundary.
- Two instructions give different trigger times for one skill.
- The user names a skill.
- You will start a new workflow phase or make a completion claim.

## Verified Workflow

### Quick Reference

Prefer the smallest set of skills that helps complete the requested task. Use their
triggers and available inputs to choose useful timing. A related skill is not an
extra approval step, and missing optional knowledge need not block independent work.

### Suggested Routing

1. Identify the requested outcome and applicable user, repository, and host constraints.
2. Retrieve relevant prior knowledge when useful. If the source is unavailable, report
   that limit and continue from current evidence.
3. Read the selected skill's trigger and relevant procedure. Defer steps whose inputs
   are not ready; use other useful guidance when it helps the present task.
4. Apply an explicitly named skill within the active instruction hierarchy. Its
   recommendations do not expand the user's authorization or override host controls.
5. Resolve routine trigger conflicts through instruction precedence and context. Ask
   only when a material ambiguity remains. Continue unaffected work while it is resolved.
6. When authorized to update conflicting guidance, align the statements at their source.
   Otherwise, report the conflict without treating it as a reason to abandon the task.
7. Revisit the selection when the task changes. At delivery, account for all relevant
   artifacts and report the work done, verification evidence, and remaining limits.

### Common Routing Map

| Task condition | Useful guidance |
| --- | --- |
| Unfamiliar work | `advise` for relevant prior knowledge |
| Several plausible designs | `brainstorm` for tradeoffs |
| Failure with an unknown cause | `systematic-debugging` for investigation |
| A behavior change benefits from a regression | `test-driven-development` for a test-first approach |
| Independent edits need isolation | The host's existing worktree mechanism |
| Completion or delivery | Relevant evidence and delivery guidance |
| High-impact or uncertain changes | Independent review where available |
| Review feedback | Examine the evidence, make justified corrections, and recheck affected behavior |

### Routing Record

A short routing note can help a complex handoff. For a small or already-bounded task,
proceed directly with the relevant guidance. Avoid a separate routing ceremony or
repeated permission requests for work the user already authorized.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Use all possible skills at task start | Treated a policy for all work as a skill trigger at task start | The procedure started before its input was available | Use the skill at its stated trigger while the policy stays active |
| Change one trigger statement | Changed the skill description but did not change another instruction | The instructions gave different boundaries | For a trigger change, examine all routing instructions that the task permits you to change |
| Start the policy with the skill | Used the policy only when the boundary skill started | Work on artifacts from previous phases did not follow the policy | Keep the policy active for all work in its scope |
| Examine only new boundary metadata | Used the deferred skill only for metadata made at the boundary | The skill did not examine applicable artifacts from previous phases | Use the boundary skill on the full input set |
| Move a skill because it can be useful | Used a preference instead of the stated trigger | The skill started before its stated boundary | Use trigger conditions and available inputs to select useful timing within active instructions |
| Treat a question as a simple task | Skipped routing because the task did not change a file | The analysis made a procedural skill necessary | Route a question when skill selection is necessary |
| Explore before routing | Started discovery before the skill selection | The applicable skill controlled the discovery method | Use relevant method guidance when it can change discovery decisions |
| Reject a skill as excessive | Used task size instead of the skill trigger | The task became complex during the work | Revisit skill relevance when new evidence changes task complexity |
| Work from memory | Used a remembered trigger instead of the current trigger | Skill triggers can change | Read the current trigger before routing |

## Results & Parameters

### Suggested Record

For complex work, record the relevant constraints, selected skills, deferred inputs,
and unresolved material decisions. Update the record when those facts change.

### Expected Output

The agent uses relevant guidance at useful points, avoids repeated process work,
and completes the authorized task. If an input or permission is missing, the report
identifies the affected action and what can still proceed.

## Verified On

| Context | Method | Result |
| --- | --- | --- |
| Repository policy change | Independent review of a boundary-specific validation workflow | The policy stayed active, and the validation skill moved to the delivery boundary |
