---
name: dataset-tree-readback-validator
description: "Add a read-back validator to a published dataset tree whose writers are gated but never re-read. Use when review must answer whether every unit holds the promised count and whether cross-record invariants still hold, or when a pipeline has writers and a reproducer but no checker."
category: testing
date: 2026-11-06
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - dataset-validation
  - read-back-validator
  - writer-without-checker
  - counts-drift
  - cross-record-invariants
  - stale-summary-docs
  - severity-and-stable-codes
  - allowlist-known-conditions
  - non-vacuous-gate-proof
  - publisher-validator-asymmetry
---

# Validate a Published Dataset Tree by Reading It Back

## Overview

| Field | Value |
| ------- | ----- |
| **Date** | 2026-11-06 |
| **Objective** | Prove that a published data tree satisfies its stated contract, and give the project a checker that reports each failure instead of a one-time manual audit. |
| **Outcome** | A validator reads the shipped tree read-only, reports findings with stable codes and severities, and fails on real defects. It found stale summary documents and a cross-repetition mismatch that the writers and the reproducer both missed. |
| **Verification** | `verified-local` — run on a tree of 6 model groups, 1375 measurement points and 4125 leaves. Every defect class below was observed on that tree and is reproduced by a deliberately corrupted copy. |

A data pipeline usually has two tools: a writer that emits the tree, and a
reproducer that re-emits the inputs. Neither one reads the finished tree. The
writer is gated on its inputs, so it never checks its output as a whole. The
reproducer reads records to build commands, so it stops at the first missing
field and never reports the rest. A tree validated only by "the publisher
exited zero" can hold stale summaries, mixed record shapes, and repetitions
that disagree with each other.

Treat "validate the tree" as its own work item with its own tool. Do not
treat it as a re-run of the publisher.

## When to Use

- A review asks whether every unit has the promised number of repetitions, or
  whether the dataset is consistent and current.
- The repository has a writer or generator for a published tree but no tool
  that reads the tree back.
- A summary document states totals per group, and each group can change
  independently.
- Records from more than one code path, or more than one release, share one
  directory layout.
- A reproducer or consumer aborted early and left it unclear how much of the
  tree was never examined.

## Verified Workflow

### Quick Reference

The validator must answer five questions. Check them in this order; each one
is cheaper than the next.

```text
1. Presence and count   does each unit hold exactly the declared leaves?
2. Decodability         does each leaf decode and have the expected shape?
3. Key correctness      do directory-encoded keys match the record's own fields?
4. Cross-record         do repetitions of one unit agree with each other?
5. Summary agreement    do the aggregate documents state the measured totals?
```

Run it read-only, with stable finding codes, and a exit status that separates
errors from warnings:

```python
ERROR, WARNING = "ERROR", "WARNING"   # exit 1 on ERROR, 2 on WARNING only, 0 clean

def add(self, severity, code, detail):
    if code in self.allowed:          # --allow CODE accepts a known condition
        return
    self.counts[code] += 1
    self.items.append((severity, code, detail))
```

### Suggested Approach

1. **Inventory first, then decide what is a defect.** Read the tree and print
   a histogram of the property under review before you call anything wrong.
   A count histogram per group (for example time taken per repetition) shows
   immediately whether the rule holds, and it also shows which groups were
   built by which code path.

2. **Derive expectations from the tree, not from a hard-coded list.** Parse
   the placement, shape, and concurrency from directory names, and compare
   them with the values the records declare. A validator that hard-codes the
   current groups goes stale in the same way the summaries do.

3. **Separate structural errors from explained conditions.** A missing
   repetition or a leaf that does not decode is an error. A value that the
   source system genuinely produces, such as a server that stops one token
   short of the request, is a warning that names the cause. Keep the code
   stable so a known condition is accepted with `--allow CODE` and is still
   counted, rather than removed from the check.

4. **Test repetitions against each other, not only against the request.**
   Comparing each record with the requested shape misses a run that differs
   from its siblings. Compare the tuples across repetitions of one unit, and
   report the disagreement as its own code. This check found a unit whose
   first repetition produced one fewer output token than the other two.

