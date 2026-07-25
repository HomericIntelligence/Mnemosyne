---
name: sglang-moe-nsys-profile-preflight
description: "Prepare a defensible Nsight Systems profile for a large SGLang MoE model on Slurm. Use when: (1) an SGLang serving image lacks Nsight tooling, (2) a checkpoint is presented through a symlink farm, (3) an exact input/output token shape must be profiled, or (4) a multi-rank trace needs proof that every rank was captured."
category: debugging
date: 2026-07-25
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: ["sglang", "moe", "nsight", "nsys", "slurm", "h200", "deepep", "profiling", "xllm"]
---

# SGLang MoE Nsight Systems Profile Preflight

## Overview

| Field | Value |
| --- | --- |
| Date | 2026-07-25 |
| Objective | Establish a low-cost, fail-closed path to a valid multi-rank Nsight Systems capture for a large SGLang MoE request. |
| Outcome | The runtime and checkpoint topology were inspected and a one-GPU profiler/mount preflight was staged before requesting an eight-GPU capture. The complete end-to-end trace remains unverified until the scheduler allocates the preflight and the resulting artifact passes rank-coverage checks. |
| Verification | verified-local: launch contract, parser flags, checkpoint topology, tool availability, and request-shape controls were inspected locally. No completed multi-rank profile is claimed. |

## When to Use

- A serving image contains SGLang but no `nsys` or `ncu` executable.
- The target checkpoint directory mostly consists of absolute symlinks to large weight shards.
- A profile must measure an exact prompt length and generation length rather than a best-effort textual request.
- Tensor-parallel or expert-parallel children may escape a profiler attached only to the parent process.
- A low-priority Slurm allocation is scarce and an eight-GPU request must not be spent on an unvalidated mount or profiler setup.

## Verified Workflow

### Quick Reference

1. Inspect runtime parser and profiler availability on both host and container.
2. Mount symlink-farm checkpoint and canonical target read-only at the same absolute paths; do not copy shards.
3. Preflight one GPU: tool injection, imports, config/tokenizer, CUDA smoke report, and `nsys stats`.
4. Capture one exact 1,024-token input plus 1,024-token output request on eight ranks.
5. Accept the trace only when report, SQLite, NVTX, OS-runtime, and all-rank CUDA coverage are present.

