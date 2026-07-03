---
name: debugging-podman-wsl2-netavark-hostnetwork-workaround
description: "Bypass podman-compose network creation failures on WSL2 rootless podman by running one-off host-network containers. Use when: (1) podman-compose up -d fails with netavark/nftables errors ('Could not process rule: No such file or directory', 'IPAM error: failed to get ips', 'nft did not return successfully') on WSL2/rootless podman; (2) a Makefile/CI recipe wrapping podman-compose exec -T dev fails with 'can only create exec sessions on running containers' because the compose network silently failed; (3) you need to replicate a compose dev-service environment for a one-off in-container command without the compose network."
category: debugging
date: 2026-07-02
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - podman
  - podman-compose
  - wsl2
  - netavark
  - nftables
  - rootless
  - host-network
  - dev-container
  - keep-id
---

# Debugging Podman WSL2 Netavark Host-Network Workaround

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-02 |
| **Objective** | Run a containerized C++ build flow (conan install, cmake configure+build, install smoke test) on a WSL2 host where `podman-compose up -d dev` cannot create its network |
| **Outcome** | Successful — bypassed the broken compose network with a one-off `podman run --network=host` that replicates the compose service environment; full build flow ran end-to-end with results identical to the compose path |
| **Verification** | verified-local (ProjectKeystone issue #596 session, WSL2 kernel 6.6.x, rootless podman) |

## When to Use

- `podman-compose up -d <service>` fails while creating the compose network with netavark/nftables errors on WSL2 or another rootless-podman host, e.g.:
  - `Could not process rule: No such file or directory`
  - `IPAM error: failed to get ips`
  - `nft did not return successfully`
  - `IPAM error: failed to find ip for subnet 10.89.0.0/24`
- A Makefile or CI recipe that wraps `podman-compose exec -T dev <cmd>` fails with `can only create exec sessions on running containers: container state improper` — often because an earlier `podman-compose up -d ... || true` guard silently swallowed the real network-creation failure
- You need to replicate a compose dev-service environment (image, working dir, bind mount, env vars, user namespace) for a one-off in-container command without the compose network
- Note: image builds are unaffected — `podman-compose build dev` (buildah) still works; only network/container creation fails

## Verified Workflow

### Quick Reference

```bash
# Symptom (WSL2, rootless podman):
podman-compose up -d dev
# -> netavark: nftables errors ("Could not process rule: No such file or directory",
#    "nft did not return successfully")
# -> IPAM error: failed to find ip for subnet 10.89.0.0/24
# Downstream symptom (root cause hidden by `up -d ... || true` guards):
podman-compose exec -T dev true
# -> Error: can only create exec sessions on running containers: container state improper

# Verified workaround — one-off run on host networking, replicating the compose service env:
podman run --rm \
  --network=host \
  --userns=keep-id \
  -v "$PWD:/workspace:Z" \
  -w /workspace \
  -e HOME=/workspace/.docker-home \
  localhost/<image>:latest <command>
```

### Detailed Steps

1. **Surface the real error.** If a Makefile CONTAINER_CHECK (or similar wrapper) does `podman-compose up -d dev || true` and downstream `exec` calls fail with "can only create exec sessions on running containers", run `podman-compose up -d dev` manually. On the affected WSL2 host this shows netavark failing to program nftables rules and an IPAM error for the compose subnet (`10.89.0.0/24`) — the compose network cannot be created at all.

2. **Confirm the image is fine.** `podman-compose build dev` succeeds — buildah does not use netavark, so the failure is scoped to network/container creation only. No rebuild is needed.

3. **Read the compose service definition** and note everything that shapes the container environment: image name, `working_dir`, volume mounts, environment variables, and `userns_mode` (here: `userns_mode: keep-id`).

4. **Run the command as a one-off host-network container**, mirroring the compose service exactly:

   ```bash
   podman run --rm \
     --network=host \
     --userns=keep-id \
     -v "$PWD:/workspace:Z" \
     -w /workspace \
     -e HOME=/workspace/.docker-home \
     localhost/<image>:latest <command>
   ```

   Why each flag matters:
   - `--network=host` — skips netavark/IPAM entirely (no compose network needed) while still providing full network access, e.g. for conan package downloads.
   - `--userns=keep-id` — maps the host uid 1:1 into the container so files written to the bind mount stay owned by the host user (the same reason the compose file sets `userns_mode: keep-id`).
   - `-v "$PWD:/workspace:Z" -w /workspace -e HOME=/workspace/.docker-home` — mirror the compose service's volume, working dir, and env so build artifacts land with in-container paths (`/workspace/...`) identical to what the compose flow produces. This keeps CMake caches and `cmake_install.cmake` consistent between the two invocation styles.

5. **Run the full flow through the workaround.** In the verifying session, conan install, cmake configure+build (release), and an install smoke-test script all ran end-to-end via this one-off invocation with results identical to the compose path.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Plain compose up | `podman-compose up -d dev` on the WSL2 host | netavark could not program nftables rules ("Could not process rule: No such file or directory", "nft did not return successfully") and IPAM failed for subnet 10.89.0.0/24 — the compose network cannot be created on this WSL2 kernel/rootless setup | Compose networking is the broken layer; image builds (buildah) are unaffected |
| Trusting the Makefile guard | Relying on the Makefile's CONTAINER_CHECK, which runs `podman-compose up -d dev \|\| true` before `podman-compose exec -T dev ...` | The `\|\| true` swallowed the network-creation failure, so the visible error was the misleading downstream "can only create exec sessions on running containers: container state improper" | When exec-session errors appear, run `podman-compose up -d dev` manually to surface the real root cause |
| Fixing nftables on WSL2 | NOT attempted — repairing nftables kernel-module support on the WSL2 kernel was out of scope for the session | (not tried) | The `--network=host` bypass was sufficient for the build workflow; a kernel-level fix may still be the proper long-term solution |

## Results & Parameters

```yaml
# Environment
os: WSL2 (kernel 6.6.x)
podman: rootless
network_backend: netavark (nftables)

# Symptom
compose_error: |
  netavark: nftables: "Could not process rule: No such file or directory",
  "nft did not return successfully";
  IPAM error: failed to find ip for subnet 10.89.0.0/24
downstream_error: "can only create exec sessions on running containers: container state improper"
unaffected: "podman-compose build dev (buildah) — image builds still work"

# Verified workaround (exact command shape)
run: >-
  podman run --rm --network=host --userns=keep-id
  -v "$PWD:/workspace:Z" -w /workspace
  -e HOME=/workspace/.docker-home
  localhost/<image>:latest <command>

# Why the flags
network_host: "bypasses netavark/IPAM completely; still has network access (conan downloads)"
userns_keep_id: "host uid mapped 1:1 — bind-mount writes stay owned by the host user (matches compose userns_mode: keep-id)"
env_mirroring: "same working_dir/volume/HOME as the compose service — /workspace/... paths identical, CMake caches and cmake_install.cmake stay consistent"

# Verification
flow: "conan install -> cmake configure+build (release) -> install smoke-test script"
result: "end-to-end success, identical results to the compose path"
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectKeystone | issue #596 session — containerized release build + install smoke test on a WSL2 host with broken compose networking | 2026-07-02 |
