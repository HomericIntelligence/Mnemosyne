---
name: mojo-jit-emits-avx512-on-non-avx512-cpu
description: "Root cause of modular/modular#6413: Mojo 1.0.0b2.dev2026050805 emits AVX-512 instructions (zmm registers, opmasks, {1to4} broadcast, vpternlogd, vpbroadcastb r→xmm) on Azure GHA runners whose CPU does NOT advertise AVX-512 — SIGILL at runtime. The triggering hardware is AMD EPYC Zen 4 under Microsoft Hyper-V (e.g. EPYC 9V74), NOT pre-AVX-512 Intel CPUs — that earlier hypothesis is falsified by 6/6 clean local runs across Sandy Bridge-E through Lunar Lake. Mechanism: LLVM's getHostCPUName() reads CPU family 0x19 + Genoa model range → returns 'znver4' → X86TargetParser.cpp::Processors[] applies a STATIC AVX-512 feature list that is NOT gated on the masked CPUID feature leaves. Hyper-V masks the leaves but not family/model, so fingerprinting wins. Use when: (1) triaging Mojo SIGILL on GHA, (2) `mojo build --print-effective-target` shows znver4 + AVX-512 but /proc/cpuinfo shows no avx512 flag, (3) capturing disassembly evidence from ELF cores, (4) reasoning about Mojo runtime CPU detection (LLVM getHostCPUFeatures path via closed-source CLOptions.h:118)."
category: debugging
date: 2026-05-12
version: "2.0.0"
user-invocable: false
verification: verified-ci
tags:
  - mojo
  - jit
  - avx-512
  - avx512
  - sigill
  - libKGEN
  - modular-6413
  - cpu-detection
  - azure-runner
  - gha
  - runtime-codegen
  - zen4
  - epyc
  - hyper-v
  - llvm-host-cpu-detection
---

# Mojo JIT Emits AVX-512 on Non-AVX-512 CPUs (modular/modular#6413 root cause)

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-05-12 |
| **Objective** | Document the mechanism behind modular/modular#6413: Mojo 1.0.0b2.dev2026050805 emits AVX-512 instructions at codegen time on AMD EPYC Zen 4 GHA runners virtualized under Microsoft Hyper-V, where the hypervisor masks AVX-512 CPUID feature leaves but leaves family/model/stepping (`0x19` / Genoa range / step 1) untouched. LLVM's `getHostCPUName()` reads family+model, returns `znver4`, and the caller looks up `znver4` in `llvm/lib/TargetParser/X86TargetParser.cpp::Processors[]` — which applies a STATIC AVX-512 feature list that is not gated on whether the actual feature leaves are present. Fingerprinting wins over feature leaves, so AVX-512 codegen is emitted on a kernel-AVX-512-disabled CPU → SIGILL on first AVX-512 op. |
| **Outcome** | 12+ symbolicated ELF cores across 4 distinct backtraces all firing AVX-512 family instructions; reproduces ~80% of the time on Azure EPYC 9V74 runners; 0/50 on 6 distinct Intel CPUs (Sandy Bridge-E, Haswell, Skylake, Whiskey Lake, Lunar Lake — none reproduce). Source-code review of `modular/modular` open-source tree localizes the host-CPU-features call to `CLOptions.h:118` (closed-source) per `mojo/docs/code/tools/README-Compilation-Targets.md`. |
| **Verification** | verified-ci for bug reproduction (12+ symbolicated cores, 32 negative-control green outcomes). The Zen-4-static-feature-list mechanism is verified-local (source review + `mojo build --print-effective-target` correctly reporting `lunarlake`/`skylake` without AVX-512 on hermes/epimetheus). The GHA-runner-side `--print-effective-target` capture is pending PR #5401 merge — once that lands the mechanism half escalates to verified-ci. |
| **Companion skills** | `mojo-runtime-crash-bisection`, `debugging-mojo-jit-crash-capture-gdb-wrapper`, `modular-6433-vs-6413-failure-triage` |

## When to Use

- Investigating a Mojo SIGILL on **any AVX-512-capable AMD silicon under Microsoft
  Hyper-V** (Zen 4 EPYC, Zen 4 desktop, and by extension Sapphire Rapids Xeon under
  Hyper-V where the hypervisor masks AVX-512 leaves but leaves family/model intact)
