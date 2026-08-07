---
name: gha-workflow-concurrency-controls
description: "Choosing GitHub Actions `concurrency:` controls for event-driven workflows from trigger identity and side-effect idempotency. Use `cancel-in-progress: true` for idempotent or supersede-able runs and `false` for non-idempotent publishers. Scope groups with stable work identity: a native issue number or required typed `workflow_call` input for per-issue work, `github.ref` for per-tag publishing, and `github.head_ref || github.ref` (not `github.sha`) for PR scans. Use `github.run_id` only when no stable entity key exists and unique per-run grouping is intentional. Use when adding concurrency, supporting both native and reusable triggers, reviewing cancellation safety, or checking branch-protection interaction."
category: ci-cd
date: 2026-08-07
version: "3.0.0"
user-invocable: false
verification: verified-local
history: gha-workflow-concurrency-controls.history
tags:
  - github-actions
  - concurrency
  - cancel-in-progress
  - concurrency-group
  - idempotency
  - publish-workflow
  - pypi-publish
  - git-tag-push
  - github-release
  - github-ref
  - github-head-ref
  - github-sha
  - pr-scan
  - per-issue-serialization
  - per-tag-serialization
  - workflow-injection
  - context-expression
  - required-status-checks
  - branch-protection
  - side-effect-idempotency
  - workflow-call
  - typed-input
  - stable-entity-key
  - verified-local
---

# GitHub Actions Workflow Concurrency Controls (Group Key + Cancel-in-Progress Selection)

**History:** [changelog](./gha-workflow-concurrency-controls.history)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-07 |
| **Objective** | Capture the durable decision rules for adding a `concurrency:` block to event-driven GitHub Actions workflows that lack one — how to choose the `group` key and the `cancel-in-progress` value from the workflow's trigger and the idempotency of its side effects. Surfaced while planning (ProjectHephaestus, issue #1548) the addition of `concurrency:` to four workflows: a per-issue automation workflow, a release/publish workflow, an auto-tag workflow, and a PR-scan workflow. |
| **Outcome** | The cancellation and ref/head-ref rules remain CI-verified by PR #1590. The per-issue rule is corrected for reusable workflows: callers provide a required numeric issue input so native and called runs share stable per-issue identity; `run_id` is not a per-issue fallback. The corrected contract and shell boundary are verified locally; hosted CI is pending. |
| **Verification** | verified-local — PR #1590 retains CI evidence for the original direct-event controls; the corrected reusable per-issue contract was exercised locally on 2026-08-07, with hosted CI pending |
| **Files Amended** | `auto-label-needs-plan.yml`, `auto-tag.yml`, `release.yml`, `security.yml` |

## When to Use

Reach for this when you are ADDING a `concurrency:` block to a workflow that currently has none, and you must justify both the group key and the cancel semantics rather than copy-pasting a template. Specifically:

- A workflow runs on a high-frequency event (issue activity, PR pushes, label changes) and stacks redundant in-flight runs because it has no `concurrency:` block — and you need to decide whether the newest run should CANCEL the older one or QUEUE behind it.
- You are tempted to reflexively set `cancel-in-progress: true` everywhere "to save runner minutes" and must first check whether the workflow has a non-idempotent side effect (tag push, PyPI upload, release creation) that a mid-flight cancel would corrupt.
- A publish/release workflow needs serialization so the SAME tag never double-publishes, but DIFFERENT tags should still proceed in parallel — you need the right group key (`github.ref`), not an over-broad one (`github.workflow`) that blocks unrelated tags.
- A PR-scan workflow re-runs on every push to a PR branch and you want successive pushes to the same PR to collapse to one run — you must use `github.head_ref || github.ref`, because `github.sha` makes every push a distinct group and collapses NOTHING.
- A security/edit hook or reviewer flags `${{ github.* }}` inside a `concurrency.group:` as a possible injection sink — you need to know it is a YAML-key context expression, not `run:` shell interpolation, so the env-var-lift rule does not apply.
- You are about to add `concurrency:` to a workflow in a branch-protected repo and must confirm the target is NOT a pinned required status-check context before assuming any merge-queue interaction.
- One workflow supports both a native entity trigger and `workflow_call`, and you need both paths for the same issue or entity to land in the same concurrency group instead of falling back to a unique `run_id`.

