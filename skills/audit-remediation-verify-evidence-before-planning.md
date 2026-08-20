---
name: audit-remediation-verify-evidence-before-planning
description: >-
  Verify every audit claim against the live tree before planning remediation. Use when
  cited lines, SHAs, paths, counts, or multi-target findings may be stale; when ownership
  limits the edit; or when a document mixes verifiable membership with inferred history.
category: architecture
date: 2026-07-01
version: "2.0.0"
user-invocable: false
verification: verified-local
license: BSD-3-Clause
history: audit-remediation-verify-evidence-before-planning.history
tags: [audit, remediation, evidence, stale-finding, stale-line-cite, scope-control, verification-boundary]
---

# Audit Remediation: Verify Evidence Before Planning

**Supporting cases:** [notes](./audit-remediation-verify-evidence-before-planning.notes.md)

**Superseded content:** [history](./audit-remediation-verify-evidence-before-planning.history)

## Overview

An audit records a past snapshot. Its line numbers, action SHAs, counts, target set, and even
named artifacts can drift independently. Before planning, relocate each claim by semantic
content, identify the current authority, and classify each target as actionable, already fixed,
partially fixed, or unverifiable. Fix only the owned, issue-named defect class unless the same
defect necessarily spans a sibling artifact.

This workflow is `verified-local` for evidence diagnosis. Some downstream remediation designs
captured in prior cases were plan-only; the notes preserve those boundaries and must not be read
as CI evidence.

## When to Use

- An issue cites `file:line`, a commit SHA, an action pin, a path, or a count from an audit.
- A finding names several targets and some may have been independently remediated.
- A path is in a submodule or separately owned repository.
- A predecessor issue or captured plan claims to have introduced an artifact you depend on.
- A doc table has verifiable membership but historical/version fields cannot be recovered.
- A proposed docs or frontmatter fix has no existing executable test contract.
- A short search term can collide with sibling names, such as `git` inside `github`.

## Verified Workflow

1. **Bind the implementation base.** Record the immutable commit and read the current issue.
   Re-run the evidence checks immediately before editing.
2. **Relocate by content, not coordinates.** Search for the described section, action name,
   symbol, or semantic marker. A stale line cite does not imply a stale finding.
3. **Verify every target independently.** For each named path, test both existence and the
   actual defect. A multi-target audit may be partially stale.
4. **Find the source of truth.** Read schemas/models for authored field names, serializers for
   wire keys, manifests for membership, and existing tests/validators for enforced contracts.
   These layers may intentionally use different names.
5. **Check ownership.** Do not edit a submodule or external repository through a meta-repo.
   Identify the owned artifact and the correct repository/PR boundary.
6. **Survey enough to determine scope.** Inspect siblings to understand the convention and find
   identical copies of the same defect. Record unrelated noncompliance as out of scope.
7. **Classify evidence.** Distinguish:
   - stale coordinates, valid content finding;
   - valid coordinates, already-fixed finding;
   - partially stale multi-target finding;
   - fully stale finding with no remaining artifact;
   - unverifiable historical metadata.
8. **Choose enforcement at the existing altitude.** Extend a nearby behavior or content test.
   Do not create a framework for a one-field prose change, and do not invent a unit test where
   repository policy uses parsing/lint checks only.
9. **Guard only provable claims.** If membership is derived from `__all__` but an “Added” value
   is best-effort archaeology, test membership both ways and label the historical value as
   inferred. Never turn inference into an asserted fact.
10. **Verify the proposed command or external contract.** Run replacement commands in this
    repository. Check a third-party action input against the pinned action definition; a text
    assertion cannot prove the input is valid.
11. **Report no-op outcomes honestly.** If every target is gone and an existing guard prevents
    recurrence, close with evidence rather than manufacturing a diff.

### Evidence commands

```bash
git rev-parse HEAD
rg -n '<described section or symbol>' <named paths>
test -e <claimed-artifact>
git ls-files -- <claimed-path-or-population>
git log -S '<symbol>' --reverse -- <owned-path>
rg -n '<existing guard or contract>' tests scripts .github
```

Treat each command as a question with an expected result. Record the actual result, including
empty output. When a scoped pytest run reports passed tests but fails a global coverage floor,
separate the behavioral result from the repository-wide gate; do not call the command green.

### Scope decisions

- **Same defect, same owned surface:** fold in a sibling copy when leaving it would preserve the
  identical contradiction.
- **Different defect discovered during survey:** note it, but do not expand the issue.
- **Already fixed target:** make no edit and cite the evidence.
- **External/submodule target:** open or plan work in the owning repository.
- **No test contract for prose/frontmatter:** validate structured syntax and run the repository's
  standard lint/gate; do not pin wording.

### Mixed-verifiability tables

Build the live symbol set from the authoritative export and compare it to documented membership
in both directions. Infer historical anchors only when required, label the method and uncertainty,
and exclude the inferred values from the drift guard. A deprecated exported symbol still needs a
membership row until it leaves the authoritative surface.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Navigate directly to the cited line | Navigate directly to the cited line | Insertions move coordinates while content remains | Search for the described section or symbol |
| Treat stale coordinates as a stale finding | Treat stale coordinates as a stale finding | The defect may still exist elsewhere in the file | Verify coordinates and content separately |
| Apply one conclusion to all named targets | Apply one conclusion to all named targets | Multi-target audits become partially stale | Check each defect independently |
| Assume a captured plan shipped | Assume a captured plan shipped | Plans are not repository artifacts | Test for the file, symbol, test, and merged commit |
| Use a prefix substring such as `pkg.git` | Use a prefix substring such as `pkg.git` | Sibling names such as `pkg.github` create false positives | Anchor package boundaries and exclude known collisions |
| Trust audit counts or SHAs | Trust audit counts or SHAs | Membership and workflow pins drift quickly | Re-derive from the current authority |
| Invent a test for ungoverned prose | Invent a test for ungoverned prose | It pins wording without a product contract | Use syntax/lint checks or extend an existing semantic guard |
| Assert an inferred historical value | Assert an inferred historical value | Best-effort archaeology becomes false certainty | Label inference and guard only membership |
| Validate an action input with text presence | Validate an action input with text presence | The name can be invalid at the pinned revision | Inspect the pinned `action.yml` or upstream contract |

## Results & Parameters

| Parameter | Rule |
| --- | --- |
| Base | Immutable commit recorded before evidence collection |
| Coordinates | Hints only; relocate by semantic content |
| Multi-target scope | Per-target classification, never all-or-nothing |
| Ownership | Edit only the repository that owns the artifact |
| Source of truth | Model/schema, serializer, manifest, or existing enforced test |
| Sibling expansion | Only the same defect on the same owned surface |
| Historical values | Best-effort and explicitly labeled when unrecoverable |
| New tests | Match an existing product contract and enforcement altitude |
| External inputs | Verify against the pinned upstream definition |
| Fully stale result | Evidence-backed no-op or documentary close |

A sound remediation plan contains current evidence, an explicit disposition for every named
target, a narrow edit boundary, verification that matches what is actually provable, and a list
of remaining uncertainties. Case-specific commands and issue/PR outcomes are indexed in notes.
