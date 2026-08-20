# HomericIntelligence Cross-Host Deployment and Mesh Topology — Notes

These notes retain project-specific cases and verification detail moved out of the retrievable
[skill](./homeric-crosshost-deployment-and-mesh-topology.md). The exact v1.11.0 main is preserved
once, in [history](./homeric-crosshost-deployment-and-mesh-topology.history); it is intentionally
not duplicated here.

## Case Index

| Case | Source | Verification at capture | Useful disposition |
| --- | --- | --- | --- |
| Cross-host compose, launchers, and cold-start | [Odysseus PR #117](https://github.com/HomericIntelligence/Odysseus/pull/117) | verified-local; publish retry separately verified-ci | Retain topology, ports, launcher, health, and retry decisions |
| NATS leaf/server authentication | [Odysseus issue #176](https://github.com/HomericIntelligence/Odysseus/issues/176) | unverified plan; validator prototype verified-local | Retain block-aware/fail-closed validation and shared-token risk |
| Distroless health check | [Odysseus issue #154](https://github.com/HomericIntelligence/Odysseus/issues/154) | unverified plan | Retain binary self-probe and runtime-health requirement |
| Grafana anonymous-access hardening | [Odysseus issue #206](https://github.com/HomericIntelligence/Odysseus/issues/206) | unverified plan | Retain health/provisioning assumptions as explicit blockers |
| NATS TLS operations runbook | [Odysseus issue #208](https://github.com/HomericIntelligence/Odysseus/issues/208) | unverified plan | Retain version-specific certificate/reload/API checks |
| Telemachy client-certificate mTLS | [Telemachy issue #304](https://github.com/HomericIntelligence/Telemachy/issues/304) | unverified overall; selected facts verified-local | Retain consumed connection boundary, async placement, and typed failure |
| NATS SIGKILL/restart | [Odysseus issue #328](https://github.com/HomericIntelligence/Odysseus/issues/328), dependency [PR #184](https://github.com/HomericIntelligence/Odysseus/pull/184) | verified-local implementation; CI not confirmed | Retain measured root cause and all process/state safeguards |

## Cross-Host Deployment Case

Observed project paths and launch details:

- `docker-compose.e2e.yml` plus `docker-compose.crosshost.yml` split a worker-side NATS,
  Agamemnon, and Hermes set from the control-side Nestor process.
- Native C++ services were built inside the declared pixi/conda environment; using the system
  compiler produced incompatible dependencies in the original sessions.
- Hermes used a `src` layout and required `PYTHONPATH=src` for direct native launch.
- Myrmidon launchers used `provisioning/Myrmidons/hello-world/main.py`; an assumed `main.cpp` was
  the wrong artifact.
- The six-host cold start used four Podman hosts, one native pixi host, and one Docker host. It
  verified reachability and service health locally, not as a reproducible CI topology.
- Agamemnon's observed API shape used `GET /healthz`, a team response with the ID at `.team.id`,
  and team-scoped task creation. Echo tasks required an external completion PATCH rather than an
  autonomous executor.

The launcher set covered install-worker, install-control, NATS, Agamemnon, Nestor, Hermes,
myrmidon, Argus, and the operator console. Treat those names as discovery hints: re-read the live
justfile and build tree before copying a path.

## NATS Authentication Planning Case

The original plan proposed credentials for both the client listener and leafnode path. Its most
valuable artifact was a failed-review correction, not a shipped configuration:

- A naïve awk parser terminated `leafnodes {}` at the closing brace of a nested `tls {}` block.
  The replacement brace-depth extractor stripped comments, counted braces, and was locally
  prototyped: the fixed fixture exited zero and the current fixture exited one.
- Both validator directions matter. A validator that always fails can appear to reject the bad
  fixture while also rejecting the fix.
- Unset environment substitution must be tested by rendering/testing the config with the token
  absent. Do not assume NATS fails closed, and do not skip the test when the binary is absent.
- The repository's CI did not invoke an existing `just validate-configs` recipe. Wiring a command
  into a justfile is not proof that CI runs it.
- `.gitignore` did not already contain the claimed NATS credentials/certificate exclusions.
  Inspect and add the intended patterns as part of the implementation.
- A shared token is acceptable only as an explicit bootstrap posture. Per-leaf credentials are
  required for individual revocation.

The full auth workflow remained unexecuted, so none of those configuration changes should be
reported as verified.

## Health and Observability Cases

### Distroless services

The proposed fix for a distroless app image was a binary `-healthcheck` mode that performs a local
`/healthz` request and exits 0/1. A Dockerfile or compose parse proves only syntax. Acceptance
requires building the actual image and observing it become healthy. This was planning-only.

### Grafana anonymous access

The proposed change disabled `GF_AUTH_ANONYMOUS_ENABLED`, removed the now-dead anonymous role, and
kept admin credentials environment-overridable. Two load-bearing claims were not exercised:

1. Grafana `/api/health` remains reachable without a session when anonymous access is disabled.
2. Provisioned datasources and dashboards still load after login-required mode starts.

Both need an actual container run; compose rendering is insufficient.

## NATS TLS Runbook Case

At capture, ADR-008—not the issue-cited ADR-009—was the extant NATS TLS ADR, and the NATS config
already contained TLS blocks. The earlier “credential-less/no TLS” premise was stale. A runbook
must rediscover that state before prescribing changes.

The proposed certificate lifecycle covered step-ca provisioning, restrictive key permissions,
zero-downtime rotation, and key-compromise replacement. None was executed. In particular, verify
against installed versions:

- exact `step` CLI flags and SAN handling;
- whether the running NATS version reloads certificates on SIGHUP or needs another signal/action;
- actual `/varz` keys that indicate TLS requirements;
- the repository's real runbook inventory rather than a hand-maintained index.

## Telemachy mTLS Case

Locally confirmed facts from the review rounds:

- No live `nats.connect()` existed in Telemachy; `_monitor_completion` polled Agamemnon over HTTP.
- Hermes defined `build_ssl_context()` but its publisher connection did not pass `tls=`. It was a
  defined-but-unused analogy, not a reference implementation.
- nats-py 2.14.0 exposed `tls`, `tls_hostname`, and `tls_handshake_first` on
  `nats.aio.client.Client.connect`; the module-level wrapper was the wrong object to inspect.
- `cryptography` and `trustme` were absent, `openssl` 3.6.2 was available, and root plus Telemachy
  ignore rules excluded PEM/key/certificate fixtures.
- `docs/runbooks/enable-nats-auth.md` and ADR-009 were absent; ADR-008 was the real TLS ADR.
- `cli.py` already used `_run_with_signals()` for the `run` command. The preflight insertion point
  was inside that coroutine after signal setup and before `AgamemnonClient`, avoiding a nested
  `asyncio.run()`.

The final plan required a real `connect_nats()` consumer as a documented fail-closed TLS
verification gate. It wrapped raw SSL/NATS exceptions in `NatsConnectionError`; the Typer CLI
printed an operator-facing message and exited 1. These were design decisions resolving review
findings, not newly executed behavior. Overall status remained unverified.

## NATS Restart Case

### Evidence evolution

The issue initially attributed rebind failures to monitor-port `TIME_WAIT`. A tight local
experiment started NATS on client/monitor ports 14299/18299, waited for health, sent SIGKILL, and
immediately relaunched on both ports. All 8/8 rebinds succeeded with no delay. This overturned the
kernel premise: a listening socket is released on process death; 2MSL applies to the active-close
endpoint of an established connection.

The actual failure crossed a process boundary:

- `e2e/run-ipc-tests.sh` launched each test with `bash "$script"` and exported ports but no PID.
- NATS started in the parent; the child sourced a fresh `_NATS_PID=""`.
- The child's kill was a no-op, so relaunch raced the still-live original process.

### Verified-local implementation facts

The final local implementation reported 15/15 unit tests, including an 8-iteration
kill/restart/healthy loop:

1. `start_nats_bg` wrote PID and store directory to
   `/tmp/hi-nats-${NATS_MONITOR_PORT}.meta`.
2. `nats_meta_pid()` and `nats_meta_store_dir()` provided cross-process reads.
3. `nats_kill()` sent SIGKILL and waited for exit; a non-child `wait` status used a bounded
   20-by-0.1-second `kill -0` fallback.
4. `wait_port_free` was wired before the restart loop and after each failed retry, but remained a
   diagnostic margin rather than the correctness gate.
5. Its `/dev/tcp` call used `timeout 1` to avoid WSL2/kernel hangs.
6. Skip blocks used explicit `exit $?` under `set -euo pipefail`.
7. The active A02 path required a non-empty metadata PID to avoid a standalone false pass.
8. `start_nats_bg_at <dir>` relaunched against the original JetStream store.
9. The test used unique loop variables because inner Bash functions could clobber `i`.
10. `nats-crash-reconnect.sh` sourced both lifecycle (`process.sh`) and NATS health (`nats.sh`)
    helpers.

Changed paths were `e2e/lib/process.sh`, `e2e/tests/fault/nats-crash-reconnect.sh`, and new
`e2e/tests/unit/test-nats-restart.sh`. CI, pixi shellcheck wiring, concurrent same-port metadata
behavior, and possible collision with parent PR #184 remained unconfirmed.

## Compaction Audit

- Retained in main: every distinct trigger; port/env/retry values; direct-versus-leaf decision;
  health-check runtime distinctions; block-aware auth validation; shared-token risk; TLS/mTLS
  insertion and exception behavior; the measured TIME_WAIT correction; all ten restart safeguards;
  and the verified/unverified boundaries.
- Moved here: project path inventories, session chronology, detailed review rounds, source issue/PR
  mapping, and expanded local evidence.
- Archived only in history: the complete v1.11.0 retrievable document and redundant worked prose.
