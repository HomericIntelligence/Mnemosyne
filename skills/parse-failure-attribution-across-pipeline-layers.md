---
name: parse-failure-attribution-across-pipeline-layers
description: "Attribute a downstream parse or contract failure to the layer that produced the bad value. Use when a parser reports that a value was empty, missing, or malformed and the producer looks at fault."
category: debugging
date: 2026-10-13
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - error-attribution
  - pipeline-layers
  - empty-collapse
  - last-write-wins
  - agent-stream-parsing
  - recorded-fixture-replay
  - contract-parser
  - false-diagnosis
  - wrong-layer-fix
---

# Attribute a Parse Failure to the Layer That Produced the Bad Value

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-13 |
| **Objective** | Stop the habit of reading a downstream decode error as a statement about the upstream producer, and replace it with a recorded end-to-end replay that names the layer at fault. |
| **Outcome** | Operational. A decode position that looked like a producer fault was reproduced end to end and traced to an intermediate selection step. A complete artifact built on the wrong attribution was withdrawn. |

## When to Use

- A downstream parser or contract validator rejects a value, and the log or the caller blames the producer: a model, a service, an upstream job.
- The decode or validation error points at offset zero of the received value, or says the value was empty, missing, absent, or not a recognized shape.
- A run reported a producer capability failure, and you have not yet checked whether the producer ever saw the input it is blamed for.
- You are about to build a guard, retry budget, or acceptance test on the assumption that the producer is at fault.
- A retry loop is spending its whole budget re-sending work to a producer that is behaving correctly.

## Verified Workflow

### Quick Reference

```text
1. Read the decode position. It describes the value the parser RECEIVED.
   Offset zero means "no token at the start of that value". It does not say
   who produced the value.
2. Find every stage between the producer and the parser. List the stage that
   selects, reduces, truncates, or last-write-wins over the value.
3. Replay the RECORDED producer output through every stage in order, offline.
   Do not reason about the error text. Reconstruct the value at each hop.
4. Compare the value at the producer hop with the value at the parser hop.
   The first hop where they differ is the layer at fault.
```

### Suggested Approach

**A decode position is evidence about one value, not about one component.** A message such as "expecting value at line 1 column 1" reports that the string the parser received began with no JSON token. Several different components can be responsible for handing that string over. The producer can be silent, and it can also be correct while an intermediate stage replaces its output.

**Enumerate the hops before you assign blame.** A typical path is: producer emits, a stream or event reader selects one payload, a selection function reduces the series, a contract parser validates. Three of those four stages can independently produce an empty value. Record them explicitly.

**Look for last-write-wins over a series.** The highest-yield defect is a selection step that assigns on every element of a series without a guard, so a later element that carries no payload overwrites an earlier element that did. The series looks ordered and the final element looks authoritative, so the code reads as correct. Only the guard is missing.

**Separate "the series carried nothing" from "the payload failed the contract".** These are different failures with different owners and different recoveries. A reader that returns an empty default for both makes them indistinguishable in the log, and then the run reports a producer fault for what was a transport or selection fault. Give each its own cause.

**Prove it with a recorded fixture, not with the error message.** Take the actual recorded producer output, feed it through the real stages in the real order, and show that the parser receives an empty value while the producer output was correct. One such fixture settles the attribution. It also becomes the regression test.

**Build the regression test from the recorded series, with the answer intact.** Keep at least these shapes: a correct payload followed by an empty element, a correct payload followed by two empty elements, a correct payload followed by a whitespace-only element, two correct payloads followed by an empty element, an empty element followed by a correct payload, and a series with no payload element at all. Assert both that the selected value is correct and that the absent-payload case reports its own cause.

**Then check whether the obvious fix even reaches the value.** Before you accept a repair at the consumer, apply it to the fixture. If the repair parses more shapes but the fixture still fails, the repair is at the wrong layer. Widening a validator cannot recover a value that a selection step already discarded.

### When a recorded artifact is not available

