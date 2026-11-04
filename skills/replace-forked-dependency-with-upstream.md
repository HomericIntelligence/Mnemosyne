---
name: replace-forked-dependency-with-upstream
license: BSD-3-Clause
description: "Move one consumer off an organization fork of a dependency while the fork stays in use by other consumers. Use when: (1) you must stop consuming a fork without archiving or changing it, (2) an engine, library, or service is pinned to a fork revision that has fallen behind upstream, (3) you must decide whether to re-base the fork, refresh its deploy automation, or adopt a pinned upstream revision plus a thin patch stack, (4) several releases must each retire one fork dependency."
category: architecture
date: 2026-11-04
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [fork-retirement, upstream-pin, vendored-dependency, patch-stack, dependency-lag, consumer-boundary, release-sequencing, supply-chain, version-gap]
---

# Replace a Forked Dependency With Upstream

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-04 |
| **Objective** | Stop one consumer from using an organization fork of a dependency, while the fork stays alive for other consumers, without losing the fork-only behavior the consumer needs. |
| **Outcome** | Operational. A read-only survey separated code divergence from automation divergence, which selected a pinned-upstream-plus-thin-patch-stack plan instead of a fork refresh. The plan was organized as one dependency per release. |
| **Verification** | verified-local — the survey used forge compare endpoints and pinned content reads. No build, qualification, or cutover ran in this session. |

## When to Use

- A request says "use upstream, not the fork" but the fork must continue to exist.
- A pinned dependency is far behind upstream and you must choose a migration shape.
- One consumer must leave a fork that other consumers share.
- Several dependencies need the same treatment and must be ordered across releases.

Do not use this skill to answer which models or features a fork supports. That is
[forked-engine-model-support-evidence](forked-engine-model-support-evidence.md).
Do not use it to retarget one model or artifact to a newer upstream revision. That is
[model-version-retarget-issue-tracked-enablement](model-version-retarget-issue-tracked-enablement.md).

## Verified Workflow

### Quick Reference

```bash
# Fork upstream and divergence, measured against the fork's own remote.
gh repo view ORG/FORK --json parent,defaultBranchRef
gh api "repos/UPSTREAM/PROJ/compare/main...ORG:main" \
  --jq '{ahead_by, behind_by, commits: [.commits[] | .commit.message | split("\n")[0]]}'

# Repeat for every branch that production can consume.
gh api "repos/UPSTREAM/PROJ/compare/main...ORG:deploy" --jq '{ahead_by, behind_by}'
```

`ahead_by` is the patch surface. `behind_by` is the version lag. Read both before
you choose a migration shape.

### Suggested Approach

1. Confirm the upstream project. A fork can point at a parent that the name does
   not suggest. Read `parent` from the forge, then repeat discovery against that
   parent.
2. Measure each branch, not each repository. Production usually consumes one
   branch of several. A branch that holds only deploy automation has a different
   migration cost from a branch that changes product code.
3. Classify every commit that the fork adds. Read the touched paths:
   - product code that the consumer needs;
   - build or release automation that only exists to publish fork artifacts;
   - workflow or CI change with no consumer-visible effect.
   Record the class per commit. This classification selects the migration shape.
4. Measure the version lag against the consumer's pin, not against the fork head.
   A fork can be current while the deployed artifact is many releases behind.
   Read the consumer's pin file and the deployed artifact version separately, and
   record both.
5. Survey the consumer surface before you plan any cutover. Enumerate every
   integration point: API calls, launch flags, environment variables, metric
   names, runtime overlays, and internal endpoints. Map each point to the
   upstream target revision. Mark missing points explicitly. An internal endpoint
   that no upstream search matches is a migration blocker, not a detail.
6. Classify the open issues that the consumer filed against the fork-dependent
   component. Each item is fixed at the target revision, needs a port, or is
   independent. This triage often reduces the target release scope.
7. Choose one migration shape from the measured facts:

   | Fork delta | Lag | Shape |
   | --- | --- | --- |
   | Product code that consumers need | Large | Pinned upstream revision plus a thin patch stack in the consumer repository |
   | Automation only | Any | Pinned upstream artifact, or a refreshed deploy workflow |
   | No patches, only a pin | Any | Pinned upstream revision, no stack |

   Keep patches only for behavior that upstream does not have. Prefer an upstream
   contribution so the stack shrinks.
