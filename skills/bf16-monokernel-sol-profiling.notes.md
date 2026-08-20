# BF16 Monokernel SOL Profiling Notes

Supporting evidence for
[`bf16-monokernel-sol-profiling.md`](bf16-monokernel-sol-profiling.md).

## Case Index

| Case | Source | Verification | Material result |
| --- | --- | --- | --- |
| Weighted-RMSNorm workload and roofline matrix | [Immutable source snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1ae0cb498e5250c341c2a4bf585f97e2a28060af/skills/bf16-monokernel-sol-profiling.md) for the CUDA monokernel benchmark, 2026-07-30 | verified-local | Full rootless host suite, H200 correctness/Compute Sanitizer, 14-case Nsys matrix |
| Five-position minimax campaign | [Immutable source snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1ae0cb498e5250c341c2a4bf585f97e2a28060af/skills/bf16-monokernel-sol-profiling.md) for the BF16 full-decoder campaign | verified-local | Immutable screen/confirmation and trigger-based reconsideration |
| Shared-lane rebaseline | [Immutable source snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1ae0cb498e5250c341c2a4bf585f97e2a28060af/skills/bf16-monokernel-sol-profiling.md) for the full-decoder campaign | verified-local | Candidate compared only with adjacent champion under one lane |
| Compiler-materialized composition | [Immutable source snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1ae0cb498e5250c341c2a4bf585f97e2a28060af/skills/bf16-monokernel-sol-profiling.md) for the full-decoder campaign | verified-local | Distinct runnable binary timed regardless of static resource direction |
| Reachability and binary deduplication | [Immutable source snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1ae0cb498e5250c341c2a4bf585f97e2a28060af/skills/bf16-monokernel-sol-profiling.md) for the full-decoder campaign | verified-local | Unreachable/byte-identical candidates marked invalid, not performance-rejected |
| Numerical topology and GPU isolation | [Immutable source snapshot](https://github.com/HomericIntelligence/Mnemosyne/blob/1ae0cb498e5250c341c2a4bf585f97e2a28060af/skills/bf16-monokernel-sol-profiling.md) for the full-decoder campaign | verified-local | Trusted-reference cache checks; overlapping-process timings invalidated |

## Reusable Parameter Record

The canonical harness kept these parameters explicit per run: model/normalization semantics,
rows/columns and learned parameter count, required sequence positions, warmup and sample counts,
grid/block geometry, compiler flags, image and dependency-lock digests, source revision and included
header hashes, H200 UUID, scheduler job, lock identity, tool versions, and result-root digest.

The source evidence used the ideal weighted-RMSNorm convention `F = 4N` and `B = 6N`. This is an
algorithmic lower bound, not the implementation's measured traffic. Runtime SOL, NCU counter SOL,
and Nsys kernel attribution stayed separate. NCU counter evidence remained unavailable where host
policy produced `ERR_NVGPUCTRPERM`; no zero was substituted.

## Detailed Verification

The rootless benchmark verified image bytes before launch, ran an independent host oracle,
exhaustively compared outputs, passed Compute Sanitizer, and recomputed artifact hashes. Nsys was
used for the 14-case duration/launch matrix; profiler timing was not substituted for uninstrumented
p50.

The full-decoder campaign fixed five required positions and promoted by the worst-position result.
Later attempts recorded evolving-champion replay, source/binary identity, static resource metrics,
matched screens, and longer confirmation. Source-equivalent control changes, scalarization effects,
shared/register liveness, address-space composition, and active-dispatch reachability all produced
cases where source intuition or aggregate counts were insufficient.

Project references retained from the source:

- [Radiance RMSNorm estimator](https://github.com/LLM360/Radiance/blob/add857a1ee42bfd907e956783213cd4e173844a0/radiance/metrics/ops/rms_norm.py)
- [Radiance H200 hardware profile](https://github.com/LLM360/Radiance/blob/add857a1ee42bfd907e956783213cd4e173844a0/fixtures/hardware_profiles/builtin_profile_evidence.json)
- `sglang-moe-nsys-profile-preflight.md`
- `machine-local-container-artifact-validation-lane.md`

## Provenance

- Superseded main SHA-256:
  `ee2dae76415650e0cd96ed95ee76dd8e0278d77c8153b1f5bd2b730f5075daa7`
- Issue #3335 base: `1ae0cb498e5250c341c2a4bf585f97e2a28060af`
- Old/new version: `1.25.0` → `2.0.0`
