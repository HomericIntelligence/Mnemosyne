---
name: sglang-moe-nsys-profile-preflight
description: "Prepare and recover a defensible Nsight Systems campaign for SGLang models on Slurm. Use when: (1) an SGLang serving image lacks Nsight tooling, (2) a checkpoint is presented through a symlink farm, (3) exact input/output and concurrency cells must be profiled, (4) a multi-rank trace needs proof that every rank was captured, or (5) partially completed preemptible model arrays must be serialized without discarding resumable raw captures."
category: debugging
date: 2026-07-29
version: "1.1.0"
user-invocable: false
verification: verified-local
tags: ["sglang", "moe", "nsight", "nsys", "slurm", "slurm-array", "h200", "deepep", "profiling", "xllm", "campaign", "recovery", "preemption", "watchdog", "cuda-graph"]
---

# SGLang MoE Nsight Systems Profile Preflight

## Overview

| Field | Value |
| --- | --- |
| Date | 2026-07-29 |
| Objective | Establish a low-cost, fail-closed path to valid multi-rank Nsight Systems captures, then run and recover a multi-model Slurm campaign without accidental cross-model concurrency or duplicate work. |
| Outcome | Exact-request, nonempty raw reports now exist. A 336-cell, five-model campaign was converted from independently submitted model arrays into sparse per-model arrays chained with `afterok`; 63 resumable raw captures were retained at conversion. The campaign remains in progress, and offline export and all-rank validation remain separate required stages. |
| Verification | verified-local: runtime flags, mount topology, exact request accounting, nonempty reports, report hashes, model-level Slurm dependencies, sparse recovery, and stage-specific failure evidence were inspected locally. Fourteen campaign contract tests pass. The complete campaign, full report validation, and extended-watchdog retry remain unverified. |

## When to Use

- A serving image contains SGLang but no `nsys` or `ncu` executable.
- The target checkpoint directory mostly consists of absolute symlinks to large weight shards.
- A profile must measure an exact prompt length and generation length rather than a best-effort textual request.
- Tensor-parallel or expert-parallel children may escape a profiler attached only to the parent process.
- A low-priority Slurm allocation is scarce and an eight-GPU request must not be spent on an unvalidated mount or profiler setup.
- Multiple per-model arrays must run one model at a time rather than merely one task at a time within each array.
- A partially completed campaign must preserve resumable raw captures and resubmit only missing or invalid cells.
- A Slurm wrapper failed after request completion and the raw profile must be classified separately from later benchmark, export, or packaging stages.
- A profiled request stopped at the SGLang scheduler watchdog and a timeout change needs evidence rather than speculation.

## Verified Workflow

### Quick Reference

1. Inspect runtime parser and profiler availability on both host and container.
2. Mount symlink-farm checkpoint and canonical target read-only at the same absolute paths; do not copy shards.
3. Preflight one GPU: tool injection, imports, config/tokenizer, CUDA smoke report, and `nsys stats`.
4. Capture one exact 1,024-token input plus 1,024-token output request on eight ranks.
5. Preserve a resumable raw capture only after exact response, nonempty report, and hash checks; accept the trace only after SQLite, NVTX, OS-runtime, and all-rank CUDA coverage are also present.
6. Serialize model arrays with fail-closed `afterok` dependencies; `%1` alone does not serialize separate arrays.
7. On recovery, retain resumable raw captures and resubmit only sparse missing or invalid indices.

