# Notes: parse-failure-attribution-across-pipeline-layers

Supporting evidence for [the main skill](parse-failure-attribution-across-pipeline-layers.md).
Everything here is generalized. No account, host, repository, or issue identifier
appears in this file or in the main entry.

## What the incident was

A long-running planning pipeline produced four terminal failures in one run. Every
item reported the same cause: the model could not satisfy the response contract. The
run spent 16 agent jobs and produced no result.

The first recorded signal was a decode error at line 1 column 1, followed by a
contract parse error. Read naively, that says the model returned nothing.

## Why the naive reading was wrong

The pipeline had more than one stage between the model and the contract parser:

1. The agent process wrote a JSONL event stream to standard output.
2. A reader decoded each line and tracked the session identifier.
3. A selection function held one slot for the assistant text and assigned to it on
   every text event.
4. The contract parser validated the selected text.

Step 3 had no guard. It assigned on every text element, including elements whose
text was empty. The recorded series for one failing item had a correct answer on
element 2 and an empty text element last. The assignment on the last element
replaced the answer.

The parser therefore received an empty string, and raised a decode error at line 1
column 1, which is exactly what an empty string produces.

## How the attribution was confirmed

An offline reproduction ran the recorded event series through the real stages in
the real order:

| Stage | Value |
| ----- | ----- |
| Model produced | a correct answer inside a lowercase JSON fence |
| Selection returned | the empty string |
| Contract parser | decode error at line 1 column 1, then a contract parse error |
| Control, same series without the trailing empty element | parsed successfully |

Removing one empty element changed the outcome from failure to success. That
isolated the fault to the selection step.

## The cost of the wrong attribution

A complete benchmark task was authored before the attribution was corrected. It
proposed a capability screen that would declare the producer nonconforming after
one retry. That repair would have:

- reported a false cause, because the producer did conform;
- spent the same retry budget it claimed to save, because its own probe read the
  same empty element;
- masked the real defect behind a plausible log line.

The artifact was withdrawn and rebuilt around the proven fault. The withdrawal and
its reason were recorded in the replacement artifact so that the mistake stays
visible.

## Evidence for the wrong-layer check

The obvious repair for the surface error is to make the contract tolerant: extract
a payload from a fenced block, from prose, or from a trailing series. That repair
was authored as a preserved negative case and replayed against the fixture.

Its failing set was exactly the failing set of the unmodified parser, plus one
integrity pin. Widening the contract changed no observable behavior. The answer
was already gone before the contract saw it.

This is the reusable form of the check: apply the candidate repair to the fixture
before accepting it. A repair that does not move the fixture is at the wrong layer,
no matter how reasonable it looks.

## Evaluation design notes

The rebuilt artifact used a hidden trusted evaluator with these controls, each of
which caught a distinct failure mode:

| Control | What it caught |
| ------- | -------------- |
| Selection checks that compare the selected value, not only that a parse failed | A repair that returned the first non-empty element instead of the last |
| Held-out recorded series that the fixture never contained | A repair that recognized recorded series by exact content |
| Pinned digests for the contract and the fixture | A repair applied at the consumer layer |
| Separate causes for an absent payload and a contract failure | A repair that collapsed both into one error |
| A no-fabrication check | A repair that substituted a valid payload when the series carried none |

Two authoring defects in the evidence itself were found and corrected: a preserved
negative case whose path arithmetic broke after relocation, so every check failed
with a crash instead of a detection; and an acceptance record written before the
runs it described.

## Terminology

- "Empty element" means a series element that carries no payload body. It is not
  the same as an element of a different type, which a correct reader skips.
- "Absent payload" and "payload that fails the contract" are separate causes. A
  reader that returns one empty default for both makes them indistinguishable.
- "Offset zero" describes the received value. It never names a component.