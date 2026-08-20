---
name: homeric-crosshost-deployment-and-mesh-topology
license: BSD-3-Clause
description: "Deploy and diagnose the HomericIntelligence mesh across Tailscale hosts using NATS JetStream, compose overlays, native launchers, and resilient process boundaries. Use for cross-host topology, NATS leaf/auth/TLS planning, Grafana hardening, Telemachy client-certificate wiring, publish retry, dual-runtime health checks, and NATS SIGKILL/restart failures."
category: architecture
date: 2026-06-20
version: "2.0.0"
user-invocable: false
verification: unverified
history: homeric-crosshost-deployment-and-mesh-topology.history
tags:
  - cross-host
  - deployment
  - tailscale
  - nats
  - jetstream
  - compose
  - podman
  - healthcheck
  - leafnode
  - tls
  - mtls
  - retry
  - e2e
  - process-boundary
---

# HomericIntelligence Cross-Host Deployment and Mesh Topology

## Overview

Use this skill to choose and verify a HomericIntelligence service topology, or to review a
NATS security/restart plan without promoting assumptions to evidence. It retains the reusable
operator decisions; project transcripts and case-specific file maps are in the
[notes](./homeric-crosshost-deployment-and-mesh-topology.notes.md), and the full superseded
content is in [history](./homeric-crosshost-deployment-and-mesh-topology.history).

The overall skill remains `unverified` because the NATS authentication, Grafana hardening,
TLS-runbook, and Telemachy mTLS workflows are plans. Cross-host deployments were verified
locally, publish retry was verified in CI, and the NATS restart implementation was verified
locally with 15/15 tests including an 8-cycle restart loop. Do not describe those local results
as CI evidence.

## When to Use

- Split the E2E stack between worker and control hosts, bring a Tailnet host up from cold state,
  or choose a compose overlay, native binary, or per-component launcher.
- Connect myrmidons and services directly to a NATS hub, or introduce a leafnode when isolation,
  local buffering, or topology requires it.
- Add JetStream publish retry, diagnose webhook delivery, compose health checks, rootless Podman
  port exposure, or container DNS behavior.
- Plan NATS leaf/server authentication, a certificate lifecycle runbook, Grafana anonymous-access
  removal, or Telemachy client-certificate wiring.
- Diagnose a multi-process NATS SIGKILL/restart test where the kill target or JetStream store must
  cross a shell-process boundary.

## Verified Workflow

### Decision rules

1. **Map the topology before launching.** Put the NATS hub where every host can reach TCP 4222;
   use Tailscale addresses, not container-only DNS, across physical hosts. A direct connection is
   simplest. Use a leafnode on TCP 7422 only when a spoke needs local NATS semantics or isolation.
2. **Inventory real entry points.** Re-grep binaries, config blocks, helper definitions, workflow
   invocation, and async connection sites at the target revision. Issue line numbers and named
   helpers can describe an unmerged branch.
3. **Separate syntax, health, and behavior.** `compose config` proves parsing only. A container
   health state proves the configured probe runs. An API or message round trip proves behavior.
4. **Preserve verification labels per claim.** A locally inspected signature or prototype does not
   verify an end-to-end plan. A design-only resolution does not become `verified-local`.
5. **Treat process exit as the restart correctness gate.** A port probe is diagnostic. For a
   cross-process harness, persist the PID and JetStream store directory, kill that PID, wait for
   exit/FD release, then relaunch against the same store.

### Copy-ready pattern 1: deploy and verify a cross-host stack

```bash
# Worker/NATS host. Use the repository's current compose filenames and image tags.
docker compose -f docker-compose.e2e.yml \
  -f docker-compose.crosshost.yml up -d nats agamemnon hermes

# Control host. Build in the declared environment, then point services at the hub.
NATS_URL="nats://<worker-tailscale-ip>:4222" \
  <build-root>/ProjectNestor/ProjectNestor_server

# Native Hermes uses a src layout.
PYTHONPATH=src NATS_URL="nats://<worker-tailscale-ip>:4222" \
  python -m hermes

# Prove transport and application health; add one message/API round trip.
curl --fail "http://<worker-tailscale-ip>:8222/healthz"
curl --fail "http://<worker-tailscale-ip>:8080/healthz"
curl --fail "http://<control-tailscale-ip>:8081/healthz"
```

