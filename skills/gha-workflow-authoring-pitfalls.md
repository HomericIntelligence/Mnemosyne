---
name: gha-workflow-authoring-pitfalls
description: "Author GitHub Actions workflows that parse, scope events, handle untrusted expressions, serialize mutations, and work under repository/organization permissions. Use for invalid job IDs, composite descriptions containing expressions, run-block injection guards, PR-creation policy failures, trigger fan-out, missing concurrency, or native-event plus workflow_call context gaps."
category: ci-cd
date: 2026-08-07
version: "2.0.0"
license: BSD-3-Clause
verification: verified-local
user-invocable: false
history: gha-workflow-authoring-pitfalls.history
tags: [github-actions, workflow, yaml, injection, permissions, concurrency, reusable-workflow]
---

# GitHub Actions Workflow-Authoring Pitfalls

## Overview

Workflow correctness begins before commands run: YAML/job identifiers must parse, event changes
apply to the whole workflow, expression values must cross into shell through environment variables,
and repository mutations need both token permissions and organization policy. Concurrency belongs at
workflow scope when it protects all jobs.

Detailed cases are indexed in
[`gha-workflow-authoring-pitfalls.notes.md`](gha-workflow-authoring-pitfalls.notes.md). The complete
prior source is in [`gha-workflow-authoring-pitfalls.history`](gha-workflow-authoring-pitfalls.history).

## When to Use

- A workflow is ignored or yields zero jobs despite valid-looking YAML.
- A composite-action input description contains expression-like documentation.
- A security hook flags direct `${{ ... }}` interpolation inside `run:`.
- A workflow is intentionally Linux-only and needs an explicit expansion condition.
- An editing hook blocks workflow-file changes.
- Actions cannot create or approve PRs despite declared `pull-requests: write`.
- Adding label/auto-merge event types should wake only policy work, not expensive CI.
- Event-driven mutations lack concurrency controls.
- One reusable workflow supports a native entity event and `workflow_call`.

## Verified Workflow

### 1. Validate syntax and identifiers

Job IDs are YAML mapping keys and must avoid `/`; use stable hyphenated IDs and keep human-readable
slashes in `name`. Update every `needs`, output, and expression reference after renaming. Parse and
inspect discovered workflows with the repository’s validator before relying on the Actions UI.

```yaml
jobs:
  security-sast:
    name: security/sast
```

A valid YAML parser alone may not enforce Actions semantics, so also run the project’s workflow
validator or action linter and confirm GitHub lists the workflow/jobs.

### 2. Keep expression syntax out of documentation fields

GitHub may evaluate `${{ ... }}` inside composite-action metadata such as input descriptions. Use
plain placeholders like `<runner.os>` when documenting syntax. Reserve expression delimiters for
fields intended to evaluate.

### 3. Lift untrusted expression values into env

Do not interpolate event, issue, PR, branch, label, or user-controlled text directly into a shell
script. Bind expressions in `env`, quote shell variables, and treat them as data:

```yaml
- name: Handle label
  env:
    EVENT_LABEL: ${{ github.event.label.name }}
  run: |
    process-label -- "$EVENT_LABEL"
```

The env-var lift satisfies injection guards because shell syntax is fixed before untrusted data is
expanded. Still validate identifiers before using them in paths, refs, or API endpoints.

### 4. Document platform asymmetry as a contract

At the workflow header, state the tested platform, why others are omitted, what package capability
still remains, the tracking issue, and the concrete expansion trigger. Do not imply that Linux-only
CI proves macOS/Windows support, or that a pure-Python import claim proves platform-specific tests.

### 5. Handle workflow-file edit controls explicitly

If a host policy blocks `.github/workflows` edits, do not disable or bypass the hook. Use an allowed
exact patch/edit capability or request authorization, then inspect the diff and run workflow
validation. A different write mechanism does not relax scope or security review.

### 6. Diagnose PR-creation permission at both layers

Declared job permissions are necessary but insufficient. Inspect repository workflow permissions
and the “Actions can create/approve pull requests” toggle. A repository cannot exceed a restrictive
organization setting; a 409 on the repo-level update indicates the organization boundary.

Choose an approved resolution:

- organization admin enables the capability;
- use a least-privilege GitHub App or fine-grained token supplied through secrets;
- change the workflow to direct-commit behavior only when repository policy permits it.

Never print tokens or pass untrusted text into token-bearing commands. Validate behavior with an
actual branch artifact mismatch and confirm the expected PR or direct commit appears.

### 7. Model event triggers at workflow scope

Adding `labeled`, `unlabeled`, or auto-merge activity under `pull_request.types` starts the entire
workflow. Job-level `if` guards decide which jobs execute but every job is still considered and the
workflow run still exists. If only policy/convergence work should wake, split it into a dedicated
workflow; keep expensive build/test triggers unchanged.

Ensure the required-check contract remains satisfiable for every event. A required job skipped on a
new activity type can leave a context missing or produce unintended duplicate runs.

### 8. Put concurrency at workflow level

Define a stable group that matches the mutation boundary and choose cancellation deliberately:

```yaml
concurrency:
  group: policy-${{ github.event.pull_request.number || inputs.pr_number }}
  cancel-in-progress: false
```

Use per-entity groups for idempotent label/comment convergence, one serializer for single-writer tag
or dispatch flows, per-ref groups for publishers, and per-branch groups for scans. Job-level
concurrency does not serialize sibling jobs that mutate the same resource.

### 9. Normalize native-event and workflow_call context

`workflow_call` does not provide the native event entity. Declare a required typed input for the
missing issue/PR identifier. Compute one normalized identifier, validate it as positive/nonempty,
and run both triggers through the same job and mutation path. Do not duplicate native/called jobs;
they drift in permissions, conditions, and concurrency.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Slash job ID | Used `security/sast` as mapping key | Workflow produced no usable jobs | Hyphenate ID; keep slash in display name |
| Literal expression docs | Put `${{ }}` in input description | Metadata evaluated documentation | Use plain angle placeholders |
| Direct run interpolation | Embedded event text in shell | Injection sink and hook rejection | Lift to env and quote |
| Permission-only fix | Added `pull-requests: write` | Organization policy still denied PR creation | Inspect repo and org settings |
| Broad trigger expansion | Added label events to monolithic CI | Every job reran | Split event-specific policy workflow |
| Job concurrency | Serialized only one job | Sibling mutators still raced | Put group at workflow scope |
| Dual copied jobs | Duplicated event and called paths | Inputs/permissions diverged | Normalize context into one job |
| Hook bypass | Disabled edit protection | Removed the safety boundary | Use approved exact edit path and validate |

## Results & Parameters

```text
workflow path, trigger types, job IDs and display names
expression-bearing fields and untrusted-data env bindings
platform scope, rationale, tracking issue, expansion trigger
job/GITHUB_TOKEN permissions plus repository/organization policy
event-to-job matrix and required-check behavior
workflow-level concurrency group and cancellation choice
workflow_call typed inputs and normalized entity validation
workflow parser/linter result and live dispatch/PR evidence
```

## Verified On

- Workflow parse, composite metadata, injection, platform, permission, trigger, concurrency, and
  reusable-workflow cases through 2026-08-07.
- Verification remains `verified-local`; live policy-dependent outcomes are classified in notes.
