---
name: documentation-github-issue-final-report-live-body
license: BSD-3-Clause
description: "Rewrite live issue, pull-request, comment, and evidence artifacts into one coherent public report without stale overwrites, provenance loss, or disclosure. Use when: (1) an issue contains incremental notes or obsolete detours, (2) an exact implementation plan has a terminal GO review and must become a reader-first handoff, (3) publication must preserve concurrent edits and source identities, (4) public artifacts may contain sensitive operator or environment details."
category: documentation
date: 2026-07-06
version: "1.2.0"
user-invocable: false
verification: verified-ci
history: documentation-github-issue-final-report-live-body.history
tags: [github, issues, pull-requests, comments, final-report, implementation-plan, go-review, provenance, live-body, redaction, concurrent-edits]
---

# GitHub Issue Final Report Live Body

## Overview

| Field | Value |
| --- | --- |
| **Objective** | Convert incremental public artifacts into a coherent final report or implementation handoff while preserving live edits, exact source provenance, and public-artifact hygiene. |
| **Outcome** | Successful. The workflow binds the live sources, composes from their accepted decisions, revalidates immediately before one authorized write, and verifies the published artifact. |
| **Verification** | The general live-body workflow is CI-verified. The reviewed-plan extension was verified through an exact plan-plus-GO read, one guarded issue-body rewrite, and live readback. |

## When to Use

- An issue body reads like a chronological investigation rather than a final report.
- A canonical implementation plan and its terminal GO review must become the issue's readable implementation handoff.
- A rewrite must preserve user edits made after an earlier draft was prepared.
- The public artifact must retain decisions and evidence while removing stale, sensitive, or operator-local details.
- Durable evidence is spread across a body, comments, review comments, or automation mirrors.

Do not use this workflow to turn a NO-GO review into an implementation handoff, to invent missing
requirements, or to hide unresolved findings. Material requirement changes start a new planning and
review epoch.

## Verified Workflow

### Quick Reference

```text
1. Fetch the live destination and every authoritative source artifact.
2. Bind source identities, normalized content digests, actors, and update timestamps.
3. Require one canonical plan and one terminal GO review bound to that exact plan.
4. Compose a complete reader-first artifact from requirements and accepted plan decisions.
5. Re-fetch and compare all bindings immediately before publication.
6. Publish once through the authorized mutation boundary.
7. Read back the live artifact and verify presence, absence, provenance, and privacy.
```

### 1. Bind the authoritative source set

For an ordinary final report, bind the current live body and every comment or evidence mirror that
contains a conclusion still needed in the result. For a reviewed-plan handoff, bind all three inputs:

| Input | Required identity |
| --- | --- |
| Requirements | Issue identity, normalized pre-publication body digest, and update timestamp |
| Canonical plan | Unique marker or role, comment identity, author ownership, update timestamp, and normalized content digest |
| Terminal review | Unique marker or role, comment identity, reviewer ownership, update timestamp, terminal status, and the requirements and plan digests it reviewed |

Titles, URLs, comment order, and labels are discovery aids, not identity. Fail closed when a source
is missing, duplicated, foreign-owned, stale, or internally inconsistent.

The review must bind the exact canonical plan digest and the same requirements digest. A GO review is
evidence that the plan is acceptable; it is not permission to add suggestions or new scope that the
plan did not accept.

### 2. Seal the planning epoch before changing the body

Treat the pre-publication requirements, canonical plan, and terminal review as immutable inputs to
one finalization attempt. The final issue body is output from that sealed source set.

This distinction prevents a digest loop: replacing the issue body necessarily changes a digest that
was computed from the old requirements body. Preserve the old requirements digest as provenance for
the completed epoch. Do not claim that it describes the new body, and never define an artifact digest
over bytes that include the digest value itself. If the published body also needs an identity, compute
it after publication or define normalization that excludes its own identity field.

### 3. Compose the reader-first artifact

Preserve the original reason and the accepted plan; remove iteration chatter and duplicated review
prose. For an implementation handoff, prefer this order:

```text
## Why
## System shape                 # only when relationships warrant a diagram
## Architecture breakdown      # decisions, ownership, boundaries, invariants
## Review status               # compact status plus source provenance
## Implementation plan         # behavior-first sequence
## Cutover and rollback
## Acceptance criteria
## Validation
## Dependencies and residuals
```

Use the requirements for the problem and constraints, the plan for the solution, and the review only
for disposition and accepted corrections. Do not replace the plan with a summary, a review recap, a
revision diff, or a list of findings. Do not silently drop non-goals, failure boundaries, tests,
rollback behavior, dependencies, or unresolved operational parameters.

For investigation reports, use the smallest structure that preserves the final finding, environment,
evidence, reproduction, controls, expected behavior, acceptance criteria, and validation. Convert
chronology into final-state language such as `observed`, `not observed`, `verified`, or
`inconclusive`.

### 4. Apply public-artifact hygiene

Before publication, scan the draft and all durable public surfaces. Generalize or remove:

