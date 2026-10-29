---
name: blocked-probe-pinned-evidence-substitution
license: BSD-3-Clause
description: "Substitute evidence-equivalent pinned artifacts when an approved plan gates its decision on a probe whose production artifact is inaccessible. Use when a plan's probe step cannot run as written (owner-only artifact mount, a scheduler with no container-capable partition, no allocation) and the plan's park row would stop the whole decision, while the pinned image file, the declared upstream source, or VCS history can supply the same probe facts under the same pinned identifiers through authorized read-only paths."
category: architecture
date: 2026-10-26
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - probe-blocked
  - evidence-substitution
  - pinned-artifacts
  - container-image-extraction
  - squashfs
  - upstream-source-of-record
  - pinned-revision
  - decision-table
  - false-park
  - read-only-access
  - least-privilege
  - deployment-investigation
---

# Blocked Probe: Pinned Evidence Substitution

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-26 |
| **Objective** | Acquire the probe facts an approved decision table needs when the plan's probe command cannot run as written, without widening authority, bypassing access controls, or parking a decision that authorized read-only paths can still settle. |
| **Outcome** | Successful. In the source case, every gated probe fact was answered in one session through three substitutions (userspace image extraction, the upstream source of record at the recipe-pinned revision, a version-pinned scratch toolchain), and repository history carried the root cause that the probe alone would not have proved. The decision closed with no further code change. |

The rule: an inaccessible production artifact blocks the *access path*, not the
*evidence*. Before accepting a plan's park row ("probe cannot run"), enumerate
substitutes that produce the same probe facts and bind each substitute to the
same pinned identifiers the original path carried (image digest, upstream
revision, packaged toolchain version, VCS path). Quote each substitution and
its binding verbatim in the decision evidence.

This is not a circumvention rule. Every substitute must be an authorized
read-only path to the same declared content. If no such path exists, the park
stands.

## When to Use

- An approved plan gates a fix on probe facts, but the probe command needs an
  owner-only mount, a container-capable scheduler partition, or an allocation
  the worker cannot get, and the plan's park row would stop the decision.
- The decision evidence lives inside a pinned container image whose image file
  is world-readable, even when no container runtime is available.
- The probed artifact declares an upstream source of record (a public hub
  repository, a manifest digest) at an exact revision the configuration pins.
- Repository or configuration history may itself contain the defect and its
  fix lineage (see also `planning-verify-issue-premise-before-implementing`
  for the deployed-versus-default-branch premise split).
- A later coordinating comment claims the work is already delivered; audit the
  merged diff before closing on linkage text alone.

Do not use this skill when:

- No authorized read path exists for the substitute. An access boundary set by
  policy is not a defect to bypass; escalate instead. The park is then correct.
- The substitute cannot be bound to the same pinned identifiers. An adjacent
  artifact (a sibling checkpoint, an unpinned toolchain, "latest" tags) proves
  something different from what the decision row needs.

## Verified Workflow

### Quick Reference

1. Identify the artifact class each probe fact needs: runtime source, artifact
   metadata and small build inputs (tokenizer, config, templates), deployed
   configuration, or behavior under a specific toolchain.
2. Runtime source: if the pinned image file is world-readable, extract only the
   needed subtree with userspace squashfs tools:

   ```bash
   unsquashfs -d <scratch> <pinned-image>.sqsh -e <source/subtree/path>
   ```

   No daemon, no root, no scheduler, no network. Bind: image path, mode, owner,
   and the pinned digest.
3. Artifact small inputs: fetch them from the declared upstream source of
   record at the revision or digest the configuration pins, never from an
   adjacent mirror. Bind: repository identifier and the exact revision.
4. Behavior probes: run them in a scratch toolchain pinned to the versions the
   image packages (read its `*.dist-info` metadata), not the default or newest
   environment. Record the pinned versions in the evidence.
5. Configuration history: `git log --follow -p` on the deployed configuration
   file. Fix lineage that already landed upstream can be the root cause the
   probe alone would not prove.
6. Re-evaluate the decision table against the gathered facts. Quote every
   substitution and binding verbatim in the plan decision record or PR. If a
   row still cannot be evidenced, park only that residual gap, not the whole
   decision.

### Suggested Approach

Prefer the least-privilege acquisition first: extraction beats a runtime, a
revision-pinned fetch beats a checkout mirror, and a scratch virtual
environment beats a shared one. Keep scratch data outside tracked checkouts
and remove it when done.

Verify the decision-table logic against the source you extracted before
selecting a row. A decision row written without knowledge of a code path can
prescribe a change that reintroduces the defect; quote the source lines that
settle which row applies instead of forcing a row.

Define completion by the requested outcome: when the gathered facts show the
defect is already fixed and history proves the fix lineage, the correct
disposition can be an evidence-backed close with no new change, plus a
follow-up issue for the residual validator or process gap.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Park on the access-path error | Record the blocked probe command and apply the plan's park row verbatim (`Refs`, no recipe change, defer to an operator re-run). | The park stopped the entire decision for more than a day even though every probe fact was reachable read-only: the image file was world-readable, and the artifact's upstream source was public at the pinned revision. | Classify the blocker before parking. "Cannot run as written" and "facts unavailable" are different states; only the second justifies a park. |
| Behavior probe in the default environment | Run tokenizer/template behavior checks with the host's default package versions instead of the image's packaged versions. | Loading behavior is version-sensitive; the default environment is a different toolchain than the deployed one and would produce evidence for the wrong artifact. | Pin the scratch toolchain to the image's `*.dist-info` versions and record the pins in the evidence. |
| Container runtime required | Assume the probe needs the scheduler's container support or a local daemon. | The scheduler had no container-capable partition; a local runtime may exist but is more privilege than a read needs. | Userspace squashfs extraction (`unsquashfs -e`) selects just the needed source files with no daemon, root, or allocation. |

## Results & Parameters

### Configuration

| Probe fact class | Substitute | Binding token to quote |
| --------- | --------- | --------- |
| Runtime source and error sites | `unsquashfs -d <scratch> <image>.sqsh -e <subtree>` | image path, mode, owner, pinned digest |
| Checkpoint metadata, tokenizer, templates | upstream source of record at the pinned revision/digest | repository identifier + exact revision |
| Load/template/chat-encoding behavior | scratch venv pinned to the image's `*.dist-info` versions | package==version list |
| Fix lineage / deployed-vs-branch split | `git log --follow -p <config path>` | config path + change commit identifiers |

### Expected Output

- Every gated probe fact answered with a verbatim substitution record (command,
  binding token, result) that a reviewer can re-bind to the pinned identifiers.
- A decision-table evaluation that quotes the source lines settling the row,
  or a named residual gap when substitution genuinely cannot supply a fact.
- A follow-up issue for any residual validation or process gap the evidence
  exposed, instead of a drive-by fix.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A fleet deployment-inference service | Single-issue worker; an approved plan had parked on "probe cannot run" one day earlier | All probe facts answered by image extraction plus revision-pinned upstream fetch plus version-pinned toolchain probes; repository history proved the root-cause fix had already merged; the issue was closed on evidence with no further code change. See [notes](blocked-probe-pinned-evidence-substitution.notes.md). |

## References

- [Planning: Verify Premises Before Acting](planning-verify-issue-premise-before-implementing.md) — the sibling rule for deployed-versus-branch premise splits and for auditing "already fixed" claims against the merged diff.
- `man 1 unsquashfs` — userspace squashfs extraction without a runtime.
