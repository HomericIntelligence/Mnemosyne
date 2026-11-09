---
name: privileged-input-root-scope
license: BSD-3-Clause
description: "Narrow a privileged read root to the caller's own namespace leaf before any filesystem call, and prove that reusing the service store as the private input root does not widen it. Use when: (1) a service account reads a client-nominated file under a broad shared root, (2) a submitted path is refused as outside the accepted roots although the caller owns a usable location, (3) a plan derives a per-caller root from an administrative root plus the deployment context, (4) one directory name serves as both a private service store and a drop area for callers."
category: architecture
date: 2026-11-07
version: "1.0.0"
user-invocable: false
verification: verified-design
tags:
  - least-privilege
  - path-confinement
  - service-account
  - per-user-leaf
  - shared-storage
  - drop-directory
  - sticky-setgid
  - reserved-names
  - derived-root
  - plan-review
---

# Scope a Privileged Input Root to the Caller's Leaf

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-07 |
| **Objective** | Keep the read scope of a privileged service at one caller's own directory when the caller nominates a file path. |
| **Outcome** | Operational. The rule set was derived from repository evidence during plan review, before any code changed. No run result is claimed. |

A service account often reads a large input file directly instead of through
the request body. The accepted roots decide what that service can open for any
caller. A broad root accepts paths that another caller owns, and a root that no
caller owns rejects every caller path. Both conditions report the same generic
rejection.

## When to Use

- A privileged account opens a path that a client supplies, and the path must
  stay inside an accepted root.
- Callers report a rejection of a file that they know exists and own.
- A design derives an input root from an administrative root and a deployment
  or tenant context, with a per-caller leaf below it.
- The chosen input root is, or contains, a directory that the service already
  uses for its own private records.

## Verified Workflow

### Quick Check Before You Design

Answer these three questions from the code, not from the issue text:

1. What is the current root, and who owns each file below it? If the roots are
   the service's own artifact directories, no ordinary caller can own a file
   there, so every caller path is refused.
2. Is the caller identity that selects the leaf the same identity that the
   owner check compares? Resolve the account through the host identity store,
   and compare the file owner with that identity.
3. Is any target directory name already used for private service state? If
   yes, the leaf area and the private store collide, and one of them must
   change its access contract.

### Suggested Approach

1. Derive the root from recorded authority. Use the administrative root that
   the deployment context already carries, append the context suffix, then
   append the caller's account name. Do not add a configuration key and do not
   parse a container mount string for this value. The context suffix check
   that already compares the administrative deployment path with
   `admin_root / suffix` gives the derivation one proof.
2. Scope per request. Pass a single root that ends at the caller's own leaf to
   the existing confinement code. Do not pass the shared parent. The existing
   lexical rule that refuses a path before any `stat()` or `open()` call then
   keeps its no-existence-oracle property, and a symlink escape inside the
   leaf stays refused.
3. Keep the leaf name from a caller that cannot choose it. The leaf comes from
   the authenticated identity, not from the request body. Refuse account names
   that the service or the shell interprets specially: names with a path
   separator, a parent component, a leading dot, or the prefix that the
   service uses for its own entries.
4. Do not widen the service store to make it a drop area, or state the
   contract change explicitly. A private store that is service-owned with a
   strict owner-only mode must reject any change that lets callers create
   entries. If the design requires callers to name entries there, the
   directory becomes a drop area: a sticky, set-group-ID, world-write-without-
   read directory owned by the service, where each caller creates one exact
   name and enumeration fails. Keep the strict owner-only mode on every child
   directory that the service creates below it.
5. Keep the reserved names unreachable. A drop area next to service state
   means a caller leaf name can collide with a service entry that already
   exists, because a sticky directory permits removal only by the entry owner
   and not by the directory owner. Refuse the reserved prefix in step 3, and
   accept this as an availability defense, not as a complete security control.
6. Publish the operational consequence. A mode change on an existing
   deployment is an operator action, and a path-policy or attestation digest
   that is computed from the policy table changes with it. Record both, and
   let the code accept the old and the new parent form during the transition.
7. State the caller-facing path in the user documentation for each
   deployment, with the exact context value and the account variable. Remove
   any claim that names a shared root that the service does not accept.

### What to Verify

- An accepted path under the caller's leaf succeeds.
- A path under another caller's leaf is refused with the same code as any
  outside path.
- An outside path is refused before any filesystem call.
- An unconfigured gateway still returns its coded server fault, not a client
  fault.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | -------------- |
| Reuse the artifact roots | Accepted input paths below the service's own image, model, and overlay directories. | No ordinary caller owns a file there, so the owner check refused every caller path while the public documentation promised a shared location. | Derive the root from the caller namespace, and never from directories that the service owns. |
| Derive the leaf from the submitted path | Prefixed or normalized the request path to build the accepted root. | A caller-chosen component controls its own confinement, so the leaf is not a control. | Take the leaf from the authenticated identity only. |
| Widen the private store in place | Turned the service-owned private directory into a caller drop area without changing the reserved names or the child modes. | A sticky parent lets each caller create one exact name, so a leaf named like a service entry collides with private state, and a relaxed child mode weakens the batch and record contract. | Keep strict modes on children, and refuse reserved leaf names at the root derivation. |

## Results & Parameters

### Configuration

```yaml
derived_input_root: "<admin_root>/<context_suffix>/<service_namespace>/<account>"
leaf_source: authenticated-identity
reserved_leaf_names: [".*", "_service_*", "<service_entry_prefix>*"]
drop_directory_mode: "3733"   # sticky, set-group-ID, write without read
private_child_mode: "0700"
refusal_order: lexical-before-filesystem
```

### Expected Output

- The confinement error names the accepted leaf and uses one stable code for
  every outside path.
- A path under another caller's leaf produces the same code as a path outside
  every root.

## Verified On

| Project | Context | Details |
| --------- | --------- | ------- |
| Repository evidence only (plan review) | Design review of a privileged batch-input root derived from an administrative root and a deployment context | Design-level evidence only. See [notes](privileged-input-root-scope.notes.md). |

## References

- [Repair the Leaf a Call Owns](directory-repair-leaf-only.md) — keep metadata changes on the leaf a call owns.
- [Shared-Filesystem Group Directory Provisioning](shared-fs-group-directory-provisioning.md) — group-writable set-group-ID directory modes.