## Verified Workflow

### Quick Reference

The single decision rule, then the group-key map:

| Workflow side effect | Idempotent / supersede-able? | `cancel-in-progress` | Group key | Why |
| - | - | - | - | - |
| Tests / scans / lint on a PR | Yes — newest commit's result is the only one that matters | `true` | `github.head_ref \|\| github.ref` | Successive pushes to the same PR collapse to one run; matches the repo's existing `test.yml` convention |
| Idempotent label POST on an issue | Yes — re-POSTing the same label is a no-op | `true` | `github.event.issue.number \|\| inputs.issue_number` | Per-issue serialization across native and reusable runs; the required typed caller input preserves stable identity |
| git tag push | NO — a cancelled run can leave a tag pushed but its release uncreated | `false` | `github.ref` | Serialize same-ref runs; never interrupt a half-done tag operation |
| PyPI publish | NO — a cancel can leave a partial/duplicate upload | `false` | `github.ref` (the tag) | Same tag never double-publishes; distinct tags publish in parallel |
| GitHub release creation | NO — half-created release is worse than serializing | `false` | `github.ref` | Same as PyPI — gate on idempotency, not convenience |

**The rule in one line:** set `cancel-in-progress` from the idempotency of the side effect, NOT from a desire to save minutes. Cancelling a half-finished publish is worse than letting it run.

### Historical Group Keys Used (Direct-Event Path CI-Verified)

The four workflows amended in PR #1590 used these exact concurrency blocks — notably WITHOUT the `${{ github.workflow }}-` prefix, which is optional for single-workflow repos:

| Workflow | Trigger | Group key used | `cancel-in-progress` | Rationale |
| -------- | ------- | -------------- | -------------------- | --------- |
| `auto-label-needs-plan.yml` | `issues` events plus an inert reusable declaration | `auto-label-needs-plan-${{ github.event.issue.number \|\| github.run_id }}` | `true` | PR #1590 verified the native `issues` path only; the job's event-only guard skipped `workflow_call`, so this is historical evidence, not the reusable-path recommendation |
| `auto-tag.yml` | `workflow_dispatch` only | `auto-tag-${{ github.workflow }}` | `false` | Non-idempotent tag push; `workflow_dispatch`-only means only one meaningful run at a time anyway |
| `release.yml` | tag push (`refs/tags/v*`) | `release-${{ github.ref }}` | `false` | Non-idempotent release publish; per-ref so different tags run in parallel |
| `security.yml` | `pull_request`, `push` | `security-${{ github.head_ref \|\| github.ref }}` | `true` | Idempotent security scan; collapses successive pushes per PR branch |

**Bare-key vs. workflow-prefixed key:** The planned snippets used `${{ github.workflow }}-${{ github.ref }}` style; the actual implementation used simpler bare keys (`release-${{ github.ref }}` etc.). Both are correct. The workflow-prefix prevents cross-workflow collision if two workflows accidentally share a group name; the bare form is more readable and sufficient for repos where this is not a concern.

### Detailed Steps

**1. Classify the workflow's side effect before touching the keys.**
Ask only one question: *if a run is killed at an arbitrary point, can the system be left in a corrupt or half-applied state?*
- No (tests, scans, idempotent label POST) → the run is supersede-able → `cancel-in-progress: true`. The newest event's result is the only one that matters; killing the older run is free.
- Yes (git tag push, PyPI publish, GitHub release creation) → the run must NOT be interrupted → `cancel-in-progress: false`. New runs QUEUE behind the in-flight one instead of cancelling it.

**2. Choose the group key to scope serialization to the right unit of work.**