Use YAML string-form health checks for Docker Compose and podman-compose compatibility. Alpine
NATS images use BusyBox `wget`, so prefer `wget -q -O - URL`, not the combined `-qO-`. A
distroless image has no shell, curl, wget, or BusyBox: expose a binary self-check such as
`["CMD", "/service", "-healthcheck"]`, then observe an actual healthy container.

If rootless Podman does not expose bridge ports because `rootlessport` is absent, use host
networking deliberately and rewrite in-stack datasource URLs to `localhost`. Do not leave service
DNS names such as `prometheus:9090` in a host-networked Grafana configuration.

### Copy-ready pattern 2: review NATS security and client TLS changes

```bash
# Discover current facts before editing or citing them.
rg -n 'authorization|leafnodes|tls|port' configs/nats
rg -n 'nats\.connect|Client\.connect|build_ssl_context' \
  provisioning/ProjectTelemachy infrastructure/ProjectHermes
ls docs/adr docs/runbooks

# Validate BOTH directions: the bad fixture must fail and the fixed fixture must pass.
nats-server -t -c <bad-config> && exit 1 || true
nats-server -t -c <fixed-config>

# Inspect the installed implementation method, not only the convenience wrapper.
python -c 'import inspect; from nats.aio.client import Client; print(inspect.signature(Client.connect))'
```

Apply these material constraints:

- Authenticate the leaf listener inside its own `leafnodes {}` block and the client listener in
  the appropriate top-level authorization block. A file-wide grep cannot prove block placement;
  use a brace-depth-aware check and test its positive and negative paths.
- Run the config check unconditionally in CI with a pinned `nats-server`; a
  `command -v nats-server` guard silently converts enforcement into a no-op.
- Decide explicitly between a shared bootstrap token and per-leaf credentials. A shared token has
  no per-leaf revocation. Verify secret-file ignore rules rather than assuming them.
- TLS plans must re-read the accepted ADR and live config. The observed TLS ADR was ADR-008;
  ADR-009 and `enable-nats-auth.md` did not exist during the captured work.
- Verify `step` flags, NATS certificate reload behavior, and monitoring JSON keys against the
  installed versions before publishing a runbook. The earlier runbook claims were unverified.
- Telemachy had no existing live NATS connection. A helper with no consumer does not satisfy
  “connects to NATS.” Put a deliberate fail-closed `tls://` preflight inside the existing
  `_run_with_signals()` async function, before `AgamemnonClient`; never add a nested
  `asyncio.run()`.
- Wrap connection/handshake failures in a typed `NatsConnectionError`, give the operator the TLS
  variables to check, and translate it to `typer.Exit(1)` at the CLI boundary.
- On nats-py 2.14.0, `Client.connect` was locally confirmed to accept `tls`, `tls_hostname`, and
  `tls_handshake_first`. Re-inspect the installed version. Generate test certificates with the
  available `openssl` binary into `tmp_path`; do not assume `cryptography` or commit ignored PEMs.
- Disabling Grafana anonymous access also requires an actual `/api/health` probe and provisioning
  check. Compose rendering alone cannot prove either remains available.

### Copy-ready pattern 3: make NATS restart cross-process and state-preserving

```bash
# The parent writes /tmp/hi-nats-${NATS_MONITOR_PORT}.meta with two lines:
#   <pid>
#   <store_dir>
# A forked test reads that file; a shell global does not cross `bash "$script"`.
pid="$(nats_meta_pid)"
store_dir="$(nats_meta_store_dir)"
test -n "$pid" && test -n "$store_dir"

kill -KILL "$pid"
wait "$pid" 2>/dev/null || {
  for _poll in $(seq 1 20); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.1
  done
}

# Relaunch against the original JetStream store, not a fresh mktemp directory.
start_nats_bg_at "$store_dir"
nats_wait_healthy
nats_stream_exists <stream>
```

The measured kernel result was 8/8 immediate rebinds after SIGKILL: `TIME_WAIT` does not apply to
the server's own listening socket. It applies to the active-close side of an established
connection. Therefore waiting out 2MSL, adding `SO_REUSEADDR`, or treating a free-port poll as the
primary fix addresses the wrong mechanism. The actual defect was a stale process: `_NATS_PID` was
empty in the child shell, the kill was a no-op, and the old listener remained alive.

