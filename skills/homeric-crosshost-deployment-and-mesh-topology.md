---
name: homeric-crosshost-deployment-and-mesh-topology
description: "Deploy and operate the HomericIntelligence mesh across multiple Tailscale hosts using NATS JetStream, compose overlays, and justfile launchers. Use when: (1) splitting the E2E stack across multiple physical hosts via compose overlay or per-component launchers, (2) bringing up Agamemnon/Nestor/Hermes natively or via containers on any new Tailnet host from cold state, (3) running hub+remote-worker topology for cross-host myrmidon dispatch, (4) configuring NATS connections (direct or leafnode) over Tailscale, (5) implementing NATS JetStream publish retry with exponential backoff, (6) debugging Hermes webhook event types, compose healthchecks, or podman rootlessport/DNS quirks."
category: architecture
date: 2026-05-19
version: "1.0.0"
user-invocable: false
history: homeric-crosshost-deployment-and-mesh-topology.history
tags:
  - cross-host
  - deployment
  - compose
  - tailscale
  - nats
  - jetstream
  - podman
  - docker
  - justfile
  - per-component
  - launcher
  - mesh
  - hermes
  - agamemnon
  - nestor
  - myrmidon
  - atlas
  - cold-start
  - retry
  - backoff
  - e2e
  - cpp20
  - homeric-intelligence
---

# HomericIntelligence Cross-Host Deployment and Mesh Topology

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-05-19 |
| **Objective** | Deploy and operate the HomericIntelligence mesh across multiple Tailscale hosts using NATS JetStream, compose overlays, justfile launchers, and resilient publish patterns |
| **Outcome** | Two-host and 6-host deployments validated; compose overlay, per-component launcher, hub+remote-worker, and cold-start patterns all confirmed working. NATS publish retry with jitter verified in CI. |
| **Verification** | verified-local (multiple Odysseus sessions 2026-04-03 to 2026-05-03) |
| **History** | [changelog](./homeric-crosshost-deployment-and-mesh-topology.history) |

## When to Use

- Splitting the HomericIntelligence E2E compose stack across multiple physical machines
- Configuring NATS connections (direct or leafnode) over Tailscale mesh networking
- Bringing up Agamemnon, Nestor, or Hermes natively (binary/uvicorn) or via podman on any Tailnet host from cold state
- Launching myrmidon Python workers across Tailnet hosts (fan-out or hub+remote-worker pattern)
- Adding justfile recipes that launch C++ binaries or delegate to submodule justfiles
- Choosing between compose overlay vs native binary vs per-component launcher deployment
- Implementing NATS JetStream publish retry with exponential backoff and jitter in Python
- Debugging cross-host service communication, NATS leafnode config, or podman networking issues

## Verified Workflow

### Quick Reference

```bash
# Compose overlay — start worker host
CONTROL_HOST_IP=<control-tailscale-ip> just crosshost-up $CONTROL_HOST_IP

# Compose overlay — start control host (Nestor native binary)
NATS_URL=nats://<worker-ip>:4222 <build-root>/ProjectNestor/ProjectNestor_server

# Per-component launchers (any host, any service)
just install-worker                                   # Worker: podman + tools
just install-control                                  # Control: C++ build chain + compile
just start-nats
just start-agamemnon NATS_URL=nats://worker-ip:4222
just start-nestor    NATS_URL=nats://worker-ip:4222
just start-hermes    NATS_URL=nats://worker-ip:4222
just start-myrmidon  NATS_URL=nats://worker-ip:4222 AGAMEMNON_URL=http://worker-ip:8080
just start-argus
just start-console   NATS_URL=nats://worker-ip:4222

# Hub+remote-worker topology (hermes=hub, epimetheus=remote worker)
just hermes-hub-up && just hermes-hub-test

# Single-host full E2E stack
podman compose -f docker-compose.e2e.yml up -d --build
just e2e-test

# Cross-host E2E validation (8 phases)
WORKER_HOST_IP=<worker-ip> just crosshost-test $WORKER_HOST_IP

# Verify NATS health
curl http://localhost:8222/varz    # monitoring (NOT port 4222)
curl http://localhost:8222/connz   # active connections
```

### Critical Binary Names and Paths

