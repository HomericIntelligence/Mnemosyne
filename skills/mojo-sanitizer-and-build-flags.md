---
name: mojo-sanitizer-and-build-flags
description: "Canonical patterns for Mojo sanitizer integration and build-flag matrices: ASAN/TSAN scope, tcmalloc/sanitizer incompatibility, sanitizer-only build flavors, build-flag matrix design, compiler-flag conflicts that break Mojo compilation. Use when: (1) enabling a sanitizer for Mojo CI, (2) diagnosing a tcmalloc/sanitizer crash, (3) designing a multi-flag CI matrix for Mojo builds, (4) reconciling conflicting compiler flags that surface only on Mojo."
category: ci-cd
date: 2026-05-18
version: "1.0.0"
user-invocable: false
verification: verified-local
history: mojo-sanitizer-and-build-flags.history
tags: [merged, mojo, sanitizer, asan, tsan, build-flags, tcmalloc]
---

# Mojo Sanitizer and Build Flags

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-18 |
| **Objective** | Consolidate canonical patterns for Mojo sanitizer integration, build-flag matrices, GLIBC environment constraints, and package-level re-export workflows |
| **Outcome** | Verified: ASAN works end-to-end; TSAN aborts at startup due to tcmalloc incompatibility (Modular-side issue); build-flag matrix with sanitizer short-circuit prevents OOM; package/re-export patterns verified in ProjectOdyssey PRs |
| **Scope** | 8 absorbed skills: sanitizer support matrix, sanitizer build scope, memory safety, package building, GLIBC awareness, `__init__.mojo` export activation, package-level re-exports, and re-export import tests |

## When to Use

1. Enabling `--sanitize=address` or `--sanitize=thread` for a Mojo CI pipeline
2. A sanitizer build sweep OOM-kills partway through on a memory-constrained host (≤16 GiB RAM)
3. TSAN binaries abort at startup with `FATAL: ThreadSanitizer: unexpected memory mapping`
4. Deciding which sanitizer flags are actually accepted by the Mojo 1.0.0b2 compiler
5. Building `.mojopkg` artifacts and designing a debug/release/asan/tsan build-mode matrix
6. Mojo fails with `GLIBC_2.32` not-found errors on an older host or pre-commit failures
7. Activating commented-out exports in `__init__.mojo` after underlying modules are ready
8. Adding convenience `from shared import X` top-level re-exports and verifying with import tests
9. Reviewing code for Mojo ownership/borrow safety or debugging memory / segfault issues

## Verified Workflow

### Quick Reference

```bash
# Build a sanitizer-aware Mojo package (Phase A only for ASAN/TSAN)
pixi run mojo package --max-notes 0 -I "$REPO_ROOT" shared -o ".build/$MODE/shared.mojopkg"

# ASAN: only sanitizer that produces a runnable binary in Mojo 1.0.0b2
pixi run mojo build --sanitize=address -g -I "$(pwd)" -I . -o /tmp/repro <file.mojo>
ASAN_OPTIONS=halt_on_error=0:abort_on_error=0:detect_leaks=1:symbolize=1 /tmp/repro

# TSAN: compile succeeds with -j1; every binary aborts at startup (tcmalloc issue)
pixi run mojo build --sanitize=thread -g1 -j1 -I "$(pwd)" -I . -o /tmp/repro <file.mojo>

# MSAN / UBSAN: compiler rejects these flags entirely in 1.0.0b2
pixi run mojo build --sanitize=memory    ...   # → invalid sanitizer 'memory'
pixi run mojo build --sanitize=undefined ...   # → invalid sanitizer 'undefined'

# GLIBC workaround: skip mojo-format on old hosts, CI enforces it
SKIP=mojo-format git commit -m "message"

# Find actual struct/fn names before activating __init__.mojo imports
grep -rn "^struct\|^fn\|^trait" shared/core/layers/ | grep -v "__"

# Import from leaf module directly (NOT via intermediate __init__.mojo)
# from shared.autograd.optimizers import AdaGrad   ← correct
# from shared.autograd import AdaGrad              ← fails (re-export chain)
```

