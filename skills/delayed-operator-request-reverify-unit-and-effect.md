---
name: delayed-operator-request-reverify-unit-and-effect
description: "Before you execute an operator or owner request that is hours or days old, or that uses a unit different from the tool's unit, re-read live state and tool version, convert the unit explicitly, and check that the change can take effect under current limits. Use when a scale, run, or change request is acted on after a delay."
category: tooling
date: 2026-11-18
version: "1.0.0"
user-invocable: false
tags: [operator-request, stale-instruction, unit-conversion, capacity, scaling, evidence-record]
---

# Delayed Operator Request: Re-verify Unit and Effect

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-18 |
| **Objective** | Act on a delayed or ambiguous request from current facts, not from old notes, and never report success for a change that has no effect. |
| **Outcome** | Operational. The action matches the live state, the unit is converted in the open, and a capacity gap is reported with numbers. |

## When to Use

- A request such as "scale this pool to N" or "run this script" is executed hours or days after it was made.
- The request unit differs from the tool unit (for example nodes in the request, groups of nodes in the tool).
- Your notes hold a binary path, a count, or a release directory from an earlier step.
- The requested value is a desired or target value, and the real result depends on free capacity.

## Verified Workflow

1. Re-read the live state now: the current count, what runs, what is pending. Do not reuse earlier counts. Live state can change a lot while you wait (for example, a pool fell from many running replicas to one because of preemption).
2. Re-resolve the tool and the release now: the binary path, the version, and the release directory. Newer releases can be deployed after your notes were written. Do not reuse an old path.
3. Convert the unit explicitly and write the conversion in the record (for example, each replica spans two nodes, so 10 nodes means 5 replicas). Ask the owner once only if the conversion changes the action. Do not ask if every reading gives the same action.
4. Check that the change can take effect under current limits. A higher desired count adds only pending low-priority work when no node is free. Compare the requested result with free capacity and with the priority of the new work.
5. Act. Then read the live state again and compare the number that runs with the number requested.
6. Report the gap with numbers (requested, converted, running, pending, free). Do not say "done" when the extra capacity does not run.
7. Log the decision in the evidence record with the owner's exact words, the conversion, and the live values that you used.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attempt 1 | Used the counts and the release tools from earlier notes. | The live pool was far smaller, and newer releases existed. The action targeted the wrong state with old tools. | Re-read state and tool version at action time. |
| Attempt 2 | Reported a scale request as done after the desired count changed. | No node was free, so only pending low-priority jobs were added and no extra replica ran. | Verify the running result and report the capacity gap. |

## Results & Parameters

| Item | Rule |
| ----- | ----- |
| Freshness | State and tool version come from a read at action time. |
| Unit | Write the conversion; ask once only if it changes the action. |
| Effect check | Compare requested result with free capacity and priority. |
| Record | Owner's words, conversion, live values, result, gap. |