8. Make "stop using" a separate outcome from "retire the fork". State the
   non-goals in the tracking artifact: no archival, no branch deletion, no change
   to fork CI, and no change to records that other teams own.
9. Define the completion boundary as a negative inventory. No build input,
   configuration, test fixture, or document in the consumer names a fork as a
   runtime dependency. This test is verifiable without touching the fork.
10. Sequence one dependency per release. Order by risk and by dependency, not by
    convenience. Choose a gapless ordering when shared test and qualification
    capacity is the constraint. Put purely additive work first, because no live
    traffic moves. Put the largest live-path change last, because the machinery
    hardened by the earlier releases is available to it.
11. Move read-only analysis forward and keep only writes in the release window.
    Gap analysis, surface mapping, and issue triage are safe at any time, and
    their output improves the earlier releases. Gate only builds, qualifications,
    and cutovers.
12. Re-verify the plan at each check. Read the consumer's default branch and the
    upstream release list again. Authoritative state changes between planning
    rounds, and the change usually matters.
13. Grant durable authority to safety only. A cutover can proceed only with
    evidence from an isolated environment on the target revision. A large version
    jump on a live request path is a risk to state, not an obstacle to design.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Read only the fork's main branch | Measured divergence from main and concluded the fork was almost current | Main held only automation commits. The branch that production consumed held the product code, so the real patch surface was missed | Measure every branch that production can consume, not the repository |
| Compare the fork head with upstream | Treated a current fork as an acceptable target | The deployed artifact was many releases behind its own fork | Measure the lag against the consumer's pin |
| Plan fork retirement from "stop using" | Listed archival, branch deletion, and other consumers' tracking records as plan steps | Other teams still use the fork. The request was to stop consuming it, not to end it | Set the outcome boundary at the consumer and state the non-goals |
| Assume the fork is the only divergence | Planned to re-base the fork | The consumed branch added only deploy automation over upstream. A pin plus a small patch stack replaced it | Classify the added commits before you choose the shape |
| Sequence releases opportunistically | Compared convenience of the dependency list | Shared test and qualification capacity is the real constraint, and live-path risk forces the last slot | Use a gapless ordering, additive work first, live-path change last |

## Results & Parameters

### Configuration

Record these fields for each dependency to migrate:

```yaml
fork: <org>/<name>
upstream_parent: <org>/<name>      # read from the forge, not from the name
branches_consumed: [<branch>, ...] # every branch production can reach
commits_ahead: <n>                 # fork commits over upstream, per branch
commits_behind: <n>                # gap at the consumed branch
deployed_release: <observed>       # artifact version in use
consumer_pin: <file>:<value>
patch_classes: {product: <n>, automation: <n>, ci_only: <n>}
surface_points: <n>                # API calls, flags, metrics, overlays, internal endpoints
unmapped_points: <list>            # each one is a blocker
target_release: <latest stable>    # floor: minimum acceptable version
```

### Expected Output

- One tracking outcome that names the consumer, not the fork.
- A per-branch commit classification with a recorded migration shape.
- A surface map between the consumer and the upstream target revision, with
  unmapped points named as blockers.
- A release sequence with one dependency per release and an explicit reason for
  each position.
- A negative inventory that proves no consumer input names a fork.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Internal inference service, three forked dependencies (engine, second engine, gateway) | A read-only replan across four planning rounds discovered a fork branch used only for deploy automation, an engine pinned to a revision far behind upstream, and a gateway whose deployed artifact was thousands of commits behind its fork. Selected pinned-upstream-plus-thin-stack for each, and one dependency per release | [notes.md](./replace-forked-dependency-with-upstream.notes.md) |

## References

- [forked-engine-model-support-evidence](forked-engine-model-support-evidence.md) — verify feature support at the pinned revision before you claim the fork can be replaced.
- [model-version-retarget-issue-tracked-enablement](model-version-retarget-issue-tracked-enablement.md) — retarget one issue-bound artifact to a newer immutable revision.
- [logical-model-family-rename-with-storage-exceptions](logical-model-family-rename-with-storage-exceptions.md) — a reference rename is not a dependency replacement.
- [planning-dependent-issue-unverified-upstream](planning-dependent-issue-unverified-upstream.md) — read the real dependency instead of planning fallbacks.