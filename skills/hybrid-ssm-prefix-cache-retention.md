---
name: hybrid-ssm-prefix-cache-retention
description: "Diagnose device-memory exhaustion caused by completed-prefix retention in a hybrid attention/recurrent model server. Use when: (1) serial requests with distinct prompts exhaust device memory, (2) a lower static-memory fraction only delays the failure, (3) a unified cache retains attention KV and recurrent state after request completion, or (4) a recurrent-state no-buffer strategy is proposed as equivalent to disabling prefix caching."
category: debugging
date: 2026-11-16
version: "1.0.0"
user-invocable: false
tags:
  - inference
  - serving
  - hybrid-ssm
  - mamba
  - prefix-cache
  - radix-cache
  - memory-growth
  - out-of-memory
  - serial-requests
---

# Hybrid-SSM Prefix-Cache Retention

<!-- Use [ASD-STE100](../docs/asd-ste100.md) for prose. Keep the headings and table
columns below so that the entry stays compatible with corpus retrieval. -->

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-16 |
| **Objective** | Separate cross-request prefix retention from in-flight memory use, select a valid cache-control experiment, and preserve a usable serving configuration while the root cause remains open. |
| **Outcome** | Operational. Distinct serial requests exhausted device memory with unified attention-KV/recurrent-state prefix retention enabled. A smaller static-memory allocation delayed the failure. Disabling prefix insertion completed the full workload without a resource error. This is a configuration workaround for the tested engine and model, not proof of a general hybrid-model defect or an allocator repair. |

## When to Use

- Device memory grows across completed requests until the server reports an
  out-of-memory error.
- The failure occurs with one running request, so concurrent in-flight state
  does not explain the growth.
- Requests use distinct prompts, so completed-prefix insertion can grow the
  cache without useful prefix reuse.
- A hybrid model uses a unified prefix tree or coordinated caches for
  attention KV and recurrent state.
- A lower static-memory fraction increases the number of completed requests
  but does not stop the growth.
- An operator proposes `no_buffer` as a substitute for disabling the prefix
  cache.

Do not use this entry to explain cache-hit numerical differences or to decide
whether a cache tier improves throughput. See the related entries below for
those questions.

## Verified Workflow

### Quick Reference

```text
1. Reproduce at concurrency 1 with distinct prompts and fixed output limits.
2. Record device memory, engine-pool free memory, cache occupancy, and the
   active/completed request counts after warm-up.
3. Treat continued growth after request completion as a cross-request
   retention problem, not proof of concurrent-request pressure.
4. Use one lower static-memory fraction only as a diagnostic. A later failure
   with the same growth pattern is a delay, not a repair.
5. Repeat the same workload with completed-prefix insertion disabled. Hold
   every other setting constant.
6. Accept the workaround only after memory reaches a stable operating range
   and every required request completes without a server resource error.
7. Benchmark the accepted configuration again because removing prefix reuse
   changes performance.
```

### Suggested Approach

1. **Make request lifetime visible.** Use serial requests and distinct
   prompts. Discard warm-up samples, then record memory and cache state at
   fixed request intervals. Include active-request count so a completed
   request cannot be mistaken for an in-flight request.
2. **Inspect both cache components.** For a hybrid attention/recurrent model,
   identify where finished requests insert attention KV and recurrent
   checkpoints. Track insertion, locking, eviction, and release for both
   components. A bounded cache can grow during warm-up; growth that continues
   through unique completed requests until exhaustion requires a retention or
   eviction investigation.
3. **Use the memory-fraction result as evidence, not as a fix.** If a smaller
   static allocation only moves the out-of-memory point later, preserve that
   result as a diagnostic and stop varying the same knob. Partial generations
   from either failed arm are not valid accuracy results.
4. **Change one cache control.** For an engine that provides
   `--disable-radix-cache`, use that flag to disable prefix insertion and
   reuse for the A/B run. Keep the model, static-memory fraction, request
   order, decoding parameters, and output limits unchanged.
