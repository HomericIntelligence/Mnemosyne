---
name: live-hotfix-content-addressed-identity-rotation
license: BSD-3-Clause
description: "Restore a live content-addressed deployment lane after an in-place recipe, flag, or qualification change rotates its release identity. Use when: (1) pools report stale or foreign runtime contracts after a hotfix, (2) a service boot fails with an identity mismatch that tells the operator to restart from the active deployment release, (3) rendered job scripts, exported identity environment files, or long-lived services keep the old identity after a document edit, or (4) an urgent fix cannot wait for a full release cut and a documented bypass is authorized."
category: architecture
date: 2026-10-22
version: "1.1.0"
user-invocable: false
verification: verified-live
tags:
  - content-addressed
  - release-identity
  - hotfix
  - identity-rotation
  - deployment
  - blue-green
  - stale-contract-pin
  - runtime-contract
  - rendered-artifacts
  - supervisor
  - checkpoint-binding
  - requeue
  - declaration-driven-scaling
  - fail-closed
---

# A Live Hotfix Rotates the Whole Content-Addressed Identity Chain

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-22 |
| **Objective** | Apply an urgent in-place fix to a live content-addressed deployment lane and return the lane to one consistent identity, with every pool unblocked and the fix serving real traffic. |
| **Outcome** | Operational. A one-flag recipe change rotated four layers of derived identity. After one full-chain recompute, one cascade repin of all stale pool contracts, a blue/green traffic drain, and a purge of every stale-identity carrier, all 15 pools cleared their contract errors and the hotfixed model served real traffic past its known failure window. |
| **Verification** | verified-live: every step ran against the production lane; liveness came from job logs, a published record, pool status files, and a pid-matched service heartbeat. See [notes](live-hotfix-content-addressed-identity-rotation.notes.md). |

## When to Use

- The deployment keeps a release document that pins a runtime-contract digest per pool and derives component, state, release, and context identifiers from content. Any edit to a recipe, serving flag, or qualification input changes those digests.
- After such an edit, pools refuse work with stale-contract or foreign-context errors, or the traffic entrypoint rejects jobs as foreign.
- A lane service fails boot with an identity mismatch whose message tells the operator to restart from the active deployment release, after the operator sourced an older release environment file.
- Rendered batch scripts, exported identity environment files, or long-lived services keep the old identity after a document edit, and lifecycle operations silently revert the edit.
- Every replica fails seconds after launch with a rendered-identity error whose *expected* value differs from the *observed* one, and the registered identity document on disk changed after the long-lived supervisor started. The replica derives *expected* from the disk document; the supervisor rendered *observed* into the job from its older in-RAM copy.
- The designed path — a full release cut with promotion attestation — cannot meet the incident time budget, and a documented, issue-tracked bypass is authorized.

Do not use this skill for a routine release cut: the designed release pipeline remains the default. Do not use it for a single-service restart that changes no digest-bearing input.

## Verified Workflow

### Quick Reference

```text
1. RECOMPUTE: new contract digests plus the full derived-ID chain, with the
   system's own deterministic functions. Revalidate the complete document
   offline in ONE pass before any live write.
2. PURGE: drain traffic (blue/green, never kill), terminate orphaned local
   services, and discard rendered scripts and exported identity environment.
3. RE-ANCHOR: write the validated document; boot services with a sanitized
   environment so identity derives from the document, not from variables.
4. RE-RENDER and bring traffic up with the new identity. Verify by behavior
   (job log, published record, real traffic), not by CLI receipts.
5. SCALE declared pools explicitly: declarations, not demand, drive floors.
```

### Choose the Repair Branch First

Compare the document's modification time with the supervisor's start time. Pick the smallest repair that gives one identity:

- **Edit not yet needed, supervisor still holds the old content:** restore the pre-edit document. Keep a copy of the edited file, record its checksum, and open a tracking issue. Replicas that start after the restore match the supervisor. No rotation and no restart are needed, and live pools keep serving. Check the result with a replica that started *after* the restore. A job that started earlier can still fail with the old error.
- **Edit must apply:** restart the supervisor through its in-place verb so it loads the edited document (the supervisor binds identity at process start, so a disk edit alone never reaches a running process). If the identity chain changed, use the rotation below.
- **Do not reset the scale-out circuit breakers by hand.** A systemic mismatch opens them for every pool after repeated failures. They probe again on their own, and the first probe after the repair clears them.