1. **Inspect the exact runtime before requesting GPUs.** Record the serving-image version, its supported launch flags, and whether `nsys` or `ncu` exists both on the host and inside the image. Do not infer profiler availability from bundled example sources.
2. **Use the runtime's current parser contract.** For the inspected SGLang family, use `--tp-size` and `--ep-size`, not obsolete tensor-parallel aliases. Keep MoE communication and model implementation explicit, including `--moe-a2a-backend deepep`, `--deepep-mode normal`, `--model-impl sglang`, `--trust-remote-code`, bfloat16, one running request, and a context limit that covers the complete request.
3. **Enable layer correlation deliberately.** In the inspected SGLang runtime, use `--disable-cuda-graph` together with `--enable-layerwise-nvtx-marker`; CUDA graph execution otherwise prevents the intended layerwise NVTX ranges from being emitted.
4. **Do not copy a symlink-farm checkpoint through a hard-link view.** The observed filesystem rejected a dereferencing hard-link copy with a permission error even though source and destination reported the same filesystem. Instead mount both the symlink-farm directory and its canonical target directory read-only at their original absolute paths so that absolute symlinks resolve inside Enroot/Pyxis without copying weights.
5. **Stage a profiler explicitly and treat it as a one-off debugging dependency.** When the SGLang image lacks Nsight Systems, extract a versioned `opt/nvidia/nsight-systems` tree from a locally available profiler-enabled image, mount it read-only at `/opt/nvidia`, and invoke its `nsys` binary inside the serving container. Record both source-image and runtime-image checksums in the external artifact bundle. Do not represent this injection as a manifest-owned production runtime feature.
6. **Run a one-GPU preflight before the full request.** The preflight must prove the profiler binary executes inside the container, SGLang and its native model implementation import, the checkpoint configuration and tokenizer load using the final mount topology, and a minimal CUDA smoke trace produces a nonempty `.nsys-rep` that `nsys stats` can read. Bound this job with explicit low-priority partition, QoS, account, GPU count, CPU count, memory, and walltime.
7. **Only after a passing preflight, request the declared H200 allocation.** For the verified 375B-class capture, request one exclusive eight-H200 Slurm node and start the SGLang server with tensor parallelism and expert parallelism both equal to eight. Other models must keep their own declared GPU width rather than inheriting this example. Use Nsight Systems to trace CUDA, NVTX, and OS runtime events, and configure child-process tracing when the installed version supports it.
8. **Make the measured request exact.** Generate exactly 1,024 token IDs with no special tokens added using the mounted checkpoint tokenizer. Send those IDs to `/v1/completions` with `max_tokens: 1024`, `min_tokens: 1024`, `ignore_eos: true`, deterministic sampling, and one request at concurrency one. Assert the response reports 1,024 prompt tokens and 1,024 completion tokens; do not infer length from source text or elapsed time.
9. **Bracket only the measured request.** Wait for server readiness, send a short uncaptured warmup, request the server's profiling start endpoint, send the exact request, then request the profiling stop endpoint after the full decode completes. Preserve the start/stop responses and request usage externally.
10. **Validate the artifact before analysis.** Require a nonempty raw `.nsys-rep`, successful `nsys stats`, successful SQLite export, CUDA activity from all eight devices/ranks, NVTX layer ranges, and OS runtime events. If a CUDA-profiler range captures only the coordinator rank, the profile is incomplete: rerun with full process capture rather than reporting it as a multi-rank trace.

### Campaign Sequencing, Recovery, and Classification

