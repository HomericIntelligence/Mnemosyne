---
name: mojo-ci-runtime-crash-diagnosis-and-mitigation
description: "Use when Mojo CI crashes with VMA allocation errors, SIGSEGV in libKGENCompilerRTShared, SIGILL on selected CPUs, or exit 134 near $HOME/.modular; when auditing compiling invocations; or when deciding whether an upstream bump permits workaround removal. Classify the signature first, reproduce the correct resource/UID/ISA boundary, and use bounded retry only for a verified immovable pre-fix toolchain."
category: ci-cd
date: 2026-07-10
version: "2.0.0"
verification: verified-ci
license: BSD-3-Clause
user-invocable: false
history: mojo-ci-runtime-crash-diagnosis-and-mitigation.history
tags:
  - mojo
  - jit
  - crash
  - ci
  - vma
  - sigill
  - sigsegv
  - uid-mismatch
  - cpu-features
  - retry
---

# Mojo CI Runtime Crash Diagnosis and Mitigation

## Overview

This skill distinguishes resource exhaustion, filesystem ownership, ISA mis-detection, source-code
memory bugs, and a narrow pinned-toolchain flake. These failures can share the same generic
`execution crashed` message, so timing, stack frames, host identity, and reproducibility determine
the response.

Verification remains `verified-ci`. Project cases, measurements, and upstream links are in the
[notes](./mojo-ci-runtime-crash-diagnosis-and-mitigation.notes.md); the byte-preserved source and
prior changelog are in [history](./mojo-ci-runtime-crash-diagnosis-and-mitigation.history).

## When to Use

- `JIT session error: Cannot allocate memory` or a nondeterministic JIT SIGSEGV on a small runner.
- `filesystem error: Permission denied [.../.modular]` followed by abort/exit 134.
- SIGILL occurs on one CPU/runner while the same artifact works elsewhere.
- A workflow contains unclassified bare `mojo test`, `run`, `build`, or `package` invocations.
- An upstream compiler/runtime fix supposedly landed and downstream workarounds are being removed.
- A crash is being called “JIT flakiness” without ruling out ownership, double-free, locking, or
  lifetime errors.
- A project is pinned to a pre-fix Mojo version that cannot be obtained or upgraded and the same
  SHA passes on a sibling runner.

## Crash Classifier

| Signature | Likely class | First discriminating action | Correct direction |
| --- | --- | --- | --- |
| Allocation error or early JIT SIGSEGV near a repeatable virtual-memory threshold | VMA exhaustion | Run the same test under two `ulimit -v` values | One job with sequential Mojo steps |
| Permission error at `$HOME/.modular`, exit 134, reproducible at CI UID | UID mismatch | Run container with the exact runner UID/GID | Traversable home, writable runtime dir, UID-aware cache |
| SIGILL only on selected hosts; driver selects unsupported AVX-512 | CPU/driver mismatch | Compare kernel, raw CPUID, compiler builtin, effective target | Upgrade past fix; validate target before peeling flags |
| Runtime frames plus output-dependent or allocation-dependent behavior | Source bug | Inspect ownership, locks, pointer aliases, and inlining | Fix the source; do not retry it away |
| Fast `libKGENCompilerRTShared` crash, no test output, same SHA sibling green, immovable old pin | Bounded flake exception | Confirm signature in failed log and pin provenance | One per-file retry, then verified failed-job rerun and ledger |

## Decision Rules

1. **Classify before changing CI.** Record exact exit code, first failing frame, time-to-failure,
   runner/CPU, UID/GID, Mojo pin, same-SHA sibling outcome, and local reproduction.
2. **Treat VMA as process count, not source size.** A matrix with `max-parallel: 1` can still overlap
   job lifecycle. Only a single job with sequential steps guarantees one Mojo process at a time.
3. **Reproduce UID failures at the CI identity.** Warm caches and UID 1000 can hide a deterministic
   failure that occurs at UID 1001.
4. **Probe all four ISA layers.** `/proc/cpuinfo`, raw CPUID/XCR0, compiler runtime builtins, and the
   compiler driver answer different questions. Omitting raw CPUID cannot distinguish absent silicon
   from hypervisor masking.
5. **Verify the pinned version before workaround removal.** If the dependency predates the shipped
   fix, stop. Passing a different version proves nothing.
6. **Preserve fail-closed behavior.** A retry is not permission to ignore a failed second attempt,
   delete the job, or mark it continue-on-error.
