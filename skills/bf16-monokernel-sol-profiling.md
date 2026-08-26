---
name: bf16-monokernel-sol-profiling
description: "Build and optimize a reproducible BF16 CUDA monokernel benchmark. Use when workload normalization may duplicate cases, semantic outputs and intermediate-state parity need separate acceptance policies, a cooperative launch needs phase attribution without external counters, GPU profiling needs provenance and isolation, tiny grids underfill the GPU, multi-position acceptance needs a minimax rule, or compiler/resource changes disagree with composed-kernel correctness and latency."
category: optimization
date: 2026-08-09
version: "2.1.0"
license: BSD-3-Clause
user-invocable: false
verification: verified-local
history: bf16-monokernel-sol-profiling.history
tags: [cuda, bf16, rmsnorm, monokernel, nvidia-h200, roofline, sol, minimax,
  optimization-campaign, composition, compiler, sass, occupancy, registers, ncu, nsys,
  provenance, gpu-isolation, semantic-validation, greedy-decoding, phase-attribution]
---

# Reproducible BF16 CUDA Monokernel SOL Profiling and Optimization

## Overview

Separate five questions that are often conflated: is the workload canonical, what observable output
must agree, which intermediate states are diagnostic, is the measurement reproducible, and did the
fully composed kernel improve every required operating point? Static resources and profiler counters
explain results; a predeclared host-owned semantic gate and matched latency adjudicate a distinct
runnable implementation. Keep stricter parity checks visible even when they are not the promotion gate.

Detailed campaign cases and artifact locations are indexed in
[`bf16-monokernel-sol-profiling.notes.md`](bf16-monokernel-sol-profiling.notes.md).
The complete prior source is in
[`bf16-monokernel-sol-profiling.history`](bf16-monokernel-sol-profiling.history).

## When to Use

- Model-derived normalization cases may duplicate learned parameter counts.
- Rootless GPU profiling needs immutable image, source, device, tool, and result provenance.
- Nsight Compute reports `ERR_NVGPUCTRPERM`, or Nsys and NCU appear to disagree.
- One cooperative launch contains many globally synchronized phases, but external tooling cannot
  attribute enough time to rank the next optimization target.
- A one-row/tiny-grid kernel has low global speed-of-light despite low latency.
- Several sequence positions must pass one promotion decision.
- Greedy-token output agrees while hidden or cache tensors differ numerically.
- A tolerance-based comparison is being described as bit-exact or one-ULP agreement.
- A rejected mechanism is reconsidered after champion, bottleneck, resource, or lane changes.
- Source-active changes compile away, select an unreachable helper, or duplicate a prior binary.
- Fewer instructions/registers, partial unrolling, index narrowing, or shared-state movement makes
  the composed kernel slower.
- Timing may be contaminated by another process or a different lock namespace on the same GPU.

## Verified Workflow

### 1. Canonicalize the workload

Derive normalization parameters from semantics, not model labels: RMSNorm width `H` has `H` learned
parameters; affine LayerNorm has `2H`; bias-free LayerNorm has `H`. Select one executable case per
total parameter count and retain equal-count model names as provenance aliases. Do not claim
LayerNorm semantics for a parameter-equivalent RMSNorm workload.

Keep baseline and optimized CUDA paths separate. The host harness owns deterministic BF16 inputs,
non-unit weights, exhaustive output comparison, nonfinite/error statistics, a small independent
oracle, timing, and failure policy. Device code returns CUDA errors rather than embedding assertions.

### 2. Freeze environment and artifact provenance

Pin and hash the dependency lock, rootless image, source tree, CUDA/header inputs that affect device
code, device identity, tool versions, and every retained benchmark/profiler artifact. Verify the
image digest before runtime creation. Bind each formal candidate to an immutable Git revision and
unique result root; raw results outside Git still need scheduler ID and SHA-256.

Record permanent RED, GREEN, and outcome evidence. A prototype does not consume a formal iteration
unless promoted into the ledger. Checkpoint reusable learning on a predeclared cadence; the verified
campaign used every five formal attempts.

