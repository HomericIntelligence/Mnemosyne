---
name: gha-mojo-coredump-capture
description: "Use when: (1) investigating a CI-only Mojo crash whose published trace ends in `<unmapped>` at frame 4 (real fault is in JIT-emitted code or freed heap and unreachable from the printed stack), (2) cannot reproduce a libKGEN crash locally and need a real coredump from CI, (3) setting up GitHub Actions infrastructure to capture coredumps from a containerized test run, (4) bundling a coredump with its matching `mojo` binary and the relevant `libKGEN*` / `libAsync*` / `libMojo*` / `libMSupport*` shared libs into a reasonably-sized artifact, (5) deciding which GHA host-side settings need root vs which container-side settings can run as the test user, (6) the artifact must survive container teardown, and (7) wanting to keep the artifact under ~1 GB by filtering shared libraries to the four JIT-related families."
category: ci-cd
date: 2026-05-09
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - github-actions
  - coredump
  - mojo
  - debugging
  - libKGEN
  - core-pattern
  - gdb
  - ci
  - podman
  - artifact
---

# GitHub Actions Core-Dump Capture for Mojo JIT Crashes

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-05-09 |
| **Objective** | Capture a real coredump from a CI-only Mojo runtime crash so that frame 4 (`<unmapped>` in the published trace) can be recovered post-mortem. The published 3-frame `libKGENCompilerRTShared.so` trace is the Crashpad signal-handler chain — the actual fault site is unreachable without a coredump. |
| **Outcome** | Workflow merged to `main` on ProjectOdyssey via PR #5363 as standing infrastructure. Exercised on PR #5364. Bundles coredumps + matching `mojo` binary + four families of shared libraries into a 14-day artifact, filtered to keep size reasonable. |
| **Verification** | verified-ci |

## When to Use

- A CI-only Mojo crash has been investigated locally with the 4-hypothesis disproof
  checklist (see `mojo-jit-crash-retry`) and ASAN (see
  `mojo-sanitizer-support-matrix`), and you still cannot reproduce; the published
  trace ends at `<unmapped>` and the real fault is unreachable from the printed
  frames
- You need to file an upstream issue (Mojo runtime is closed-source; see
  `mojo-binary-closed-source-debugging`) and Modular asks for a coredump
- You want to add coredump capture as **standing CI infrastructure** so future Mojo
  JIT crashes are debuggable without a re-run

## Verified Workflow

### Architecture

The capture has to span two trust domains: the **GHA runner host** (root-capable, can
modify kernel sysctls) and the **test container** (unprivileged, runs as the test user).
Coredumps are written to a path that is bind-mounted from host into container so the
files survive container teardown without an explicit volume mount.

```text
GHA runner host  (root)                Test container (test user)
─────────────────────────              ────────────────────────────
 kernel.core_pattern  ────────────►    /workspace/crash-bundle/cores/
   = $WORKSPACE/crash-bundle/...        (same path, bind-mounted)
 systemd-coredump  STOPPED              ulimit -c unlimited  (in justfile)
 apport            STOPPED              mojo run ...  (may crash → core file)

 always-runs post-step                  test recipe exits → container torn down
   bundles cores + mojo binary +        cores remain on host because
   libKGEN*/Async*/Mojo*/MSupport*      $WORKSPACE is bind-mounted
   into 14-day artifact
```

### Quick Reference — minimal skeleton

