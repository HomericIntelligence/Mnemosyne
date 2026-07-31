---
name: bf16-monokernel-sol-profiling
description: "Build and interpret a reproducible BF16 CUDA RMSNorm monokernel benchmark. Use when: (1) model-derived normalization workloads may duplicate parameter counts, (2) a rootless H200 profile needs verified latency, correctness, and artifact provenance, (3) Nsight Compute counters are policy-restricted, or (4) a tiny one-row kernel reports unexpectedly low global speed-of-light."
category: optimization
date: 2026-07-30
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [cuda, bf16, rmsnorm, monokernel, nvidia-h200, roofline, sol, ncu, nsys, slurm, enroot, provenance]
---

# Reproducible BF16 CUDA Monokernel SOL Profiling

## Overview

| Field | Value |
| --- | --- |
| Date | 2026-07-30 |
| Objective | Measure a latency-oriented BF16 weighted-RMSNorm CUDA monokernel without conflating model naming, correctness, profiler overhead, or global hardware roofline utilization. |
| Outcome | A 14-case H200 matrix used one workload per unique normalization parameter count, passed exhaustive harness and host-oracle validation, and preserved rootless profiling provenance. |
| Verification | verified-local: rootless image contracts and full host suite passed; H200 GPU validation and Compute Sanitizer passed; a 14-case Nsys matrix completed with artifact hashes verified. |

## When to Use

- A CUDA microkernel should represent model normalization-module parameter sizes rather than a model's total parameters or an entire transformer layer.
- Multiple representative models map to the same RMSNorm or LayerNorm parameter count and would otherwise create duplicate benchmark rows.
- A low-latency BF16 kernel needs independent baseline comparison, exhaustive correctness checks, and a reproducible rootless H200 environment.
- A roofline report must distinguish an algorithmic lower bound from native Nsight Compute counters and Nsight Systems timing attribution.
- Nsight Compute fails with a GPU-counter permission error, but a valid Nsight Systems trace can still be collected.
- A one-row kernel has very low global SOL and an optimization decision must distinguish launch/grid underfill from poor HBM use.

## Verified Workflow

### Quick Reference

1. Derive each workload from one source normalization module and deduplicate by total learned parameter count.
2. Keep baseline and optimized CUDA implementations separate; make the host harness own input generation, timing, exhaustive comparison, and failure policy.
3. Verify the rootless image digest before creating the runtime, then record image, dependency-lock, source-tree, device, tool, and profiler artifact hashes.
4. Measure verified uninstrumented p50 first. Capture a separate Nsys trace for kernel duration and launch attribution; collect NCU counters only when permitted.
5. Report algorithmic, NCU, and Nsys SOL as separate fields. Interpret global SOL together with CTA-to-SM coverage.

### Detailed Steps

1. **Map model normalization parameters, not model size.** Map RMSNorm width `H` to `H` learned parameters, affine LayerNorm to `2H`, and bias-free LayerNorm to `H`. A parameter-count-equivalent RMSNorm workload must retain the source normalization type and must not claim to execute LayerNorm semantics.
2. **Make the execution ladder canonical.** Select exactly one representative case for each total parameter count. Keep other models with an equal count as provenance aliases only; do not give them independent CLI identifiers, profiler directories, or correctness results.
3. **Keep validation outside CUDA implementation code.** Generate deterministic BF16 inputs and non-unit weights in the harness. Run independent baseline and optimized implementations on identical inputs, compare every output, record nonfinite and error statistics, and run a small host oracle. Return CUDA errors to the harness instead of embedding device-side assertion policy.
4. **Create a reproducible rootless profile environment.** Pin the dependency lock and SquashFS image; verify image bytes by SHA-256 before rootless runtime creation. Mount source and a dedicated result directory, record device and tool versions, and make a post-run provenance document hash every retained benchmark and profiler artifact.
5. **Separate timing from tracing.** First run a verified, uninstrumented benchmark with stable warmup and sample counts. Then use a short `nsys` or `ncu` capture to identify the optimized kernel. Do not treat profiler-instrumented host timing as the latency benchmark result.
6. **Compute the algorithmic lower bound explicitly.** For `N = rows * columns` BF16 weighted-RMSNorm elements, use `F = 4N` FLOPs and ideal traffic `B = 6N` bytes for one input, one learned scale, and one output. With the selected hardware profile, calculate `T_SOL = max(F / peak_compute, B / peak_memory)` and `runtime_SOL = min(T_SOL / verified_p50, 1) * 100`.
7. **Keep three profiling views distinct.** Report algorithmic/runtime SOL from the uninstrumented p50; report NCU counter SOL as the greater of DRAM and SM percent-of-peak only when counters were collected; and report Nsys average kernel duration, estimated launch gap, and a separately calculated kernel-only lower-bound SOL. The harness's implementation-specific traffic convention is not the ideal roofline byte count.
8. **Fail closed on missing NCU access.** If NCU returns `ERR_NVGPUCTRPERM`, record counter SOL as unavailable and preserve the failure reason. Do not report zero utilization or bypass host policy. Use Nsys to preserve kernel duration and launch attribution, while clearly stating that it does not measure native bandwidth or SM utilization.
9. **Interpret grid coverage before choosing an optimization.** Include `min(grid_blocks / SM_count, 1)` in every report. A one-CTA workload cannot saturate all SMs, so a low global SOL can primarily indicate launch overhead or underfill. To improve single-invocation latency, prioritize launch reduction or legal fusion; increasing concurrent work changes the workload and should be reported separately.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Run each model-size label independently | Several representative models had identical normalization parameter counts | The result duplicated a measurement while making the ladder appear broader than it was | Deduplicate by total normalization parameter count; retain equal-count models as provenance aliases only. |
| Treat profiler output as the latency benchmark | Used the instrumented process timing as the measured p50 | Tracing materially changed process timing and mixed profiler overhead into the result | Use verified uninstrumented event timing for p50; use traces only for attribution. |
| Parse profiler stdout as CSV from its first line | Passed NCU/Nsys export text directly to a CSV reader | Both tools can prepend informational lines before the real CSV header | Locate and validate the expected header before parsing rows. |
| Require NCU counters on a restricted host | Ran Nsight Compute despite `ERR_NVGPUCTRPERM` | GPU-counter access was denied by host policy, not by kernel behavior | Mark native counter SOL unavailable and use Nsys without attempting a privilege workaround. |
| Reuse the generic eight-byte traffic figure as roofline traffic | Used two input reads, scale read, and output write for every SOL calculation | That is an implementation-specific effective-traffic convention, not the ideal RMSNorm model | Use six ideal BF16 bytes per element for the lower bound and keep effective bandwidth separate. |