### 1. Sanitizer Support Matrix (Mojo 1.0.0b2)

| Flag | Compiler accepts? | Links? | Runs? | Notes |
| ---- | ----------------- | ------ | ----- | ----- |
| `--sanitize=address` | YES | YES | YES | Instruments user code; does NOT instrument pre-built `libKGEN*`/`libAsync*`/`libMSupport*` |
| `--sanitize=thread` | YES | NO | — | Linker error: `duplicate symbol: DW.ref.__gcc_personality_v0` — filed as `modular/modular#6512` |
| `--sanitize=memory` | NO | — | — | Compiler rejects: `invalid sanitizer 'memory', expected one of: 'address' or 'thread'` |
| `--sanitize=undefined` | NO | — | — | Compiler rejects: `invalid sanitizer 'undefined', expected one of: 'address' or 'thread'` |

**Decision rule:** If user code looks ASAN-clean but the `libKGEN` crash persists, the bug is in Mojo runtime itself. Stop modifying user code; escalate upstream with the dynsym fingerprint.

### 2. Sanitizer Build Scope — Two-Phase Pattern

Scope sanitizer builds to the shared-library package only (Phase A); defer per-binary instrumentation to test time (Phase B). This prevents OOM on memory-constrained hosts.

```just
# justfile recipe — verified in ProjectOdyssey PR #5389
[private]
_build-inner mode="debug":
    #!/usr/bin/env bash
    set -euo pipefail
    MODE="{{mode}}"
    STRICT="--max-notes 0"
    JOBS=""

    case "$MODE" in
        debug)   FLAGS="-g $STRICT" ;;
        release) FLAGS="-O3 $STRICT" ;;
        asan)    FLAGS="-g1 --sanitize address $STRICT" ;;
        tsan)    FLAGS="-g1 --sanitize thread  $STRICT" ; JOBS="-j1" ;;
        *) echo "unknown mode: $MODE" >&2; exit 2 ;;
    esac

    # Phase A: package the shared library (ALWAYS — sanitizer or not)
    pixi run mojo package $STRICT -I "$REPO_ROOT" shared \
        -o ".build/$MODE/shared.mojopkg"

    # Phase B: sanitizer modes STOP here (prevents OOM from 46 parallel AOT builds)
    if [ "$MODE" = "asan" ] || [ "$MODE" = "tsan" ]; then
        echo "Sanitizer build complete (shared package only)"
        echo "  Run sanitized tests: just test-mojo-${MODE}"
        exit 0
    fi

    # debug / release modes continue with per-binary AOT compile here
```

Companion test recipe:

```just
test-mojo-asan:
    @for t in tests/**/test_*.mojo; do \
        pixi run mojo build -g1 --sanitize address -I shared -o "$$t.bin" "$$t" && \
        ASAN_OPTIONS=halt_on_error=0:abort_on_error=0:detect_leaks=1 "$$t.bin"; \
    done

test-mojo-tsan:
    # Recipe is correct; every binary aborts at startup with tcmalloc/TSAN error
    # (Modular-side fix required — not user code)
```

### 3. TSAN Runtime: tcmalloc Shadow-Memory Abort

Every TSAN-built Mojo binary currently aborts at startup before reaching `main()`:

```text
FATAL: ThreadSanitizer: unexpected memory mapping 0x<addr>-0x<addr>
<pid> external/tcmalloc+/tcmalloc/internal/system_allocator.h:585]
  MmapAligned() failed - unable to allocate with tag
<pid> external/tcmalloc+/tcmalloc/arena.cc:59] CHECK in Alloc: FATAL ERROR:
  Out of memory trying to allocate internal tcmalloc data
Aborted (core dumped)
```

**Root cause:** tcmalloc requests 48-bit address regions. Under ThreadSanitizer, those regions overlap TSAN's shadow-memory map; tcmalloc has no fallback and aborts. Fix must come from Modular: rebuild tcmalloc with `TCMALLOC_ADDRESS_BITS` matching the runtime VA, or link sanitizer builds against libc malloc instead of tcmalloc.