### Suggested Approach

1. **Treat every editable input as an identity change.** In a content-addressed lane, each input feeds a contract digest; contract digests pin each pool; component, state, release, and context identifiers derive from them. One serving flag (a `trust_remote_code`-class recipe change in the capture case) rotates all layers. Nothing that carries the old identity pair interoperates with the new one.

2. **Audit every pool before writing.** The contract function is context-neutral, so offline audit has no ordering trap: compute the digest each pool's current recipe produces and compare it with the pin in the release document. Stale pins cluster where pool recipes were authored before the current recipe generation (the capture case found 10 of 15 stale, in two family groups). Repin all stale contracts in one cascade; a partial repin leaves the derived chain invalid and the lane split.

3. **Compute, never hand-edit.** Derive the new identifiers with the release's own functions, including supervisor-reported observed values where the schema requires them. Re-run full offline revalidation until the document validates clean. Keep a backup of each document before writing.

4. **Enumerate identity carriers before the rotation.** Four carrier classes hold a resolved identity, and each fails differently:
   - *Rendered job scripts* bake identity environment at render time and are stale by construction after a rotation: re-render, never re-submit the old script.
   - *Exported release environment files* pin the old identity trio: sanitize, do not source.
   - *Long-lived services* resolve identity at boot and hold it in RAM; their lifecycle verbs re-serialize identity documents from RAM, so a disk edit is silently reverted while such a process lives. Drain/teardown verbs do not reap operator-host service processes: find them through the socket and process table and terminate them before the disk write.
   - *Published records* describe the live generation: re-publish only after activation verifies.

5. **Boot services with a sanitized environment.** Unset every exported identity variable and let the service derive identity from the on-disk document; supply data-path credentials from the rotation-managed store and never echo them. Sourcing an old release environment file before boot is the verified cause of the identity-mismatch refusal that tells the operator to restart from the active deployment release.

6. **Disable requeue before cancelling requeue-marked jobs.** A batch script that carries a requeue directive comes back under a new job ID after cancellation and keeps serving the old identity. Set requeue off with the scheduler control verb first, then cancel. Verified twice in the capture case: once on the traffic entrypoint, once on replica jobs.

7. **Blue/green the traffic entrypoint, never kill.** The drain verb refuses foreign jobs, so it is safe under mixed identity. The replacement lands about 90 seconds after submission. A CLI receipt-verification timeout is a cosmetic known class: verify the activation line in the job log and the identity in the published record. Never blind-resubmit after an unknown-outcome operation.

8. **Repair checkpoint bindings through the designed verb.** Launch-time binding checks can be membership checks: the launch gate requires the qualification digest of the current recipe to be an element of the manifest's digest set. A manifest rewritten by an untracked actor can hold a wrong or missing digest; the error then names expected = current recipe digest and got = the manifest set. The rebind verb appends and preserves membership; never byte-edit a read-only, signature-protected manifest.

9. **Scale declaration-driven pools explicitly.** A declared replica floor persists independently of demand; autoscale never zeroes a declared floor. Scale to zero with the positional CLI form, then cancel the supervisor's orphaned pending submissions by hand (the supervisor does not reap them on scale-to-zero), requeue disabled first.

10. **Reproduce swallowed errors in process.** A catch-all administrative CLI message hides the traceback. Re-run the same operation in process, through the same parse-and-execute path, to see the real failure before selecting a repair.