5. **Compare summary documents with measured totals.** Parse each
   document's stated totals and per-group rows, recompute both from the tree,
   and report a mismatch with the numbers on both sides. Report a listed but
   absent group and a present but unlisted group as separate facts.

6. **Make the exit status meaningful and bounded.** Exit 1 on errors, 2 on
   warnings only, 0 when clean, so CI can fail on defects while an explained
   condition stays visible. Add `--json` for machines and `--max-report N`
   for humans, because a systematic condition can produce thousands of
   lines.

7. **Prove the validator is not vacuous.** Copy one group, delete a leaf,
   corrupt one compressed file, and alter the summary. Confirm that each
   produces the expected code, then discard the copy. A validator that only
   ever returns clean has proved nothing.

8. **Document the validator and its allowance policy** next to the writer in
   the project README, including the exit-status contract and what each
   warning code means.

9. **Fix the summary documents by regenerating them from the tree**, not by
   adding the difference to the old numbers. Recompute points, leaves, bytes,
   and per-group rows in one pass so the values cannot disagree.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Trusted the writer's exit status | Treated a successful publish run as proof that the tree was consistent | The writer is gated on inputs and never re-reads its output; a stale summary and a cross-repetition mismatch both survived | Validation of the shipped tree is a separate step with its own tool |
| Trusted the reproducer | Used the reproducer's clean exit as an overall check | It stops at the first missing field, so it reported a fraction of the tree and said nothing about the rest | A consumer aborting early is not a coverage report |
| Compared only against the request | Checked each record's achieved length against the requested length | Missed one repetition that differed from its siblings while each value was individually plausible | Compare repetitions of the same unit with each other |
| Classified every shortfall as a defect | Reported a server's uniform one-token shortfall as an error | The source system produces it consistently; calling it an error buries the real defects | Give explained conditions their own warning code and an explicit allowance |
| Hard-coded the group list | Wrote expected groups into the validator | The list goes stale exactly as the summaries did | Derive expectations from directory names and record fields |
| Hand-edited the stale totals | Added the new counts to the old figures in each summary | The old figures were themselves wrong in several rows | Recompute from the tree in one pass |

## Results & Parameters

### Configuration

```bash
python3 scripts/validate_dataset.py \
  --dataset-root perf \
  --json \
  --max-report 40 \
  --allow ITLS_SHORT,RUNS_DISAGREE_ITL
```

| Option | Effect |
| --- | --- |
| `--dataset-root` | Root of the published tree; default `perf`. |
| `--json` | Emit findings, counts, and totals as JSON. |
| `--max-report` | Limit printed findings; the remainder is summarized. |
| `--allow` | Comma-separated codes accepted silently but still run. |

### Expected Output

- A per-code finding list with severity, then a totals line and an error and
  warning count.
- Exit 0 when clean, 1 when any error is reported, 2 when only warnings are.
- After remediation on the captured tree: 10 summary-document errors fixed,
  1 cross-repetition error left open and reported, and explained conditions
  retained as warnings.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| Local dataset tree | 6 model groups, 1375 points, 4125 leaves | Found 5 of 6 summary documents stale, 1 cross-repetition output mismatch, and two record shapes in one tree. The corrupted-copy check reproduced each error code. |

## References

- [doc-claim-drift-liveness-and-provenance-gate](doc-claim-drift-liveness-and-provenance-gate.md)
  repairs documents that disagree with live state; this skill repairs and
  gates a data tree that disagrees with its own contract.
- [generated-artifacts-stale-after-input-change-pinned-regeneration](generated-artifacts-stale-after-input-change-pinned-regeneration.md)
  covers regenerating derived artifacts after an input change; this skill
  covers checking that the published result satisfies its invariants.
- [dataset-download-checksums-scope-manifests-per-source](dataset-download-checksums-scope-manifests-per-source.md)
  covers per-source integrity of downloaded artifacts.