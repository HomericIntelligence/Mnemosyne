---
name: inference360-dynamic-serving-capacity
description: Compute Warden serving concurrency from the selected checkpoint and the exact assigned H200 GPU subset rather than static profile limits.
category: inference360
date: 2026-07-27
version: 1.0.0
verification: implementation-and-focused-tests
tags: [inference360, warden, h200, slurm, vllm, sglang, kv-cache, capacity]
---

# Inference360 Dynamic Serving Capacity

## When to use

Use when an ExecutionProfile needs a request-concurrency limit that is safe for
the selected checkpoint, context window, GPU allocation, and engine.

## Verified workflow

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

## Failed approaches

- Static YaRN caps such as one request do not account for checkpoint weights,
  HBM allocation, utilization fraction, or KV-cache geometry.
- Deriving context from a profile duplicates checkpoint-owned configuration and
  can launch a server with a mismatched sequence limit.
- A host-wide GPU probe can calculate capacity from GPUs not assigned to the
  serving step.

## Evidence

Inference360 change `2feacedcd1113cb8c9d840e7a57c6cbee8d4afc8` implemented
the calculation, engine adapters, profile migration, and behavior tests. Focused
capacity, manifest, lifecycle, and profiling tests passed before merge.