```yaml
# .github/workflows/<your-test>.yml — relevant steps only
jobs:
  test:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4

      - name: Configure host for coredump capture
        run: |
          sudo mkdir -p "$GITHUB_WORKSPACE/crash-bundle/cores"
          sudo chmod 1777 "$GITHUB_WORKSPACE/crash-bundle/cores"
          # Workspace is bind-mounted into the container, so cores written here
          # survive container teardown without needing an explicit volume mount.
          echo "$GITHUB_WORKSPACE/crash-bundle/cores/core.%p.%e.%t" \
            | sudo tee /proc/sys/kernel/core_pattern
          # Stop interceptors so cores are raw ELF (not journald / .crash files)
          sudo systemctl stop systemd-coredump.socket 2>/dev/null || true
          sudo systemctl stop apport.service          2>/dev/null || true
          ulimit -c unlimited
          cat /proc/sys/kernel/core_pattern

      - name: Run tests (justfile sets `ulimit -c unlimited` inside the container)
        run: just test-group "tests/<group>" "test_*.mojo"

      - name: Bundle crash artifacts
        if: always()
        run: |
          BUNDLE="$GITHUB_WORKSPACE/crash-bundle"
          mkdir -p "$BUNDLE/bin" "$BUNDLE/lib"

          # Find the mojo binary the container actually used (pixi env path)
          MOJO_BIN=$(pixi run -- bash -c 'command -v mojo' 2>/dev/null || true)
          [ -n "$MOJO_BIN" ] && cp -L "$MOJO_BIN" "$BUNDLE/bin/" || true

          # Copy ONLY the four JIT-related shared-library families.
          # The full env is multi-GB; this filter keeps the artifact reasonable.
          MOJO_LIBDIR=$(pixi run -- bash -c 'echo $CONDA_PREFIX/lib' 2>/dev/null || echo "")
          if [ -n "$MOJO_LIBDIR" ] && [ -d "$MOJO_LIBDIR" ]; then
            find "$MOJO_LIBDIR" -maxdepth 3 \
              \( -name 'libKGEN*'    \
              -o -name 'libAsync*'   \
              -o -name 'libMojo*'    \
              -o -name 'libMSupport*' \) \
              -exec cp -L {} "$BUNDLE/lib/" \;
          fi

          ls -lah "$BUNDLE/cores" "$BUNDLE/bin" "$BUNDLE/lib" || true

      - name: Upload crash bundle
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: mojo-crash-bundle-${{ github.run_id }}
          path: crash-bundle/
          retention-days: 14
          if-no-files-found: ignore
```

### Container-side setup (justfile)

The host's `core_pattern` only takes effect if the process is allowed to dump core. The
test runner inside the container must raise its core-dump limit:

```just
# justfile — inner test recipe that runs the actual mojo command
_test-group-inner GROUP PATTERN:
    #!/usr/bin/env bash
    set -e
    ulimit -c unlimited
    pixi run mojo run "{{GROUP}}/{{PATTERN}}"
```

Without the `ulimit -c unlimited` inside the container, the kernel will not write a
core file even though `core_pattern` is set on the host.

### Why these specific decisions

| Decision | Why |
| --- | --- |
| Use `$GITHUB_WORKSPACE/crash-bundle/cores/...` as the core_pattern path | The workspace is automatically bind-mounted into the container by the action's container setup; cores written there survive container teardown without configuring an extra mount. |
| `sudo` set `kernel.core_pattern` (not just `ulimit -c unlimited` inside the container) | `core_pattern` is a kernel-wide sysctl; only root on the host can set it. Without it, cores either go to systemd-coredump (compressed, hard to retrieve) or are silently dropped. |
| Stop `systemd-coredump.socket` and `apport.service` | Both intercept core dumps and rewrite them into their own formats (`.crash` files, journal entries). Stopping them ensures cores are raw ELF that `gdb` can open directly with the matching binary. |
| `chmod 1777` on the cores directory | Cores may be written by the unprivileged container user; sticky-bit world-writable matches `/tmp` semantics so any UID can write. |
| Filter shared libs to `libKGEN*` / `libAsync*` / `libMojo*` / `libMSupport*` | The full Mojo install is multi-GB. The four families above are the JIT runtime libraries that appear in crash traces. Filtering keeps the artifact under the 1 GB GHA artifact ceiling. |
| `cp -L` (not `cp`) | Mojo install paths often contain symlinks; `-L` follows them so `gdb` can load the actual files from the artifact. |
| `if: always()` on bundling and upload steps | The point is to capture artifacts when tests **fail**; without `always()` the bundling step is skipped on failure. |
| 14-day retention | Long enough to triage and file upstream issue, short enough not to inflate storage cost. |

### Using the captured bundle