## Results & Parameters

### Canonical Parameter Ladder

The verified one-row BF16 ladder contained these unique total normalization parameter counts:

```text
128, 256, 512, 576, 896, 1024, 1536, 2048, 2560, 4096,
5120, 6144, 7168, 8192
```

Use stable workload identifiers and source provenance for each count. Equal-count model aliases are documentation only, never repeated measurement rows.

### H200 Profile Parameters

| Parameter | Verified value | Interpretation |
| --- | ---: | --- |
| Precision | BF16 input, scale, and output; FP32 accumulation | One weighted-RMSNorm numerical contract. |
| Timing | 100 warmups, 5,000 uninstrumented samples | Use the verified optimized p50 for runtime SOL. |
| Selected H200 profile | 989 BF16 TFLOP/s, 4.8 TB/s HBM | Hardware-profile inputs, not universal device constants. |
| One-row grid coverage | `1 / 132 = 0.758%` | Explain low global SOL before diagnosing HBM saturation. |
| NCU result | unavailable on the verified host | `ERR_NVGPUCTRPERM` is a policy result, not zero utilization. |

### Verified Results

| Metric | Result |
| --- | --- |
| Correctness | 14 of 14 cases passed GPU comparison and host oracle; 40,256 elements compared with zero mismatches, nonfinite values, absolute error, relative error, and RMSE. |
| Optimized latency | 5.856 to 9.760 microseconds across the ladder. |
| Baseline-to-optimized speedup | 1.027x to 1.695x; 1.274x geometric mean. |
| Representative 7,168-parameter case | 15.392 to 9.312 microseconds, 1.653x speedup. |
| Mean global runtime SOL | 0.0443%. |
| Mean Nsys kernel-only SOL | 0.0886%. |

The low global SOL is expected for a one-CTA latency microkernel. In the representative 7,168-parameter case, Nsys attributed 5.344 microseconds to the GPU kernel and approximately 3.968 microseconds to launch/other elapsed work; optimize this attribution before claiming an HBM bottleneck.

### Required Artifact Contract

Keep a dedicated profile root containing:

- the verified uninstrumented benchmark JSON for every canonical case;
- raw NCU or Nsys report and a parsable export for every captured case;
- one SOL JSON per case plus CSV and Markdown matrix summaries;
- image digest, dependency-lock digest, source-tree digest, hardware inventory, profiler versions, selected tool, warmup/sample counts, and scheduler identity; and
- SHA-256 records for every retained artifact.

If a source revision is unavailable, the source-tree digest remains the binding source identity. Refuse to overwrite a completed provenance record.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| CUDA monokernel benchmark | Rootless NVIDIA H200 BF16 weighted-RMSNorm profiling, 2026-07-30 | Full rootless host suite, H200 correctness/Compute Sanitizer, and a 14-case Nsys matrix passed; artifact hashes were independently recomputed. |

## References

- [Radiance RMSNorm estimator](https://github.com/LLM360/Radiance/blob/add857a1ee42bfd907e956783213cd4e173844a0/radiance/metrics/ops/rms_norm.py)
- [Radiance H200 hardware-profile evidence](https://github.com/LLM360/Radiance/blob/add857a1ee42bfd907e956783213cd4e173844a0/fixtures/hardware_profiles/builtin_profile_evidence.json)
- [Nsight Systems profile preflight](sglang-moe-nsys-profile-preflight.md)
- [Machine-local container artifact validation](machine-local-container-artifact-validation-lane.md)