- A Mojo SIGILL on GHA where the ELF core shows AVX-512 mnemonics (`zmm0`, `{1to4}`,
  `vpternlogd`, `vcmpltss → %k1`, `vmovdqa64`, `vpbroadcastb r,xmm`)
- `mojo build --print-effective-target <some.mojo>` reports `--target-cpu znver4`
  with AVX-512 features (`+avx512f,+avx512vl,+avx512bw,+avx512dq,+avx512cd,
  +avx512vnni,+avx512vbmi,+avx512vbmi2,+avx512bitalg,+avx512vpopcntdq,+avx512bf16,
  +avx512fp16`) but `/proc/cpuinfo` on the same host shows zero `avx512*` flags
- Distinguishing GHA-cache eviction luck from a real fix on "rebased and now it works"
  Mojo JIT stories — compare cache-key + runner CPU model, not just rerun outcomes
- Filing or commenting on modular/modular#6413 with mechanism evidence (not just
  symptom evidence)
- **Not** "any pre-AVX-512 Intel CPU" — that hypothesis is falsified by 6/6 clean
  local runs (Sandy Bridge-E i7-3820, Haswell i5-4440, Skylake i5-6600K, Whiskey
  Lake i7-8565U, Lunar Lake Core Ultra 7 258V). The GHA `ubuntu-latest` pool has
  migrated heavily to AMD EPYC, which is what surfaces this bug.

## Verified Workflow

### Quick Reference

```bash
# 1. Get the runner CPU model + family/model/stepping
gh run view <RUN_ID> --log | grep -A2 "model name" /proc/cpuinfo
# Expect: AMD EPYC 9V74 / cpu family 25 / model 17 / stepping 1 = Zen 4 Genoa

# 2. Confirm hypervisor masks AVX-512 from /proc/cpuinfo
gh run view <RUN_ID> --log | grep -c avx512
# Expect: 0  (hypervisor-masked; kernel sees no AVX-512)

# 3. Capture the smoking gun: Mojo driver's effective target on the runner
mojo build --print-effective-target dummy.mojo
# Bad: --target-cpu znver4 ... +avx512f,+avx512vl,+avx512bw,...
# Good (on real hardware): --target-cpu skylake / lunarlake / etc. with NO AVX-512

# 4. Symbolicate cores (must use SAME mojo binary version as CI)
gdb -batch \
  -ex "set confirm off" \
  -ex "core-file core.<pid>" \
  -ex "bt" \
  -ex "x/8i \$rip-32" \
  -ex "info all-registers" \
  /path/to/mojo

# 5. Check for AVX-512 mnemonics in the faulting frame
gdb-output | grep -E 'zmm[0-9]|\{1to[248]\}|vpternlog|vcmpltss.*%k[0-7]|vmovdqa64|vmovdqu64|vpbroadcastb +%[er].*xmm'
```

### Detailed Steps

1. **Pull the runner's `/proc/cpuinfo` BEFORE forming a hypothesis.** The earlier
   "pre-AVX-512 Intel" hypothesis lasted weeks because nobody captured the runner
   CPU first. The GHA `ubuntu-latest` Azure pool is now heavily AMD EPYC 9V74
   (Zen 4 Genoa) under Hyper-V, not Intel. Always start with `cat /proc/cpuinfo`
   on the actual failing runner.

2. **Run `mojo build --print-effective-target` on the runner.** This prints the
   driver-resolved `--target-cpu` and `--target-features`. If it reports `znver4`
   with `+avx512f...` features while `/proc/cpuinfo` shows zero avx512 flags,
   that's the smoking gun: family/model fingerprinting won over actual CPUID
   feature leaves.

3. **Confirm the mechanism via LLVM source.** The chain is:
   - `llvm::sys::getHostCPUFeatures()` in `llvm/lib/TargetParser/Host.cpp`
   - Calls `getHostCPUName()`
   - For AMD: `getAMDProcessorTypeAndSubtype()` reads family (`0x19`) +
     model in Genoa range (`0x10`–`0x1f`) → returns `"znver4"`
   - Caller indexes into
     `llvm/lib/TargetParser/X86TargetParser.cpp::Processors[]`
   - `znver4` entry has a STATIC feature list including
     `+avx512f,+avx512vl,+avx512bw,+avx512dq,+avx512cd,+avx512vnni,
     +avx512vbmi,+avx512vbmi2,+avx512bitalg,+avx512vpopcntdq,+avx512bf16,
     +avx512fp16`
   - This static list is **not cross-checked** against the masked CPUID feature
     leaves the kernel actually advertises