Note: `-j1` is **required** for the TSAN compile to succeed (workaround for `modular/modular#6413` parallel-JIT crash), but it does not fix the runtime abort.

### 4. GLIBC Constraint Workflow

Mojo requires GLIBC 2.32+ but older Linux hosts (e.g., Debian 10) only provide GLIBC 2.28.

```bash
ldd --version          # Check host GLIBC
/path/to/.pixi/envs/default/bin/mojo --version  # Will fail on old hosts

# Symptom: /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.32' not found
# Fix: skip mojo-format hook; CI (Docker Ubuntu 22.04+ with GLIBC 2.35) enforces it
SKIP=mojo-format git commit -m "message"

# Verify all other hooks pass (they don't require Mojo)
pixi run pre-commit run --files <changed-files>
```

Only `mojo-format` (and `check-list-constructor` if it calls mojo) require Mojo. All other hooks (markdownlint, ruff, trailing-whitespace, YAML) run fine on old-GLIBC hosts.

### 5. Mojo Package Build Workflow

```bash
# Build single package
mojo package src/tensor -o packages/tensor.mojopkg

# Build and test
./scripts/build_package.sh tensor --test

# Build all packages
./scripts/build_all_packages.sh
```

Every package needs `__init__.mojo`. Packages compile to `.mojopkg` binary format with no circular dependencies.

| Error | Cause | Solution |
| ----- | ----- | -------- |
| `Missing __init__.mojo` | No package entry point | Add `__init__.mojo` to package dir |
| `Circular dependency` | Modules depend on each other | Refactor to break cycle |
| `Export not found` | Missing from `__all__` | Add name to `__all__` list |

### 6. Activating Commented-Out `__init__.mojo` Exports

In Mojo v0.26.1, re-export chains do not work. Top-level `__init__.mojo` must import from leaf modules directly.

```bash
# 1. Verify which struct/fn names actually exist
grep -rn "^struct\|^fn\|^trait" shared/core/layers/ | grep -v "__"

# 2. Check if a specific struct exists
grep -rn "^struct Conv2D\b" shared/
```

```mojo
# WORKS — absolute leaf-module path
from shared.core.layers.linear import Linear

# FAILS in v0.26.1 — chained re-export
from shared.core import Linear

# comptime alias bridges documented API name to actual struct name
comptime Conv2D = Conv2dLayer
```

Keep commented entries for not-yet-implemented symbols so future contributors know they're still pending.

### 7. Package-Level Re-exports and Top-Level API

When adding new symbols (e.g., optimizers, data transforms) to the top-level package:

```bash
# 1. Find defining module (NOT the intermediate __init__.mojo)
grep -rn "^struct AdaGrad" shared/

# 2. Audit active imports (not commented blocks — they may point to stale paths)
grep -n "^from" shared/__init__.mojo
grep -n "# from" shared/__init__.mojo  # WARNING: may reference wrong submodule
```

```mojo
# Use absolute module path, import ALL symbols from a group in one line
from shared.autograd.optimizers import SGD, Adam, AdamW, AdaGrad, RMSprop

# Expose plan-canonical names without breaking existing callers
alias Accuracy = AccuracyMetric
```

### 8. Package Import Tests

Test both package-level and direct-submodule import paths:

```mojo
fn test_adagrad_top_level_import() raises:
    from shared import AdaGrad
    var opt = AdaGrad(learning_rate=0.01)
    assert_almost_equal(opt.get_lr(), 0.01, tolerance=1e-10)
    print("AdaGrad top-level import test passed")

fn test_adagrad_direct_import() raises:
    from shared.autograd.optimizers import AdaGrad
    var opt = AdaGrad(learning_rate=0.01)
    print("AdaGrad direct import test passed")
```

Always update both `test_imports.mojo` AND `test_imports_part1.mojo` (≤10 `fn test_` functions per file).

### 9. Mojo Memory Safety Ownership Patterns

```mojo
# Owned parameter - takes ownership
fn consume(var data: Tensor):
    process(data)  # data moved here

# Borrowed parameter - read-only reference
fn read_only(data: Tensor):
    let value = data[0]  # OK: read-only

# Mutable reference - in-place modification
fn modify(mut data: Tensor):
    data[0] = 42  # Mutate in caller's variable
```

