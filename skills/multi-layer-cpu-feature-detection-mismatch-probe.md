---
name: multi-layer-cpu-feature-detection-mismatch-probe
description: "Language-agnostic 4-layer diagnostic methodology for 'SIGILL on this host but works on others' / 'wrong instruction emitted' reports. Probes (1) kernel-mediated view (`/proc/cpuinfo`, `AT_HWCAP`), (2) silicon-direct view (raw `cpuid` + `xgetbv(0)`), (3) compiler-rt view (`__builtin_cpu_supports`), (4) compiler driver-resolved target (Mojo `--print-effective-target`, `rustc --print=target-features`, `clang -march=native -E -dM`, `llc --print-supported-cpus`). When layers 1-3 agree but layer 4 disagrees, the bug is in the compiler driver's CPU detection path; when layer 1 (kernel) and layer 2 (silicon) disagree, it's hypervisor/kernel CPUID masking. Use when: (1) triaging a SIGILL-on-some-hosts crash across a fleet, (2) pre-flighting a compiled binary for a mixed CPU deployment, (3) validating that a `--target-features=-foo` override is honored, (4) confirming hypervisor CPUID masking behavior, (5) diagnosing modular/modular#6413-style cross-CPU codegen mismatches in LLVM-based toolchains."
category: debugging
date: 2026-05-12
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - cpu-feature-detection
  - cpuid
  - xgetbv
  - hwcap
  - builtin-cpu-supports
  - target-features
  - print-effective-target
  - sigill
  - hypervisor-masking
  - cross-cpu
  - codegen
  - llvm
  - mojo
  - rust
  - clang
  - modular-6413
  - diagnostic
  - language-agnostic
---

# Multi-Layer CPU Feature-Detection Mismatch Probe

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-05-12 |
| **Objective** | Provide a language-agnostic, 4-layer probe methodology to localize the source of any "SIGILL on this host" / "wrong instruction emitted on this CPU" report. The four orthogonal layers — kernel-mediated, silicon-direct, compiler-runtime, and compiler-driver-resolved — let you pinpoint **which layer's view of CPU features is wrong** without guessing. |
| **Outcome** | Verified-CI: applied to modular/modular#6413 on a GHA Azure AMD EPYC 9V74 (Zen 4) runner under Hyper-V. Layers 1-3 unanimously reported "no AVX-512"; layer 4 (Mojo `--print-effective-target`) reported `--target-cpu znver4` with 12 `+avx512*` features. The disagreement pinned the bug to the Mojo driver's static feature table (via LLVM `X86TargetParser.cpp::Processors[]`). CI runs 25778579617 + 25778580407. |
| **Verification** | verified-ci |
| **Companion skills** | `mojo-print-effective-target-codegen-diagnostic` (Mojo-specific subset of layer 4), `mojo-jit-emits-avx512-on-non-avx512-cpu` (specific bug class this probe exposed), `cross-cpu-survey-gha-only-crash` (multi-host fanout pattern when you suspect this class of bug) |

## When to Use

- Investigating "SIGILL on instruction X" reports across hosts (especially when one
  host SIGILLs and another succeeds with the same binary or same compiler)
- Pre-flight check before deploying compiled binaries to a mixed CPU fleet
- Validating that a compiler is honoring a `--target-features=-foo` override or that
  a `-mno-avx512f`-style flag actually disables codegen for that ISA
- Confirming hypervisor CPUID masking behavior (the layer 1 vs layer 2 gap)
- Diagnosing modular/modular#6413-style cross-CPU codegen mismatches in any
  LLVM-based toolchain (Mojo, Rust, clang, Zig)
- Any "rebased and now it works" CPU-detection story where you need to prove which
  layer changed

## The Four Layers

| Layer | What it queries | API |
| --- | --- | --- |
| 1. Kernel-mediated view | `/proc/cpuinfo flags` after Linux's CPUID interpretation, including hypervisor masking | shell, `getauxval(AT_HWCAP/AT_HWCAP2)` |
| 2. Silicon-direct view | raw `cpuid` instruction + `xgetbv(0)` for OS-enabled XCR0 state-component mask | inline asm or `<cpuid.h>` in C |
| 3. Compiler-rt view | `__builtin_cpu_supports("name")` (gcc/clang) — reads the CPU-features global initialized by `__builtin_cpu_init` from a vendor-specific cpuid + hwcap path | gcc/clang builtin |
| 4. Driver-resolved target | What the compiler actually decided to use for codegen — populated from `llvm::sys::getHostCPUName()` + `llvm::sys::getHostCPUFeatures()` and the static per-CPU feature table | Mojo: `--print-effective-target`; Rust: `rustc --print=target-features`; clang: `clang -march=native -E -dM - </dev/null \| grep -i avx`; LLVM: `llc --print-supported-cpus` |

**Key insight:** these four layers can disagree, and **which pair disagrees tells you
which subsystem is wrong**.

## Verified Workflow

### Quick Reference

