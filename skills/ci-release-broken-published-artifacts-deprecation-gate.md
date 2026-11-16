---
name: ci-release-broken-published-artifacts-deprecation-gate
license: BSD-3-Clause
description: "Gate a package release on verified deprecation of already-published artifacts that cannot load. Use when: (1) a published package release breaks consumers at module load time and older published versions in the same package remain installable, (2) the release pipeline publishes with OIDC trusted publishing or another credential model that cannot run registry mutations such as deprecation, (3) a one-time manual registry action is required to stop installs of the broken versions, and (4) you need an automated control that fails the release until that manual action is done."
category: ci-cd
date: 2026-11-16
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [ci, release, publish, deprecation, registry, fail-closed, trusted-publishing, npm]
---

# CI Release Gate: Verify Deprecation of Known-Broken Published Artifacts

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-16 |
| **Objective** | Stop a release from shipping while already-published artifacts stay installable but broken |
| **Outcome** | Operational. Gate logic and workflow syntax were verified locally and by CI checks; a production tag release has not yet exercised the gate |

## When to Use

- A published package release breaks consumers at module load time (module shape, missing
  entrypoint, or runtime loader error) and older published versions in the same package remain
  installable.
- The release pipeline publishes with OIDC trusted publishing or any credential model that grants
  publish scope only to publish, not to registry mutations such as the deprecation command.
- A one-time manual registry action is required, and it must be done by a maintainer. You want
  the release to block until that action is complete.
- You need an automated check that fails the release, not an advisory log line.

## Verified Workflow

### Quick Reference

For each known-broken published artifact, `npm view '<pkg>@<version>' deprecated` must print a
non-empty message. Gate the publish job on every per-artifact check. Fail closed on query errors.
Print the exact remedy command in the failure output.

### Suggested Approach

1. Build the population explicitly. Run `npm view '<pkg>@<range>' version` and enumerate every
   published version in the broken range. Do not infer the list; read it from the registry.
2. Query the deprecation message for each version individually. A range query
   (`npm view '<pkg>@<range>' deprecated`) exits 0 and prints output when any single version is
   deprecated; the gate passes while other broken versions remain installable.
3. Put the check before the publish step in the publish job. Exit non-zero on any miss, so the
   workflow shell stops before the publish command.
4. In the failure message, print the exact one-time remedy command with the exact range and
   message. Do not soften the error into a warning.
5. Treat registry query failures as gate failures. An unreadable or erroring registry must block
   the release; the nonzero exit stops the job before it publishes.
6. Do not use `continue-on-error`, `set +e`, `|| true`, or an advisory log for this gate. An
   external manual action cannot be enforced by a warning; a fail-closed check is the honest
   control.
7. Document the stop condition in the release procedure: the release stays blocked until a
   maintainer deprecates each broken version. Also document the inverse: after the one-time
   action the gate passes forever and costs about one second.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Range-wide deprecation check | The gate ran `npm view '<pkg>@<range>' deprecated` and passed on any output | Any single deprecated version satisfies the range query; the other broken versions stayed installable and the gate waved the release through | Query each known-broken version individually; enumerate the population explicitly from the registry |
| Publish-side deprecation attempt | The design assumed the publish job (OIDC trusted publishing) could run the deprecation | Trusted publishing grants no registry-mutation scope beyond publish; deprecation needs maintainer credentials | Verify the credential model before promising automation; ship a verification gate and a documented manual command instead |
| Advisory warning for the manual step | The failure was logged as a warning while the release proceeded | The release proceeded exactly as the warning described, and the broken artifacts stayed the default install | An external action that must not be skipped needs a fail-closed check, not a warning |

## Results & Parameters

### Configuration

```yaml
gate:
  population: explicit list of known-broken versions (for example 0.4.4, 0.5.0, 0.5.1, 0.5.2, 0.5.3)
  check: per-version npm view '<pkg>@<version>' deprecated
  requirement: non-empty deprecation message on every listed version
  failure: exit 1; print the exact remedy command; nothing is published
  preconditions: registry reachable; a query error blocks the release by design
  scope: verification only; the deprecation itself is a maintainer action
  placement: before the publish step in the publish job, not after
```

### Expected Output

- After the one-time deprecation: the gate prints the success line on every tag release with
  near-zero cost.
- Before the one-time deprecation: the publish job fails with an error line naming each missing
  version and the exact remedy command, and nothing is published.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| an isolated checkout | A plugin package published to npm; its older published artifacts could not load in the supported host; the publish job gained a load-check gate and the per-artifact deprecation gate | Gate logic and workflow syntax verified locally and by CI checks (hand-run against the live registry; every listed version reported empty deprecation). A production tag release has not yet exercised the gate. See [notes](../skills/ci-release-broken-published-artifacts-deprecation-gate.notes.md) |

## References

- [tooling-opencode-v2-invalid-server-plugin](tooling-opencode-v2-invalid-server-plugin.md) — diagnosing and repairing the broken load on the consumer side
- [planning-verify-issue-premise-before-implementing](planning-verify-issue-premise-before-implementing.md) — gate populations must be explicit and re-checked at each boundary
- [ci-release-gate-stricter-than-branch-green-not-transferable](ci-release-gate-stricter-than-branch-green-not-transferable.md) — a release gate is stricter than branch green; green does not transfer