```
CORRECT:  control/ProjectAgamemnon/build/debug/ProjectAgamemnon_server
WRONG:    control/ProjectAgamemnon/build/debug/agamemnon

CORRECT:  control/ProjectNestor/build/debug/ProjectNestor_server
WRONG:    control/ProjectNestor/build/debug/nestor

CORRECT:  PYTHONPATH=src uvicorn hermes.server:app
WRONG:    uvicorn hermes.server:app     (no PYTHONPATH — module not found)
WRONG:    uvicorn hermes.main:app       (module does not exist)

CORRECT:  ~/.local/bin/nats-server -js  (use full path — not in PATH by default)
WRONG:    nats-server -js               (bare name, command not found on most hosts)

NATS:     port 4222 = client pub/sub;  port 8222 = HTTP monitoring
```

### Native Mesh Bringup (single host, pixi available)

```bash
# 1. NATS (binary NOT in PATH — use full path)
~/.local/bin/nats-server -js &

# 2. Agamemnon — build inside pixi for correct conda toolchain
pixi run bash -c "
  cd control/ProjectAgamemnon
  cmake -B build/debug -DCMAKE_BUILD_TYPE=Debug \
    -DProjectAgamemnon_ENABLE_CLANG_TIDY=OFF
  cmake --build build/debug
  ./build/debug/ProjectAgamemnon_server &
"

# 3. Nestor
pixi run bash -c "
  cd control/ProjectNestor
  cmake -B build/debug -DCMAKE_BUILD_TYPE=Debug
  cmake --build build/debug
  ./build/debug/ProjectNestor_server &
"

# 4. Hermes — src layout requires PYTHONPATH
cd infrastructure/ProjectHermes
pixi run bash -c "PYTHONPATH=src uvicorn hermes.server:app --host 0.0.0.0 --port 8085" &

# 5. Verify
curl -s http://localhost:8080/health    # {"service":"ProjectAgamemnon","status":"ok"}
curl -s http://localhost:8081/v1/health
curl -s http://localhost:8085/health
curl -s http://localhost:8222/varz | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print('connections:', d['connections'])"
```

### Multi-Host Cold-Start Strategy (up to 6 Tailnet Hosts)

| Host | Odysseus Present | Strategy | Special Notes |
| ------ | ---------------- | -------- | ------------- |
| titan, aeolus, athena | No | `gh repo clone` + podman containers | Agamemnon build ~5-10 min (Conan C++ deps) |
| artemis | Yes, pixi available | Native build inside `pixi run bash -c "..."` | Must use `-DProjectAgamemnon_ENABLE_CLANG_TIDY=OFF` |
| hephaestus | No | Clone fresh, native build | Nestor needs `-DCMAKE_EXE_LINKER_FLAGS='-lz'` |
| apollo | No | Python 3.7 — too old for Hermes | Use `docker run --network=host` for all services |

**Pre-check**: `ls ~/<project-root>` — clone via `gh repo clone` if missing.

```bash
# Podman container build (hosts without native toolchain)
gh repo clone HomericIntelligence/Odysseus ~/<project-root>
cd ~/<project-root> && git submodule update --init --recursive
podman build -t agamemnon control/ProjectAgamemnon/
podman run -d --name agamemnon --network=host agamemnon
```

**Hermes Dockerfile**: requires `prometheus_client` in pip install; use `HERMES_PORT=8085` (not 8080 — conflicts with Agamemnon). Fixed in PR #415.

### Compose Overlay Pattern for Cross-Host Splits

```yaml
# docker-compose.crosshost.yml (overlay on docker-compose.e2e.yml)
services:
  nestor:
    profiles: ["disabled"]     # runs on control host as native binary
  argus-exporter:
    environment:
      - NESTOR_URL=http://${CONTROL_HOST_IP}:8081
```

```bash
podman compose -f docker-compose.e2e.yml -f docker-compose.crosshost.yml up -d
```

**Disable-via-overlay pattern**: `profiles: ["disabled"]` is the correct way to exclude a service from an overlay without removing it from the base compose file.

### NATS Connection Strategy: Direct vs. Leaf Node

| Topology | Recommended | Reason |
| ---------- | ------------- | -------- |
| 2 hosts, 1 remote client | Direct connection | Zero additional complexity; Tailscale handles routing |
| 2+ hosts, multiple remote clients | Leaf node | Reduces WAN connections; local pub/sub for co-located services |
| Hub-and-spoke (many remotes) | Leaf nodes per spoke | Each spoke gets local NATS; leaf auto-reconnects |

**Leafnode config — critical**: leaf.conf must connect to port **7422** (leafnode listen port), **NOT** port 4222 (client port).

```hcl
# server.conf (hub)
leafnodes { port = 7422 }

# leaf.conf (spoke)
leafnodes {
  remotes [{ url: "nats-leaf://<hub-ip>:7422" }]
}
```

### Agamemnon API Shape (Confirmed)