### 3. Separate timing, tracing, and roofline views

Measure verified, uninstrumented p50 first with fixed warmup and samples. Capture a separate Nsys
trace for kernel duration and launch attribution. Collect NCU counters only when policy allows.
Never use profiler-instrumented host timing as the latency result.

When external profiling cannot separate phases inside one cooperative launch, build a distinct
compile-time diagnostic artifact. At existing grid-wide synchronization boundaries, let one fixed
leader thread sample `clock64()`, accumulate deltas by stable phase identifier, and emit one
machine-parseable summary after the final boundary. Do not add synchronization, public parameters,
runtime branches, or fallback paths merely for measurement. Validate the diagnostic artifact, use
only its phase ordering and approximate shares to choose the next experiment, then restore the
uninstrumented production source before correctness and latency adjudication. Instrumentation can
change registers, stack, scheduling, and total latency, so its resource report and host timing are
diagnostic artifacts, never production performance evidence.

For `N = rows * columns` weighted RMSNorm elements, use the declared ideal model:

```text
F = 4N FLOPs
B = 6N bytes
T_SOL = max(F / peak_compute, B / peak_memory)
runtime_SOL = min(T_SOL / verified_p50, 1) * 100
```

Report three distinct fields:

1. Algorithmic/runtime SOL from uninstrumented p50.
2. NCU counter SOL as `max(DRAM%, SM%)`, only when counters were collected.
3. Nsys kernel duration, launch gap, and separately calculated kernel-only lower-bound SOL.

On `ERR_NVGPUCTRPERM`, report counter SOL unavailable with the reason. Do not bypass host policy or
substitute zero. Include `min(grid_blocks / SM_count, 1)`; a one-CTA workload cannot saturate all
SMs, so prioritize launch reduction/legal fusion for single-invocation latency rather than changing
the workload through extra concurrency.

### 4. Declare the semantic contract, then use immutable minimax acceptance

Before optimization, define the observable output, numerical comparator, and semantic horizon. A
valid greedy-inference contract can require all decision logits to be finite, logits to satisfy a
declared absolute/relative, bitwise, or ULP bound, and the selected token to match exactly at every
required step. Test the full continuation horizon when subsequent generated tokens matter; agreement
for one next token proves only that one-step contract.

Match each claim to its comparator. Zero tolerance violations do not prove bit identity or a one-bit
bound. A bit-exact claim needs a bitwise comparison; a ULP claim needs a defined ULP computation,
including signed zero, NaN, and infinity handling. Any nonfinite decision logit fails the semantic gate.

Classify hidden states and caches separately. They may remain diagnostic for a one-step output contract,
but become authoritative when the API exposes them or when later decoding consumes them beyond the
tested horizon. Never delete, weaken, or relabel a strict parity validator to manufacture a pass;
report both the semantic result and the stricter diagnostic result.

Treat approximate device math as an explicit mechanism, not an informal compiler flag. Put it behind
a compile-time target policy so unaffected targets retain the precise operation and the hot path gains
no runtime length branch or fallback. Qualify the changed symbol independently at its nominal workload,
at the largest supported context, and with the minimum legal grid. Require the declared semantic gate
at every point and retain all stricter diagnostics. A fast intrinsic is neither safe nor fast by name;
only the forced-symbol boundary checks and matched uninstrumented timing establish those properties.

Define the required position set before optimization. Screen the exact candidate at every position
with identical image, fixtures, grid, warmup, and iterations. Promote only if the minimum
required-position SOL improves, the predeclared semantic gate passes, and no other authoritative
output regresses. Confirm a screen winner with a longer run before replacing the champion; prototype,
diagnostic-parity failure, or isolated-position gains are not substitutes for the formal revision.

When execution moves to another node or a shared non-exclusive lane, rebaseline the champion there.
Serialize on one pinned physical GPU, keep baseline and candidate adjacent, record GPU UUID/index,
co-tenant/process snapshot, node, and lock identity, and repeat noisy winners.

### 5. Prove physical GPU isolation