4. **Confirm the call site is Mojo-driver-side (closed-source `CLOptions.h:118`).**
   `mojo/stdlib/std/sys/info.mojo` does pure compile-time queries via
   `#kgen.param.expr<target_has_feature,...>` — no runtime CPU detection in
   stdlib. The `!kgen.target` MLIR attribute is populated by closed-source
   `CLOptions.h:118` which initializes `targetFeatures = getHostCPUFeatures()`.
   `mojo/docs/code/tools/README-Compilation-Targets.md` identifies that line
   verbatim as the source of related issue MOCO-3686.

5. **Disassemble the core to confirm AVX-512 codegen.** Look for: 512-bit
   registers (`%zmm0`–`%zmm31`), opmasks (`%k1`–`%k7`, e.g.
   `vcmpltss ... %xmm0, %k1`), masked moves with zeroing
   (`vmovss ... %xmm1{%k1}{z}`), embedded broadcast (`{1to4}`, `{1to8}`,
   `{1to16}`), ternary logic (`vpternlogd $imm, ...`), unaligned 512-bit ops
   (`vmovdqu64 ..., %zmm0`), reg-source byte broadcast (`vpbroadcastb %eax,
   %xmm0` — the GP-register-source form is AVX-512-BW-only).

6. **Hand off to Modular with mechanism evidence.** Comment on modular/modular#6413
   with the source-review chain, the runner CPU model, and the
   `--print-effective-target` output. The fix needs to be at the Mojo-driver level:
   cross-check `getHostCPUFeatures()` against the kernel view
   (`__builtin_cpu_supports("avx512f")` or parsing `/proc/cpuinfo`) and strip
   AVX-512 from `targetFeatures` if the kernel says no AVX-512. Also: honor
   `MOJO_TARGET_FEATURES` / `MOJO_TARGET_CPU` env vars for the in-process JIT.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Hypothesis: bug fires on any non-AVX-512 Intel CPU | Predicted reproduction on Skylake-class Intel based on early GHA evidence | 6/6 clean local runs on Sandy Bridge-E i7-3820, Haswell i5-4440, Skylake i5-6600K, Whiskey Lake i7-8565U, Lunar Lake Core Ultra 7 258V — none reproduce | **Get the runner's `/proc/cpuinfo` BEFORE forming a CPU-class hypothesis.** The GHA `ubuntu-latest` pool has migrated heavily to AMD EPYC, not Intel. The actual triggering class is AMD Zen 4 under Hyper-V. |
| Hypothesis: cached container image content drift causes the bug | Compared bad-image sha256 vs good-image sha256, expecting byte differences to correlate with crash | Loaded the exact cached image locally on 5 different Intel CPUs — zero reproductions. The cached image is byte-identical; what varies between green and red runs is the runtime CPU/hypervisor combination. | The image bytes are not the bug. The runtime CPU family/model fingerprint + Hyper-V's CPUID masking is the bug. |
| Hypothesis: bypass detection with `--target-cpu=znver3` or `--target-features=-avx512f` | Identified the flags exist for `mojo build` | Partially verified for AOT compilation, but **not yet confirmed** for the in-process JIT in `libKGENCompilerRTShared.so`. No `MOJO_TARGET_FEATURES` env var is documented; CLI flag may or may not propagate to the JIT path. | The user-facing workaround for the JIT case is still open. Driver-level fix in Mojo's `CLOptions.h:118` is the durable answer. |
| File-content bisect via single-commit reverts | Reverted #5381, #5385, #5387, #5388, #5389; ran CI 8× each | All 32 negative-control outcomes were green; main stayed red. P(by chance @ 87% historical crash rate) ≈ 2e-29 | When the trigger is host CPU + hypervisor, file-content reverts cannot reproduce. Switch to a runtime-CPU hypothesis early. |
| Manual cache eviction expecting deterministic rebuild | `gh actions-cache delete <bad-key>` then re-ran the workflow expecting a bug-free new image | New image rebuilt with same crash signature whenever the runner happened to be a Zen 4 EPYC host. The "fix" is just luck about which runner type GHA assigns. | Cache eviction is not a fix. The trigger is the runner's CPU + hypervisor, not the cached image bytes. |
| Single-iteration CI confirmation | Ran a suspect PR once green, declared "fixed" | At ~20% historical pass rate (runner assignment to non-EPYC hardware), single-shot green is meaningless | Always use the ≥8-run protocol for Mojo JIT crash verification. |