11. **Plan capacity before submitting profile arrays.** Record each model's GPU width, workload coordinates, concurrency values, task count, and walltime. Use the model's declared allocation shape and keep Slurm as the scheduler of record.
12. **Serialize across models explicitly.** An array concurrency suffix such as `%1` limits tasks only inside that array. Submit the first model array without a dependency, then submit each later model array with `--dependency=afterok:<previous-array-job-id>`. Keep `%1` on each array when the requirement is one profile task at a time. Do not use `afterany`: a failed predecessor must stop the chain until its evidence is classified and its missing cells are recovered.
13. **Recover parallel work without destroying evidence.** If independent model arrays were submitted accidentally, allow at most the selected current model to continue and stop the other arrays. For every completed cell, require exact request usage, a nonempty report, and a durable report hash before treating it as resumable. Preserve those raw captures for offline export and coverage validation; do not call them complete profiles yet. Construct sparse array specifications from only the cancelled, missing, request-failed, or raw-capture-invalid indices, then chain those sparse arrays in model order.
14. **Classify each stage independently.** Track at least request execution, raw report finalization and hashing, profile validation/export, benchmark analysis, and packaging/publication. A later wrapper failure does not erase a raw report that already passed the resume gates, but it also does not make either the profile or the overall task successful. Record the preserved raw artifact, its current validation level, and every stage that still needs recovery.
15. **Change the SGLang watchdog only from explicit evidence.** Require the server log to name the watchdog timeout, identify the last request progress, and show a gap exceeding that configured timeout. Compare neighboring successful cells when available. Then pass the runtime's supported `--watchdog-timeout` value and rerun the exact failed cell. A configured value is not verified until the retry completes and its profile passes the same acceptance gates.
16. **Keep graph and layer-correlation campaigns distinct.** CUDA-graph-enabled timelines answer graph execution questions. Layerwise NVTX correlation requires the graph-disabled launch described above. Label every report with its graph mode; do not compare them as though they were the same capture contract.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Dereference the checkpoint into a hard-link view | Materialize resolved checkpoint files as hard links before container launch | The filesystem accepted reads but rejected creation of hard links to the resolved shards, before the container or server started | Preserve the symlink topology with matching read-only mounts; do not duplicate the checkpoint. |
| Submit the full eight-GPU job before validating the checkpoint and Nsight setup | Attempt to materialize a hard-link checkpoint view for the full job, while separately assuming the serving image or GPU host provides Nsight Systems | The attempt failed at checkpoint materialization before the container, server, or profiler started; independent runtime inspection also found no host or embedded `nsys` | Prove mount topology first, then tool injection, imports, and a smoke report on one GPU before requesting a full node. |
| Assume a parent-process capture covers all SGLang ranks | Attach a ranged capture to the server parent and infer child-rank coverage | Tensor/expert-parallel workers can be child processes, and a ranged capture can contain only the coordinator | Export and inspect rank/device coverage; child-process tracing is a hypothesis until the artifact proves it. |
| Treat a pending low-priority job as a launch failure | Interpret an unallocated one-GPU preflight as a script or image error | Slurm can leave a valid one-GPU request pending solely for scheduler priority | Distinguish `PENDING (Priority)` from script, image, checkpoint, or profiler failure; retain queue age and do not substitute a production allocation. |
| Submit five arrays with `%1` and expect one model at a time | Give every model its own throttled array with no dependency between arrays | `%1` serialized tasks within each array, but Slurm could run one task from every model array concurrently | Chain the model arrays with `afterok`; array throttling and cross-array ordering are separate controls. |
| Resubmit every task after changing the campaign topology | Replace the original arrays with complete new arrays | Valid reports would be duplicated and scarce profiler time would be wasted | Validate completed cells first, preserve passing artifacts, and resubmit sparse missing or invalid indices only. |
| Treat the Slurm terminal state as the profile verdict | Discard the raw capture because a later benchmark or packaging command failed | Exact requests, nonempty reports, and hashes can complete before a wrapper fails in an unrelated later stage | Keep a stage-specific outcome record. Preserve resumable captures, perform the pending offline profile validation, and recover the later failed stage separately. |
| Increase the watchdog preemptively | Raise the timeout whenever a profiled request runs slowly | A slow capture alone does not prove the SGLang watchdog caused termination | Require the explicit watchdog log and timing evidence, change only the supported runtime flag, and verify the exact retry. |

## Results & Parameters

### Capture Contract

| Concern | Required evidence |
| --- | --- |
| Runtime provenance | Runtime image path/digest, profiler-source image digest, SGLang version, and the redacted effective launch arguments. |
| Checkpoint topology | Config/tokenizer load in the final container mount layout; no copied weights; symlink-farm and canonical targets both read-only. |
| Request shape | Generated token-ID input, request JSON, response usage proving 1,024 input and 1,024 output tokens. |
| Timeline validity | Raw report, `nsys stats` output, SQLite export, and CUDA/NVTX/OS-runtime evidence. |
| Distributed coverage | Eight unique devices or ranks present in the trace; otherwise label the result incomplete. |

For models that do not use eight GPUs, replace the final row's count with the model's declared rank/device width. The invariant is complete expected coverage, not a universal eight-rank allocation.

### Campaign Contract

| Concern | Required evidence |
| --- | --- |
| Model ordering | First model has no dependency; every later model uses `afterok` on the immediately preceding model array. |
| Intra-model concurrency | `%1` when profiling must be serialized within the model; a higher value is a separate, explicitly justified experiment. |
| Sparse recovery | Durable mapping from array index to workload cell, resume-gate result for every preserved cell, and a resubmission list containing only missing or invalid raw captures. |
| Request identity | Model identifier, graph mode, input tokens, output tokens, requested concurrency, seed/token construction, and response usage. |
| Artifact identity | Nonempty raw report, hash, export status, expected rank/device coverage, and links from the workload cell to its artifacts. Report raw-capture and full-validation states separately. |
| Stage outcome | Separate states for request, report finalization, validation/export, analysis, and packaging/publication. |

### Stage Classifier

| Exact request completed | Nonempty report and hash | Export and expected-rank checks passed | Classification and action |
| --- | --- | --- | --- |
| Yes | Yes | Yes | Validated profile; preserve it and recover only any explicitly failed later analysis or publication stage. |
| Yes | Yes | No or pending | Resumable raw capture; preserve it, omit it from recapture, and finish offline validation before analysis claims. |
| Yes | No | Any | Invalid raw capture; diagnose finalization or hashing and rerun the exact cell. |
| No | Any | Any | Failed request; diagnose the serving/request failure and rerun the exact cell. |

