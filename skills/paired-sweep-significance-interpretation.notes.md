# Notes: Paired Sweep Significance Interpretation

Supporting detail for
[paired-sweep-significance-interpretation.md](paired-sweep-significance-interpretation.md).

These notes hold measurements and method detail. The main entry holds the rules.
Project, model, organisation, host, path, job, and issue identifiers are
withheld under the private and proprietary information rules.

## What was compared

Two matched inference replicas of one large mixture-of-experts model. Image,
weights, topology, and prompt shape were identical. The only changed setting was
the cache precision.

Two benchmarks ran against the same replica pair:

| Benchmark | Scope |
| --- | --- |
| Qualification suite | 96 cases. 80 ordinary cases and 16 that bury a key under filler at 32,909 / 65,677 / 262,286 / 500,143 prompt tokens |
| Breadth sweep | 339 tasks and subtasks across long context, commonsense, multilingual, knowledge, reading, math, code, instruction following, long-form, bias, and tokenisation |

Both dtypes had one record per qualification case with the same case
identifiers, so the comparison was paired at the case level.

## Qualification suite result

| Measure | Baseline | Candidate |
| --- | --- | --- |
| Strict pass | 78 / 96 | 78 / 96 |
| Case-insensitive pass | 94 / 96 | 94 / 96 |
| Pass and fail flips | 0 | 0 |
| Byte-identical outputs | 78 / 96 |  |

All 18 strict failures were shared. Classification:

| Class | Cases | Detail |
| --- | ---: | --- |
| Letter case only | 16 | Expected `bird`, answered `Bird`. Identical on both dtypes |
| Diacritics | 1 | Expected `Brasilia`, answered `Brasília`, which is correct |
| Unaccepted synonym | 1 | Expected `reptile`, answered `Snake`, which is correct |

The relaxed match raised both configurations from 78 to 94 out of 96. The two
remaining cases were correct model answers that the suite does not accept. A
strict-only score understated both configurations by 16 cases and implied a
precision effect that did not exist.

The 18 non-identical outputs changed no verdict. Of the 18, 10 were long-context
cases that kept the same key and differed only in the appended explanation or in
the wording of the surrounding context. One changed markdown emphasis. Eight were
held-out cases with different wording.

## Breadth sweep result

| Measure | Value |
| --- | ---: |
| Tasks and subtasks scored on both dtypes | 339 |
| Paired documents | 72,066 |
| Flipped documents | 15,704 (21.79 percent) |
| Median score delta | +0.0000 |
| Score delta range | -0.2000 to +0.5525 |
| Tasks significant at p<0.05 (exact McNemar) | 3 |

### The chance-rate reading

At 339 tasks and alpha 0.05, about 17 tasks would be expected to cross the
threshold by chance alone. Three is below that expectation, so the sweep does
not support a family-level regression. It also does not support a per-task
"nothing regressed" claim, because one significant task favoured the baseline.

| Task | Delta | Flips | p | Direction |
| --- | ---: | ---: | ---: | --- |
| `truthfulqa_kn_mc2` | +0.0117 | 267 | 0.0048 | Candidate better |
| `paws_de` | -0.0460 | 71 | 0.0086 | Baseline better |
| `putnam_axiom_original` | +0.0900 | 17 | 0.0490 | Candidate better |

The McNemar test on paired documents is the appropriate test, and it is the one
the report uses. A normal approximation on the per-task rates is not a substitute
for it, because that approximation needs the true paired count rather than a value
inferred from the reported standard error.

### Why the flip rate is not damage

The tasks with the highest flip rates were probability-scored. Many rows flipped
almost every document while scoring within 0.01 of each other. Examples:

- `truthfulqa_mc2`: 499 of 500 documents flipped, candidate better on 254 and
  baseline better on 245.
- `crows_pairs_english`: 300 of 300 flipped, split 161 to 139.
- `truthfulqa_pt_mc2`: 300 of 300 flipped, split 158 to 142.

A correct/incorrect verdict changes rarely at equal accuracy. A probability
score changes on almost every item after a small numeric change. The flip count
is therefore a property of the metric and not a measure of accuracy loss. The
paired test and the delta carry the accuracy claim.

### Contradiction found in the summary

The published summary stated 86 tasks and 15,416 flips out of 64,966 paired
documents, or 23.7 percent. The retained result files held 339 tasks and 7,100
more paired documents. The stated figures understated the sweep and overstated
the flip rate at the same time. Neither figure came from the retained results.
Both were withdrawn in place and replaced.

The summary also ended "no task regresses significantly". That sentence was
false as written. `paws_de` moved against the candidate by 4.6 points at p=0.0086.

## Scope limit

The sweep ran at one topology on two nodes. The deployment that followed the
change ran a different expert-parallel size, so the sweep does not cover the
deployed configuration on that axis. The claim was written at the measured
topology and the uncovered axis was named as a gap. Do not extend this result to
a topology that was not measured.

## Method note for reuse

Read the task family as one unit. A count of significant tasks needs its chance
expectation and its direction split to mean anything. A flip count needs the
metric kind next to it. A pass rate needs to say whether the matcher was strict
or relaxed. Each of these three readings failed separately in this engagement,
and each produced a confidently worded claim that the raw files did not support.