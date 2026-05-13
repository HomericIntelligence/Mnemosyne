---
name: symbolicate-mojo-cores-inside-container
description: "Post-mortem symbolication of Mojo JIT crash cores must run INSIDE the pixi container via `podman compose exec`, because the host runner doesn't share the pixi env tree where the `mojo` binary lives. Use when: (1) extending a coredump-capture GHA composite action with a symbolication step that dumps backtrace/registers/disasm around $pc, (2) host-side gdb fails with `Could not resolve mojo binary` even though `podman compose exec which mojo` returned a valid path, (3) you need `info all-registers` output to diagnose AVX-512 / ISA-feature-mismatch JIT crashes, (4) symbol bundling steps silently produce an empty `crash-bundle/symbols/` because container paths were used on the host."
category: ci-cd
date: 2026-05-12
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - coredump
  - symbolicate
  - gdb
  - disasm
  - mojo
  - libkgen
  - podman
  - github-actions
  - mount-namespace
  - avx-512
---

# Symbolicate Mojo Cores Inside the Container

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-12 |
| **Objective** | After capturing Mojo JIT crash cores in CI (see `gha-mojo-coredump-capture` + `ci-cd-coredump-capture-container-namespace-fix`), produce per-core symbolicated logs containing backtrace, registers, raw instruction stream around `$pc`, a `disassemble $pc-64,$pc+64` window, and `info all-registers` — without losing the symbolication step to mount-namespace mismatch. |
| **Outcome** | Symbolication step added to `.github/actions/coredump-capture/action.yml` (ProjectOdyssey commit `78f75f22` on `bisect/6413-positive-control`). Across PR #5399 and dispatches `25746055958+`, 10+ cores were successfully symbolicated; 6 distinct AVX-512 instruction sites identified as the smoking gun for an ISA-feature-mismatch JIT codegen bug (modular/modular#6413). |
| **Verification** | verified-ci |

## When to Use

- You already have `gha-mojo-coredump-capture` capturing real ELF cores into `crash-bundle/cores/` and want to add automated symbolication
- A host-side `gdb -batch ... "$MOJO_BIN" "$core"` step exits with "Could not resolve mojo binary — skipping" even though `podman compose exec ... which mojo` printed a valid-looking path
- A symbol-bundling step silently produced an empty `crash-bundle/symbols/` (host-side `cp` of a container-side `mojo` path)
- You need to diagnose a Mojo JIT crash where the suspected cause is ISA-feature mismatch (AVX-512 emitted on a non-AVX-512 CPU) and need `info all-registers` to surface zmm/k0–k7 state at fault time
- You want to avoid wasting 30–60s per CI run installing `gdb` on the host runner when the container already ships it via the Dockerfile

## Companion Skills

- `gha-mojo-coredump-capture` — host-side capture infrastructure (`core_pattern`, `mojo-under-gdb.sh`, artifact upload)
- `ci-cd-coredump-capture-container-namespace-fix` — the prior mount-namespace lesson (cores must land on a path visible to BOTH host and container)

This skill applies the same namespace-alignment principle, but for the **symbolication** step rather than the **capture** step.

## Verified Workflow

### Quick Reference

```yaml
# Drop this step into .github/actions/coredump-capture/action.yml
# AFTER the metadata-building step, BEFORE artifact upload.

- name: Symbolicate cores (disasm + registers around $pc)
  if: inputs.phase == 'collect' && always()
  shell: bash
  run: |
    set -x
    mkdir -p crash-bundle/symbolicated
    shopt -s nullglob
    CORES=( crash-bundle/cores/core.* crash-bundle/cores/core.gdb.* )
    shopt -u nullglob
    if [ ${#CORES[@]} -eq 0 ]; then
      echo "[symbolicate] No cores to symbolicate — skipping."
      exit 0
    fi
    for core in "${CORES[@]}"; do
      base=$(basename "$core")
      c_core="/workspace/crash-bundle/cores/$base"
      out="crash-bundle/symbolicated/${base}.symbolicated.log"
      if ! podman compose exec -T projectodyssey-dev bash <<HEREDOC > "$out" 2>&1
    set -e
    MOJO_BIN=\$(pixi run which mojo 2>/dev/null | tail -1)
    echo "==== ${base} ===="
    echo "symbol_binary=\$MOJO_BIN"
    echo "---- Backtrace (top 25 frames) ----"
    pixi run gdb -batch -ex "set pagination off" \\
      -ex "thread apply 1 bt 25" \\
      "\$MOJO_BIN" "${c_core}" 2>&1 | head -80
    echo "---- Instruction stream around \\\$pc ----"
    pixi run gdb -batch \\
      -ex "set pagination off" \\
      -ex "set print pretty on" \\
      -ex "info registers" \\
      -ex "info frame" \\
      -ex "x/16i \\\$pc - 30" \\
      -ex "x/16i \\\$pc" \\
      -ex "disassemble \\\$pc - 64, \\\$pc + 64" \\
      -ex "info all-registers" \\
      "\$MOJO_BIN" "${c_core}" 2>&1 | head -400
    HEREDOC
      then
        echo "[symbolicate] podman exec for $base exited non-zero (see $out)"
      fi
    done
```

### Detailed Steps

1. **Run gdb inside the container, not on the host.** Both the `mojo` binary
   (under `/home/dev/.cache/pixi/envs/.../bin/mojo`) and the cores
   (`/workspace/crash-bundle/cores/...` via bind mount) only exist in the
   container's mount namespace. Wrap the entire gdb invocation in a single
   `podman compose exec -T projectodyssey-dev bash <<HEREDOC ... HEREDOC` block.

