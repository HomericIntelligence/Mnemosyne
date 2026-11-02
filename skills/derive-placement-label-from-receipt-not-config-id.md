---
name: derive-placement-label-from-receipt-not-config-id
description: "Derive an execution-placements label such as nodes x GPUs-per-node from the run receipt and the node ceiling, not from the config id alone. Use when (1) a config id encodes only a total GPU or device count, (2) a dataset or report names topology in a nodes-by-devices-per-node form, or (3) an aggregate count can be satisfied by more than one physical placement."
category: architecture
date: 2026-11-01
version: "1.0.0"
user-invocable: false
tags:
  - placement
  - topology-label
  - topology
  - scheduling
  - gpu-count
  - config-id
  - receipt
  - partial-result
  - python
---

# Derive Placement Labels From Receipts, Not Config IDs

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Prevent a published label that asserts a physical placement the cluster cannot host. |
| **Outcome** | Successful. The placement rule was verified offline against real run receipts and refused every unreachable placement. |

## When to Use

Use this skill when one of these conditions applies:

- A config id or job name encodes only a total device count, and the label must name nodes as well.
- A dataset, report, or directory path names topology as `<nodes>x<devices-per-node>`.
- An aggregate count maps to more than one physical placement.
- A label is built once at parse time, before any run has been observed.

## Verified Workflow

### Quick Reference

Derive the label from two facts, then refuse the placements that the hardware or the launcher cannot produce:

```python
GPUS_PER_NODE = 8  # take this from live scheduler facts, not from memory

def placement(gpus, nodes):
    if nodes < 1 or gpus < 1 or gpus % nodes:
        raise ValueError("uneven or empty placement")
    per_node = gpus // nodes
    if per_node > GPUS_PER_NODE:
        raise ValueError("exceeds the per-node ceiling")
    if nodes > 1 and per_node != GPUS_PER_NODE:
        raise ValueError("multi-node launcher claims whole nodes")
    return f"{nodes}x{per_node}"
```

### Suggested Approach

1. Read the node ceiling from live scheduler facts (`sinfo` reports the per-node Generic Resource counts for every partition) before you fix any constant. Do not infer it from the request under study.
2. Treat the total device count as insufficient. Any count above the per-node ceiling forces a multi-node placement, and the label must say so.
3. Because more than one node count satisfies a given total, keep the node count out of parse-time output. Have the parser report the total and defer the label:
   - return an empty label, or omit the field, when the caller has no receipt yet;
   - fill the label per run, where the receipt is readable.
4. Read the node count from the run's launch receipt, and default to a single node when no receipt exists. Accept both the probe-level and the attempt-level receipt location, because layouts differ.
5. Refuse two classes of unreachable placement, and report each refusal as a work item, not a crash:
   - more devices per node than the ceiling allows;
   - a multi-node count that leaves some node partly used, when the launcher reserves a whole node per rank.
6. Test the refusal branches explicitly. An exceeded ceiling is the easy case; the partial-node case is the one that silently passes a naive ceiling-only check.
7. Widen any stage or output walker to the layout that multi-node jobs actually write. A correct label still yields nothing if the collector never descends into that directory shape.
8. Verify the reported placement against the clusters that the dataset will serve before you publish. A label that resolves no config is a verified defect.

Treat a missing receipt as single-node, which matches the existing single-node evidence. When the scheduler is unavailable, state the limit and keep the deferred-label design rather than guessing the ceiling.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Build the label with a fixed single-node prefix | Interpolated a total device count into a `1x<count>` label at parse time | Produced a label asserting one node with more devices than any node provides | An aggregate count does not determine the node count |
| Enforce only the per-node ceiling | Refused a count above the ceiling | Accepted partial-node multi-node placements such as half-full second node, which the launcher never produces | Enforce whole-node packing separately from the ceiling |
| Require the node count as a parser argument with a default of one | Kept the parse-time signature but added the placement call | Callers parse configs before any receipt is read, so the default one silently recreated the wrong label | Defer the label; supply it where the receipt exists |
| Verify only by plan review, then test with an ad-hoc harness | Reused the original settled config paths in a synthetic stage | The harness called the changed parser with its old signature and failed on the harness, not on the code | A synthetic test must call the current signature; separate harness defects from product defects before drawing a conclusion |

## Results & Parameters

### Configuration

```yaml
placement:
  per_node_ceiling: from live scheduler facts    # not a stored guess
  label_form: "<nodes>x<devices_per_node>"
  multi_node_policy: whole nodes only            # matches a whole-node-per-rank launcher
  missing_receipt: assume one node
  deferred_label: parser reports total; collector fills label per run
refusal_reporting:
  per_work_item: true
  abort_whole_run: false
```

### Expected Output

- A single-node run keeps its existing label.
- A high-count run produced on several nodes gets a multi-node label.
- A count that exceeds the ceiling on one node is refused, with a message that names the minimum node count.
- A partial-node placement is refused, with a message that names the launcher constraint.
- A collector descends the multi-node layout and yields the same record fields as the single-node layout.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| Mnemosyne | Derived from an inference-size dataset publication session on 2026-11-01 | The ceiling came from live scheduler facts, the refusal branches were probed directly, and a real multi-node receipt resolved to two nodes. Delivery was not published. See [notes](derive-placement-label-from-receipt-not-config-id.notes.md). |

## References

- [sinfo(1) — per-node Generic Resource reporting](https://slurm.schedmd.com/sinfo.html)
- [Related: evaluate multi-account capacity before planning](slurm-multi-account-capacity-evaluation.md)
- [Related: derive limits from the manifest, not from defaults](manifests-config-derived-limits-digest-hardening.md)