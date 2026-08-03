---
name: inference360-dynamic-serving-capacity
description: "Compute serving concurrency from the selected checkpoint and exact assigned GPU subset. Use when: (1) an inference profile needs a safe request limit, (2) capacity depends on checkpoint KV-cache geometry, or (3) a scheduler allocation must be measured instead of relying on static profile limits."
category: optimization
date: 2026-07-27
version: 1.0.0
user-invocable: false
verification: implementation-and-focused-tests
tags: [inference360, warden, h200, slurm, vllm, sglang, kv-cache, capacity]
---

# Inference360 Dynamic Serving Capacity

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-27 |
| **Objective** | Derive a safe serving-concurrency limit from the selected checkpoint, context window, engine, and exact scheduler-assigned GPUs. |
| **Outcome** | Operational. The verified Inference360 change implemented checkpoint-aware capacity calculation, engine adapters, profile migration, and behavior tests. |

## When to Use

Use when an ExecutionProfile needs a request-concurrency limit that is safe for
the selected checkpoint, context window, GPU allocation, and engine.

## Verified Workflow

### Quick Reference

1. Inspect the selected checkpoint and the exact scheduler-assigned GPU subset.
2. Compute the full-context request budget for every assigned rank.
3. Use the minimum rank budget, clamp it to at least one, and apply any optional upper-bound override.
4. Pass the result through the engine adapter and persist the calculation facts.

### Detailed Steps

1. Treat `gpu_memory_utilization` as the desired per-GPU HBM fraction and keep
   `max_running_requests` optional. A supplied value is only an upper bound.
2. Before launch, query `nvidia-smi` through a nested Slurm step scoped to the
   exact allocated GPU subset; do not inspect unrelated host GPUs.
3. Derive weight payload, dtype, KV-head geometry, and context length from the
   selected checkpoint inspection. The checkpoint configuration, not a service
   profile or YaRN label, owns the maximum context length.
4. Compute a full-context request budget per assigned rank, select the minimum,
   and clamp the effective value to at least one. Apply an optional override as
   `min(computed, override)`.
5. Pass the result through the engine adapter: vLLM uses `--max-num-seqs` and
   SGLang uses `--max-running-requests`. Persist raw, computed, effective,
   shortfall, and override facts in Warden runtime state for status.
6. Fail closed if checkpoint inspection is unavailable or the selected engine
   has no dynamic-capacity adapter.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------ | -------------- |
| Static profile cap | Used a fixed limit such as one request for YaRN profiles | It ignores checkpoint weights, HBM allocation, utilization fraction, and KV-cache geometry | Compute capacity from the selected checkpoint and allocation. |
| Profile-owned context | Derived context length from the service profile | It duplicates checkpoint configuration and can launch a mismatched sequence limit | Treat the checkpoint configuration as authoritative. |
| Host-wide GPU probe | Measured all visible host GPUs before launch | The result can include GPUs that are not assigned to the serving step | Scope measurement to the exact scheduler allocation. |

## Results & Parameters

### Configuration

```yaml
gpu_memory_utilization: <desired-per-GPU-HBM-fraction>
max_running_requests: <optional-upper-bound>
checkpoint: <selected-checkpoint>
engine: vllm | sglang
capacity_policy: min(full-context-budget-per-rank)
minimum_effective_requests: 1
```

### Expected Output

Persist raw allocation, computed capacity, effective capacity, shortfall, and
override facts in runtime state. vLLM receives `--max-num-seqs`; SGLang receives
`--max-running-requests`. Missing checkpoint facts or an unsupported engine must
fail closed before launch.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| Inference360 | Warden dynamic serving-capacity implementation | Commit `2feacedcd1113cb8c9d840e7a57c6cbee8d4afc8` passed focused capacity, manifest, lifecycle, and profiling tests. |

## References

- [Inference360 source commit](https://github.com/LLM360/Inference360/commit/2feacedcd1113cb8c9d840e7a57c6cbee8d4afc8)