Every launcher—benchmark, profiler, and helper—must share one canonical lock keyed by physical GPU
UUID. Hold it through the run. After acquisition and immediately before timing, query the physical
device and require zero active compute processes. Per-tool or per-stream lock roots do not isolate
one GPU.

Check scheduler/process history before adjudication. Proven overlap invalidates latency even if
correctness passed and the local launcher held a lock. Preserve contaminated artifacts as invalid,
wait for all overlapping steps to terminate, and rerun in a new result root.

### 6. Bind source intent to the linked hot path

Before GPU timing, prove the mechanism is present in source, reachable through the selected dispatch,
and materialized in linked device code. Record call-path/compiler evidence, device-code hash,
registers, stack, spills/local instructions, shared memory, residency, occupancy, and legal launch
ceiling.

If the changed helper is unreachable and the linked SASS is byte-identical to the parent, mark the
candidate invalid/inapplicable and skip correctness/timing. Deduplicate against the whole campaign:
a new source tuple that equals a previously measured subset binary has no new implementation to
adjudicate. This identity shortcut never applies to distinct runnable binaries, even if aggregate
resource counts match.

Dispatch substitution is only a reachability control because it changes topology as well as the
mechanism. For the real candidate, retain accepted dispatch and implement equivalent lowering in
every active path where the geometry is legal.

### 7. Diagnose the composed kernel without static rejection gates

Build the exact full composition. Resource metrics are diagnostic and cannot reject a runnable
candidate: more registers/spills/instructions can win by removing tails or synchronization, while
fewer can lose by reducing memory-level parallelism or lengthening dependencies.

Audit these interactions explicitly:

- Moving online state to shared memory retains pointers, address arithmetic, predicates, and
  temporaries; live ranges can increase register allocation.
- Fusing K/V loads can serialize independent issue; staging scores can delay the reduction
  recurrence; hoisting a 64-bit base can keep it live across the loop.
- Source-equivalent predicates, scopes, or unrolling can change scheduling despite identical totals.
- Partial unrolling or narrower indices can retain dynamic arrays and create stack-backed local
  traffic; inspect linked local load/store sites and stack size.
- Address-space intrinsics require proof that the materialized pointer has the intended storage;
  successful compilation does not establish this.
- Whole-binary counts include cold alternatives; inspect the benchmark-selected path.
- BF16 pair conversion mixes transport, lane ownership, score dependencies, and value lifetime;
  preserve transport/ownership and screen key-only and value-only controls separately.

Numerical validation is bound to reduction topology. Higher precision, two-pass softmax, and
vectorized reductions can round differently. Compare every produced cache element at required
context boundaries to the same trusted reference and retain those results as diagnostic evidence.
Whether a disagreement blocks promotion is determined only by the predeclared semantic contract and
horizon; neither candidate may silently replace the oracle after a disagreement.

### 8. Reconsider and compose mechanisms conditionally

Every rejection records mechanism, parent champion, controlling position, failure, resource state,
and an objective recheck trigger. Audit triggers after each accepted champion. Replay a queue
sequentially against the evolving champion; an accepted replay changes the parent for the next.

A historical threshold may prioritize experiments but never relax correctness or promotion. Recover
exact deltas, classify them as additive, mutually replacing, or no-op, and measure the fully composed
binary; percentages are not additive. Focused source contracts run before GPU qualification.

When several losing tuples share one mutually exclusive replacement, measure the smallest control
that preserves the champion's other mechanisms. Compare each candidate with both:

- the accepted champion, which alone decides promotion; and
- the shared-replacement control, which diagnoses compiled-away, partial-rescue, or harmful
  interaction.