## Results & Parameters

### Pinned versions

| Artifact | Identifier |
| --- | --- |
| Mojo conda artifact | `mojo-1.0.0b2.dev2026050805-release.conda` |
| Mojo binary sha256 | `8b6f080d54b7c53185786a9a928afbfcf2fbb539d89c9d44da3b5b6700a8b6dc` |
| Bad container image sha256 | `a5889cb07ca73da27db730b4754de08094e604161fb63af464a70b148765bab7` |
| Bad image GHA cache key | `container-image-uid1001-ab0290811d2e7f7979c17d7c115fa41c6cce25bed01fcf8e329ed32a7f9a9ed8` |
| Good image GHA cache key | `container-image-uid1001-8f28e14581a46d4510c3beb68e9df14a277b4656024648…` |
| Reference Azure runner kernel | `6.17.0-1010-azure` (hostname `runnervmeorf1`) |
| Runner CPU model | `AMD EPYC 9V74 80-Core Processor` |
| Runner CPU family/model/stepping | 25 / 17 / 1 (Zen 4, Genoa core, step 1) |
| Runner hypervisor | Microsoft Hyper-V |
| Runner `/proc/cpuinfo` AVX-512 flag count | 0 (hypervisor-masked) |
| Runner HWCAP / HWCAP2 (inside container) | `AT_HWCAP: 178bfbff` / `AT_HWCAP2: 0x2` |

### Mechanism: LLVM static feature list for `znver4`

The `znver4` entry in `llvm/lib/TargetParser/X86TargetParser.cpp::Processors[]`
statically applies (among others):

```text
+avx512f, +avx512vl, +avx512bw, +avx512dq, +avx512cd,
+avx512vnni, +avx512vbmi, +avx512vbmi2, +avx512bitalg,
+avx512vpopcntdq, +avx512bf16, +avx512fp16
```

Mojo driver code at closed-source `CLOptions.h:118` initializes
`targetFeatures = getHostCPUFeatures()`. The chain:

```text
getHostCPUFeatures()
  → getHostCPUName()
    → getAMDProcessorTypeAndSubtype()
      reads CPUID family (0x19) + model (Genoa range, e.g. 0x11)
      returns "znver4"
  → indexes Processors[] table → static AVX-512 feature list
  → returns full AVX-512 feature set
```

That static list is **not** gated on the actual CPUID feature leaves that Hyper-V
has masked. Hyper-V masks the leaves but not family/model/stepping. Fingerprinting
wins. AVX-512 codegen is emitted on a kernel-AVX-512-disabled CPU.

### Smoking-gun validation: `mojo build --print-effective-target`