11. **Keep validation behavioral and workstream-independent.** Never block an entire release on one model's failure; record and continue. Open one tracking issue per workaround and attest each documented bypass.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Hand-edit derived identifiers | Edited release and state identifiers directly in the release document | The document failed its own base and schema validation; derived identifiers are computed fields | Compute the full chain in one pass with the system's functions and revalidate offline |
| Partial repin | Repinned only the two pools that first reported errors | Sibling pools authored before the current recipe generation still pinned stale contracts; the lane stayed foreign | Audit every pool contract against the current recipe generation and repin in one cascade |
| Disk edit under a live stale service | Corrected the identity document while an operator-host service held the old identity in RAM | The next lifecycle verb re-serialized the document from RAM and reverted the edit | Terminate stale-RAM services before the disk write; drain verbs do not reap them |
| Edit a registered document under a running supervisor | Lowered scale bounds in the installed release's registered document to fit a quota while the supervisor ran | The supervisor kept the old identity; every replica derived a different one from disk and exited in about 20 seconds; breakers opened on nine pools | Restore the pre-edit document at once (keep the edited copy), or restart the supervisor so it loads the edit. Never leave disk and supervisor on different content |
| Cancel of a requeue-marked job | Cancelled the old-generation traffic job directly | The scheduler resurrected it under a new job ID and it kept admitting old-identity traffic | Disable requeue through the scheduler control verb before cancelling |
| Boot with a sourced release environment | Exported the pinned release environment file, including its identity trio, before starting the service | Boot refused with an identity mismatch telling the operator to restart from the active deployment release | Sanitize every identity variable; services derive identity from the disk document |
| Re-submit a rendered script | Identified the previously rendered entrypoint script for re-submission after the rotation | Caught before submission: the script baked the old identity environment at render time and would have launched the old identity | Re-render after any rotation; rendered scripts are stale by construction |
| Trust a receipt timeout as failure | The CLI reported an activation-receipt timeout for the replacement entrypoint | The entrypoint had in fact activated about 90 seconds later; a blind resubmit would have double-submitted | Treat receipt timeouts as unknown outcome; verify through the job log and published record first |
| Byte-edit the checkpoint manifest | Considered editing the manifest to add the current recipe digest | The manifest is read-only and signature-protected; the designed rebind verb appends while preserving membership semantics | Use the designed rebind verb; binding checks are membership checks against a digest set |

## Results & Parameters

### Configuration

```yaml
identity_chain:
  editable_inputs: [recipe, serving flags, qualification inputs]
  derived_layers: [contract digest, pool pin, component id, state id, release id, context id]
  rule: compute with the system's own functions; revalidate the complete document offline before any live write
carrier_purge_order:
  - write the validated identity document
  - drain the traffic entrypoint (blue/green; drain refuses foreign jobs)
  - terminate orphaned operator-host services (RAM re-serialization reverts disk edits)
  - discard rendered scripts and exported identity environment files
  - boot services with a sanitized environment
  - bring traffic up with the new identity; verify by behavior
scheduler:
  cancel_rule: disable requeue on the job before cancelling requeue-marked jobs
  binding_check: membership of the current recipe digest in the manifest digest set; repair only through the designed rebind verb
  pool_scaling: declaration-driven; scale-to-zero is explicit, then reap orphaned pending submissions by hand
observability:
  cli_receipt_timeout: cosmetic class; verify through the job log and the published record
  cli_catch_all: reproduce in process through the same parse-and-execute path for the real traceback
governance:
  validation: behavioral and workstream-independent; never block the release on one model
  audit: one tracking issue per workaround; attest each documented bypass
```

### Expected Output

- One final identity on the disk document, in service RAM, on live jobs, and in the published record, with zero foreign-context rejections.
- Every pool unblocked, and the hotfixed behavior serving real traffic past its known failure window.
- A tracking issue per workaround and per documented bypass, and stale release environment files marked as such.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Shared-cluster multi-model inference deployment (Slurm, content-addressed release document, blue/green traffic entrypoint) | Live production hotfix: a serving-flag change rotated the identity chain; the full rotation executed live across 15 pools | Generalized evidence in [notes](live-hotfix-content-addressed-identity-rotation.notes.md); product, model, host, and job identifiers intentionally omitted |

## References

- [Unix sockets on shared storage serve only the binding host](unix-socket-shared-fs-host-locality.md) — the socket/host-locality rule behind the orphaned-service purge step
- [Give every service one supervision owner](service-supervision-ownership-parity.md) — supervision ownership for the services this workflow terminates and reboots
- [Scheduler service replacement identity continuity](scheduler-service-replacement-identity-continuity.md) — adjacent identity problem: preserving the execution principal across allocation renewal (requeue as eligibility); this entry covers content release identity rotating under a hotfix
- [Checked-in generated artifacts go stale after input changes](generated-artifacts-stale-after-input-change-pinned-regeneration.md) — the CI-side analogue of input-digest fan-out
- [Manifest config-derived limits and digest hardening](manifests-config-derived-limits-digest-hardening.md) — manifest digest provenance discipline
- [Model version retarget for issue-tracked enablement](model-version-retarget-issue-tracked-enablement.md) — the designed tracked path that a hotfix bypasses only under attestation
- [Slurm foreign-job observer and produced-artifact pin gate](slurm-foreign-job-artifact-gate.md) — scheduler-metadata-only verification discipline
