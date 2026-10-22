---
name: comet-live-readonly-release-status-probe
license: BSD-3-Clause
description: "Probe a live Comet deployment read-only and produce a green/orange/red status matrix for components and release stages. Use when: (1) validating a deployed Comet release without mutating cluster state, (2) building per-component health evidence for `comet` / `comet-admin` / `comet-service`, (3) deciding whether a live failure needs a new issue or a comment on an existing owner, (4) the environment mixes a public client with operator tooling and selector state can be poisoned."
category: testing
date: 2026-10-22
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [comet, live-probe, read-only, status-matrix, deployment-context, sysexits, "401", "408", manifest-perms, issue-triage]
---

# Comet Live Read-Only Release Status Probe

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-10-22 |
| **Objective** | Assess a live Comet release with read-only commands only, and deliver a per-component and per-release-stage green/orange/red matrix backed by captured evidence and issue cross-references. |
| **Outcome** | Operational. A full three-CLI probe plus release-stage review completed with zero mutations; two new issues filed, twelve existing issues enriched. |

The core discipline: separate the two selector worlds before you run anything.
The public client resolves its target from the gateway. The operator CLIs
resolve from a deployment-context path. Mixing the two environments — or a
stale context path — produces failures that look like product defects but are
probe defects.

## When to Use

Use this skill when one of these conditions applies:

- You must validate a deployed Comet release without changing cluster state
  (no submit, cancel, seal, activate, migrate, or serve paths).
- You need a green/orange/red matrix across `comet`, `comet-admin`,
  `comet-service`, and release stages, with evidence an issue author can use.
- The shell environment carries ambient Comet variables whose values may be
  stale (for example a `COMET_DEPLOYMENT_CONTEXT` that points at a retired
  release).
- A live gateway is available and you must classify 401/404/408 responses and
  designed nonzero exits as either defects or intended behavior.
- Findings may already have owning issues, and filing strategy (new issue vs
  evidence comment) matters.

For review of CLI behavior without any cluster access, use
[comet-cli-offline-review-evidence-reporting](comet-cli-offline-review-evidence-reporting.md)
instead; it treats live probing as out of scope. For ordinary-user credential
failures found during a probe, the sibling skill
`comet-user-credential-lifecycle-diagnosis` covers the lifecycle classification.

## Verified Workflow

### Quick Reference

Three environment rules prevent the most common probe defects:

```bash
# 1. Public client: start from a clean selector environment.
env -u COMET_DEPLOYMENT_CONTEXT comet status

# 2. Operator CLIs: pass an explicit canonical context path (symlink-free).
CTX=$(readlink -f <operator-venv>/lib/python3.12/site-packages/comet/data/deployment/contexts/<deployment-id>.yaml)
comet-admin --deployment-context "$CTX" status

# 3. Manifest reads: copy the manifest tree into a private probe dir first.
install -d -m 0700 "$HOME/.comet-status-probe"
install -m 0600 /path/to/manifest "$HOME/.comet-status-probe/"
```

### Suggested Approach

1. Define the mutation boundary in writing before the first command. List the
   forbidden verb classes (submit, cancel, seal, activate, migrate, serve,
   approve) and the allowed classes (status, show, list, validate, diff,
   whoami, smoke, chat). Note that `smoke` and `chat` do not mutate cluster
   state but do send inference traffic; include them only when the requester
   accepts that.
2. Locate the deployed components from the deployment root: the public client
   shim under `<deployment-root>/prod/client/current`, the operator venv under
   `<operator-root>/prod/venv/current`, and the deployment context file inside
   the operator venv's site-packages. Record the resolved release SHA; every
   later claim binds to it.
3. Establish selector hygiene per CLI:
   - Public client: run with `env -u COMET_DEPLOYMENT_CONTEXT`. An ambient
     value that points at a retired release poisons client resolution.
   - `comet-admin` and `comet-service`: pass `--deployment-context` with a
     canonical path from `readlink -f`. A path through the `current` symlink
     defeats guards that compare resolved locations, and some surfaces behave
     differently per level (a group-level `--help` can need a context where a
     leaf `--help` does not).
4. Run the read-only matrix per CLI and capture, for every command: the exact
   command line, exit code, elapsed time, and the saved raw output. Keep one
   session evidence directory with raw outputs, a results TSV, and one
   authoritative report file.
5. Handle privileged-artifact guards explicitly. `release show/validate/diff`
   refuse manifests that fail the 0700-directory / 0600-file privacy guard;
   stage copies under a private probe directory instead of relaxing the source
   tree or reading as the owner.
6. Classify live HTTP semantics before calling anything a defect:
   - `401`: authentication rejected. Distinguish a missing key from an
     un-admitted key (see the credential-lifecycle sibling skill); both print
     401.
   - `404`: route or pool unknown to this gateway generation; re-check naming
     against `comet status`.
   - `408` / timeouts: usually a pool that is offline or recycling, not a dead
     gateway; confirm gateway liveness with `comet status` live-count fields.
   - Exit codes 69 (`EX_UNAVAILABLE`) and 75 (`EX_TEMPFAIL`): designed CLI
     rejection contracts, not crashes. Record them as behavior, and only flag
     a defect when the contract is violated (for example raw tracebacks, or
     exit 0 on an operation that did not complete).