Key rules:
- Use `^` operator **only** when transferring ownership
- `mut self` for mutating methods (NOT `out self`)
- `out self` ONLY for constructors (`__init__`)
- List/Dict/String are non-copyable — must use `^` when returning

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| -------- | -------------- | ------------- | -------------- |
| Full `--sanitize=address` AOT of all examples/benchmarks | Compiled all 46 example/benchmark binaries under `--sanitize address` in `just build asan` | Each `mojo build --sanitize=address` peaks at 3-6 GB; container OOM-killed after ~4 binaries on 15 GiB RAM host; resulting binaries were never run | Scope sanitizer mode to shared-library package only; do per-binary instrumentation at test time (one process at a time) |
| Raise `ODYSSEY_MEM_LIMIT` above physical RAM | Set `ODYSSEY_MEM_LIMIT=24g` hoping cgroups would allow swap use | cgroups caps at physical RAM regardless; setting limit > RAM just delays the OOM kill | Reduce demand (Phase B short-circuit) rather than growing the memory ceiling |
| `-j1` to "fix" TSAN runtime abort | Added `JOBS="-j1"` for TSAN mode | `-j1` fixed the JIT crash on TSAN compiles but every binary still aborts at startup with tcmalloc/ThreadSanitizer shadow-memory error | Keep `-j1` (required for TSAN compile); understand it does NOT fix the runtime abort |
| `podman compose restart` to free memory | Restarted dev container between sanitizer builds | cgroups memory counters not reset; restart also lost workspace bind mount | Memory pressure bounded by recipe (Phase A only), not container lifecycle tricks |
| Dispatch TSAN sanitizer agent | Sub-agent ran `mojo build --sanitize=thread -g -o /tmp/repro` | Linker error: `duplicate symbol: DW.ref.__gcc_personality_v0` between `libMSupport.so` and `libtsan.a` | TSAN is broken in Mojo 1.0.0b2 (`modular/modular#6512`); do not include in escalation playbooks |
| Run `--sanitize=memory` | `pixi run mojo build --sanitize=memory ...` | Compiler rejected: `invalid sanitizer 'memory', expected one of: 'address' or 'thread'` | MSAN is not implemented in Mojo 1.0.0b2 |
| Conclude "Mojo runtime fine" from clean ASAN | After ASAN reported 0 errors on user code, considered closing investigation | ASAN does not instrument pre-built `libKGEN*`/`libAsync*`/`libMSupport*` shared libs | Clean ASAN + persistent `libKGEN` crash = bug is in Mojo runtime; escalate upstream |
| Import via intermediate `__init__.mojo` | `from shared.core import Linear` in `shared/__init__.mojo` | Mojo v0.26.1 re-export chain limitation: chained re-exports do not propagate | Always use absolute leaf-module paths in top-level `__init__.mojo` |
| Activating `SGD`/`Adam` from wrong path | Extended `# from .training.optimizers import SGD, Adam, AdamW` | That line points to `training.optimizers` — the symbols actually live in `shared.autograd.optimizers` | Always grep for the canonical struct before extending a commented block |
| Running `mojo test` locally on old-GLIBC host | `pixi run mojo test tests/...` | GLIBC_2.32/33/34 not found | Mojo pixi env requires newer GLIBC; rely on CI Docker for compilation verification |
| Using `Float32` in test instantiation | `var normalizer = Normalize(Float32(0.5), Float32(0.5))` | `Normalize.__init__` takes `Float64` — compile error | Always grep the leaf module `__init__` signature before writing test code |
| Modifying `__init__.mojo` from scratch | Tried to add re-exports anew | Export was already present (added in prior work with `# Issue #NNNN` comment) | Always check `__init__.mojo` first — the re-export is often done; only tests are missing |
| Using `just` command runner | `just build` or `just --list` | `just` not in PATH on this host | Use `pixi run <cmd>` directly; fall back to CI for compilation |

## Results & Parameters