```yaml
# Per-issue automation (idempotent label POST): preserve one stable issue
# identity on both the native event and reusable call paths.
# Bare-key form (no workflow prefix) — sufficient for single-workflow repos.
on:
  workflow_call:
    inputs:
      issue_number:
        required: true
        type: number
  issues:
    types: [opened, reopened]

concurrency:
  group: auto-label-needs-plan-${{ github.event.issue.number || inputs.issue_number }}
  cancel-in-progress: true

# Auto-tag (workflow_dispatch only — non-idempotent tag push):
# Use github.workflow as the bare key; only one dispatch can run at a time.
concurrency:
  group: auto-tag-${{ github.workflow }}
  cancel-in-progress: false

# Release / publish (tag push, PyPI, release): serialize per TAG so the
# same tag never double-publishes, while DIFFERENT tags proceed in parallel.
# Do NOT cancel — a half-done publish must finish or queue.
concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false

# PR scan (tests/security): collapse successive pushes to the SAME PR.
# Use head_ref (the PR branch), NOT github.sha — each sha is a distinct
# group and would collapse nothing. Matches the repo's test.yml convention.
concurrency:
  group: security-${{ github.head_ref || github.ref }}
  cancel-in-progress: true
```

Key facts:
- `github.ref` per-tag: distinct tags get distinct groups (parallel), the same tag re-run serializes (never double-publishes).
- `github.head_ref || github.ref`: `head_ref` is only set on `pull_request`; the `|| github.ref` keeps push/non-PR events grouped. Successive pushes to one PR share the branch ref → they collapse.
- `github.sha` is WRONG for "collapse successive pushes": every commit is a new SHA → every push is a new group → no collapse ever happens.
- `github.event.issue.number || inputs.issue_number`: a reusable workflow does not inherit the caller's native issue payload. Require the caller to pass the stable issue identifier so native and called runs for the same issue share a group.
- `github.run_id` is unique per invocation, not stable per entity. It is appropriate only when uniqueness is the desired fallback because no meaningful entity key exists. It prevents an empty shared group, but it cannot provide per-issue serialization and cannot supply the issue number required by downstream API work.
- Bare keys vs. workflow-prefixed: `${{ github.workflow }}-` prefix is defensive but optional. Use it if cross-workflow collision is a realistic concern; omit it for readability in repos with clear event-to-workflow mapping.

For the complete dual-trigger contract—including one ungated job, positive-integer shell
validation, caller documentation, `yaml.BaseLoader`, and fake-`gh` regression tests—see pitfall #9
in `gha-workflow-authoring-pitfalls`.

**3. Confirm the group expression is NOT an injection sink.**
`concurrency.group:` is a workflow-level YAML KEY whose value is a context expression evaluated by the Actions runner — it is NOT `run:` shell that splices attacker-controllable text into a command. The workflow-injection / env-var-lift mitigation (lift `${{ github.* }}` into `env:` before using in `run:`) applies to shell interpolation, NOT to a `group:` key. So `${{ github.head_ref }}` or `${{ github.event.issue.number }}` in a group key introduces no injection sink. (Contrast: the SAME `github.head_ref` IS a dangerous source inside `run:` — see `gha-workflow-authoring-pitfalls`.)

**4. Confirm no branch-protection interaction before assuming one.**
Adding `concurrency:` to a workflow that is NOT a pinned required status-check context cannot brick the merge queue — there is no required context whose cancellation/serialization would leave a PR un-mergeable. Before assuming any interaction, enumerate the repo/org ruleset required contexts and confirm the target workflow's jobs are not among them. (For issue #1548, none of the four target workflows were required contexts — confirmed by enumerating ruleset contexts.)