1. **Inspect the exact runtime before requesting GPUs.** Record the serving-image version, its supported launch flags, and whether `nsys` or `ncu` exists both on the host and inside the image. Do not infer profiler availability from bundled example sources.
2. **Use the runtime's current parser contract.** For the inspected SGLang family, use `--tp-size` and `--ep-size`, not obsolete tensor-parallel aliases. Keep MoE communication and model implementation explicit, including `--moe-a2a-backend deepep`, `--deepep-mode normal`, `--model-impl sglang`, `--trust-remote-code`, bfloat16, one running request, and a context limit that covers the complete request.
3. **Enable layer correlation deliberately.** In the inspected SGLang runtime, use `--disable-cuda-graph` together with `--enable-layerwise-nvtx-marker`; CUDA graph execution otherwise prevents the intended layerwise NVTX ranges from being emitted.
4. **Do not copy a symlink-farm checkpoint through a hard-link view.** The observed filesystem rejected a dereferencing hard-link copy with a permission error even though source and destination reported the same filesystem. Instead mount both the symlink-farm directory and its canonical target directory read-only at their original absolute paths so that absolute symlinks resolve inside Enroot/Pyxis without copying weights.
5. **Stage a profiler explicitly and treat it as a one-off debugging dependency.** When the SGLang image lacks Nsight Systems, extract a versioned `opt/nvidia/nsight-systems` tree from a locally available profiler-enabled image, mount it read-only at `/opt/nvidia`, and invoke its `nsys` binary inside the serving container. Record both source-image and runtime-image checksums in the external artifact bundle. Do not represent this injection as a manifest-owned production runtime feature.
6. **Run a one-GPU preflight before the full request.** The preflight must prove the profiler binary executes inside the container, SGLang and its native model implementation import, the checkpoint configuration and tokenizer load using the final mount topology, and a minimal CUDA smoke trace produces a nonempty `.nsys-rep` that `nsys stats` can read. Bound this job with explicit low-priority partition, QoS, account, GPU count, CPU count, memory, and walltime.
7. **Only after a passing preflight, request one exclusive eight-H200 Slurm node.** Start the SGLang server with tensor parallelism and expert parallelism both equal to eight. Use Nsight Systems to trace CUDA, NVTX, and OS runtime events, and configure child-process tracing when the installed version supports it.
8. **Make the measured request exact.** Generate exactly 1,024 token IDs with no special tokens added using the mounted checkpoint tokenizer. Send those IDs to `/v1/completions` with `max_tokens: 1024`, `min_tokens: 1024`, `ignore_eos: true`, deterministic sampling, and one request at concurrency one. Assert the response reports 1,024 prompt tokens and 1,024 completion tokens; do not infer length from source text or elapsed time.
9. **Bracket only the measured request.** Wait for server readiness, send a short uncaptured warmup, request the server's profiling start endpoint, send the exact request, then request the profiling stop endpoint after the full decode completes. Preserve the start/stop responses and request usage externally.
10. **Validate the artifact before analysis.** Require a nonempty raw `.nsys-rep`, successful `nsys stats`, successful SQLite export, CUDA activity from all eight devices/ranks, NVTX layer ranges, and OS runtime events. If a CUDA-profiler range captures only the coordinator rank, the profile is incomplete: rerun with full process capture rather than reporting it as a multi-rank trace.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Dereference the checkpoint into a hard-link view | Materialize resolved checkpoint files as hard links before container launch | The filesystem accepted reads but rejected creation of hard links to the resolved shards, before the container or server started | Preserve the symlink topology with matching read-only mounts; do not duplicate the checkpoint. |
| Submit the full eight-GPU job before validating the checkpoint and Nsight setup | Attempt to materialize a hard-link checkpoint view for the full job, while separately assuming the serving image or GPU host provides Nsight Systems | The attempt failed at checkpoint materialization before the container, server, or profiler started; independent runtime inspection also found no host or embedded `nsys` | Prove mount topology first, then tool injection, imports, and a smoke report on one GPU before requesting a full node. |
| Assume a parent-process capture covers all SGLang ranks | Attach a ranged capture to the server parent and infer child-rank coverage | Tensor/expert-parallel workers can be child processes, and a ranged capture can contain only the coordinator | Export and inspect rank/device coverage; child-process tracing is a hypothesis until the artifact proves it. |
| Treat a pending low-priority job as a launch failure | Interpret an unallocated one-GPU preflight as a script or image error | Slurm can leave a valid one-GPU request pending solely for scheduler priority | Distinguish `PENDING (Priority)` from script, image, checkpoint, or profiler failure; retain queue age and do not substitute a production allocation. |

## Results & Parameters

### Capture Contract

| Concern | Required evidence |
| --- | --- |
| Runtime provenance | Runtime image path/digest, profiler-source image digest, SGLang version, and the redacted effective launch arguments. |
| Checkpoint topology | Config/tokenizer load in the final container mount layout; no copied weights; symlink-farm and canonical targets both read-only. |
| Request shape | Generated token-ID input, request JSON, response usage proving 1,024 input and 1,024 output tokens. |
| Timeline validity | Raw report, `nsys stats` output, SQLite export, and CUDA/NVTX/OS-runtime evidence. |
| Distributed coverage | Eight unique devices or ranks present in the trace; otherwise label the result incomplete. |

### Limits

- Nsight Systems correlates CPU, CUDA, NVTX, and OS-runtime timeline activity; it does not itself establish FLOP efficiency, memory bandwidth, or speed-of-light roofline utilization. Use a separate Nsight Compute campaign for kernel counters after the Systems trace identifies candidate kernels.
- A passing one-GPU preflight does not prove model load, multi-rank startup, or request completion on eight GPUs.
- An exact token count does not make arbitrary tokens semantically representative. Record a seed and token-construction method so later runs can reproduce the workload shape.

## Evidence

- Local inspection of a SGLang runtime confirmed native XLLM support and current tensor/expert-parallel parser flags, but found no embedded Nsight executable.
- Local inspection of the 375B-class checkpoint showed a symlink-dominated shard layout; a hard-link materialization attempt failed before container startup.
- The external preflight was constructed to verify profiler injection, image imports, checkpoint topology, and a minimal Nsight report before any full-node request.
- At capture-planning time, the submitted low-priority preflight remained pending for scheduler priority only. This is not evidence of a completed profile and must be revalidated before reuse.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| Inference360 | 375B-class SGLang MoE profile investigation, 2026-07-25 | Local runtime/checkpoint inspection and isolated Slurm preflight staging; no complete multi-rank Nsight report yet. |