### Sanitizer Escalation Matrix (Updated for Mojo 1.0.0b2)

| Sanitizer | Status | Use it? | Notes |
| --------- | ------ | ------- | ----- |
| ASAN | Works | YES | Only sanitizer that produces a runnable binary; instruments user code only |
| TSAN | Linker error | NO (until `modular/modular#6512` fixed) | Reference `modular/modular#6512` in upstream issues |
| MSAN | Compiler rejects | NO | Not implemented in 1.0.0b2 |
| UBSAN | Compiler rejects | NO | Not implemented in 1.0.0b2 |

### Expected Outputs (PR #5389)

```text
# ASAN sweep
298 tests passed under ASAN
46 leaks reported in shared/  (real leaks — file as separate issues)

# TSAN sweep
298 binaries aborted at startup with:
    FATAL: ThreadSanitizer: unexpected memory mapping ...
    Aborted (core dumped)
```

### Environment Variables

| Setting | Effect | Recommendation |
| ------- | ------ | -------------- |
| `ODYSSEY_MEM_LIMIT=24g` on 15 GiB-RAM host | cgroups still caps at physical RAM | Set equal to physical RAM at most |
| `JOBS="-j1"` for TSAN | Fixes `modular/modular#6413` parallel-JIT crash during TSAN compile | **Required** for TSAN compile; does not fix runtime tcmalloc abort |
| `ASAN_OPTIONS=halt_on_error=0:abort_on_error=0:detect_leaks=1` | Collect all ASAN reports per test run | Use for `just test-mojo-asan` |

### Import Depth Decision

| Approach | Works? | Notes |
| -------- | ------ | ----- |
| `from shared.training.metrics import X` in root `__init__.mojo` | Yes | Direct leaf import — bypasses intermediate chain |
| `from shared.training import X` in root `__init__.mojo` | Sometimes | May fail if Mojo re-export resolution is incomplete for that chain |

### Key Mojo Memory Safety Rules

| Error | Cause | Solution |
| ----- | ----- | -------- |
| `Use after move` | Variable used after ownership transfer | Create copy or don't move |
| `Dangling reference` | Reference to local variable | Return owned value with `^` |
| `Mutable aliasing` | Multiple mutable refs to same data | Ensure single mutable reference |
| `Type not copyable` | Missing `^` on non-copyable return | Add transfer operator `^` |

### GLIBC Environment Details

| Component | Version |
| --------- | ------- |
| Host GLIBC (Debian 10) | 2.28 |
| Required GLIBC | 2.32+ (Mojo pixi env) |
| CI Docker base | Ubuntu 22.04+ (GLIBC 2.35) |

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectOdyssey | PR #5389 — Mojo 1.0 sanitizer build system | ASAN sweep: 298/298 tests, 46 real leaks. TSAN sweep: 298/298 binaries compiled with `-j1`, every binary aborted at startup with tcmalloc/TSAN error. Recipe is correct; TSAN runtime requires Modular-side fix. |
| ProjectOdyssey | PR #5364 — Mojo 1.0.0b2 KGEN crash sanitizer escalation | Confirmed: ASAN works; TSAN linker error; MSAN/UBSAN rejected. Filed `modular/modular#6512`. |
| ProjectOdyssey | Issue #3219, PR #3738 / Issue #3745, PR #4785 — Package re-exports | SGD/Adam/AdamW activated; AdaGrad/RMSprop added to top-level shared package. |
| ProjectOdyssey | Issue #3221, PR #3748 — LossTracker/AccuracyMetric chain wiring | Intermediate and root `__init__.mojo` wired; alias pattern confirmed. |
| ProjectOdyssey | Issue #3851, PR #4814 — DataLoader/DataBatch export | Import tests added to both `test_imports.mojo` and `test_imports_part1.mojo`. |

## See Also

- `mojo-jit-crash-retry` — `-j1` context and `modular/modular#6413`
- `architecture-shipping-mojo-package-prefix-dev` — full distribution story (conda recipe, prefix.dev publish, optional wheel)
- `mojo-module-docstring-limitation` — documenting a known re-export limitation