Keep a bounded port probe only as a diagnostic margin. Guard `/dev/tcp` with `timeout 1` because
it can hang on WSL2. Source `process.sh` for lifecycle helpers and `nats.sh` for health/stream
helpers. Under `set -euo pipefail`, a skip helper that merely returns still falls through; use an
explicit `exit $?`. Use unique loop variables because Bash functions share variables unless
declared local.

### Publish retry rules

Retry only transient acknowledgement/connection states: `TimeoutError`, `NoRespondersError`,
`DrainTimeoutError`, `ConnectionReconnectingError`, and `StaleConnectionError`. Propagate
authorization failures, bad subjects, and unknown exceptions immediately. With defaults of three
attempts, 0.1-second exponential base delay capped at 2 seconds, 0.5–1.5 jitter, and a 5-second
per-attempt timeout, the worst-case budget is about 15.3 seconds. Preserve message identity if the
publish can be retried after an uncertain ACK.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Container DNS across hosts | Use Compose service names between machines | Names resolve only inside their container network | Use reachable Tailnet addresses or a deliberate leaf topology |
| Syntax-only health proof | Treat `compose config` as runtime evidence | It never starts or probes a container | Observe health and perform a behavioral round trip |
| File-wide auth grep | Search for authorization anywhere in a config | It can match the wrong nested block | Parse brace depth and test bad plus fixed fixtures |
| Optional CI validator | Guard validation on tool presence | A missing runner tool silently skips enforcement | Pin the tool and run the validator unconditionally |
| Defined-but-unused TLS helper | Add an SSL-context builder | No real connection consumes it | Find or add the narrow consumed connection boundary |
| Nested async entry point | Add a second `asyncio.run()` | It fails inside the existing event loop | Insert the preflight into `_run_with_signals()` |
| Shell-global PID | Kill a parent PID stored only in a variable | A forked test does not inherit that state | Persist PID and store directory in a port-keyed meta file |
| Fresh restart store | Relaunch with a new `mktemp --store_dir` | It silently loses JetStream state | Relaunch at the recorded store and assert the stream survives |
| TIME_WAIT listener theory | Wait out 2MSL before rebinding | A killed listener rebinds immediately | Measure first; kill the real PID and wait for exit |
| Catch-all publish retry | Retry every exception | Permanent auth, schema, and code failures repeat | Retry only named transient NATS errors |

## Results & Parameters

| Parameter | Value or rule |
| --- | --- |
| NATS client / monitoring / leaf | `4222` / `8222` / `7422` |
| Agamemnon / Nestor / Hermes | `8080` / `8081` / `8085` |
| Observability defaults | Prometheus `9090`, Grafana `3001`, Loki `3100`, exporter `9100` |
| Cross-host URLs | `NATS_URL=nats://<hub>:4222`; service URLs use reachable Tailnet IPs |
| Hermes native import | `PYTHONPATH=src` |
| Publish retry | 3 attempts; 0.1-second base; 2-second cap; 0.5–1.5 jitter; 5-second timeout |
| NATS meta file | `/tmp/hi-nats-${NATS_MONITOR_PORT}.meta`, containing PID and store directory |
| Kill completion fallback | 20 polls × 0.1 seconds when `wait` reports a non-child |
| Hermes task events | `task.updated`, `task.completed`, `task.failed`, `agent.*`; not `task.created` |

## Verified On

| Scope | Status | Evidence boundary |
| --- | --- | --- |
| Two-host, compose, launcher, and six-host cold-start deployments | verified-local | HomericIntelligence/Odysseus sessions from 2026-04-03 through 2026-05-03 |
| JetStream publish retry | verified-ci | ProjectHermes retry loop and settings integration |
| NATS authentication plan | unverified overall | Brace-depth validator alone was prototyped locally against bad/fixed fixtures |
| Grafana anonymous-access and NATS TLS runbooks | unverified | No container/runbook commands or CI were run |
| Telemachy mTLS plan | unverified overall | Selected source/API facts and insertion point were verified locally; no CI |
| NATS SIGKILL/restart implementation | verified-local | 15/15 unit tests, including 8/8 kill/restart/healthy cycles; CI not confirmed |

## References

- [Detailed cases and provenance](./homeric-crosshost-deployment-and-mesh-topology.notes.md)
- [Version history and superseded full content](./homeric-crosshost-deployment-and-mesh-topology.history)
- [nats-py](https://github.com/nats-io/nats.py)
- [NATS connection resilience](./nats-py-connection-resilience-patterns.md)
- [Transient-error retry](./retry-transient-errors.md)
