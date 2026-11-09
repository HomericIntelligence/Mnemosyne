---
name: comet-source-lane-revision-rotation
license: BSD-3-Clause
description: "Rotate a Comet canonical development or main source lane end to end — stage, operator, records, and gateway generation — through its documented refusal ladder. Use when: (1) `python3 -m comet.source_bootstrap` refuses a re-stage with 'the selected source pointer conflicts' or 'the source runtime conflicts with the existing record', (2) `comet-service operator-stop` refuses with 'no process path names the expected release' or 'the release layout is not known', (3) `comet-admin gateway restart` or `gateway bootstrap-reconcile` refuses with `deployment_context_drift` or `the public gateway does not match the selected context`, or (4) `gateway keeper` prints `skipped one pass: the accounting observation of job <id> failed: ValueError` on every pass."
category: tooling
date: 2026-11-09
version: "1.0.0"
user-invocable: false
tags: [comet, source-runtime, source-lane, revision-rotation, staging, operator, gateway-keeper, records-aside, dev-lane, domain-bootstrap]
---

# Comet Source-Lane Revision Rotation

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-09 |
| **Objective** | Move a canonical development or main source lane — its staged control environment, operator, and gateway generation — to one newer pinned revision and leave it live and consistent with no deleted state. |
| **Outcome** | Operational. One rotation playbook handles the full refusal ladder: the stage refuses to rotate, the typed operator stop does not cover the source-venv layout, the operator must roll over with the control identity of its build, the in-allocation gateway restart cannot retire across a revision change, and one stale-record-aside repair frees the keeper and the fresh submission. The lane ends with `control_revision` equal to the pinned revision, one active gateway generation, and the keeper clean. |

This lesson covers lanes whose active runtime is a **source runtime**
(`source-runtime.json`, `venv/sources/<revision>`, `venv/current`), not a
stack release (`stack-release.json`, `venv/releases/<revision>`). Their
rotations differ. Rotation of release lanes is covered by the release
procedures, the publish-without-activation flow, and the cutover runbooks.

## When to Use

1. A re-stage through `python3 -m comet.source_bootstrap` refuses early with
   `the selected source pointer conflicts with this bootstrap`, or later with
   `the source runtime conflicts with the existing record` (or
   `the existing source installation conflicts with the stage` after an
   interrupted attempt).
2. The operator of the lane must roll onto the new build and
   `comet-service operator-stop --expected-release <sha>` refuses with
   `No process path names the expected release <sha>. The release layout is
   not known, so use the documented manual procedure.`
3. `comet-admin gateway restart` ends with `gateway reload rollback failed` or
   refuses; `comet-admin gateway bootstrap-reconcile` refuses with `the exact
   scheduler identity proof failed`. The message classes are
   `deployment_context_drift` (`expected context ID ctX..., observed ctY...`);
   the lane keeps serving the old generation.
4. After the old generation is gone, `comet-admin gateway up` refuses with
   `the public gateway does not match the selected context`, or the gateway
   keeper prints `gateway keeper skipped one pass: the accounting observation
   of job <id> failed: ValueError` on every pass.

## Verified Workflow

### Quick Reference

```text
RE-STAGE    move `venv/current` and `source-runtime.json` -> labeled-aside, never delete
            run comet.source_bootstrap cleanly (fresh pointer + record)
OPERATOR    kill the watchdog session (TERM forwards; watchdog exits); start it again
            (the same command line resolves `venv/current` -> the new build)
GENERATION  in-allocation restart refused? -> the expected branch across a revision change
            cancel the old allocation with the fleet owner
            gateway-state/current.json, stack-observed/gateway.json,
            public gateway.json, public status.json, gateway-control/*.active-release
            -> one labeled records-aside directory, never delete
            comet-admin gateway up -> one fresh submission -> blue activation
```

### Suggested Approach

1. **Rotate the record and pointer first.** The stage writes only a virgin
   lane: `venv/current` must point at the new source revision or be absent,
   and no `source-runtime.json` may exist. First move both to one clearly
   labeled aside directory (for example adjacent to the deployment root,
   named with the old revision and the date). Never delete: renamed records
   stay traceable, and the verbose guard paths (`_reject_unexpected_venv_links`,
   `publish_source_runtime`, `install_source_prefix`) verify the tree contents
   as long as only the approved placeholders are missing. An interrupted
   earlier attempt leaves a partial `venv/sources/<revision>` whose immutable
   mode rejects later inventory confirms; re-widen the tree (`chmod -R u+w`)
   and remove it before the clean re-run.