7. **Retry only the verified exception.** Prefer an upstream bump. If the pin is truly immovable,
   retry each file once, then rerun failed jobs only after reading the signature. Maintain a dated
   known-issues entry with affected SHAs and an explicit revisit trigger.
8. **Rule out source bugs first.** Check synthesized shallow copies of pointer-owning structs,
   non-CAS locks, pointer aliases surviving source destruction, oversized `@always_inline` bodies,
   and cumulative tests in a single JIT process.
9. **Validate the real invocation log.** A reproduction workflow badge can be red because old
   coredump infrastructure failed even when the Mojo step succeeded.

## Verified Workflow

### 1. Capture and reproduce

```bash
mojo --version
id
uname -a
free -h
ulimit -a
gh run view <run-id> --log-failed
```

For a suspected VMA threshold:

```bash
ulimit -v 3500000 && pixi run mojo --Werror -I . tests/<test>.mojo
ulimit -v 4000000 && pixi run mojo --Werror -I . tests/<test>.mojo
```

A fail near 3.5 GB and pass near 4.0 GB supports the recorded ~3.6 GB per-process signature; measure
the current toolchain rather than assuming the historical value.

For a UID failure:

```bash
podman compose down -v
USER_ID=1001 GROUP_ID=1001 podman compose up -d
podman compose exec -T <service> bash -c 'id; ls -ld "$HOME" "$HOME/.modular"; mojo run <test>'
```

### 2. Apply the class-specific mitigation

#### VMA exhaustion

Replace a test matrix with one job and named sequential steps. Do not use `continue-on-error`.
Keep memory snapshots and add line-table debug information when supported so residual crashes are
symbolicated.

```yaml
test-mojo:
  runs-on: ubuntu-latest
  timeout-minutes: 120
  steps:
    - uses: actions/checkout@v4
    - name: Memory snapshot
      run: free -h && ulimit -v
    - name: Core tensors
      run: just test-group tests/shared/core 'test_tensors*.mojo'
    - name: Remaining groups
      run: just test-group tests/shared '<remaining patterns>'
```

#### UID mismatch

- Make the declared home traversable (`chmod 755`), never recursively lock runtime directories to
  mode 700 for a different runtime UID.
- Pre-create `${HOME}/.modular`; if the mounted home is not writable, redirect `HOME` and
  `PIXI_HOME` to a UID-specific writable location.
- Reclaim bind-mounted trees recursively when necessary; use non-interactive elevation only for an
  explicit allowlisted command set.
- Include the actual runner UID in container/cache keys. Use a step output such as
  `${{ steps.uid.outputs.user_id }}`, not an environment value assumed to persist from a prior step.

```yaml
- name: Get runner UID
  id: uid
  run: echo "user_id=$(id -u)" >> "$GITHUB_OUTPUT"
- uses: actions/cache@v4
  with:
    key: container-uid${{ steps.uid.outputs.user_id }}-${{ hashFiles('Dockerfile', 'pixi.lock') }}
```

#### CPU feature mismatch

Probe the same host, inside and outside the container:

```bash
grep -m1 '^flags' /proc/cpuinfo | tr ' ' '\n' | rg '^(avx512.*|avx2|avx|fma)$' | sort -u
pixi run mojo build --print-effective-target <reproducer>.mojo
```

Add a small C raw-CPUID/XCR0 probe and a `__builtin_cpu_supports` probe. If kernel, raw CPUID, and
builtin all say no AVX-512 while the driver selects it, the driver is wrong. If raw CPUID says yes
but kernel/builtin say no, investigate hypervisor/XCR0 masking rather than blaming silicon.

### 3. Validate an upstream fix before demolition

The historical protocol names gates 0, 1, 2, and 4; retain those identifiers when comparing older
evidence.

| Gate | Required evidence |
| --- | --- |
| 0 | Current pin is at or after the fix-shipped build; pin history read directly |
| 1 | Cheapest class-specific reproducer is clean; effective target matches host for ISA bugs |
| 2 | Existing reproduction workflow runs at least 10 times without signature-library frames |
| 4 | At least 8 consecutive green runs across every required check |

```bash
rg '^mojo' pixi.toml
git log --oneline -- pixi.toml | head -5
pixi run mojo build --print-effective-target /tmp/repro.mojo
gh workflow run repro-<issue>.yml --ref <bump-branch>
gh pr checks <bump-pr> --watch
```

For filesystem fixes, build once and execute with an unwritable home, nonexistent home, unset
`HOME`, and `HOME=/dev/null`. Keep the validation PR open as a canary through the first workaround
removal. Fix real standard-library API regressions introduced by the bump before demolition.

### 4. Audit all compiling workflow calls