7. Expect runtime drift during the session. Pool live-counts change as
   replicas recycle. Timestamp each observation, and re-probe the specific
   value before you write a final claim that depends on it.
8. Score each component green (all read-only classes behave to contract),
   orange (degraded with a usable workaround), or red (a designed path fails).
   Score release stages the same way: tag/publish, cutover, serving health,
   and open follow-ups.
9. For every non-green finding, search the tracker before filing. When an
   owning issue exists, add a bounded evidence comment (command, exit, elapsed,
   key output) instead of opening a duplicate. File a new issue only for an
   unowned defect. Cross-link every matrix row to its issue or to the current
   release verification.

### Degraded Conditions

- No `py-spy` / `strace` permissions for a suspected hang: use
  `/proc/<pid>/wchan` and the fd list; timed `stat` excludes mount stalls.
- Operator-only paths block unprivileged accounts: probe what the account can
  reach and record the permission boundary as the finding, not as a probe
  failure.
- `comet status` unreachable: fall back to the published `status.json` /
  `gateway.json` metadata (mtime and contents) as the liveness signal, and
  mark dependent probe rows as not run, not red.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Admin probe without explicit context | `comet-admin status` with no `--deployment-context` | Resolution failed: the CLI had no deployment binding in that environment | Operator CLIs need an explicit context flag; do not rely on ambient state |
| Client probe with ambient context | `comet smoke` with a stale `COMET_DEPLOYMENT_CONTEXT` inherited from the operator shell | Client resolution followed a retired release path and failed until the variable was unset | Public-client runs start from `env -u COMET_DEPLOYMENT_CONTEXT`; keep the two selector worlds separate |
| Manifest read from a plain copy | Copied a release manifest into a shared temp dir and ran `release show` | The privacy guard refused: manifests require 0700 directories and 0600 files | Stage probe copies with `install -d -m 0700` / `install -m 0600`; never relax the source |
| Context path through `current` symlink | Passed `--deployment-context` under the `.../current/...` symlink | Path-sensitive behavior resolved inconsistently until the canonical path was used | Canonicalize with `readlink -f` once, store it, reuse it for the whole session |
| Reading 408 as a gateway outage | Classified pool request timeouts as a gateway defect in an early matrix draft | `comet status` showed the gateway up with zero live replicas in that pool; the 408 was designed tempfail semantics | Check gateway liveness and per-pool live counts before classifying any timeout |

## Results & Parameters

### Configuration

Probe skeleton that produced the verified matrix:

```yaml
session_evidence_dir: "<session-dir>"     # raw outputs, results TSV, one report
selectors:
  public_client: "env -u COMET_DEPLOYMENT_CONTEXT <client-shim>"
  operator_clis: "--deployment-context $(readlink -f <context-yaml>)"
boundary:
  forbidden: [submit, cancel, seal, activate, migrate, serve, approve]
  allowed: [status, show, list, validate, diff, whoami, smoke, chat]
manifest_guard:
  probe_dir_mode: "0700"
  manifest_mode: "0600"
scoring:
  green: "all read-only classes behave to contract"
  orange: "degraded with a usable workaround"
  red: "a designed path fails (traceback, refusal, wrong terminal state)"
drift_control: "timestamp every observation; re-probe values a final claim needs"
```

### Expected Output

- One results matrix per CLI (green/orange/red per command class) and one per
  release stage, each row bound to saved raw evidence.
- Zero commands from the forbidden list executed; the boundary is checkable
  from the captured command log.
- Every non-green row terminates in a new issue or an evidence comment on an
  existing owner, with the link recorded in the matrix.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| LLM360/comet | m2 production, release v0.2.3 / `69db2296`, 2026-10-22, operator account; client / admin / service matrix plus release-stage review | [notes.md](comet-live-readonly-release-status-probe.notes.md) |

## References

- [LLM360/comet#2878 — `comet-service` group `--help` traceback without a context](https://github.com/LLM360/comet/issues/2878)
- [LLM360/comet#2879 — `comet-admin logs` fails for an operator](https://github.com/LLM360/comet/issues/2879)
- [LLM360/comet#2709 — public client misreports reasoning-consumed responses as gateway errors](https://github.com/LLM360/comet/issues/2709)
- [LLM360/comet#2106 — `--deployment-context` rejects documented `current/` paths; selector friction](https://github.com/LLM360/comet/issues/2106)
- [LLM360/comet#2783 — viewer ingest service cannot authenticate after lane credential rotation; ingest routes 500](https://github.com/LLM360/comet/issues/2783)
- [comet-cli-offline-review-evidence-reporting](comet-cli-offline-review-evidence-reporting.md) — offline counterpart; dedupe and evidence-comment discipline
- [debugging-openai-chat-null-content-reasoning-shape](debugging-openai-chat-null-content-reasoning-shape.md) — the empty-content finding's existing diagnosis