```bash
# Health
curl -s http://localhost:8080/health
# Returns: {"service":"ProjectAgamemnon","status":"ok"}

# Create team — response wraps ID under .team.id
TEAM_ID=$(curl -s -X POST http://localhost:8080/v1/teams \
  -H "Content-Type: application/json" \
  -d '{"name":"my-team","description":"..."}' \
  | jq -r '.team.id')   # NOT .id

# Create task — team-scoped path (NOT /v1/tasks)
curl -s -X POST "http://localhost:8080/v1/teams/$TEAM_ID/tasks" \
  -H "Content-Type: application/json" \
  -d '{"name":"my-task","type":"echo","params":{}}'

# Complete task — echo tasks require external PATCH (no autonomous executor)
curl -s -X PATCH "http://localhost:8080/v1/teams/$TEAM_ID/tasks/<task_id>" \
  -H "Content-Type: application/json" \
  -d '{"status":"completed"}'
```

### Multi-Host Myrmidon Fan-Out

```bash
# On each reachable remote host — always use main.py (Python), NOT main.cpp
NATS_URL=nats://<controller-tailscale-ip>:4222 \
  nohup python3 provisioning/Myrmidons/hello-world/main.py \
  > /tmp/hello-myrmidon.log 2>&1 &

# Verify cross-host NATS connection count
curl -s http://<hub-ip>:8222/varz | jq .connections
```

### NATS JetStream Publish Retry with Exponential Backoff

```python
import asyncio, json, random, time, nats

_RETRYABLE_PUBLISH_ERRORS = (
    nats.errors.TimeoutError,
    nats.errors.NoRespondersError,
    nats.errors.DrainTimeoutError,
    nats.errors.ConnectionReconnectingError,
    nats.errors.StaleConnectionError,
)

async def publish_with_retry(js, subject, message, retries=3, base_delay=0.1, timeout=5.0):
    last_exc = None
    for attempt in range(retries):
        try:
            return await js.publish(subject, message, timeout=timeout)
        except _RETRYABLE_PUBLISH_ERRORS as exc:
            last_exc = exc
            if attempt < retries - 1:
                delay = min(base_delay * (2 ** attempt), 2.0) * random.uniform(0.5, 1.5)
                await asyncio.sleep(delay)
    raise last_exc
```

Retry budget defaults (`retries=3`, `base_delay=0.1s`, `timeout=5.0s`): ~15.3s worst case.
Non-retryable errors (`AuthorizationError`, `BadSubjectError`, generic `Exception`) propagate immediately.

### Host-Network Workaround (rootlessport absent)

```bash
# SYMPTOM: start-stack.sh hangs at `podman wait --condition=healthy`
# ROOT CAUSE: rootlessport absent — bridge networking never binds host ports
kill $(cat /run/user/$(id -u)/containers/networks/aardvark-dns/aardvark.pid 2>/dev/null) 2>/dev/null || true
podman run -d --name hi-nats --network=host nats:alpine -js -m 8222
# When using --network=host, Grafana datasources must use localhost, not service names
```

**Grafana on air-gapped hosts** — add to grafana service to prevent startup hang:

```yaml
environment:
  - GF_ANALYTICS_REPORTING_ENABLED=false
  - GF_ANALYTICS_CHECK_FOR_UPDATES=false
  - GF_ANALYTICS_CHECK_FOR_PLUGIN_UPDATES=false
```

### Compose Healthchecks (Dual-Runtime: podman-compose 1.5.0 + Docker Compose v2/v5)

```yaml
# CORRECT — YAML string form; Docker Compose v2 and v5 both treat it as CMD-SHELL
healthcheck:
  test: "wget -qO- http://localhost:8080/v1/health 2>/dev/null || exit 1"
  interval: 5s
  timeout: 3s
  retries: 10
  start_period: 10s

# For nats:alpine (BusyBox wget rejects combined -qO- flag)
healthcheck:
  test: "wget -q -O /dev/stdout http://localhost:8222/healthz 2>/dev/null | grep -q ok"
```

### After NATS Restart

Agamemnon and Nestor do NOT auto-reconnect after NATS restarts. Always kill and restart them:

```bash
pkill -f ProjectAgamemnon_server || kill $(pgrep -f ProjectAgamemnon_server)
pkill -f ProjectNestor_server    || kill $(pgrep -f ProjectNestor_server)
```

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Leaf.conf to port 4222 | Connected leaf node to NATS client port | Leaf nodes require dedicated leafnode listener port 7422 | Always use port 7422 for leafnode remotes, not 4222 |
| `agamemnon` as binary name | Called `./build/debug/agamemnon` | Binary is `ProjectAgamemnon_server` — exact CMake target name | Check `ls build/debug/` to confirm binary name |
| `nestor` as binary name | Called `./build/debug/nestor` | Binary is `ProjectNestor_server` — exact CMake target name | Always use `ProjectNestor_server` |
| Hermes without PYTHONPATH | `uvicorn hermes.server:app` with no env prefix | src layout — Python cannot find `hermes` module | Always prefix `PYTHONPATH=src` |
| `uvicorn hermes.main:app` | Used `hermes.main:app` entry point | Module is `hermes.server:app`; `hermes.main` does not exist | Always use `hermes.server:app` |
| `nats-server` without full path | Called bare `nats-server` | `~/.local/bin` not in PATH on most remote hosts | Always use `~/.local/bin/nats-server` |
| NATS monitoring on port 4222 | `curl localhost:4222/varz` | Port 4222 is client port; monitoring HTTP is on 8222 | NATS monitoring: port 8222; client pub/sub: port 4222 |
| NATS via podman (slirp4netns) | Podman container NATS without rootlessport | slirp4netns remaps 4222 to ephemeral port invisible to external clients | Run NATS as native binary when rootlessport absent |
| cmake without pixi on artemis | Ran cmake directly without `pixi run bash -c` | pixi conda toolchain not activated; wrong sysroot | Run cmake inside `pixi run bash -c "..."` |
| cmake without `_ENABLE_CLANG_TIDY=OFF` | Default cmake on artemis | clang-tidy sysroot mismatch causes build failure | Always pass `-DProjectAgamemnon_ENABLE_CLANG_TIDY=OFF` on conda sysroot hosts |
| Nestor without `-lz` on hephaestus | Standard cmake for Nestor | OpenSSL zlib dep not automatically linked | Pass `-DCMAKE_EXE_LINKER_FLAGS='-lz'` on hephaestus |
| `POST /v1/tasks` Agamemnon | Used flat `/v1/tasks` path | Returns 404 — endpoint is team-scoped only | Correct: `POST /v1/teams/<teamId>/tasks` |
| `POST .../complete` task completion | Used POST complete endpoint | Returns 404 — endpoint does not exist | Use `PATCH /v1/teams/<id>/tasks/<id>` with `{"status":"completed"}` |
| `jq -r '.id'` on team response | Extracted `.id` directly | Team ID is nested: `{"team": {"id": "..."}}` | Always use `.team.id` |
| Hermes with `HERMES_PORT=8080` | Default port for Hermes container | Conflicts with Agamemnon on 8080 | Set `HERMES_PORT=8085`; Agamemnon owns 8080 |
| Hermes Dockerfile without `prometheus_client` | Built without prometheus_client | Hermes imports it at startup; container crashes | Add `prometheus_client` to pip install (PR #415) |
| hello-myrmidon `main.cpp` | Used C++ file in hello-world | Requires build step; Python `main.py` is the worker | Always use `main.py`; it subscribes via JetStream push consumer |
| `worker.py` in start-myrmidon recipe | Referenced non-existent worker.py | File does not exist — correct file is `main.py` | Use `main.py`; subscribes to `hi.myrmidon.hello.>` |
| `task.created` to Hermes webhook | Sent `task.created` event | Hermes `_TASK_EVENTS` allowlist: `task.updated`, `task.completed`, `task.failed`, `agent.*` only — silently dropped | Always use `task.updated` for test webhook validation |
| Submodule scripts as-is | Used provisioning/Myrmidons scripts | Submodule pinned to old commit with `aim_*` functions targeting ai-maestro | Verify submodule pins match standalone checkouts after migrations |
| Monolithic e2e-all launcher | Single `just e2e-all` starts everything | Defeats multi-machine flexibility; per-component granularity needed | Individual launchers compose better for distributed deployment |
| `nats:latest` for healthchecks | Used `nats:latest` container | `nats:latest` is distroless — no shell, wget, or curl | Use `nats:alpine` for compose healthchecks |
| CMD-SHELL array healthcheck on podman-compose 1.5.0 | `["CMD-SHELL", "wget ..."]` format | podman-compose 1.5.0 rejects this array format | Use `["CMD", "sh", "-c", "wget ..."]` or YAML string form |
| CMD/CMD-SHELL array on Docker Compose v5 | JSON array `["CMD","sh","-c","full cmd"]` | Docker Compose v5 splits 4th element on spaces — `sh -c wget` runs wget alone | Use YAML string `test: "cmd"` — both v2 and v5 treat it as CMD-SHELL without splitting |
| `wget -qO-` in nats:alpine | Combined short flag with BusyBox wget | BusyBox wget rejects `-qO-`; prints usage and exits 1 | Use `-q -O /dev/stdout` (space-separated, explicit path) |
| Sleeping after final retry attempt | `if attempt < retries` guard | Adds unnecessary latency after retries exhausted | Guard with `if attempt < retries - 1` |
| Catching bare `Exception` in retry | Catch-all in retry loop | Hides non-retryable bugs as transient failures; burns retry budget | Only catch explicit `_RETRYABLE_PUBLISH_ERRORS` tuple |
| No restart after NATS port change | Left Agamemnon/Hermes running | Processes lose NATS connection and do not auto-reconnect | Restart both services after NATS is stable |
| Assuming Odysseus present on all hosts | Skipped `gh repo clone` step | Only some hosts had a clone; others needed fresh clone | Pre-check `ls ~/<project-root>` — clone if missing |
| `podman cp` to overwrite read-only bind-mount | Tried `podman cp` on `:ro` Prometheus config | Volume is `:ro` — copy fails with "device or resource busy" | Write resolved-IP config to host bind-mount source, then `/-/reload` |
| Forking Atlas branch from feature branch | Created feat branch from `feat/issue-22-ci-hardening` | Picked up 12 extra CI commits; PR not rebased to main | Always fork from `main`; check base before `git worktree add` |

## Results & Parameters

```yaml
# Service ports
services:
  nats:    client=4222, monitoring=8222
  agamemnon: 8080
  nestor:    8081
  hermes:    8085  # NOT 8080 -- conflicts with Agamemnon
  prometheus: 9090 (or 19090 if conflicting)
  grafana:   3001 (or 13001)
  loki:      3100 (or 13100)
  argus-exporter: 9100

# Key environment variables
env_vars:
  NATS_URL:         "nats://<worker_ip>:4222"
  AGAMEMNON_URL:    "http://<worker_ip>:8080"
  NESTOR_URL:       "http://<control_ip>:8081"
  CONTROL_HOST_IP:  "<Tailscale IP of the control host>"
  WORKER_HOST_IP:   "<Tailscale IP of the worker host>"
  PYTHONPATH:       "src"   # required for Hermes

# NATS publish retry defaults (Python/nats-py)
nats_publish_retry:
  retries: 3
  base_delay: 0.1s          # doubles each attempt; cap at 2.0s
  jitter: "uniform(0.5, 1.5)"
  publish_timeout: 5.0s
  worst_case_total: ~15.3s

# Hermes supported webhook event types (_TASK_EVENTS allowlist)
hermes_event_types:
  - task.updated
  - task.completed
  - task.failed
  - "agent.*"
  # NOT supported (silently dropped): task.created

# Justfile recipes (per-component launchers)
recipes:
  install-worker:   "e2e/doctor.sh --role worker --install + submodule init"
  install-control:  "e2e/doctor.sh --role control --install + build Agamemnon/Nestor"
  start-nats:       "podman run -d --replace nats:alpine -js -m 8222"
  start-agamemnon:  "NATS_URL=... <build-root>/ProjectAgamemnon/ProjectAgamemnon_server"
  start-nestor:     "NATS_URL=... <build-root>/ProjectNestor/ProjectNestor_server"
  start-hermes:     "delegates to infrastructure/ProjectHermes justfile"
  start-myrmidon:   "NATS_URL=... python3 provisioning/Myrmidons/hello-world/main.py"
  start-argus:      "delegates to infrastructure/ProjectArgus justfile"
  start-console:    "python3 tools/odysseus-console.py"
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| HomericIntelligence/Odysseus | 2026-04-03 Cross-host compose overlay | Two-host deployment: epimetheus (worker) + control host; full 6-phase validation PASS 2026-04-06 |
| HomericIntelligence/Odysseus | 2026-04-04 Per-component launchers | 9 justfile recipes; commit 82742b7 on feat/crosshost-e2e-pipeline |
| HomericIntelligence/Odysseus | 2026-04-20 Hermes-hub topology | Hub+remote-worker scripts written; validated 2026-04-27 in Atlas session |
| HomericIntelligence/Odysseus | 2026-04-21 E2E compose pipeline | 10-container stack; all 7 phases passing on podman + docker; PR #117 |
| HomericIntelligence/Odysseus | 2026-04-24 NATS publish retry | Full retry loop with jitter verified in CI (ProjectHermes) |
| HomericIntelligence/Odysseus | 2026-05-03 Atlas 6-host cold-start | 6 hosts started (4 podman, 1 pixi native, 1 docker); Agamemnon API confirmed |