```bash
# Download the artifact
gh run download <run-id> -n mojo-crash-bundle-<run-id>
cd mojo-crash-bundle-<run-id>

# Open the core with the matching binary; tell gdb where the libs are
gdb -ex "set solib-search-path $(pwd)/lib" \
    -ex "core-file $(ls cores/core.* | head -1)" \
    bin/mojo

# Inside gdb:
(gdb) bt full          # full backtrace including frame 4
(gdb) info registers   # state at fault
(gdb) disas $rip       # what JIT-emitted code was executing
(gdb) info shared      # confirm matching libKGEN* etc. are loaded
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Set `ulimit -c unlimited` only inside the container | Edited justfile recipe to set it; left host core_pattern at distro default | Distro default `core_pattern` is `\|/lib/systemd/systemd-coredump %P %u %g %s %t %c %h`, which redirects cores into journald-managed compressed storage that the post-step cannot find. No core files appeared in the artifact. | Must set `core_pattern` on the host to a plain filesystem path; container `ulimit` alone is insufficient |
| Use a tmpfs volume mount for the coredump path | Added `-v tmpfs:/cores` to the container | Cores were written but disappeared on container teardown before the post-step could bundle them | Use `$GITHUB_WORKSPACE/...` so the path is on the host filesystem (auto-bind-mounted); avoids needing an explicit volume |
| Bundle the entire Mojo install into the artifact | `cp -r $CONDA_PREFIX/lib $BUNDLE/lib` | Artifact exceeded 1 GB GHA ceiling and upload failed; most of those libs are not in the crash trace anyway | Filter to `libKGEN*`, `libAsync*`, `libMojo*`, `libMSupport*` — the four families that show up in JIT crash traces |
| Leave `systemd-coredump` running | Did not stop the socket; assumed cores would still go to the configured path | systemd-coredump intercepted SIGSEGV before kernel `core_pattern` rule fired and rewrote the core into `.crash` format under `/var/lib/systemd/coredump/`, where the post-step did not look | Stop both `systemd-coredump.socket` and `apport.service` so the kernel-level `core_pattern` rule is the only handler |
| Upload artifact only on `failure()` | Used `if: failure()` instead of `if: always()` on the upload step | When the workflow itself is cancelled or the failure mode is "no test output, runner exits" the `failure()` condition does not trigger and the artifact is lost | Use `if: always()` on both bundling and upload; cost is one extra step per successful run, which is negligible |
| Forget `cp -L` and copy symlinks | Used plain `cp`; symlinks pointed into the pixi env which is not in the artifact | gdb on a workstation could not resolve the libs; symlinks dangled | Always use `cp -L` to dereference symlinks when bundling shared libraries for offline analysis |
| Skip copying the `mojo` binary itself | Bundled only cores and libs | gdb cannot debug a coredump without the original executable; the mojo binary version hash is build-specific and cannot be re-downloaded later | Always include the matching `mojo` binary (`cp -L $(command -v mojo) $BUNDLE/bin/`) |

## Results & Parameters

### Verified output structure

```text
crash-bundle/
├── bin/
│   └── mojo                                  (the exact binary the crashing run used)
├── cores/
│   └── core.<pid>.<exe>.<unix-ts>            (one or more raw ELF cores)
└── lib/
    ├── libKGENCompilerRTShared.so
    ├── libAsyncRTMojoBindings.so
    ├── libAsyncRTRuntimeGlobals.so
    ├── libMojo*.so
    └── libMSupport.so
```

### Companion skills

- `mojo-jit-crash-retry` v4.1.0+: dynsym/objdump procedure (use this on the bundled
  `libKGEN*` to confirm the published frames are signal-pipeline noise)
- `mojo-binary-closed-source-debugging`: explains why a coredump is the only path to
  the real fault site (Mojo runtime is not buildable from public source)
- `mojo-sanitizer-support-matrix`: alternative escalation when ASAN can run; coredump
  is the fallback when the crash is inside libKGEN itself (not ASAN-instrumented)

### Where to install this in a repo

| File | Purpose |
| --- | --- |
| `.github/workflows/<your-test>.yml` | Add the four steps under "Quick Reference" — host config, test, bundle, upload |
| `justfile` | Add `ulimit -c unlimited` to the container-side test recipe (e.g. `_test-group-inner`) |

### What this DOES NOT do

- It does not symbolicate the JIT-emitted code in frame 4 — that code has no DWARF.
  You will see the instruction stream and registers but not source lines.
- It does not give you Mojo compiler/runtime source. The shared libraries are
  closed-source; gdb will show offsets within them, not source lines. See
  `mojo-binary-closed-source-debugging`.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| ProjectOdyssey | PR #5363 (merged to main as standing infra), PR #5364 (first exercise) | `kernel.core_pattern = $WORKSPACE/crash-bundle/cores/core.%p.%e.%t`; `ulimit -c unlimited` in `_test-group-inner`; bundling filters to `libKGEN*`, `libAsync*`, `libMojo*`, `libMSupport*`; 14-day retention |
