---
name: skill-advisor-task-routing
license: BSD-3-Clause
description: >
  Use this skill to select procedural skills and their first workflow phases.
  Use it when work starts.
  Use it when a policy is applicable to all work but its related skill is for
  a subsequent boundary.
  Use it when instructions give different trigger times.
  Use it when a user names a skill.
category: tooling
date: 2026-07-16
version: "1.1.0"
user-invocable: false
verification: verified-review
tags: [workflow, routing, process, skills, policy, boundary]
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

| Condition | Action |
| --- | --- |
| A skill procedure is necessary in the current phase | Use the skill before the first applicable action |
| A policy is applicable to all task work | Keep the policy active |
| A skill has a subsequent boundary | Record the skill as deferred |
| The user names a skill | Use the skill now |
| Trigger statements give different boundaries | Use instruction precedence to select the controlling statement |
| You cannot use instruction precedence to identify one controlling statement | Stop the affected work. Report the conflict. |
| A deferred boundary starts | Use the skill for all applicable artifacts from previous phases |

### Detailed Steps

1. **Find policies for the work.** Keep each policy active for all work in its
   scope. Do not wait for a related skill to start.

2. **Get previous knowledge.** For work where skill selection is necessary,
   use the necessary knowledge-retrieval procedure before planning or
   implementation. Prepare a knowledge source before you use a skill that has
   the source as a prerequisite. A source-preparation failure prevents use of
   the related skill.

3. **Find procedural skills.** Read each skill trigger. Find its specified action,
   condition, or workflow boundary. Do not use the skill before this boundary
   only because the procedure can help you.

4. **Find current and deferred skills.** Use a current skill before the first
   action for which it is necessary. Record a skill for a subsequent phase and
   its boundary. Do not use a skill at task start only because its related
   policy is applicable to all task work.

5. **Use a skill that the user names.** Use it now. Do not wait for its phase
   boundary.

6. **Use instruction precedence.** When statements give different boundaries,
   use precedence to select the statement that controls the workflow. If
   precedence cannot select one statement, stop the affected work. Report the
   conflict.

7. **Examine all routing instructions that control the workflow.** List the skill
   description, repository instructions, workflow guides, and other trigger
   statements. If the task permits changes to all conflicting instructions,
   change the statements to specify the same boundary. If the task does not
   permit these changes, stop the affected work. Report the conflict.

8. **Use the boundary skill on the full input set.** When the boundary starts,
   include all applicable artifacts from previous phases. A deferred skill
   must not examine only metadata made at the boundary.

9. **Examine routing at each phase change.** A deferred skill becomes current
   when its boundary starts. Do not start it before this boundary only because
   it can help you. If the user names the skill, use it now. If an instruction
   with higher precedence gives a different boundary, use that boundary.

### Common Routing Map

| Task condition | Skill and time of use |
| --- | --- |
| You do not know how to do the work | Use `advise` before planning or implementation |
| The task has multiple possible designs | Use `brainstorm` before the plan or implementation |
| A failure has an unknown cause | Use `systematic-debugging` before you propose a correction |
| A feature or correction requires a code change | Use `test-driven-development` before implementation |
| An isolated checkout is necessary | Use the applicable isolation skill before file changes. Do not add a second isolation procedure when the orchestrator supplies one. |
| You will make a completion claim | Use `verification-evidence-audit` before the claim |
| The verified work is ready for delivery | Use `finish-branch-delivery-workflow` at the delivery boundary |
| Independent quality assurance is necessary | Use an independent review before merge when a reviewer is available |
| You receive review feedback | Examine each comment with evidence before you change the work. After the change, ask an independent reviewer to examine the changed work. |

### Skill Order

Use skills in this general order when their conditions occur:

1. Process skills give the work method.
2. Execution skills control implementation and investigation.
3. Completion skills examine evidence and control delivery.

The phase boundary controls the time of skill use. The list does not change a
named trigger. The fact that a skill can help you does not change its trigger.

### Skip Conditions

You can skip this routing procedure when one condition is true:

- An orchestrator gives a subagent one bounded task and names the necessary
  procedure.
- The user tells you to do one action, and no repository workflow is
  applicable.
- The task has no action, artifact, or completion claim.

Record the cause when you skip the procedure.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Use all possible skills at task start | Treated a policy for all work as a skill trigger at task start | The procedure started before its input was available | Use the skill at its stated trigger while the policy stays active |
| Change one trigger statement | Changed the skill description but did not change another instruction | The instructions gave different boundaries | For a trigger change, examine all routing instructions that the task permits you to change |
| Start the policy with the skill | Used the policy only when the boundary skill started | Work on artifacts from previous phases did not follow the policy | Keep the policy active for all work in its scope |
| Examine only new boundary metadata | Used the deferred skill only for metadata made at the boundary | The skill did not examine applicable artifacts from previous phases | Use the boundary skill on the full input set |
| Move a skill because it can be useful | Used a preference instead of the stated trigger | The skill started before its stated boundary | Use the stated trigger unless the user or a higher-precedence instruction gives a different trigger |
| Treat a question as a simple task | Skipped routing because the task did not change a file | The analysis made a procedural skill necessary | Route a question when skill selection is necessary |
| Explore before routing | Started discovery before the skill selection | The applicable skill controlled the discovery method | Route the task before discovery |
| Reject a skill as excessive | Used task size instead of the skill trigger | The task became complex during the work | Use the skill trigger instead of the first complexity estimate |
| Work from memory | Used a remembered trigger instead of the current trigger | Skill triggers can change | Read the current trigger before routing |

## Results & Parameters

### Routing Record

Use this format before work that has an action, artifact, or completion claim.
Update it at each phase change.

```text
Applicable policies:
- <policy and scope>

Skills to use now:
- <skill>: <first applicable action>

Skills for subsequent phases:
- <skill>: <workflow boundary>

Trigger conflicts:
- <conflict or none>
```

### Expected Output

A routing decision is satisfactory when these conditions are true:

- Each applicable policy is active for all work in its scope.
- Each current skill starts before the first applicable action.
- Each deferred skill has a named boundary.
- Each boundary examination includes all applicable artifacts from previous
  phases.
- The agent uses instruction precedence to identify one controlling trigger
  statement. If instruction precedence does not identify one controlling
  statement, the agent stops the affected work and reports the conflict.

## Verified On

| Context | Method | Result |
| --- | --- | --- |
| Repository policy change | Independent review of a boundary-specific validation workflow | The policy stayed active, and the validation skill moved to the delivery boundary |