**5. Verify per-file specifics against the live files before assuming line numbers.**
The group-key decision rules are durable. Exact insertion lines in any specific workflow file may drift — always re-read the live file and confirm the insertion point (top-level, after `on:`/`permissions:`, before `jobs:`) before editing.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Universal cancel | Assume `cancel-in-progress: true` is universally safe "to save minutes" | WRONG for publishers: a cancelled tag-push/PyPI/release run can leave a tag pushed but release uncreated, or a partial PyPI upload | Gate cancel semantics on side-effect IDEMPOTENCY, not convenience; publishers get `cancel-in-progress: false` |
| Key publish on `github.workflow` alone | Group a release/publish workflow on just `github.workflow` | Over-serializes (blocks unrelated tags) or under-serializes depending on form — wrong granularity | For `release.yml` prefer `github.ref` (the tag): same-tag races serialize while DISTINCT tags proceed in parallel |
| Key PR scan on `github.sha` | Use `github.sha` for PR-scan concurrency group | Each SHA is a distinct group, so rapid successive pushes to the same PR branch do NOT collapse | Use `github.head_ref \|\| github.ref` so successive pushes to one PR share a group and collapse |
| Use `github.run_id` as a per-issue reusable fallback | Group on `github.event.issue.number \|\| github.run_id` | Every reusable invocation receives a different group, including two runs targeting the same issue; the value also cannot identify the issue for the API call | Require a typed `workflow_call` issue input and group on `github.event.issue.number \|\| inputs.issue_number`; reserve `run_id` for intentional per-run uniqueness |
| Treat `${{ github.* }}` in group as injection | Apply env-var-lift to `${{ github.head_ref }}` inside `concurrency.group:` | The mitigation is for `run:` shell splicing; a `group:` key is a context-expr YAML key, not a shell sink | No env-var-lift needed in a `concurrency.group:`; it introduces no injection sink |
| Assume branch-protection interaction | Assume adding `concurrency:` could brick the merge queue | A non-required workflow's serialization can't leave a PR un-mergeable; the assumption was unchecked | Enumerate ruleset required contexts FIRST; only a pinned required context could interact |
| Using `github.workflow-` prefix in group key | Plan proposed `${{ github.workflow }}-${{ github.ref }}` etc. to prevent cross-workflow collisions | Not incorrect but unnecessary — simpler bare keys work fine in repos where workflows don't accidentally share a concurrency group name; the actual implementation used the shorter form | For single-repo, single-workflow-per-event scenarios, the workflow-prefix is defensive but optional; use bare event-scoped keys for readability, add prefix if cross-workflow collision is a real concern |

## Results & Parameters

| Parameter | Value |
| --------- | ----- |
| **Verification level** | verified-local for the corrected reusable per-issue rule; PR #1590 remains verified-ci evidence for direct-event cancellation and the other group-key patterns |
| **Decision rule** | `cancel-in-progress: true` ⇔ idempotent/supersede-able side effect; `false` ⇔ non-idempotent publisher (tag/PyPI/release) |
| **Per-issue group** | `auto-label-needs-plan-${{ github.event.issue.number \|\| inputs.issue_number }}`, `cancel-in-progress: true`; declare `workflow_call.inputs.issue_number` as required `number` and pass the same resolved value to the job |
| **Per-tag (publish) group (confirmed)** | `release-${{ github.ref }}`, `cancel-in-progress: false` |
| **Auto-tag group (confirmed)** | `auto-tag-${{ github.workflow }}`, `cancel-in-progress: false` (workflow_dispatch-only) |
| **PR-scan group (confirmed)** | `security-${{ github.head_ref \|\| github.ref }}`, `cancel-in-progress: true` |
| **Anti-pattern** | `github.sha` for PR-scan collapse (each sha = distinct group, no collapse) |
| **Bare vs. prefixed keys** | Bare keys (no `github.workflow-` prefix) are sufficient for single-workflow repos; prefixed form is defensive but optional |
| **Injection** | `${{ github.* }}` in `concurrency.group:` is a context-expr key, NOT a `run:` sink — no env-var-lift needed |
| **Branch protection** | Only a pinned required status-check context can interact — none of the four amended workflows are required contexts (confirmed) |
| **auto-tag.yml trigger** | `workflow_dispatch`-only (confirmed) — validates the planning assumption |
| **label POST idempotency** | `auto-label-needs-plan.yml` uses add-label (idempotent) — confirms `cancel-in-progress: true` is safe (confirmed) |

### Verified On

| Repo | Context | Status |
| ---- | ------- | ------ |
| ProjectHephaestus | issue #1548 / PR #1590 — added `concurrency:` to auto-label-needs-plan.yml, auto-tag.yml, release.yml, security.yml | verified-ci (all required CI checks passed: test, integration, pr-policy, lint; 2026-06-24) |
| ProjectHephaestus | proposed dual-trigger `auto-label-needs-plan.yml` contract | verified-local (typed input, shared identity expression, positive-integer shell guard, and fake-`gh` boundary exercised on 2026-08-07); hosted CI pending |
