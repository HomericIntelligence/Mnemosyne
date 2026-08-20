# Mojo CI Runtime Crash Diagnosis and Mitigation — Case Notes

These notes retain measured cases and project-specific outcomes. The full superseded main appears
only in the history companion.

## Case Index

| Case | Source | Verification |
| --- | --- | --- |
| VMA reservation and sequential-job mitigation | [modular#6433](https://github.com/modular/modular/issues/6433) | verified-ci |
| `$HOME/.modular` filesystem startup crash | [modular#6412](https://github.com/modular/modular/issues/6412) | verified-ci |
| AVX-512 target mis-emission and SIGILL | [modular#6413](https://github.com/modular/modular/issues/6413) | verified-ci |
| ProjectOdyssey workflow retry audit | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/mojo-ci-runtime-crash-diagnosis-and-mitigation.md) | verified-ci |
| ProjectOdyssey source-bug investigation | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/mojo-ci-runtime-crash-diagnosis-and-mitigation.md) | verified-ci |
| Predictive-coding immovable-pin flake | [Immutable source at batch base](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/mojo-ci-runtime-crash-diagnosis-and-mitigation.md) | verified-ci |

## VMA Case

The recorded GitHub-hosted runner had roughly 7 GB RAM while each Mojo process reached about
3.6 GB VmPeak. Two processes therefore exceeded available capacity. `max-parallel: 1` did not
guarantee machine exclusivity because separate jobs overlapped during lifecycle transitions.
ProjectOdyssey PR #5351 replaced the matrix with sequential steps and retained a hard failure gate.

These measurements belong to that Mojo/runtime generation. Re-run the two-threshold experiment
before using 3.6 GB as a current limit.

## Upstream-Fix Validation Cases

The filesystem case used a hostile-`HOME` matrix: unwritable existing directory, nonexistent path,
unset `HOME`, and `/dev/null`. The ISA case compared `--print-effective-target` against kernel,
raw-CPUID, and compiler-runtime views, then repeated the real reproducer. At least ten reproduction
workflow dispatches and eight consecutive required-check runs were used before workaround removal.

Gate 4 exposed a real standard-library API change that accompanied a nightly bump. This is why a
green micro-reproducer is not sufficient evidence for a dependency upgrade.

## CPU Root Cause

On the recorded Azure AMD EPYC host, family/model resolution selected `znver4`, then a static
processor feature list supplied AVX-512 without intersecting the hypervisor-masked CPUID leaves.
The kernel, raw/direct probe interpretation, compiler runtime, and Mojo driver disagreed; the driver
emitted instructions unavailable to the guest and caused SIGILL. The upstream issue records the
fix; downstream target pins became removal candidates only after the gate sequence passed.

## UID Case

The deterministic signature was a C++ filesystem exception while checking `$HOME/.modular`, then
`std::terminate`, abort, and exit 134. The durable remediation combined a traversable declared home,
a writable or redirected runtime home, recursive ownership repair for bind-mounted descendants,
non-interactive narrow elevation, and a runner-UID cache key. Merely setting `MODULAR_HOME` did not
affect the native startup read.

## Source-Bug Case

Sixteen initially “flaky” ProjectOdyssey test files reduced to three source bugs:

- shallow synthesized copying of raw-pointer ownership caused double-free;
- a `fetch_add`-based spinlock did not provide compare-and-swap exclusion;
- a bitcast pointer alias outlived the tensor under ASAP destruction.

Large `@always_inline` additions worsened JIT pressure. A separate threshold case split test files to
no more than ten functions per JIT process, copied complete imports to each part, changed deprecated
`fn main()` to `def main()`, and updated CI globs.

## Immovable-Pin Exception

On Mojo `1.0.0b1`, about ten hosted runs produced three rescued fast JIT-library crashes. One runner
crashed twice consecutively while a twin same-SHA run passed. The retained policy therefore layers
one retry per test file with a signature-verified failed-job rerun. It does not treat rerun success as
an upstream fix: a ledger records dates, SHAs, and the trigger to revisit when the pin advances.

## Compaction Disposition

- Kept in main: classifier, VMA/UID/ISA/source decision rules, upstream gates, bounded retry
  exception, copy-ready probes, hard parameters, and failed approaches.
- Moved here: measurements, project PR narratives, and deep root-cause cases.
- Archived only: repeated workflow fixtures, long transcripts, and the complete prior main.
