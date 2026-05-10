---
name: ci-cd-coredump-capture-container-namespace-fix
description: "GHA workflow capturing core dumps from a process that crashes inside a Podman/Docker container must use a path that exists in BOTH host and container mount namespaces, AND must always write metadata + symbols even when no cores exist. Use when: (1) wiring up coredump capture for libKGEN/Mojo or any other JIT runtime that crashes opaquely in CI, (2) debugging why an actions/upload-artifact step uploads nothing despite a known crash, (3) deciding where to point /proc/sys/kernel/core_pattern when the crashing PID is in a non-host mount namespace."
category: ci-cd
date: 2026-05-10
version: "1.0.0"
user-invocable: false
verification: verified-precommit
tags:
  - coredump
  - gdb
  - podman
  - docker
  - mojo
  - libkgen
  - github-actions
  - mount-namespace
---

# Coredump Capture in Containerized CI: Mount-Namespace Pitfall

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-10 |
| **Objective** | Capture real ELF core dumps from a Mojo runtime JIT crash (modular/modular#6413) inside a Podman container running on a GHA Ubuntu runner, so the crash can be walked with gdb. |
| **Outcome** | Initial capture-action wiring (PR #5378 in ProjectOdyssey) collected ZERO cores across all 7 days / all 6 instrumented jobs — two distinct bugs identified by an Opus forensic agent. PR #5380 fixed both bugs; verification end-to-end pending the next JIT-crash CI run. |
| **Verification** | verified-precommit (YAML parses, container can write to the path; live capture not yet observed) |

## When to Use

- You're wiring core-dump capture into a GHA workflow where the crashing process runs inside `podman compose exec` or `docker exec`
- A previous capture iteration uploaded only a metadata-only artifact (e.g. ~565 bytes) despite a known crash in the same job
- A capture iteration uploaded NO artifact at all even though `actions/upload-artifact` was in the workflow
- You need to debug a libKGEN/Mojo-style crash where the published 3-frame trace is the signal-handler chain, not the real fault, and you need a real ELF core to walk with gdb

## Companion Skill

This skill complements `gha-mojo-coredump-capture` (which describes the host-side
infrastructure for capturing Mojo cores). This one specifically covers the
**container-side mount-namespace bugs** that broke the original wiring when the test
process moved inside `podman compose exec`.

## Verified Workflow

### Quick Reference

```yaml
# .github/actions/coredump-capture/action.yml — KEY pieces only
- name: Enable core dumps (host kernel + container)
  if: inputs.phase == 'setup'
  shell: bash
  run: |
    set -x
    # Workspace is bind-mounted by docker-compose.yml as `.:/workspace`.
    # Use the CONTAINER-side path so the kernel resolves it from the
    # crashing process's mount namespace.
    mkdir -p crash-bundle/cores
    chmod 1777 crash-bundle/cores
    echo '/workspace/crash-bundle/cores/core.%p.%e.%t' \
      | sudo tee /proc/sys/kernel/core_pattern
    sudo sysctl -w fs.suid_dumpable=2 || true
    podman compose exec -T <service> bash -c \
      'ulimit -c unlimited && ulimit -a | grep core'
    # Sanity-check container can write the path
    podman compose exec -T <service> bash -c \
      'mkdir -p /workspace/crash-bundle/cores && touch /workspace/crash-bundle/cores/.writable && rm /workspace/crash-bundle/cores/.writable'

- name: Collect crash bundle
  if: inputs.phase == 'collect' && always()
  shell: bash
  run: |
    set -x
    mkdir -p crash-bundle/cores crash-bundle/symbols
    # ALWAYS bundle symbols + metadata — even with no cores. A
    # metadata-only artifact is a positive signal that the action ran.
    podman compose exec -T <service> bash -c '
      ENV_DIR=$(pixi info --json 2>/dev/null | sed -n "s/.*\"prefix\":[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -1)
      cp -av "$ENV_DIR/bin/<binary>" /workspace/crash-bundle/symbols/ 2>/dev/null || true
      for so in "$ENV_DIR"/lib/lib<JIT>*.so; do
        [ -e "$so" ] && cp -av "$so" /workspace/crash-bundle/symbols/ 2>/dev/null || true
      done
    ' || true
    {
      echo "=== /proc/sys/kernel/core_pattern ==="
      cat /proc/sys/kernel/core_pattern
      echo "=== container ulimit -c ==="
      podman compose exec -T <service> bash -c 'ulimit -c'
      echo "=== Coredumps found ==="
      ls -la crash-bundle/cores/
    } > crash-bundle/metadata.txt

- name: Upload crash bundle
  if: inputs.phase == 'collect' && always()
  uses: actions/upload-artifact@<pinned-sha>  # vN
  with:
    name: crash-bundle-${{ inputs.job-name }}
    path: crash-bundle/
    retention-days: 14
    # `warn` (NOT `ignore`) — missing artifact becomes visible in UI
    if-no-files-found: warn
```

### Detailed Steps

1. **Identify the crashing process's mount namespace.** If it runs via `podman compose exec` / `docker exec`, the workspace is bind-mounted at a different path than the host's `$(pwd)`. Find the bind mount in `docker-compose.yml` (typical: `.:/workspace`).
2. **Set core_pattern to the CONTAINER-side path.** `/proc/sys/kernel/core_pattern` is a global kernel parameter, but the path is interpreted in the crashing process's mount namespace. The host runner uses `/home/runner/work/...` while the container sees `/workspace/...`. Use `/workspace/crash-bundle/cores/core.%p.%e.%t` so the kernel can resolve the path inside the container; the file lands on the host via the bind mount.
3. **Set ulimit -c unlimited inside the container, not just on the host.** Per-exec `ulimit -c` is transient and does NOT propagate to subsequent `podman compose exec` calls. Re-set it in the same `exec` that runs the test command, OR raise it on the running container service.
4. **Always write metadata + symbols, regardless of whether cores exist.** This is the diagnostic distinction between "no crash this run" (metadata present, cores empty) and "capture broken" (no artifact at all).
5. **Set `if-no-files-found: warn`, not `ignore`.** A missing artifact must be visible in the UI; otherwise broken capture is silent.
6. **Sanity-check writability.** Touch a `.writable` file from inside the container at setup time. If this fails, abort early — capture cannot work.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| 1 | core_pattern set to `$(pwd)/crash-bundle/cores/core.%p.%e.%t` (host runner CWD) | The crashing `mojo` runs inside `podman compose exec` where `/home/runner/...` doesn't exist. Kernel silently writes nothing. | core_pattern paths resolve in the crashing PID's mount namespace, NOT the host's. |
| 2 | Collect step `exit 0`'d when `cores/` was empty, skipping metadata + symbol bundling | `actions/upload-artifact` then logged "No files were found" and skipped the upload entirely. Result: no signal at all that capture had failed. | Always emit at least metadata.txt; let an empty `cores/` directory still produce a non-empty bundle. |
| 3 | `if-no-files-found: ignore` on upload-artifact | Combined with attempt 2, this hid the broken capture: no warning, no artifact, no failure mode visible in the UI. | Use `warn` for diagnostic uploads — the noise is worth the signal. |
| 4 | Setting `ulimit -c unlimited` once via a transient `podman compose exec` at setup time | The ulimit applies only to that one exec process. Subsequent test execs (where the crash actually happens) reset to default `ulimit -c 0`. | ulimit must be re-set in the same exec that runs the crashing process, OR persistently raised on the long-running container service. |

## Results & Parameters

```yaml
# Required action inputs
inputs:
  phase: required, "setup" or "collect"
  job-name: required, used in artifact name

# Container-side path (matches workspace bind mount)
core_pattern: '/workspace/crash-bundle/cores/core.%p.%e.%t'

# Always-on capture knobs
suid_dumpable: 2
ulimit_c: unlimited (in-exec, not just at setup)
upload-artifact.if-no-files-found: warn
upload-artifact.retention-days: 14

# Symbols to bundle for libKGEN-class crashes (Mojo)
symbols:
  - $ENV_DIR/bin/mojo
  - $ENV_DIR/lib/libKGEN*.so
  - $ENV_DIR/lib/libAsync*.so
  - $ENV_DIR/lib/libMojo*.so
  - $ENV_DIR/lib/libMSupport*.so
```

Expected post-fix bundle (when no crash):

- `metadata.txt` — version banners, core_pattern, ulimit -c, ls of cores/
- `symbols/` — mojo binary + 4 libKGEN/libAsync/libMojo/libMSupport .so files (~MB-scale)
- `cores/` — empty directory

Expected post-fix bundle (when crash):

- everything above PLUS
- `cores/core.<pid>.mojo.<timestamp>` — real ELF core walkable with `gdb symbols/mojo cores/core.<pid>.mojo.<ts>`

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectOdyssey | PR #5380 fixing PR #5378's broken capture; investigating modular/modular#6413 JIT crash | Forensic agent confirmed zero cores captured pre-fix across 7 days / 6 jobs / 1 known crash |
