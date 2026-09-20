---
name: evaluation-baseline-parity-cross-matrix
license: BSD-3-Clause
description: "Compare training runs when architectures or data pipelines differ; design controlled cross-runs and preserve artifact provenance."
category: evaluation
date: 2026-07-11
version: "1.1.0"
user-invocable: false
verification: verified-local
tags: [baseline, parity, confound, cross-matrix, ablation, fair-comparison, experiment-design, provenance]
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/evaluation-baseline-parity-cross-matrix.history"
history-cleanup-date: "2026-09-20"
---

# Baseline Parity and Cross-Matrix Evaluation

## Overview

| Field | Value |
| --- | --- |
| Date | 2026-07-11 |
| Objective | Separate learning-rule effects from architecture and pipeline differences. |
| Outcome | A prior research review identified confounded comparisons and proposed cross-runs. Private measurements and project identifiers are omitted. |
| Verification | verified-local for the recorded design review; cross-run results were not available in that record. |

## When to Use

- A baseline and treatment run differ in more than the variable under study.
- Follow-up experiments could separate architecture effects from learning-rule effects.
- Cross-run costs depend on the architecture or update rule.
- Data artifacts move between branches whose commit identifiers can change.

## Verified Workflow

### Quick Reference

Compare the configurations before interpreting a metric gap. Useful fields include
layer strides, widths, normalization, augmentation, seeding, and batch composition.

```bash
diff <(grep -E "stride|width|channels|fc|dropout" baseline/config) \
     <(grep -E "stride|width|channels|fc|dropout" treatment/config)
sha256sum data/copied_artifact.bin
```

The commands support inspection and provenance; they do not prove experimental
parity by themselves. Review other fields that can affect the comparison.

### Suggested Approach

1. Record architecture and data-pipeline differences. If their effect is unknown,
   describe the observed gap without attributing it to the learning rule alone.
2. Consider a two-by-two design with rules R1 and R2 on architectures A and B.
   Holding each rule's protocol constant while swapping architecture gives
   within-rule architecture contrasts. Within-architecture rule comparisons
   still include any remaining pipeline differences; state that limitation.
3. Estimate each cross-run's cost from its actual computational scaling. A stride
   change can substantially change spatial work. Choose concurrency from available
   resources and the metric; contention can invalidate wall-clock comparisons.
4. For copied artifacts, record a content hash and a durable source reference.
   A rewritten branch commit alone may no longer locate the original artifact.
5. If logs lack event timestamps, label derived timing estimates with their method
   and assumptions. File modification time is not direct per-event timing evidence.
6. When the user changes the experiment scope, distinguish results under the new
   criteria from earlier trajectories. Continue independent analysis and use the
   revised direction when clear. Ask only for a material unresolved choice.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Confounded comparison | Attributed a baseline-treatment gap to the update rule | Architecture and pipeline also differed, with unknown bias | Describe confounds before making a causal claim. |
| Branch-only provenance | Cited a copied artifact by another branch's commit | Rebase rewrote the locator | Record the artifact hash and a durable source reference. |
| Timing overclaim | Presented an interim cadence estimate as a measurement | The estimate did not match the available timing evidence | State the derivation and its limits. |
| Cost assumption | Assumed one cross-run would be cheaper | The rule's cost depended on the changed spatial dimensions | Estimate both directions from the actual computation. |

## Results & Parameters

- **Comparison record:** architecture deltas, pipeline deltas, metric, and attribution limits.
- **Cross-matrix:** R1/A, R1/B, R2/A, R2/B, with the retained protocol documented.
- **Compute plan:** cost estimates, resource assumptions, and contention limits.
- **Artifact provenance:** byte-preserving copy, content hash, and durable source reference.
- **Evidence status:** distinguish measured results, derived estimates, and proposed runs.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| Private research project | Baseline comparison and proposed cross-matrix | Prior review covered the design and confounds. Identifying details and private numerical results are omitted. No new run is claimed. |
