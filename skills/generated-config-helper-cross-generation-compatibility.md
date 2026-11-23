---
name: generated-config-helper-cross-generation-compatibility
description: "Keep a generated configuration and the executable helper it invokes compatible across installation, refresh, fallback, and rollback. Use when an installer or updater changes their command interface while older installed helpers or running consumers can coexist with the update."
category: architecture
date: 2026-11-22
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - generated-configuration
  - credential-helper
  - cross-generation-compatibility
  - installer
  - staged-refresh
  - legacy-fallback
  - identity-binding
  - rollback
---

# Preserve Generated Configuration and Helper Compatibility Across Generations

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-22 |
| **Objective** | Change a generated command configuration and its executable helper without exposing an unsupported invocation or an incomplete endpoint and credential identity. |
| **Outcome** | Successful. Writer-path and mixed-generation tests reproduced the defects. Compatible publication, identity validation, and complete rollback passed the focused behavior suite and independent review. |

Treat the configuration and helper as one compatibility unit even when they are
separate files. A valid final pair is not sufficient. Every intermediate state
that a running consumer can observe must also be valid.

This rule applies to command arguments, selected identity records, and other
inputs that the configuration passes to the helper. It also applies when a
staged refresh or legacy fallback writes the live configuration before the
normal installation path publishes the helper.

## When to Use

- An installer, updater, or refresh command owns both a generated configuration
  and an executable helper, plug-in, or script that the configuration invokes.
- A new configuration uses a command mode, argument, or identity selector that
  an older installed helper does not support.
- Normal installation, staged refresh, legacy fallback, and recovery can write
  the same live artifacts through different paths.
- An endpoint change must select different credentials or another identity in
  the same configuration generation.
- A failure can leave a new configuration with an old helper, a new helper with
  an old configuration, or only some related artifacts rolled back.

Do not use this entry as a replacement for per-file atomic publication. Use it
with the atomic-publication entry when a reader can also observe incomplete
bytes or metadata in one artifact.

## Verified Workflow

### Quick Reference

Preserve this invariant at every visible step:

> The installed helper must support the currently configured invocation, and
> that invocation must contain a complete identity for the configured endpoint.

For an additive helper interface, use this order:

```text
enumerate every writer and observable intermediate state
resolve the endpoint and its required credential identity
stage the helper, configuration, and related artifacts
prove that the new helper still supports the old configured invocation
publish the compatible helper
publish the dependent configuration and related artifacts
on any failure, restore every artifact mutated by the attempt
```

Helper-first publication is safe only when the new helper supports the old
configuration. If it cannot, use versioned helper paths with one atomic selector,
or prevent staged paths from mutating the live pair until both sides are ready.

### Suggested Approach

1. **Inventory writers and generations.** List the normal installer, update,
   staged refresh, legacy fallback, scheduler, recovery, and rollback paths that
   can write either artifact. Include the old helper already on disk and the old
   configuration that a running consumer can retain. Do not limit the review to
   the final state produced by the primary path.
2. **Define the invocation compatibility matrix.** Cover old and new helpers
   against old and new configured commands. A compatible cell must execute the
   real generated command successfully. For each incompatible cell, prove that
   no publication order or writer path exposes it.
3. **Prefer an additive helper contract.** Keep the previous default invocation
   working and add the new operation as an explicit mode. Publish the compatible
   helper before configuration that requests that mode. If compatibility is
   impossible, keep generations at separate paths and switch one atomic pointer,
   or defer live configuration mutation. Two independent atomic file replaces
   do not make an incompatible pair safe between those replaces.
4. **Bind endpoint and identity before mutation.** Resolve the selected
   deployment or record generation and obtain the endpoint plus the credential
   identity required by the command. Treat an empty identity as invalid when the
   helper needs one. Apply this validation to refresh and fallback paths as well
   as initial installation. A missing or malformed live record must not produce
   a configuration with an empty selector. Stop with an actionable recovery
   message before the first live write.
5. **Regenerate after final selection.** If fallback or refresh changes the
   selected endpoint or record generation, regenerate or rebind the configuration
   after that selection. Do not reuse a command rendered for the previous
   identity. Preserve the old endpoint and old identity together until the new
   pair is ready.