Key every interaction label to its exact parent/source/binary. A partial rescue that remains slower
than the champion is still rejected and is not a globally beneficial mechanism.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Treat model names as unique cases | Treat model names as unique cases | Duplicate parameter workloads | Canonicalize by learned parameter count |
| Use profiled host timing | Use profiled host timing | Instrumentation distorts latency | Benchmark first; trace separately |
| Report zero when NCU is forbidden | Report zero when NCU is forbidden | Converts missing data into a measurement | Report unavailable and use Nsys attribution |
| Optimize global SOL for one CTA | Optimize global SOL for one CTA | Confuses underfill with kernel inefficiency | Report CTA/SM coverage and target launch latency |
| Promote an isolated/prototype win | Promote an isolated/prototype win | Misses controlling positions/composition | Immutable minimax screen plus confirmation |
| Reject by register/SASS count | Reject by register/SASS count | Static totals do not predict dependencies | Time every distinct runnable binary |
| Add individual speedups | Add individual speedups | Compiler interactions are non-additive | Build and measure the full composition |
| Modify an unreachable helper | Modify an unreachable helper | Candidate compiles to parent binary | Prove dispatch and linked identity first |
| Treat dispatch substitution as isolation | Treat dispatch substitution as isolation | Changes topology and mechanism together | Use only as a control; transplant to active paths |
| Trust separate launcher locks | Trust separate launcher locks | Co-tenancy contaminates one physical GPU | One UUID-keyed lock and in-lock process audit |
| Equate zero tolerance failures with bit identity | Reused a threshold comparator to claim one-bit agreement | The comparator never measured bit or ULP distance | State only the property the comparator proves |
| Make strict parity the only semantic gate | Rejected matching finite logits and exact greedy output solely for diagnostic hidden/cache drift | Intermediate parity exceeded the declared one-step output contract | Preserve the diagnostic failure, but adjudicate with the declared semantic horizon |
| Validate only the first greedy token | Treated one matching token as proof of continuation correctness | Divergent cache state can affect later decoding | Check every token in the required continuation horizon |
| Treat phase-clock instrumentation as production timing | Used an instrumented cooperative kernel's latency or resources as the promotion result | Clock reads, counters, and reporting perturb the compiled kernel | Use phase ordering only; restore and time an uninstrumented immutable candidate |
| Apply approximate math through a runtime length check | Specialized one target by branching in the shared hot path | Added dispatch cost and left other target symbols unqualified | Use a compile-time policy and force the changed symbol at nominal, extreme-context, and minimum-grid cases |

## Results & Parameters

Formal attempt record:

```text
candidate revision + included source hashes
parent champion and exact linked-device-code hash
image/lock/source/result artifact SHA-256 values
node, physical GPU UUID, scheduler job, lane/process audit
required positions, warmup, screen samples, confirmation samples
host correctness/nonfinite/max-error statistics
declared observable outputs, numerical comparator, and continuation horizon
semantic-gate result plus separate hidden/cache diagnostic-parity result
approximate-math policy, unaffected precise targets, forced-symbol contexts, and minimum-grid result
p50 and algorithmic SOL per position; minimax result
Nsys kernel duration/launch gap; NCU SOL or unavailable reason
diagnostic revision, compile-time selector, phase boundaries, raw cycle deltas, and phase ordering
registers, stack, spills/local ops, shared memory, residency/occupancy
outcome: accepted | rejected | invalid duplicate | invalid execution
reconsideration trigger and learning checkpoint disposition
```

Canonical H200 numeric results and campaign-specific paths belong in the notes companion, not in
this reusable decision procedure.

## Verified On

- Verified-local rootless image, host suites, H200 correctness, Compute Sanitizer, RMSNorm/Nsys,
  and multi-position campaign evidence through 2026-08-09.
- Verified-local BF16 prefill evidence through 2026-08-24 separated finite-logit and exact-greedy
  acceptance from sparse hidden/cache diagnostic divergence without weakening the strict comparator.
- Verified-local cooperative BF16 decode evidence through 2026-08-25 used macro-gated leader-clock
  sampling at existing grid barriers to redirect optimization toward the measured dominant phase,
  then restored the production source before candidate qualification.
- Verified-local BF16 decode evidence through 2026-08-26 qualified a target-policy fast intrinsic at
  nominal and extreme contexts plus the minimum legal grid, retained stricter parity, and confirmed a
  matched uninstrumented latency improvement without changing unaffected target policies.
- Compaction for issue #3335 preserved the verification boundary and did not claim NCU counters
  where host policy denied them.