5. **Keep `no_buffer` separate.** In an engine with
   `--mamba-radix-cache-strategy no_buffer`, the strategy changes recurrent
   state buffering and checkpoint placement while prefix caching remains
   enabled. It is not equivalent to `--disable-radix-cache`. Confirm the
   installed engine version's documentation and effective launch arguments,
   then test this strategy as a separate arm if needed.
6. **Bound the claim.** A successful cache-disabled run isolates the operative
   configuration. It does not by itself distinguish an eviction defect, an
   ownership error, or an undersized cache budget. Inspect per-component
   cache counts and ownership before naming an upstream root cause.
7. **Preserve reuse as a follow-up requirement.** If the production workload
   shares prefixes, do not make cache disablement the unexamined final state.
   Supply the serial distinct-prompt reproducer and per-component retention
   evidence to the cache-lifecycle investigation. Measure the performance
   cost of the workaround in the meantime.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Attributing exhaustion to concurrent requests | Ran the workload with one running request | Memory continued to grow across completed requests until the scheduler failed | Use serial distinct-prompt requests to expose cross-request retention; concurrency is not required for this failure class |
| Reducing the static-memory fraction | Repeated the cache-enabled run with a smaller static allocation | More requests completed, but the same growth ended in device-memory exhaustion | Treat a later failure as a diagnostic delay, not a completed workaround |
| Accepting a partial evaluation | Calculated results from rows completed before the server failure | The failed arm omitted requests and contained request errors | Reject partial or error-containing artifacts; rerun the full workload after the configuration change |
| Calling the cache-disabled run an allocator fix | Used successful completion as proof of an upstream repair | The A/B result isolated prefix retention but did not identify the faulty ownership or eviction mechanism | Report a validated configuration workaround and keep the root-cause investigation open |

## Results & Parameters

### Configuration

```yaml
reproducer:
  concurrency: 1
  prompts: distinct
  output_limit: fixed_per_dataset
  warmup: discard
  hold_constant: [model, memory_fraction, decoding, request_order]
record_each_interval:
  - device_memory
  - engine_pool_free_memory
  - attention_cache_occupancy
  - recurrent_cache_occupancy
  - active_requests
  - completed_requests
controls:
  lower_memory_fraction: diagnostic_only_when_growth_continues
  disable_radix_cache: disables_prefix_insertion_and_reuse
  mamba_no_buffer: changes_recurrent_buffering_not_global_cache_enablement
acceptance:
  memory: stable_after_warmup
  requests: complete_required_workload
  resource_errors: zero
  partial_results: reject
  performance: rerun_with_accepted_cache_configuration
```

### Expected Output

- A serial request/memory series that separates completed-prefix retention
  from in-flight request state.
- One matched cache-enabled/cache-disabled comparison, with any separate
  recurrent-buffer strategy arm labeled correctly.
- A completed workload and stable memory under the selected workaround, or a
  bounded retention investigation if cache reuse must remain enabled.
- Performance and accuracy artifacts from complete runs under the accepted
  configuration only.
- A claim scoped to the tested engine, model, cache implementation, and
  workload shape.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Isolated single-accelerator inference comparison | Serial distinct-prompt evaluation of a hybrid attention/recurrent checkpoint | Two cache-enabled configurations reached device-memory exhaustion after different numbers of completed requests. The lower static-memory fraction delayed the failure. The same lower fraction with prefix caching disabled completed the performance run and two full evaluation datasets without a server resource error. Project, model, host, job, dataset, issue identifiers, and private measurements are withheld. See [notes.md](../skills/hybrid-ssm-prefix-cache-retention.notes.md). |

## References

- [Cache Tier Verdict Depends On Reuse Shape](cache-tier-verdict-depends-on-reuse-shape.md)
- [Prefix-Cache Shape and Kernel Evidence](debugging-prefix-cache-nsight-kernel-evidence.md)
- [Inference Benchmark Warmup Regime](inference-benchmark-warmup-regime.md)