2. **Build the new stage cleanly.** `python3 -m comet.source_bootstrap
   --deployment-context <abs registered context> --source <clean checkout> --python-prefix <shared python> --uv <uv> --smg-image <cluster smg image>`.
   It runs under an exclusive transition guard: it installs
   `venv/sources/<rev>` (immutable, verified by the trusted release checker),
   writes the new `source-runtime.json` (0600, with `source_sha`, the source
   tree hash, and the smg image digest), and selects `venv/current -> sources/<rev>`.
   Conditions that the build check enforces and that the rotation must honor:
   the checkout matches the new revision and is perfectly clean (even ignored
   files fail it), the staging umask is 022 (group-writable entries fail an
   inventory policy), and the context argument is the absolute canonical
   packaged path (a relative path is refused).
3. **Roll the operator onto the control identity of its new build.** The
   context identity changes with the source revision even when the registered
   context YAML bytes are identical (the identity derives the runtime-control
   component digests, not the YAML alone). An operator built from revision A
   refuses requests against the staged B context with a context mismatch.
   For a source release the typed stop does not apply: pass `--expected-release`
   and the identity proof answers only for `venv/releases` layouts. The
   documented manual path: kill the watchdog session (the watchdog forwards
   SIGTERM to the service child, waits for its exit, and exits itself; the
   session ends cleanly), confirm the heartbeat file stops advancing and the
   socket is stale, then start the identical watchdog command so the child
   launches from `venv/current` — now the new build. Verify the heartbeat
   advances and the startup lines show the new pid.
4. **Expect the in-allocation handoff to refuse across a revision change.**
   `comet-admin gateway restart --wait` starts a new candidate, but the mark-down
   of the old generation runs a retirable-job proof against the job's stored
   identity (context id and source SHA from revision A) and refuses with
   `deployment_context_drift`. The rollback runs, and the old generation keeps
   serving healthy. `comet-admin gateway bootstrap-reconcile` hits the same
   proof on the `live` job (`the exact scheduler identity proof failed`). These
   are fail-closed protections against cross-identity lifecycle operations,
   not data damage.
5. **Reset the generation with a fleet-owner cancel and one records-aside
   move.** The lane owner cancels the old gateway allocation. Then every gate
   changes to its intended branch: `gateway up` reads stale records. Three
   record classes stop it with their own closed fail:
   - **private**: `gateway-state/current.json` — the typed reader answers
     `deployment has no active source or release runtime` is wrong; the branch
     is a stale lifecycle record checked with the drift class, refused everywhere.
   - **observed**: `stack-observed/gateway.json` — a mismatched observed gateway.
   - **public**: `<public deployment root>/gateway.json` and `status.json` —
     an existing foreign, malformed, or linked record keeps the fail-closed rule,
     so `gateway up` ends with `the public gateway does not match the
     selected context`.
   - **receipt**: `gateway-control/*.<job>.active-release` — every later
     observation error message `keeper` logs as `skipped one pass` per pass.
   Move **all of them** to one labeled records-aside directory on the same
   store (rename; keep every byte). The _records never authorize a lifecycle
   operation_ rule caps this repair: node placement, admission, and scheduler
   ownership do not depend on them; they are traceability writes that a new
   generation rewrites during activation. With no records left,
   `comet-admin gateway up` retires nothing and submits one fresh gateway
   generation; after the cold start it activates and republishes every record
   above with the new identity.
6. **Verify the keeper heals on the healthy observation.** The keeper stands
   down only on its designed conditions: one received live-job observation, a
   deliberate down, or three consecutive failed submissions. A live, healthy
   new generation makes observations successful and returns the state to
   `consecutive_failures: 0`, `pending_retry: false`, `last_submitted_job_id`
   on the new record. If the keeper still skips passes after the new
   activation, a record mismatch remains — look for the same error line again
   before you try any new move.