```bash
# Layer 1: Kernel view
echo "=== Layer 1: Kernel view ==="
grep -m1 ^flags /proc/cpuinfo | tr ' ' '\n' | \
  grep -E '^(avx512[a-z0-9_]*|avx_vnni|avx|avx2|fma|f16c|sse4_[12]|vaes|sha_ni)$' | sort -u
echo "AT_HWCAP/HWCAP2 via LD_SHOW_AUXV:"
LD_SHOW_AUXV=1 /bin/true 2>&1 | grep -E '^AT_HWCAP'

# Layer 2: silicon-direct
cat > /tmp/probe.c <<'EOF'
#include <stdio.h>
#include <cpuid.h>
int main(void) {
    unsigned eax, ebx, ecx, edx;
    __cpuid_count(7, 0, eax, ebx, ecx, edx);
    printf("cpuid(7,0).ebx: AVX2=%d AVX512F=%d AVX512VL=%d AVX512BW=%d AVX512DQ=%d AVX512CD=%d\n",
           !!(ebx&(1u<<5)), !!(ebx&(1u<<16)), !!(ebx&(1u<<31)),
           !!(ebx&(1u<<30)), !!(ebx&(1u<<17)), !!(ebx&(1u<<28)));
    __cpuid_count(0xd, 0, eax, ebx, ecx, edx);
    printf("cpuid(0xd,0).eax (silicon XCR0 mask): 0x%x\n", eax);
    __cpuid_count(1, 0, eax, ebx, ecx, edx);
    if (ecx & (1u<<27)) {  // OSXSAVE
        unsigned lo, hi;
        __asm__("xgetbv" : "=a"(lo), "=d"(hi) : "c"(0));
        printf("xgetbv(0) (OS-enabled XCR0): 0x%x\n", lo);
    }
    return 0;
}
EOF
gcc -O2 -o /tmp/probe /tmp/probe.c && /tmp/probe

# Layer 3: compiler-rt
cat > /tmp/builtin.c <<'EOF'
#include <stdio.h>
int main(void) {
    __builtin_cpu_init();
    printf("avx512f=%d avx512vl=%d avx512bw=%d avx512dq=%d avx512cd=%d avx512vnni=%d\n",
           __builtin_cpu_supports("avx512f"), __builtin_cpu_supports("avx512vl"),
           __builtin_cpu_supports("avx512bw"), __builtin_cpu_supports("avx512dq"),
           __builtin_cpu_supports("avx512cd"), __builtin_cpu_supports("avx512vnni"));
    return 0;
}
EOF
gcc -O2 -o /tmp/builtin /tmp/builtin.c && /tmp/builtin

# Layer 4: driver-resolved target (language-specific)
# Mojo:
pixi run mojo build --print-effective-target some.mojo
# Rust:
rustc --print=target-features
# Clang:
echo | clang -march=native -E -dM - | grep -i avx
# LLVM:
llc --print-supported-cpus
```

### Detailed Steps

1. **Run all four layers on the same host in the same shell session.** Capture the
   output verbatim — order matters for the diff later. Save into one file per host.

