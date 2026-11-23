---
name: testing-real-producer-output-through-consumer-gate
license: BSD-3-Clause
description: "Test a multi-stage flow with the real output of its first stage, not a hand-built input. Use when a stage generates a document that a later stage validates, and the tests build that document by hand."
category: testing
date: 2026-11-23
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [contract-test, fixture, producer-consumer, generated-config, validation-gate, review, end-to-end]
---

# Test the Real Producer Output Through the Consumer Gate

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-23 |
| **Objective** | Catch a producer that can never satisfy its consumer's validation gate, a defect that hand-built test inputs hide. |
| **Outcome** | Successful. A fresh review that ran the real producer output through the real gate found a defect that every merged test had missed. |

## When to Use

- A stage generates a document (a config file, a manifest, a recipe, a record), and a later stage validates it before it acts.
- The tests for the later stage build the input by copying a known-good sample and adding fields.
- A feature is split across several changes, and each change has green tests for its own slice.
- A review or acceptance check states that a flow "works end to end", and no one has run it with real producer output.
- A validation gate requires fields that the producer's template does not write.

## Verified Workflow

### Quick Reference

```text
1. Name the producer function and the consumer gate.
2. Build the smallest realistic source for the producer (for example, a tiny input directory with the real field shapes).
3. Call the REAL producer on it. Do not copy a sample.
4. Feed its exact output to the REAL gate, in a test.
5. Assert the gate accepts it, or refuses it with a message that names the missing field.
6. Add the second-call case: the same input again must not change anything.
```

### Suggested Approach

1. Find every field the gate requires, from the gate's code and not from its tests.
2. Compare that list with what the producer writes. A required field that the producer never writes is a defect, even if all tests pass.
3. Decide where the missing values come from: the producer, the gate (derive and record them), or the input. If a value cannot be derived, make the gate refuse with a reason that tells the user what is missing.
4. Write the contract test from real producer output. Keep one hand-built case only for a gate branch that the producer cannot reach.
5. When you review a change that claims the flow works, execute it. Write a throwaway script that runs the real producer and the real gate on a small realistic input, and report what the run printed. A failing run outranks a reading of the code.
6. Check the neighbouring risks in the same run: a second call that must write nothing, two callers at once, a refusal that must write nothing, and malformed numeric input (infinity, NaN, a float where an integer is required).
7. If a step cannot run (no cluster, no network), say what was not run and what the evidence covers.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Trust green tests | Seven changes merged with green CI and a clean first review. | The tests copied a full sample and added fields. The real producer wrote a minimal document that the gate always refused. | A green test proves the gate accepts the sample, not the producer. |
| Review by reading | The first review read the code and the tests and found no defect. | The defect lives in the gap between two stages, and neither stage's tests cross it. | A reviewer must run the producer and the gate together. |
| Fix the gate to accept the minimal document | Considered loosening the gate. | The gate protects later stages that need the missing fields. | Derive and record the values at the gate, or refuse with a clear reason. Do not weaken the gate. |
| Interpolate a user string into the generated text | The producer built its document from string templates. | A crafted value with a newline added fields to a valid document. | Build generated documents with a serializer. Validate the input grammar at the entry. |

## Results & Parameters

- **Contract test shape:** real input, real producer, real gate, one assertion on acceptance or on the refusal message, one assertion that a repeat call changes nothing.
- **Review shape:** one throwaway script, run on the same kind of node as the tests, with the printed result in the review.
- **Verification status:** verified by execution in one project. Other projects may need different producers and gates, but the decision rule is the same.