If no recorded producer output exists, capture one before changing anything. Run the producer once against a known input and save the raw output. A fixture that you build from the error message proves nothing, because the error message is the claim under test.

If the producer cannot be run because it needs a network call or a rate-limited quota, extract the series from any retained transcript, session store, or debug log. Preserve the element structure exactly, and replace only the payload body with a placeholder of the same length class. The structure is the evidence.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Read the decode offset as a statement about the producer | A "no value at offset zero" message was treated as proof that the producer emitted nothing | The offset describes the string the parser received. An intermediate stage produced that string, not the producer | The position is evidence about one value. Name the layer that handed it over |
| Reason about the error text instead of replaying the series | Assembled a plausible explanation of why the producer might return nothing | The explanation was consistent with the symptom and wrong about the cause. It survived until a recorded replay contradicted it | Replay recorded output through the real stages. Explanations do not survive a fixture |
| Build a complete artifact on the inferred cause | Wrote an acceptance test, a trusted evaluator, and a reference repair around the inferred producer fault | Every layer was real and every check passed, but the artifact measured a defect that did not exist. The reference repair would have reported a false cause and spent the budget it claimed to save | An artifact built on an unverified cause is expensive to withdraw. Verify the cause before building |
| Repair the consumer to be tolerant of more shapes | Hardened the validator to extract a payload from a fence, from prose, and from a trailing series | The fixture still failed, because the value never reached the validator. Tolerance cannot recover a discarded value | Apply the candidate repair to the fixture first. A repair that cannot move the fixture is at the wrong layer |
| Assume the run's own classification of the failure is evidence | The run logged that the producer could not meet the contract | The run applied that classification using the same selection step that caused the fault, so the classification was circular | A layer that produced the fault does not get to name it |
| Write an acceptance record before running the checks | Recorded several rows describing repairs and rejections, then ran them | The counts and totals were stale, and some rows described work not yet performed | Record results after the run. An unattempted row is a fabrication |

## Results & Parameters

### Failure-class signature to recognize

```text
Producer:   correct output, recorded and replayable
Stage 1:    series reader. Assigns on every element, or defaults to empty.
Stage 2:    selection. Last-write-wins, no guard for an element with no payload.
Stage 3:    contract parser. Receives an empty value. Reports a decode offset.
Observed:   a decode error at offset zero, plus a cause that names the producer.
Missing:    any record of which element the selection chose.
```

### Decision table

| Evidence | Conclusion |
| --------- | ---------- |
| Offset zero and the producer output is empty in the record | The producer is at fault |
| Offset zero and the producer output is correct in the record | An intermediate stage is at fault. Go to step 4 of the quick reference |
| The stage returns an empty default for both an absent payload and a contract failure | Both faults are conflated. Split them before you can attribute either |
| A candidate repair does not move the fixture | The repair is at the wrong layer |

### Expected Output

- A one-line attribution naming the stage at fault, not the component blamed by the run.
- A recorded fixture that reproduces the fault offline, with the producer output intact.
- A regression set that asserts the selected value, not only that a parse failed.
- Two distinct causes: one for an absent payload, one for a payload that fails the contract.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal incident, 2026-10-13 | Agent output stream selection discarded a correct answer | Reproduced offline from the recorded series. The fault was an unconditional assignment in the selection step, not a producer fault. A complete task artifact built on the inferred cause was withdrawn. See [notes](../skills/parse-failure-attribution-across-pipeline-layers.notes.md). |

## References

- [Last-match versus first-match parsing of a discrete marker](llm-output-verdict-parse-last-line-not-substring.md) — the same mechanism class, applied to marker semantics. A last-match rule is correct only when every element can carry a value.
- [A validator that discards repeated entries before validation](planning-validator-false-assurance-flatten-duplicate-guard.md) — the empty-collapse branch. There the discarded value is a duplicate, and the symptom is a false clean report. Here the discarded value is empty, and the symptom is a false producer fault.