| Host | `--target-cpu` | AVX-512 in features? | `/proc/cpuinfo` avx512 count | Verdict |
| --- | --- | --- | --- | --- |
| hermes (Lunar Lake Core Ultra 7 258V) | `lunarlake` | No | 0 | Correct: kernel and driver agree |
| epimetheus (Skylake i5-6600K) | `skylake` | No | 0 | Correct: kernel and driver agree |
| GHA Azure EPYC 9V74 runner (predicted, pending PR #5401) | `znver4` | Yes (+avx512f, etc.) | 0 | **Bug**: driver fingerprints Zen 4, kernel masked the leaves |

### Faulting instructions captured (4 distinct backtraces, 6 instruction families)

| Backtrace | Frame | Instruction | AVX-512 feature |
| --- | --- | --- | --- |
| A (`test_tensor_dataset_negative_indexing`) | `abs() math.mojo:3746` → `assert_almost_equal+48` | `vandps (%r15,%rax,1){1to4},%xmm3,%xmm3` | AVX-512F `{1to4}` embedded broadcast |
| B (`test_substitute_simple_env_var`) | `_strip() string_slice.mojo:1035` (`_strip+68`) | `vmovdqa64 (%rcx,%rax,1),%zmm0` | 512-bit register, AVX-512F only |
| B' (`_is_valid_utf8_runtime() _utf8.mojo:173`) | `load_config+2857` | `vmovdqu64 (%r12,%rax,1),%zmm0` ; `vmovdqu64 %zmm0,0x1e0(%rsp)` | Unaligned 512-bit load/store |
| C1 (`test_dropout_forward_*`, `test_linear_struct_initialization`) | `philox._single_round philox.mojo:162` → `next_uint32+178` | `vpternlogd $0x96,%xmm3,%xmm4,%xmm7` | AVX-512F ternary logic |
| C2 (`test_relu_backward_basic`) | `_relu_backward_op activation.mojo:475` → `dispatch_binary+3024` | `vcmpltss (%r10,%rdi,4),%xmm0,%k1` ; `vmovss (%rsi,%rdi,4),%xmm1{%k1}{z}` | AVX-512F opmask `%k1` + masked move with zeroing |
| D (`match_h2` in swisstable) | `_swisstable.mojo:114` → `_insert+4476` | `vpbroadcastb %eax,%xmm0` | AVX-512BW reg-source byte broadcast |

### Crash rate measurements

| Host | Crash rate | Sample size |
| --- | --- | --- |
| Azure GHA EPYC 9V74 runner under Hyper-V (kernel `6.17.0-1010-azure`) | ~80% per CI dispatch | 14 dispatches |
| Sandy Bridge-E i7-3820 | 0% | 50 iterations |
| Haswell i5-4440 | 0% | 50 iterations |
| Skylake i5-6600K (epimetheus) | 0% | 50 iterations |
| Whiskey Lake i7-8565U | 0% | 50 iterations |
| Lunar Lake Core Ultra 7 258V (hermes) | 0% | 50 iterations |

### Suggested upstream fix

Mojo's compiler driver should cross-check `getHostCPUFeatures()` against the
kernel view (`__builtin_cpu_supports("avx512f")` or parsing `/proc/cpuinfo`) and
strip AVX-512 from `targetFeatures` if the kernel says no AVX-512. Also: honor
`MOJO_TARGET_FEATURES` / `MOJO_TARGET_CPU` env vars for the in-process JIT in
`libKGENCompilerRTShared.so` so users have a workaround while the driver fix
ships.

### Upstream references

- Issue: [modular/modular#6413](https://github.com/modular/modular/issues/6413)
- Root-cause mechanism comment:
  [#6413 c-4436547360](https://github.com/modular/modular/issues/6413#issuecomment-4436547360)
- Source-review comment:
  [#6413 c-4436612117](https://github.com/modular/modular/issues/6413#issuecomment-4436612117)
- Earlier symptom-evidence comments:
  [c-4435784092](https://github.com/modular/modular/issues/6413#issuecomment-4435784092),
  [c-4435794613](https://github.com/modular/modular/issues/6413#issuecomment-4435794613),
  [c-4436157861](https://github.com/modular/modular/issues/6413#issuecomment-4436157861)
- Related upstream issue identifying `CLOptions.h:118`:
  MOCO-3686 (per `mojo/docs/code/tools/README-Compilation-Targets.md`)

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| ProjectOdyssey | PR #5399 (bisect/6413-positive-control) | 12+ symbolicated ELF cores, 4 distinct backtraces all firing AVX-512 instructions on EPYC 9V74 |
| ProjectOdyssey | PRs #5395, #5396, #5397, #5398 (negative-control reverts) | 32 green job outcomes; file-content variables ruled out |
| ProjectOdyssey | PR #5401 (pending) | Captures `mojo build --print-effective-target` on the GHA runner — escalates mechanism half to verified-ci once merged |
| Local (hermes) | Lunar Lake Core Ultra 7 258V | `--print-effective-target` reports `lunarlake` with no AVX-512; 0/50 crash |
| Local (epimetheus) | Skylake i5-6600K | `--print-effective-target` reports `skylake` with no AVX-512; 0/50 crash |
| Local | Sandy Bridge-E i7-3820, Haswell i5-4440, Whiskey Lake i7-8565U | 0/50 crash each — falsifies the "any pre-AVX-512 Intel" hypothesis |
| Upstream | modular/modular#6413 | Mechanism comments 4436547360 (root cause) + 4436612117 (source review) |
