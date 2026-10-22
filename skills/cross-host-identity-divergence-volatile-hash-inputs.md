---
name: cross-host-identity-divergence-volatile-hash-inputs
license: BSD-3-Clause
description: "Keep a content-derived identity hash free of launch-volatile inputs so that every host of a shared filesystem computes the same identity. Use when (1) a job rendered on one host fails an identity check after re-resolution on another host while all declared inputs are identical; (2) you design or review a digest or identity that different hosts must compute identically; (3) two resolutions of one logical deployment give different digests with no specification change."
category: architecture
date: 2026-10-22
version: "1.0.0"
user-invocable: false
verification: verified-live
tags:
  - content-addressed
  - identity-hash
  - shared-filesystem
  - cross-host
  - mount-metadata
  - st-dev
  - inode
  - render-run-boundary
  - fail-closed
---

# Cross-Host Identity Divergence from Volatile Hash Inputs

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-22 |
| **Objective** | Keep one content-derived identity equal on every host of a shared filesystem, without masking real identity changes. |
| **Outcome** | Successful. Removing the mount-instance fields from the identity payload restored cross-host agreement; a rendered job now verifies after re-resolution on any node; the constancy rule held again in live cross-host probes. |
| **Verification** | verified-live - the defect was proven by cross-host payload diffs and deterministic short-lived job failures, the fix was verified by the same probes on the same hosts, and regression coverage guards the render/verify boundary. |

## When to Use

- A job specified or rendered on one host fails on another host with an identity mismatch. The recomputed value differs from the rendered value, while every declared input (specification, release, paths, principals) is identical.
- Two resolutions of one logical deployment produce different digests with no operator edit.
- A cross-host fingerprint check in a rendered environment, scheduler-retained evidence, or a service record fails closed although the compared artifacts are identical.
- You design or review a content-addressed identity that different hosts must compute identically on a shared or parallel filesystem, or across launcher and mount lifecycles.

Do not use this skill to plan the live rotation chain after an intentional identity change. Rotation mechanics have their own entry; the rotation here is a one-time consequence of removing bad inputs, not the recurring operation.

## Verified Workflow

### Quick Reference

```text
An identity hash MAY contain only inputs that stay constant on every host
and at every launch of the same logical object:
  - specification or configuration content,
  - release and component identities,
  - agreed path strings, and
  - static binding digests.
An identity hash MUST NOT contain mount-instance metadata:
  - device numbers (st_dev), and
  - inode numbers (st_ino).
Keep the volatile values in a same-host revalidation. On one host they are
consistent, so they still detect a root or path swap inside a live process.
Diagnostic: dump the canonical hash payload on each host and diff every
leaf field. Each differing leaf is evidence for or against removal.
If the second host cannot run probes, re-run the production payload
construction on one host and change exactly the suspect leaf class: an
exact digest match is decisive; a mismatch only removes that hypothesis.
```

### Suggested Approach

1. **Apply the constancy rule to every hash input.** An input belongs in a cross-host identity only when a change to that input means a genuinely different logical object. Device numbers are a property of one client's mount instance: on some shared or parallel filesystems, different clients report different values for the same object. Inode numbers change at any directory replacement. Both change with no change to the logical deployment. Exclude the full class, not only the field that failed today.
2. **Keep host-local protections.** The same volatile fields continue to serve a binding or revalidation that compares two resolutions on the SAME host. Those checks still detect a root or path swap within one running process; the fields are invalid only as cross-host identity material.
3. **Expect one controlled rotation.** Identities computed before the correction differ from identities after it. Stored records that pin the old identity fail closed until their owner publishes again. That fail-closed churn is the designed migration path for an identity change; plan for it once.
4. **Diagnose divergence with data, not with payload retyping.** Resolve the canonical payload on the real second host and diff every leaf. A healthy diff is empty. Each differing leaf must be either a real identity difference (path, binding digest) or a volatile value to remove. A manual replay that retypes candidate values into a hand-built copy can diverge from the production payload construction and mislead; see the failed attempts. When the second host cannot execute probes (scheduler queues, drained node, missing permission), use a bounded alternative: on any reachable host, resolve the real object through production code and re-hash the production payload with exactly the suspect leaf class changed. An exact match with the observed second-host digest is decisive. A mismatch only removes that hypothesis; it does not clear other leaf classes, because the replay construction or the hypothesis can still be wrong.
5. **Test the cross-boundary property directly.** Build two mount-instance fixtures that differ in every volatile field and in nothing else. They must give the same identity, and the production verification function must accept the rendered evidence of the first fixture when evaluated after resolution with the second.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Manual payload replay | Flip the suspect values in a hand-built copy of the payload on one host and compare the digest with the observed second-host digest. | The manual replica did not reproduce the observed digest: its construction diverged from the production payload code (field set and branch handling). | Retype nothing into a hand-built copy. A complete leaf diff between real resolutions is decisive. If second-host execution is unavailable, a re-hash that starts from the production payload object and changes one suspect leaf class is decisive only on an exact digest match. |
| Keep inode numbers in the hash | Cross-host probes showed equal inode values, so only device numbers looked unsafe. | The equal inode values were luck of one mount generation, not a contract. Any directory replacement changes inode numbers at the next launch. | Constancy must hold across launches, not only across the mount instances that exist today. Remove the full volatile class in one change. |

## Results & Parameters

### Configuration

```yaml
identity_payload:
  allowed_inputs:
    - specification_content
    - release_and_component_identities
    - agreed_path_strings
    - static_binding_digest
  excluded_inputs:
    - device_number        # st_dev: client mount-instance property
    - inode_number         # st_ino: changes at any directory replacement
same_host_revalidation:
  keep_inputs:
    - device_number        # valid and useful within one host
    - inode_number
```

### Expected Output

- One identity digest on the control node and on every compute node of the shared filesystem, including nodes whose client reports a different device number.
- A job rendered on the control node passes its in-job identity check at the first attempt on any node.
- Stored identities rotate exactly once when the correction deploys, and then stay stable across nodes and relaunches.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private shared-cluster deployment (identifiers withheld) | Content-derived deployment identity verified through a scheduler-submitted job across login and compute hosts of one parallel filesystem | Cross-host probes and failure shapes in [notes.md](cross-host-identity-divergence-volatile-hash-inputs.notes.md). |

## References

- Related intent with different scope: live rotation of a content-addressed identity chain after an intentional input change (entry `live-hotfix-content-addressed-identity-rotation`, pending publication at authoring time).
- Public background on `stat` device and inode fields: POSIX `stat(2)` manual page for the host.