7. **Verify the terminal assertions.** `comet-admin ... status` reports
   `control_revision` equal to the pinned revision and the new generation with
   the new node and port; `curl <gateway>/health` returns HTTP 200; the public
   `gateway.json` and `status.json` carry the new generation and the pinned
   source SHA; `squeue` shows no `comet-donate-*` jobs; and a healthy lane
   needs no operator restarts (`serve.log` holds one start per start).

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Rotate the revision by running `comet.source_bootstrap` again without moving anything. | Refused instantly by the create-style pointer preflight (`the selected source pointer conflicts`). The publication equality check refused next (`the source runtime conflicts with the existing record`). | The stage builds a virgin lane, not a rotation. Move pointer and record aside first, never delete. | Source-stage rotation always begins with the pointer and record moved to one labeled aside directory. |
| Roll the operator with `comet-service operator-stop --expected-release <sha>`. | Refused: `No process path names the expected release ... The release layout is not known, so use the documented manual procedure.` | The typed release identity proof covers only `venv/releases`. | A source-lane operator rolls with the watchdog-session kill and the identical watchdog restart, never with the typed stop. |
| Swap the generation across a revision with `gateway restart`. | The mark-down refused with `deployment_context_drift` (`expected ctX..., observed ctY...; expected source_sha A, observed B`). The rollback finished and the old generation kept serving. | The cross-revision retire-by-drift wall is fail-closed by design. | Reset with a fleet-owner cancel and a records-aside move; the fresh submission activates with its write path intact. |
| Revert the records to the new build with `gateway bootstrap-reconcile`. | Refused: `the exact scheduler identity proof failed` because the live job carried the old revision as its worker identity. | The reconcile of a live job obeys the same identity proof. | The typed reconcile corrects nothing after a revision change. |
| Wait for the gateway keeper to repair the mismatch alone. | `gateway keeper skipped one pass: the accounting observation of job <id> failed: ValueError` printed once per pass, forever. | The keeper's designed off-state needs one valid live-job observation, and the proof itself failed. | The keeper's skip-empty loop ends only when a coherent recorded identity exists again, after the records-aside move. |
| Start once before the stale public record is gone (`gateway up`). | Refused with `the public gateway does not match the selected context`. | An existing foreign, malformed, or linked public record keeps the fail-closed rule. | The public record must go with the stale set; the fresh generation republishes a coherent one during activation. |

## Results & Parameters

```yaml
rotation:
  moves:
    pointer_and_record:
      - "mv <admin>/venv/current <labeled-aside>"
      - "mv <admin>/source-runtime.json <labeled-aside>"
    stale_generation_records:
      - gateway-state/current.json
      - stack-observed/gateway.json
      - "<public deployment root>/gateway.json"
      - "<public deployment root>/status.json"
      - gateway-control/*.active-release
    keep_logically: rename, never delete
  stage:
    install: venv/sources/<revision>
    record: source-runtime.json (0600)
    select: venv/current -> sources/<revision>
  operator:
    roll: watchdog session kill + identical restart command
    proof: heartbeat advances, one pid, listening line on one socket
  generation:
    submit_after: fleet-owner cancel of the old allocation + records-aside
    activate: blue candidate activation
    keeper_heals: consecutive_failures==0 and pending_retry==false
verification:
  control_revision: equals pinned revision
  gateway_health: "curl <gateway>/health -> 200"
  public_records: name the new generation and the pinned source SHA
  donate_jobs: zero  # when a node-donation opt-in applies to the lane
```

### Expected Output

- The lane executes one request flow at the pinned revision: operator,
  gateway progression, and one unchanged serving read against its endpoint.
- `comet-admin status` and the public `gateway.json` / `status.json` show the
  same new generation and the same new source SHA.
- The operator audit names its accepted requests again, and the keeper's
  state is `consecutive_failures: 0` with no pending retry.
- Every moved byte is retained in labeled aside directories; nothing was
  deleted, retired, or root-moved at any step.

## Stay inside the walls

- A source-lane rotation covers exactly its own lane. It never changes a
  sibling lane (production or main), the administrative-root locator record, or
  a registered deployment context file, and it never runs a retirement or an
  administrative-root move.
- The lane-bootstrap direction (`comet-admin domains bootstrap`) is fenced to
  governed lanes (production and main) by design; a development lane cannot
  call it. An existing issued product contract owns the rule change, so a new
  deployment's one-time common-domain registry follows the tracked record in
  the tracker, not a hand edit.
- The rotation never resets credentials. The machine credential
  (`credentials.env`), service credential (`keys/service.key`), and the
  offline administrator enrollment of the lane survive the rotation untouched.
- A host can see another node's Unix-socket path on shared storage, but clients
  on that node cannot connect to it. Probe the operator's liveness through its
  heartbeat and its own node only; see
  [unix-socket-shared-fs-host-locality](unix-socket-shared-fs-host-locality.md).

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Comet development-lane rotation | One live canonical-development lane moved end-to-end from a pinned revision to the tip of an approved PR branch, with a fresh domain bootstrap inside it | Generalized coordinates. See [comet-source-lane-revision-rotation.notes.md](comet-source-lane-revision-rotation.notes.md). |

## References

- [unix-socket-shared-fs-host-locality](unix-socket-shared-fs-host-locality.md): host-local Unix sockets on shared filesystems.
- [comet-live-readonly-release-status-probe](comet-live-readonly-release-status-probe.md): read-only per-component status probing; stale-socket handling.
- [comet-user-credential-lifecycle-diagnosis](comet-user-credential-lifecycle-diagnosis.md): DSN/offline credential posture on development lanes.
- [serving-pool-replica-outage-diagnosis](serving-pool-replica-outage-diagnosis.md): replica lifecycle evidence classes for the gateway generation's pools.
- [cutover-stop-previous-release-daemon](cutover-stop-previous-release-daemon.md): the release-layout stop that a source-lane roll does not fit.
