---
name: release-entry-mode-from-runtime-state
description: "Select upgrade, source-to-release, or first-install mode from the observed deployment runtime record. Use when one release driver serves environments that differ in active release, source runtime, or missing runtime state."
category: ci-cd
date: 2026-11-25
version: "1.0.0"
user-invocable: false
tags: [release, deployment, runtime-record, first-install, source-runtime, upgrade, activation, transaction]
---

# Select the Release Entry Mode from the Runtime Record

## Overview

| Field | Value |
| ------- | -------- |
| **Date** | 2026-11-25 |
| **Objective** | Choose one release path for each environment from the active runtime record, and convert a source runtime to a release without leaving mixed state. |
| **Outcome** | Operational. One driver distinguishes upgrade, source-to-release, and first install; source conversion writes the release, moves the pointer, and retires the source record in one compensated transaction. |

A multi-environment release driver needs one path, not one copy for each
environment. The cluster name, host name, environment variable, or default
context must not select that path. The active runtime record does.

Three states need different first steps:

| Observed state | Entry mode | First step |
| --- | --- | --- |
| Valid release record and a usable prior | Upgrade | Save rollback material, then run the normal upgrade |
| Valid source runtime record, no release identity | Source-to-release | Convert the source runtime during activation |
| Neither source nor release record | First install | Bootstrap lane identity, then activate with no prior |

If both a source record and a release record are active, refuse. That state is
ambiguous, and a driver must not guess which record is authoritative.

## When to Use

Use this skill when one or more of these conditions applies:

- One release driver serves several environments with different runtime states.
- A normal upgrade path fails on an environment that has no prior release.
- A lane runs from a source runtime and the release activation refuses to
  convert it.
- A driver selects behavior from a cluster name or another ambient selector.
- A conversion writes the new release but leaves the old source record.

## Verified Workflow

### Quick Reference

```text
read the active runtime record before any change

release record + usable prior -> UPGRADE
source record only            -> SOURCE-TO-RELEASE
neither record                -> FIRST INSTALL
both records                  -> REFUSE (ambiguous)

select the path from that result, never from the environment name
```

### Suggested Approach

1. **Read the records before the first mutation.** Treat a missing record as a
   valid state, not as an error to repair by hand. Do not synthesize a prior
   release, a source record, or a pointer.
2. **Pass the selected mode explicitly.** A first install and a source
   conversion pass a first-release flag and no prior. An upgrade passes the
   prior revision, version, and prior evidence. The cluster remains an input
   from the selected deployment context; it is not a mode.
3. **Upgrade mode preserves rollback.** Save the exact prior material first.
   The existing rollback and activation behavior stays unchanged.
4. **Source-to-release is one transaction.** Write the release record, replace
   the current pointer, and retire the source record under one exclusive
   guard. On any failure, restore the prior source record, release record, and
   pointer. Do not remove or rename the source record outside that transaction.
5. **First install has no prior.** Skip rollback-save and prior-manifest
   checks. Seed the lane identity records before activation. Do not create a
   fake prior release to satisfy an upgrade check.
6. **A missing peer is a normal state.** A missing gateway, operator, or prior
   release must produce a typed, actionable message. It must not stop a driver
   that has not changed a running component.
7. **Gate production-only steps by capability.** Public client, public docs,
   and forge publication run only where the selected lane permits them. A
   designed lane refusal is not a failed release.
8. **Test each mode and the mixed state.** Add one behavior test for upgrade,
   one for source conversion, one for first install, one for mixed records,
   and one for conversion failure compensation.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Normal upgrade on a source or empty lane | Used the prior-release path because the target was a production environment | The lane had no release record or no prior release; activation refused or reported a raw missing-record error | The observed runtime state selects the path, not the environment name |
| One wrapper per environment | Kept separate release scripts for each cluster | The copies drifted, and a fix reached only one environment | Keep one driver and pass environment-specific values as explicit inputs |
| Delete the source record before activation | Removed the old record, then wrote the release record | A failure between the two writes left no valid runtime record | Retire the source record inside the same guarded transaction as the release write and pointer move |

## Results & Parameters

### Configuration

```yaml
entry_mode_inputs:
  upgrade: [prior_revision, prior_version, prior_evidence]
  source_to_release: [first_release]
  first_install: [first_release, lane_identity_records]
  mixed_state: refuse
```

### Expected Output

- A selected mode name and the observed record state.
- A source conversion that ends with exactly one active release record.
- A first install that ends with a release record and no fabricated prior.
- A typed refusal for a mixed or unreadable runtime state.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| Multi-cluster release driver (generalized) | Production release and focused activation tests | Source-specific paths, hosts, and identifiers are withheld |

## References

- [Release activation with a live old release](release-activation-with-live-old-release-outage.md)
- [Deployed-version runbook goal feasibility](deployed-version-runbook-goal-feasibility.md)
- [Immutable publish target must equal the live candidate](immutable-release-publish-target-live-candidate.md)