- personal, account, customer, organization, or non-public project identifiers;
- internal hostnames, URLs, repository names, environment names, and infrastructure details;
- absolute paths, local cache or scratch locations, operator names, and allocation identifiers;
- secrets, tokens, proprietary payloads, raw logs, or unneeded operational metrics; and
- obsolete detours or raw reasoning that do not change the final conclusion.

Keep only the request or response shape, relevant controls, conclusions, and safely shareable
evidence needed to execute or verify the result.

### 5. Revalidate immediately before the write

Re-fetch the destination plus every bound source. Compare identities, ownership, timestamps,
normalized digests, plan-review binding, and terminal status. Abort instead of merging implicitly if:

- the destination or any source changed;
- another canonical plan or terminal review appeared;
- the review no longer binds the exact plan and requirements;
- the review is not GO or contains unresolved required findings; or
- the authenticated actor lacks explicit authority to replace the destination body.

If the destination changed only because of a known user edit, restart from the new live source and
merge deliberately. Never publish from an older local draft.

### 6. Publish once and verify the live result

Use one body mutation. Then fetch the live artifact rather than trusting the local file or command
exit code. Verify:

- every required section and accepted decision exists;
- source links or stable identities point to the exact plan and review;
- no new scope, unresolved finding, or stale iteration language was introduced;
- forbidden sensitive details are absent across the body and durable comments; and
- the live body is byte-equivalent to the approved candidate after provider normalization, or its
  normalized digest matches the expected candidate digest.

If readback differs, stop and preserve evidence. Do not retry with another blind overwrite.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Publish an old local draft | Reused a body prepared before later live edits | It can overwrite user changes or resurrect stale language | Re-read and rebind the live destination immediately before mutation |
| Replace the plan with a summary or review recap | Posted conclusions, findings, or a revision delta as the final artifact | Implementers lose exact steps, tests, rollback, and accepted constraints | The final handoff is the complete accepted plan in reader-first order |
| Hash the mutable destination as both input and output identity | Treated the pre-review requirements digest as if it also identified the rewritten body | Publication changes the bytes and invalidates its own provenance | Seal the source epoch and keep input identity distinct from published-output identity |
| Treat GO as fresh mutation authority | Used review success without rebinding sources and actor authority | GO proves plan quality, not that live artifacts stayed unchanged or that a write is authorized | Revalidate exact artifacts and mutation authority immediately before the write |
| Clean only the latest body | Left sensitive or stale material in older comments and evidence mirrors | The durable public timeline still exposed or contradicted the final report | Scan every durable public surface and verify absence after publication |

## Results & Parameters

### Minimal identity record

```yaml
requirements:
  artifact_id: "<stable-issue-id>"
  content_digest: "<normalized-pre-publication-digest>"
  updated_at: "<timestamp>"
plan:
  artifact_id: "<stable-comment-id>"
  actor_id: "<stable-actor-id>"
  content_digest: "<normalized-plan-digest>"
  updated_at: "<timestamp>"
review:
  artifact_id: "<stable-comment-id>"
  actor_id: "<stable-reviewer-id>"
  status: "GO"
  requirements_digest: "<normalized-pre-publication-digest>"
  plan_digest: "<normalized-plan-digest>"
  updated_at: "<timestamp>"
candidate:
  content_digest: "<normalized-final-body-digest>"
```

### Decision table

| Condition | Result |
| --- | --- |
| One owned canonical plan, exact terminal GO binding, no drift | Compose, revalidate, publish once, and read back |
| Destination or source timestamp/digest changed | Abort and restart from live sources |
| Multiple or foreign canonical artifacts | Abort; resolve authority explicitly |
| NO-GO or unresolved required finding | Do not finalize; return to planning |
| Material requirements change after GO | Start a new planning/review epoch |
| Candidate cannot be generalized safely for public use | Do not publish |

### Verification checklist

```text
[ ] Live destination and all authoritative sources were fetched.
[ ] Stable IDs, actors, timestamps, and normalized digests were recorded.
[ ] The terminal GO review binds the exact requirements and canonical plan.
[ ] The candidate begins with the reason and retains the complete accepted plan.
[ ] Diagram, architecture, implementation, tests, rollback, and acceptance are present when applicable.
[ ] Review prose did not introduce unaccepted scope.
[ ] Sensitive identifiers and obsolete detours are absent from every durable surface.
[ ] Every binding was rechecked immediately before the single write.
[ ] The live readback matches the approved candidate after normalization.
```

## Verified On

| Surface | Context | Evidence |
| --- | --- | --- |
| Public issue tracker | Final report rewrite after an operational investigation | Live read, guarded single update, public-hygiene scan, and live readback |
| Public issue tracker | Reader-first handoff from an exact canonical plan and terminal GO review | Exact source binding, one body rewrite, preserved provenance, and live readback |
| Public review artifacts | Body, comments, review comments, and evidence mirrors | CI-backed checks for required content and absence of local operator details |