### Slurm and Runtime Failure Classification

| State or evidence | Meaning | Recovery |
| --- | --- | --- |
| `PENDING (Dependency)` | The predecessor has not completed successfully | Wait for the chain; inspect the predecessor rather than changing the dependency. |
| `PENDING (Priority)` | Slurm accepted the job but has not allocated it | Preserve queue evidence and wait; this is not a launch or profiler failure. |
| `PREEMPTED` | The low-priority allocation was reclaimed | Requeue only the affected missing cell; do not discard other resumable captures. |
| Explicit scheduler watchdog log | The runtime terminated stalled request progress at its configured watchdog | Record the effective timeout and last progress, change only a supported flag, and rerun the exact cell. |
| Slurm `FAILED` after report hashing | A later wrapper stage may have failed | Inspect the stage ledger; preserve the raw capture while completing offline validation and recovering the failed downstream stage. |

### Watchdog Evidence

- One profiled 1K-input/1K-output cell at concurrency eight advanced through 112 completion tokens, then logged the SGLang scheduler's configured 300-second watchdog timeout on every tensor-parallel rank. Its raw report was not hashed and none of the eight requests met the exact completion contract, so the cell is invalid.
- Neighboring concurrency-four, concurrency-16, and concurrency-32 cells completed, making the concurrency-eight result anomalous rather than a general assertion that the workload cannot complete.
- The runtime accepts `--watchdog-timeout 3600`, and the campaign launch guard now passes that supported argument. The exact retry has not completed, so 3,600 seconds is a pending hypothesis, not a verified remedy.

### Limits

- Nsight Systems correlates CPU, CUDA, NVTX, and OS-runtime timeline activity; it does not itself establish FLOP efficiency, memory bandwidth, or speed-of-light roofline utilization. Use a separate Nsight Compute campaign for kernel counters after the Systems trace identifies candidate kernels.
- A passing one-GPU preflight does not prove model load, multi-rank startup, or request completion on eight GPUs.
- An exact token count does not make arbitrary tokens semantically representative. Record a seed and token-construction method so later runs can reproduce the workload shape.
- A resumable raw capture does not imply full profile validation, benchmark analysis, derived exports, or publication completed.
- The five-model campaign was still running at the evidence cutoff. Do not infer complete model or workload coverage from the preserved-cell count.
- The extended watchdog argument is parser- and launch-verified only; its efficacy remains unverified until the exact failed cell produces a valid report.

## Evidence

- Local inspection of a SGLang runtime confirmed native XLLM support and current tensor/expert-parallel parser flags, but found no embedded Nsight executable.
- Local inspection of the 375B-class checkpoint showed a symlink-dominated shard layout; a hard-link materialization attempt failed before container startup.
- Later exact-request runs produced nonempty Nsight Systems reports with durable hashes. Offline export and all-rank validation are still required before calling them complete profiles.
- The campaign planned 336 tasks across five models and 100 input/output/concurrency coordinates. At conversion, 63 raw captures passed the exact-response, nonempty-report, and hash resume gates and were retained rather than resubmitted.
- Two long-input requests completed their exact token shape and produced reports before a downstream benchmark wrapper failed because its temporary output root lacked required repository metadata. Those reports are preserved raw evidence; their offline profile-validation and downstream stages remain incomplete.
- The concurrency-eight watchdog event and neighboring completed cells support a targeted retry with the runtime's supported extended timeout. That retry was pending at the evidence cutoff.
- Fourteen campaign unit tests enforce per-model `%1` throttling, `afterok` chaining, exact response contracts, and propagation of `--watchdog-timeout 3600`; this does not substitute for live completion.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| Inference360 | 375B-class SGLang MoE profile investigation, 2026-07-25 | v1.0.0 evidence: local runtime/checkpoint inspection and isolated Slurm preflight staging; no complete multi-rank Nsight report yet. |
| Inference360 | Five-model SGLang Nsight Systems campaign recovery, 2026-07-29 | v1.1.0 evidence: resumable exact-request raw captures, `afterok` model serialization, sparse-array preservation, stage-specific outcome classification, and evidence-gated watchdog retry planning. Full campaign completion, offline rank validation, and the extended-watchdog retry remain pending. |
