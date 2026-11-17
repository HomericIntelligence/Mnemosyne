---
name: supersession-gate-advisory-output
license: BSD-3-Clause
description: "Design new output around a durable artifact's ownership gate before writing code. Use when a reviewed or published artifact may be replaced only under one authority state, a new feature produces an improved or extended version of that artifact while the accepted state holds, or a write fails at runtime with an ownership or exclusive-state violation. Deliver the extra output as advisory payload to the next stage and keep the reviewed artifact exactly as reviewed; never force, relabel to satisfy, or bypass the gate."
category: architecture
date: 2026-11-17
version: "1.0.0"
user-invocable: false
verification: execution-observed
tags:
  - ownership-gate
  - supersession
  - advisory-payload
  - durable-artifact
  - reviewed-artifact
  - pipeline-design
  - execution-observed
---

# Supersession Gate Advisory Output

## Overview

| Field | Value |
| --- | --- |
| Objective | Keep a reviewed durable artifact immutable under its accepted verdict state by delivering new feature output as advisory payload instead of forcing a supersession write. |

A durable artifact that a reviewer approved (a plan, a record, a document) often
carries an ownership gate: its journal accepts a replacement only under one
explicit authority state, such as an exclusive rejection label. A new feature
that runs while the acceptance state holds cannot publish a replacement. The
gate is correct. The feature design must route its extra output around the
artifact, not through it.

## When to Use

- You design a feature whose output would replace or extend an artifact that a
  review gate owns, while the artifact's approving state is still current.
- A write fails at runtime with an ownership, exclusive-state, or
  "cannot supersede revision" violation.
- You must decide between forcing the write, relabeling the artifact to unlock
  it, or reshaping the feature.

## Verified Workflow

1. **Find the gate before you design.** Read the artifact journal's write path
   first. Identify the exact condition that authorizes a replacement. If the
   condition requires a state that your feature does not hold, the feature
   cannot publish — decide that before writing code.
2. **Classify the output.** If the reviewed artifact stays correct without the
   new output, the output is advisory. If the artifact is wrong without it, the
   feature needs a real review cycle instead.
3. **Deliver advisory output as payload.** Attach the output to the work item
   or hand-off structure that the next stage already reads, next to the
   artifact itself, as fenced untrusted input like every other contextual
   block. The artifact on record stays exactly as reviewed.
4. **Make the pass bounded and non-blocking.** Run the generating step at most
   once per item lifetime, guarded by a payload flag set before the job is
   requested. Either outcome — changed output, unchanged output, or a failed
   step — continues the accepted flow. The acceptance verdict and its labels
   are never re-decided.
5. **Never satisfy the gate artificially.** Do not apply the rejection state to
   unlock the write, do not lower the gate's requirement, and do not publish a
   side channel that future readers could mistake for the reviewed artifact.

### Quick Reference

| Situation | Decision |
| --- | --- |
| Gate requires an authority state the feature does not hold | Output is advisory; deliver it beside the artifact |
| Artifact is wrong without the new output | Route through the real review cycle instead |
| Generating step fails or changes nothing | Continue the accepted flow; never block the verdict |
| Tempted to relabel to unlock the write | Stop; that defeats the gate's ownership rule |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Publish-through | The first design published the integrated output as a new artifact revision on the accepted path. | The journal raised an ownership violation: a revision may be superseded only under an exclusive rejection label, and the item held acceptance. | The gate was the design constraint all along; reading it before coding would have saved one redesign. |
| Keep the output unbound | Dropping the output when the publish was refused. | The findings were real reviewer feedback; discarding them lost the value the feature existed to deliver. | Route the value, do not drop it: advisory delivery keeps the finding alive without touching the artifact. |

## Results & Parameters

The pattern adds no new authority, no attempt budget beyond the one-pass guard,
and no re-review round. The reviewed artifact keeps its approved identity, so
every downstream reader of the artifact sees exactly what was approved. The
next stage receives both the artifact and the advisory output and can weigh the
finding without mutating the record of what was approved.
