---
name: registry-map-total-lookup-silent-empty-fallback
license: BSD-3-Clause
description: "Repair a registry map that a consumer reads as total while no writer fills it, and remove fallbacks that cannot work in the deployment. Use when a launch, render, or activation step falls into a fallback path, when a published context or manifest holds empty per-key entries, or when a fallback points to a path that cannot exist in that deployment type."
category: architecture
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [registry, map, publication, activation, fallback, silent-failure, single-source-of-truth, deployment]
---

# Registry Map: Total Lookup, Empty Writer, Silent Fallback

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Find why a consumer leaves the normal path for a fallback, and remove the cause without adding a second authority. |
| **Outcome** | Operational. A published context held an empty per-key registry, so every consumer used a fallback. The repair fills the registry at activation, refuses activation with a per-key reason, and deletes the fallback that cannot work in the deployment. |
| **Verification** | verified-local. The reasoning comes from one deployment defect and its fix. Behavior tests were added for the fill, the refusal, and the removed fallback. |

## When to Use

- A consumer indexes a registry map by key (`registry[name]`), and the key is absent at run time.
- A published context, manifest, or release record holds empty or missing per-key entries, while the consumer treats the map as total.
- A launch, render, or activation step uses a fallback path, and the fallback path is not the designed behavior.
- A fallback names a path, interpreter, or directory that cannot exist in this deployment type.
- Two records declare the same facts, and it is not clear which record is authoritative.

## Verified Workflow

### Quick Reference

```text
1. Find every writer of the map.  No writer -> the map is a defect, not a cache.
2. Fill the map at publication or activation, before any consumer needs it.
3. Validate at activation. Refuse with one reason for each key that is absent.
4. Delete fallbacks that cannot work in the deployment type. Keep one that can work as documented behavior with a warning.
5. Document one record as the authority for each value.
```

### Suggested Approach

1. Reproduce the symptom, and record the exact error or fallback text. Read the consumer to find the lookup that starts the fallback chain.
2. Search the repository for each writer of the map (`git grep -n '<registry-name>' -- src/`). When no writer fills the entries, the map is not a cache that went stale. The publication path is incomplete.
3. Read the second record that declares the same facts, such as the per-unit configuration file. If that record is correct and the map is empty, the map is not the authority. Do not add logic that copies the second record into the consumer. Fill the map where the keys are known: at publication or activation.
4. Add a validation step at activation. For each configured key that has no entry, refuse activation with a reason that names the key. When the deployment declares images but the map is empty, this check is not optional. The empty state must not be silent.
5. Audit each fallback in the chain. A fallback to a resource that cannot exist in the deployment type (for example, a host virtual environment in a container deployment) is a defect. Remove it. Keep a fallback that can work only when you document it and it emits a warning.
6. Write down one authority for weights, image paths, and other shared values. State where each value is produced and where it is read.
7. Add focused tests for three behaviors: the fill at activation, the refusal with the per-key reason, and the absence of the removed fallback in the rendered output.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Treat the empty map as a stale cache | Waited for a later write to fill the map | No writer existed, so the map stayed empty and every launch used the fallback | Find the writers first. An absent writer is a defect, not a cache miss. |
| Patch the consumer to read the second record | Added a fallback copy of the per-unit configuration in the consumer | It created a second authority and hid the empty map | Fill the map at its source, and refuse activation when it is empty. |
| Keep the old fallback path that cannot exist | Left the host virtual environment path in the render path | The path cannot exist in a container deployment, so the failure was permanent | Delete fallbacks that the deployment type cannot satisfy. |
| Warn only | Logged that the map was empty | The launch continued and drifted to an unintended path | Refuse, with a reason for each key, when the map is empty for configured keys. |

## Results & Parameters

### Decision Table

| Observed state | Decision |
| -------------- | -------- |
| Consumer indexes the map; no writer fills it | Add the fill at publication or activation. |
| Configured keys have no entries at activation | Refuse activation, and list each key. |
| Deployment declares images; map is empty | Refuse activation. Do not continue with a fallback. |
| Fallback resource cannot exist in the deployment type | Delete the fallback. |
| Fallback resource can work, and the design accepts it | Keep it, document it, and emit a warning. |
| Two records hold the same value | Select one as the authority, and document the choice in the owning page. |
