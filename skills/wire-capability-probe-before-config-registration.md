---
name: wire-capability-probe-before-config-registration
license: BSD-3-Clause
description: "Probe a deployed service's wire capability with minimal live requests before an installer writes client configuration that depends on it, and hold the last known-good form when the probe is unsupported or inconclusive. Use when: (1) an installer or refresh writes references in a new wire form that the current source supports, (2) a deployment record's version or source fields would decide what the serving binary supports, (3) the deployed endpoint answers a not-found error for the new form while the old form still answers, or (4) a fallback mode must flip automatically after the deployment upgrades."
category: tooling
date: 2026-11-26
version: "1.0.0"
user-invocable: false
verification: verified-live
tags: [installer, deployment-record, version-skew, capability-probe, adaptive-registration, fallback, wire-compatibility, refresh, model-serving]
---

# Wire-Capability Probe Before Config Registration

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-26 |
| **Objective** | Stop an installer from registering client references that the deployed service binary cannot route. |
| **Outcome** | Successful — the installers probe the live endpoint, select the reference form from a decision table, hold the safe form when the probe is inconclusive, and flip to the new form automatically after the deployment upgrades. |

## When to Use

- An installer, generator, or refresh writes client configuration that references a service capability in a new wire form: a reference prefix, a route, a field, or a flag.
- The current source tree supports the new form, and you are about to conclude that the deployed binary supports it too.
- A deployment record, manifest, or registry names a version or a source revision, and you would trust that field to learn what the serving binary runs.
- The deployed endpoint answers a not-found-class error for the new form while the old form still answers.
- You design a fallback mode and need decision rules for supported, unsupported, and inconclusive probes.

## Verified Workflow

### Quick Reference

```text
Treat a deployment record's identity fields as provenance of the record
producer, not of the serving binary.

One minimal request per form, on a target the deployment serves in the old
form, decides the mode. Inconclusive means the old form plus a warning.
Re-probe on every refresh.
```

Decision table:

| Old form | New form | Mode to register |
| --------- | --------- | ----------------- |
| answers   | answers   | new form |
| answers   | not-found-class error | old form |
| answers   | 5xx, timeout, auth failure, cold target, redirect | old form, warn (inconclusive) |
| no answer | any answer | old form, warn (inconclusive) |

### Suggested Approach

1. Name the capability and its two forms: the old form that shipped releases
   already serve, and the new form that the current source supports.
2. Pick a probe target that the deployment demonstrably serves in the old
   form. A live-pool or serving-set status source names one. Never probe a
   starting, stopped, or unknown target; a cold target makes the probe
   inconclusive.
3. Send the minimal request in the old form first. Require a success status.
   Without that baseline, the probe cannot blame the form.
4. Send the same minimal request in the new form. A success status selects
   the new form. A not-found-class error selects the old form. Any other
   result is inconclusive; select the old form and warn.
5. Write the configuration in the decided mode. Keep the full inventory in
   both modes: the mode changes the reference form, not the registered set.
6. Bake the decided mode into every background component that rewrites the
   same configuration (a monitor, a refresher, a scheduler). A background
   component must not re-probe or rewrite forms on its own, or it flips the
   configuration back between user runs.
7. Re-probe on every refresh, and again when the record moves the endpoint.
   When support appears, the refresh flips the mode without a code change.
8. When a mismatch surprises you, capture the deployed error text and search
   the current source tree for it. Error text that does not exist in the
   source is evidence that the serving binary predates the source you read.
   A record's version field or source digest can describe the component that
   wrote the record, not the component that serves the requests.
9. While the gap is open, restore the live configuration to the last
   known-good form first, then ship the probe. Do not leave live inference
   broken while a fix is in review.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| 1 | Trusted the deployment record's version and source fields to conclude that the serving binary supported the new reference form | The fields described the record producer; the serving binary ran an older release; every request in the new form answered a not-found error on every route | Verify the capability with a live request. Treat record identity fields as producer provenance only |
| 2 | Registered the new form unconditionally, because the current source canonicalizes it at request time | Live requests failed for every client; the deployed error text did not exist anywhere in the source tree | Absent error text in the source is evidence of an older deployed binary. Probe before you write |
| 3 | Left the live client configuration on the new form while the gap was open, and planned to fix it in a follow-up change | Live inference broke for the whole gap window; a restore to the previous configuration became an extra emergency step | Restore the last known-good configuration first. Ship the adaptive probe second |

## Results & Parameters

### Configuration

Probe request shape:

```text
target    one model or route the deployment serves in the old form
form-old  the reference form shipped releases serve
form-new  the reference form the current source supports
request   minimal authenticated request; smallest possible body; short timeout
baseline  form-old must answer success; otherwise the probe is inconclusive
```

Mode rules:

```text
supported      form-new answers success            -> register form-new
unsupported    form-new answers not-found-class
               while form-old answers success      -> register form-old
inconclusive   any other result                    -> register form-old, warn
re-probe       every refresh and endpoint move     -> flip when supported
```

### Expected Output

- The installer prints the decided mode and the evidence for it.
- In the old-form mode, the installer tells the user to run a refresh after
  the deployment upgrade; the refresh then flips the form.
- The background components honor the baked mode between user runs.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A model-serving platform | Client installer rewrite with a new provider-qualified reference form | The deployment record named a current source revision, but the serving binary predated the canonicalization; two independent live probe passes confirmed the gap. Evidence in [notes](wire-capability-probe-before-config-registration.notes.md) |

## References

- [Deployed-version runbook goal feasibility](deployed-version-runbook-goal-feasibility.md) — read the deployed ref before you publish version-keyed directions
- [Release embedded-script capability guard](release-embedded-script-capability-guard.md) — guard embedded-script calls against older fleet releases
- [Comet live read-only release status probe](comet-live-readonly-release-status-probe.md) — read-only status evidence from a live deployment