2. **Repeat on every suspect host.** Include the "known-good" baseline host (where
   the binary doesn't SIGILL) so you have something to diff against. In CI, add a
   workflow step that runs all four layers and uploads the result as an artifact.

3. **Compare across layers on the same host first** (vertical analysis). Use the
   interpretation matrix below. The dominant signal is the **disagreement pattern**,
   not the absolute values.

4. **Compare across hosts on the same layer** (horizontal analysis). If layer 4
   diverges across hosts but layers 1-3 agree, the compiler driver is non-deterministic
   in its CPU naming (e.g. `znver4` vs `generic` from the same silicon). If layers 1-3
   diverge across hosts but layer 4 is the same, the issue is environmental (different
   hypervisor mask, different kernel) and you should mask the feature out at build time.

5. **Probe inside vs outside the container.** Both must be tested. The container's
   `/proc/cpuinfo` may differ from the host's if cgroups/namespaces are configured
   to filter (rare but possible). cpuid is always the silicon view regardless of
   container — running cpuid inside an unprivileged container reads the same physical
   instruction.

### Interpretation matrix

| Layer 1 (kernel) | Layer 2 (cpuid) | Layer 3 (builtin) | Layer 4 (compiler) | Diagnosis |
| --- | --- | --- | --- | --- |
| no AVX-512 | no AVX-512 | no AVX-512 | no AVX-512 | Consistent (silicon really lacks AVX-512) |
| AVX-512 | AVX-512 | AVX-512 | AVX-512 | Consistent (silicon has it, all paths agree) |
| no AVX-512 | AVX-512 (silicon) | no AVX-512 | varies | Hypervisor masking — compiler-rt correctly stops at kernel/XCR0 view |
| no AVX-512 | no AVX-512 | no AVX-512 | **AVX-512** | **Bug in compiler driver** — emitted AVX-512 codegen despite all 3 lower layers agreeing it's unavailable. Either (a) CPU-name fingerprinting overrides feature view, or (b) build-time feature snapshot ignored runtime detection. |
| AVX-512 | AVX-512 | AVX-512 | no AVX-512 | Compiler is conservative or honoring an explicit `--target-features=-avx512f` override — usually intentional |
| AVX-512 | AVX-512 | no AVX-512 | varies | gcc/clang version too old to know about the feature name; upgrade the host toolchain |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Skip layer 1 (kernel) and trust cpuid only | Assumed silicon CPUID is always authoritative | In hypervisor-masked environments, the kernel's view is the authoritative one because XCR0 state-component bits are kernel-managed; cpuid alone misses this and reports features the kernel won't let userspace use | Always include layer 1; it's the layer that captures hypervisor masking |
| Skip layer 2 (silicon cpuid) | Assumed `/proc/cpuinfo` plus `__builtin_cpu_supports` is enough | Without raw cpuid, you can't distinguish "no AVX-512 silicon" from "AVX-512 silicon with hypervisor mask". Both look the same from layers 1, 3, 4 | Always include layer 2; it's the only ground-truth view of the silicon |
| Skip layer 4 (compiler-resolved target) | Hoped runtime probes alone would localize the bug | This is the smoking-gun layer. Without it you only know the runtime view; you can't prove the compiler is wrong | Always include layer 4; it's the only layer that captures the codegen-time decision |
| Probe only on the failing host | Skipped the known-good baseline | Can't tell "feature is genuinely missing here" from "feature is masked here but not on the good host" without a diff target | Always include a known-good host in the survey |
| Probe only outside the container | Assumed container inherits host CPUID verbatim | Usually true, but namespaced `/proc/cpuinfo` or `--cpu-shares`-driven masking can differ; verifying both rules out container-as-cause | Probe inside AND outside the container if a containerized binary is the SIGILL victim |

## Results & Parameters

### Example from modular/modular#6413 investigation

All 4 layers captured on the same GHA Azure runner (AMD EPYC 9V74 Zen 4 under Hyper-V):

```text
Layer 1 (kernel /proc/cpuinfo): no avx512* flags
Layer 2 (cpuid):                 AVX512F=0 AVX512VL=0 AVX512BW=0 AVX512DQ=0 (all 0)
                                 xgetbv(0)=0x7 (no AVX-512 state enabled in XCR0)
Layer 3 (__builtin_cpu_supports): avx512f=0 (all AVX-512 features = 0)
Layer 4 (mojo --print-effective-target):
  --target-cpu znver4
  --target-features +avx512f,+avx512vl,+avx512bw,+avx512dq,+avx512cd,
                    +avx512vnni,+avx512vbmi,+avx512vbmi2,+avx512bitalg,
                    +avx512vpopcntdq,+avx512bf16,+avx512ifma (12 features)
```

**Layer 4 disagrees with 1-3 → bug in Mojo's driver.** Confirmed root cause: LLVM
`getHostCPUName()` returns `"znver4"` from family/model/stepping (which Hyper-V doesn't
mask), then `X86TargetParser.cpp::Processors[]` applies a static feature list with full
AVX-512 without intersecting against the masked CPUID feature leaves.

### Pinned versions

| Artifact | Identifier |
| --- | --- |
| Mojo version under test | `1.0.0b2.dev2026050805` |
| Container image | `projectodyssey:dev` |
| GHA runner | Azure `ubuntu-24.04`, AMD EPYC 9V74 (Zen 4) under Hyper-V |
| Companion CI runs | 25778579617, 25778580407 |

## Companion Skills

- [`mojo-print-effective-target-codegen-diagnostic`](mojo-print-effective-target-codegen-diagnostic.md)
  — Mojo-specific implementation of layer 4 of this probe
- [`mojo-jit-emits-avx512-on-non-avx512-cpu`](mojo-jit-emits-avx512-on-non-avx512-cpu.md)
  — the specific Mojo bug class this probe exposed (modular/modular#6413)
- [`cross-cpu-survey-gha-only-crash`](cross-cpu-survey-gha-only-crash.md)
  — multi-host fanout pattern that wraps this probe when you suspect this bug class

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| ProjectOdyssey | modular/modular#6413 root-cause confirmation | 4-layer probe on GHA Azure EPYC 9V74 confirmed layer 4 (Mojo) emits AVX-512 despite layers 1-3 unanimously saying no AVX-512. CI runs 25778579617 + 25778580407. |

## References

- [modular/modular#6413](https://github.com/modular/modular/issues/6413) — upstream issue
- [Intel SDM Vol 2A, cpuid instruction](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
- [LLVM `X86TargetParser.cpp`](https://github.com/llvm/llvm-project/blob/main/llvm/lib/TargetParser/X86TargetParser.cpp)
- [gcc `__builtin_cpu_supports` docs](https://gcc.gnu.org/onlinedocs/gcc/x86-Built-in-Functions.html)
