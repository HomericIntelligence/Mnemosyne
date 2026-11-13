---
name: llm-behavioral-benchmark-failure-channels
description: "Separate score channels when building or reading an LLM behavioral benchmark sweep. Use when: (1) a benchmark score sits far below its measured accuracy, (2) models differ in how they fail rather than how often, (3) task difficulty must scale with a magnitude parameter, (4) test cases must come from realistic input structure, or (5) an endpoint rejects burst traffic."
category: evaluation
date: 2026-11-12
version: "1.0.0"
user-invocable: false
tags:
  - llm
  - benchmark
  - evaluation
  - doom-loop
  - score-channels
  - sweep
  - difficulty-scaling
  - endpoint-concurrency
---

# LLM Behavioral Benchmark Failure Channels

## Overview

| Field | Value |
| ----- | ----- |
| **Date** | 2026-11-12 |
| **Objective** | Tell apart the ways a model fails a behavioral benchmark, and keep the benchmark itself from flattering the model. |
| **Outcome** | Operational. Four served models ran one 61-case sweep; the channel split separated an always-answers model from two repeat-and-stall models and one that timed out before answering. |

## When to Use

- A benchmark score sits far below its measured accuracy and the gap is unexplained.
- Models with similar accuracy fail in qualitatively different ways and a single number hides it.
- Task difficulty must increase with a magnitude parameter (a count, a length, a depth) and you need to know where capability breaks.
- Test cases are generated programmatically and you must decide what population they draw from.
- A model endpoint rejects burst traffic or single-replica pools starve under batch load.

## Verified Workflow

### Quick Reference

Score every case on three channels and report them beside each other:

```text
response correctness   did the final answer parse and match the expected value
reasoning mention      did the reasoning state the exact answer exactly once
loop/non-completion    verbatim repeats in the reasoning, timeout or max-token exits
```

`score = 1.0` for a correct response minus a loop penalty, and `0.25` for an
incorrect response whose reasoning stated the exact answer once. A response that
states the answer twice earns no mention credit anywhere.

### Suggested Approach

1. **Define the answer contract structurally.** Express the accepted answer as a
   shape tied to the question, not as a list of exceptions. One asked-for item
   means exactly one entry in the answer; a form that names the item twice or
   adds unrelated items states no single count and yields no prediction. Write
   the shape into the specification before writing fixtures, and derive fixtures
   from the shape.
2. **Anchor the answer to its line.** Require the answer form to stand alone on
   its line, with only whitespace around it. Prose on the same line makes it
   malformed. Reasoning on other lines is unaffected, so a reply may reason
   above or below the answer.
3. **Separate the channels.** Keep a repeated answer from earning mention credit
   by making the mention a 0/1 existence check: stated exactly once counts,
   stated twice or zero times does not. With mentions at 0/1, mention-penalty
   tiers above one mention are dead code; drop them and let the loop penalty
   carry the rest.
4. **Report accuracy and score side by side.** Score near accuracy means the
   model answers and is wrong. Score far below accuracy means loops or
   non-completion dominate. Both numbers are needed; either alone is a different
   model's story.
5. **Draw cases from the realistic structure of the input.** When a parameter
   picks what a task operates on (a letter in a word, a field in a record), draw
   it from the values that occur in real inputs, not from the full universe.
   Values absent from real inputs produce degenerate cases that are trivially
   easy and inflate every model's result.
6. **Scale difficulty in bands and report per band.** Group cases by the
   magnitude parameter and report accuracy per band. The band where accuracy
   falls below half is the capability boundary; a single aggregate hides it.
7. **Match concurrency to endpoint capacity.** Send as many concurrent requests
   as the endpoint has serving replicas, not as many as the batch holds. A
   single-replica endpoint starves under burst traffic and returns admission
   errors. Keep timeouts and retry budgets in the surrounding runner, not
   hardcoded in the benchmark script.
8. **Treat an audit contradiction between the specification and the fixtures as
   the first thing to fix.** Honest agents fail on a specification/fixture
   contradiction regardless of capability, so more time or a better model does
   not help. Align the two in whichever direction is stricter, then re-run.

### Reading the results

- Accuracy near the score: the model answers and is wrong. Improve counting or
  reasoning quality.
- Score far below accuracy: loops or non-completion dominate. Expect long
  reasoning, repeated text, and empty or missing responses.
- Errors concentrated on one model: that model's replica count or timeout budget
  is too small for the workload, so its unscored cases are survivorship-biased
  toward fast cases. Report scored counts beside accuracy.
- A model that cannot measure the input and starts guessing from prompt
  statistics or from prior exposures is past its capability boundary; the sweep
  should stop there rather than report the guess.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| 1 | Drew test letters from the whole alphabet and inserted runs at word edges for absent letters. | Absent-letter edge runs are trivially easy; every model's score was inflated and the capability boundary was invisible. | Draw test inputs from the values that occur in real inputs. |
| 2 | Accepted any entry list and took the last value for a repeated character; later made duplicates malformed "because the count is ambiguous". Both readings were wrong. | The structural rule is the entry count: one asked-for item means exactly one entry. A form with two entries states two counts; a form with an unrelated entry answers a different question. | Derive the answer contract from the question's arity, not from ambiguity arguments. |
| 3 | Hardcoded a 30-minute request timeout and a 40-attempt re-queue loop in the benchmark script. | A single pathological generation held a whole batch past the timeout while the re-queue chained, and the script could not be used by a runner with its own deadline policy. | Leave the deadline and the retry budget to the surrounding runner. |
| 4 | Sent a 25-wide burst at a single-replica endpoint. | 24 of 25 requests failed admission; the one survivor made the model look unusable. | Match burst width to serving replicas, or run serially with re-queue retries. |

## Results & Parameters

### Configuration

```yaml
sweep:
  magnitude_parameter: count of the target item in the input
  values: primes across the intended range   # primes avoid accidental regularity
  cases_per_value: 3 placements + shared baseline
  letter_source: values that occur in the input
score:
  correct_no_loops: 1.0
  loop_penalty: 0.1 per verbatim repeat, capped at 0.3
  incorrect_reasoned_once: 0.25
  incorrect_unreasoned: 0.0
channels:
  - response correctness (structural answer contract, one entry)
  - reasoning mention (exactly-once existence check)
  - loop count and non-completion (timeout, max-token)
runner:
  concurrency: serving replica count
  timeout: set by the runner, not the benchmark
```

### Expected Output

A per-case record with all three channels, plus per-placement and per-band
aggregates. From one 61-case, four-model sweep:

| profile | accuracy | score | signature |
| ------- | -------- | ----- | --------- |
| answers, no reasoning channel | 43% | 0.426 | score equals accuracy, zero loops |
| reasons, then loops | 31% | 0.285 | 840 verbatim loops, three empty responses at max tokens |
| reasons, times out | 48% of scored | 0.433 | 37 of 61 requests exceeded the runner timeout |
| reasons, repeats, sometimes answers | 43% | 0.367 | 654 loops, 16 max-token exits |

Accuracy degraded with the magnitude parameter on every model: roughly 85% at
the low band, under 10% at the top band.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Internal character-counting doom-loop task | Prime-count sweep, 4 served models, 61 cases each | The channel split separated an always-answers model from two repeat-and-stall models and one that timed out; see [notes](llm-behavioral-benchmark-failure-channels.notes.md). |