```bash
rg -n '(^| )(?:pixi run )?mojo (test|run|build|package)' .github/workflows
```

Route test files through the repository’s group runner where available. Version and format commands
do not invoke the same JIT path. For a verified immovable-pin exception:

```bash
for test_file in tests/**/test_*.mojo; do
  echo "== $test_file =="
  if ! mojo run -I src "$test_file"; then
    echo "== bounded retry: $test_file =="
    mojo run -I src "$test_file" || exit 1
  fi
done
```

If the job still fails, inspect the log for the exact fast JIT signature and only then run:

```bash
gh run rerun <run-id> --failed
```

### 5. Inspect source-level crash causes

- A `Copyable` type owning `UnsafePointer` fields needs an explicit deep `__copyinit__`; a
  synthesized shallow copy can double-free after list reallocation.
- A spinlock requires compare-and-swap semantics; `fetch_add` plus a later branch is not a lock.
- Replace transient `_data.bitcast[T]()[i]` aliases with safe setters, or acquire
  `data_ptr[dtype]()` before loops so the source remains live.
- Large branching methods are poor `@always_inline` candidates and can multiply JIT pressure.
- If cumulative functions in one JIT session trigger heap corruption, split files conservatively,
  copy complete imports, update CI globs, and use the toolchain’s current `def main() raises:` form.

## Examples

### VMA result

Two matrix jobs each reserved roughly 3.6 GB on a roughly 7 GB runner. `max-parallel: 1` did not
eliminate lifecycle overlap; a single job with sequential named steps did.

### Pinned-toolchain exception

An old unavailable pin produced a fast JIT-library crash while a sibling run at the same SHA was
green. A per-file retry plus signature-verified failed-job rerun preserved the test gate. The retry
was paired with a known-issues ledger and a “remove after pin advances” trigger.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Failure 1 | Matrix `max-parallel: 1` | Adjacent jobs can overlap during setup/teardown | One job, sequential Mojo steps |
| Failure 2 | Raise `ulimit` inside CI | Cannot override the runner cgroup/hypervisor limit | Reduce concurrent processes |
| Failure 3 | Shrink imports for pure VMA | Compilation volume is not the per-process reservation | Reproduce the threshold first |
| Failure 4 | Blanket retry or continue-on-error | Hides reproducible bugs and removes upstream evidence | Fix/bump; use the bounded exception only when proven |
| Failure 5 | Remove a workaround before checking the pin | Tests the wrong premise | Gate 0 first |
| Failure 6 | Trust the repro badge | Old diagnostic infrastructure may be what failed | Read the Mojo step log |
| Failure 7 | Skip raw CPUID | Cannot separate missing features from virtualization masks | Probe all four layers |
| Failure 8 | Reproduce only at local UID | Warm UID-owned caches hide deterministic permission bugs | Use exact CI UID/GID |
| Failure 9 | Redirect only `MODULAR_HOME` | Native startup reads `$HOME/.modular` directly | Fix/redirect `HOME` and permissions |
| Failure 10 | Non-recursive ownership repair | Root-owned children remain inaccessible | Reclaim the required tree recursively and narrowly |
| Failure 11 | Assume every runtime frame is compiler flakiness | Memory ownership and lock bugs can be nondeterministic | Audit source invariants before retry |
| Failure 12 | Add `@always_inline` to a large branchy method | Multiplies compilation volume and can worsen crashes | Keep inlining small and measured |
| Failure 13 | Delete the failing job | Deletes real regression signal | Keep the job and preserve fail-closed exit |
## Results & Parameters

| Parameter | Recorded contract |
| --- | --- |
| Historical VMA threshold | About 3.6 GB per Mojo process; remeasure current toolchain |
| VMA concurrency | One compiling Mojo process on the affected small runner |
| Upstream Gate 2 | At least 10 reproduction-workflow runs |
| Upstream Gate 4 | At least 8 consecutive green required-check runs |
| Pinned exception | One retry per file, then signature-verified failed-job rerun |
| Retry failure | Second failure exits nonzero; never silently ignored |

## Output Contract

Report the classifier evidence, current pin, exact reproducer and exit code, chosen mitigation,
workflow calls audited, source invariants checked, focused and required-check results, and any
remaining workaround with owner and removal trigger. Never label a crash flaky from the generic
message alone.

## Companions

- [Case notes](./mojo-ci-runtime-crash-diagnosis-and-mitigation.notes.md)
- [Version history and superseded snapshot](./mojo-ci-runtime-crash-diagnosis-and-mitigation.history)