2. **Get the right heredoc quoting.** Variables that should expand on the host
   (the loop's `${base}` and `${c_core}`) are written bare. Variables that must
   expand inside the container (`\$MOJO_BIN`) get a single backslash. Variables
   passed through the heredoc AND into a gdb `-ex` string (`\\\$pc`) need
   three backslashes — one stripped by the outer shell, one by the heredoc, one
   by the gdb command parser.

3. **Use `set -e` inside the heredoc** so the in-container shell aborts on the
   first gdb failure rather than silently emitting a partial log.

4. **Cap log size with `head -80` / `head -400`.** Multi-megabyte cores can
   produce enormous `info all-registers` dumps; truncate to keep the
   `crash-bundle/symbolicated/*.symbolicated.log` files within artifact-size
   budget.

5. **Always emit `info all-registers`.** This is the section that surfaces
   `zmm0..zmm31` / `k0..k7` register state — the load-bearing signal for
   AVX-512 codegen on non-AVX-512 hardware. Skipping it leaves you blind to
   ISA-feature-mismatch crashes.

6. **Glob both `core.*` and `core.gdb.*` patterns.** The `mojo-under-gdb.sh`
   wrapper writes `core.gdb.<pid>.<timestamp>`; the pipe-handler writes
   `core.<exe>.<pid>.<timestamp>`. Missing one prefix loses half the captures.

7. **Wrap the whole thing in `if ! podman compose exec ... ; then ... fi`** so
   a single failing core does not abort the loop. Each failure gets its own
   log entry.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Run gdb on the host runner | `MOJO_BIN=$(podman compose exec ... pixi run which mojo); gdb -batch -ex "..." "$MOJO_BIN" "$core"` directly on the host | `pixi run which mojo` returns the container-side path (`/home/dev/.cache/pixi/envs/.../bin/mojo`). Subsequent `[ ! -e "$MOJO_BIN" ]` is true on the host → exits with "Could not resolve mojo binary — skipping" | When both the binary and the cores live inside the container, run gdb inside the container. Don't resolve container-side paths and then act on them from the host |
| `apt-get install gdb` on the runner | Pre-install gdb on the host runner image so host-side gdb works | Even with gdb on the host, the container-side mojo binary path remains unresolvable. Also wastes 30–60s per CI run | The bottleneck isn't gdb availability — it's mount-namespace alignment. The container already has gdb via the Dockerfile |
| Pre-bake gdb into the runner base image | Build a custom runner image with gdb pre-installed | Same root cause as above: mojo binary path is container-side. Image-build complexity for no gain | Don't solve symptom-level problems (tool availability) when the actual bug is namespace mismatch |
| Use empty `crash-bundle/symbols/` bundle | Earlier capture iterations expected `cp "$MOJO_BIN" crash-bundle/symbols/` to populate symbols from a `which mojo` call | `which mojo` was executed via `podman compose exec` and returned the container-side path, so the host-side `cp` silently failed | Any host-side file operation targeting a path discovered via `podman compose exec` is wrong. Do the file operation inside the container too |

## Results & Parameters

### Captured AVX-512 instruction sites (PR #5399 + dispatches)

Six distinct AVX-512 instructions identified across 10+ symbolicated cores —
all on runners advertised as non-AVX-512 — confirming an ISA-feature-mismatch
JIT codegen bug:

| Instruction | Feature Required | Notes |
|-------------|------------------|-------|
| `vandps (mem){1to4},%xmm3,%xmm3` | AVX-512F | Embedded broadcast |
| `vpternlogd $0x96,%xmm3,%xmm4,%xmm7` | AVX-512F | Ternary logic |
| `vcmpltss → %k1` + `vmovss {%k1}{z}` | AVX-512F | Opmask + masked move with zeroing |
| `vmovdqa64 (mem),%zmm0` | AVX-512F | 512-bit register |
| `vmovdqu64 %zmm0,...` | AVX-512F | Unaligned 512-bit store |
| `vpbroadcastb %eax,%xmm0` | AVX-512BW | Reg-source byte broadcast |

### Expected output structure

```text
crash-bundle/
├── cores/
│   ├── core.mojo.12345.1715515200
│   └── core.gdb.12346.1715515200
└── symbolicated/
    ├── core.mojo.12345.1715515200.symbolicated.log    # ~5-20 KB each
    └── core.gdb.12346.1715515200.symbolicated.log
```

Each `.symbolicated.log` contains, in order:

1. Header line: `==== <core basename> ====`
2. `symbol_binary=<resolved container-side mojo path>`
3. Top-25-frame backtrace (capped at 80 lines)
4. `info registers` (integer + SSE/AVX)
5. `info frame`
6. `x/16i $pc - 30` (16 instructions before fault)
7. `x/16i $pc` (16 instructions from fault forward)
8. `disassemble $pc - 64, $pc + 64` (full window)
9. `info all-registers` (capped at 400 lines — surfaces zmm/k-register state)

### Reference implementation

- **Repo**: HomericIntelligence/ProjectOdyssey
- **Branch**: `bisect/6413-positive-control`
- **Commit**: `78f75f22`
- **File**: `.github/actions/coredump-capture/action.yml`

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectOdyssey | PR #5399, dispatches 25746055958+, modular/modular#6413 | 10+ symbolicated cores captured + analyzed; 6 distinct AVX-512 instruction sites identified as root cause |