6. **Make rollback cover the whole mutation set.** Snapshot the helper,
   configuration, catalog, and other artifacts before the attempt. Restore every
   mutated artifact on failure, in an order that preserves the same invocation
   invariant. Describe the operation as atomic only if the mechanism really gives
   multi-artifact atomic visibility; otherwise, document the compatible
   intermediate states and the all-artifact restoration boundary.
7. **Test behavior at the generated-command boundary.** Execute old and new
   helpers with the configured commands; do not inspect configuration text alone.
   Exercise every writer and the intermediate publication states. Change the
   actual endpoint identity from A to B and verify that old and new credentials
   stay isolated. Cover valid, missing, and malformed records, identity-less
   fallback rejection, rotation, and byte-identical rollback of all artifacts.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Protect the primary install path | The new configuration and helper were correct on the main install path, but a staged refresh could write live configuration before final helper publication. | A running consumer could invoke the new command mode with the old helper, which rejected the unsupported mode. | Enumerate every writer and validate each observable intermediate state, not only the final primary-path state. |
| Validate identity only during initial installation | An endpoint-only legacy refresh used a fallback after the live record became unavailable. | The fallback supplied an empty identity and could render a command that could not select credentials. | Resolve and validate endpoint-bound identity before every write path. Reject identity-less fallback with recovery guidance and roll back all artifacts. |
| Test matching generations only | Tests executed the new helper with new configuration and exercised legacy record fallback separately. | They did not expose old-helper/new-command skew or prove that an actual endpoint change rebound the credential identity. | Execute the mixed-generation command matrix and an actual A-to-B identity transition. |

## Results & Parameters

### Configuration

| Decision | Required setting |
| ------- | ---------------- |
| Helper contract | Preserve the old configured invocation while adding the new mode, or isolate incompatible generations behind one atomic selector. |
| Publication order | Publish a backward-compatible helper before dependent configuration. Otherwise, prevent live mixed-generation states. |
| Identity | Require the endpoint and its nonempty credential identity in the same rendered configuration generation. |
| Fallback | Resolve identity again after fallback selection. Reject an unresolved required identity before mutation. |
| Failure handling | Restore the helper, configuration, catalog, and every other artifact changed by the attempt. |
| Verification | Run generated commands across old/new generations, every writer path, identity changes, invalid records, and rollback. |

A useful test matrix has these rows:

| Installed helper | Live configuration | Required result |
| ------- | ------- | ---------------- |
| Old | Old | Existing behavior remains valid. |
| New | Old | The old invocation still works during helper-first publication. |
| Old | New | This state is unreachable, or the helper explicitly supports the new invocation. |
| New | New | The new endpoint and credential identity work together. |

Add each staged and legacy writer as a separate scenario. A green final-state
row does not prove that an intermediate row is safe.

### Expected Output

- A running consumer never receives an unsupported helper invocation during a
  supported update or refresh.
- Old endpoint and credential identity remain paired until the complete new
  pair is published.
- Missing or malformed identity data causes an actionable refusal without live
  mutation; it does not produce an empty command selector.
- A forced failure restores all mutated artifacts to their previous bytes.
- Rotation selects the new credential only with its intended endpoint and does
  not reuse the old endpoint's credential.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Private installer and command-line client integration | Generated provider configuration, saved-credential helper, staged refresh, and legacy endpoint fallback | Review found staged helper-ordering and identity-less fallback defects. Focused regressions reproduced them before repair. The final 61-test targeted suite passed, independent re-review returned GO, and the change merged. |

## Related Entries

- [concurrent-reader-observes-half-configured-artifact](concurrent-reader-observes-half-configured-artifact.md) — finish and atomically publish each artifact; this entry adds the cross-artifact invocation contract.
- [release-embedded-script-capability-guard](release-embedded-script-capability-guard.md) — guard the reverse skew where a new embedded script runs against an older release capability.
- [publish-new-top-level-deployment-artifact](publish-new-top-level-deployment-artifact.md) — account for older generations during publication and rollback.
- [external-request-boundary-invariants](external-request-boundary-invariants.md) — test coherent endpoint and credential identity with actual A-to-B changes.
