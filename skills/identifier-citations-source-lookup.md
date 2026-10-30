---
name: identifier-citations-source-lookup
description: "Verify every implementation identifier a deliverable cites as existing evidence against the live source before publication, and convert a failed lookup to an explicit coverage limit instead of a substitute claim. Use when (1) review prose, a review carrier, a PR body, or a plan asserts that a named function, guard, seal, validator, or policy table exists and does something, (2) the citation comes from memory, naming conventions, or adjacent code rather than a fresh lookup, or (3) the text will be bound as evidence (for example a digest-bound exchange carrier or a terminal review)."
category: architecture
date: 2026-10-30
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - code-review
  - evidence
  - hallucination
  - identifiers
  - grep
  - coverage-limit
  - delivery-text
---

# Identifier Citations Need a Source Lookup Before Publication

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Keep citations of named implementation structure (guards, seals, validators, policy tables) in evidence-bound text true at the moment of publication. |
| **Outcome** | Successful. A fabricated-seal citation was caught by a lookup before publication, removed, and replaced with an honest coverage statement; the corrected text was then bound and merged. |

## When to Use

- You draft review prose, a review exchange carrier, a PR body, or a plan that says a named symbol does something: "the registry seals X", "`foo_bar()` rejects Y", "policy table Z declares the mode".
- The identifier came from memory, from the naming conventions of the codebase, or from adjacent code you read earlier, not from a current lookup.
- The deliverable is evidence-bound: an exchange carrier whose digest binds the exact text, a terminal review that later workflows read as evidence, or a plan that gates implementation.
- You cite a control as justification for narrowing or widening scope (for example "this shape is already sealed at bind time, so the new check can stay equality-only").

Do not use this entry for numeric or arithmetic claims in delivery text; that intent has its own entry, `planning-pr-body-numeric-claims-source-derived`, whose recovery is an explicit placeholder for an unavailable measurement. The distinction: a number is either available or not; an identifier can be fabricated whole, so the recovery is removal plus a coverage statement, not a placeholder.

## Verified Workflow

### Quick Reference

```text
Before publication, for each cited identifier:
  1. Look it up against the live source (grep / symbol search on the
     exact reviewed revision, not on a stale or adjacent checkout).
  2. Missing or contradicting   -> remove the claim; write an explicit
     coverage-limit sentence ("whether a nested binding can be
     constructed at all is not established by this review").
  3. Verified                   -> keep the claim; cite the location
     narrowly (file or harness), so a later drift is discoverable.
Never keep an unverified identifier because it "should exist" under
the codebase's naming conventions.
```

### Suggested Approach

1. Treat every prose sentence of the shape "`X does Y`" or "`X prevents Z`" as a factual claim, including sentences inside coverage-limit or rationale sections. Those sections read as caveats but still bind evidence when the text is published.
2. Run one lookup for each identifier in the same revision the deliverable binds. On a heavy-traffic base, confirm the lookup target is the exact reviewed revision, not an older or newer tree.
3. Classify each lookup before you write the final sentence: verified claim (keep), absent concept (remove), concept present under a different name (verify behavior, then cite the real identifier), contradicted behavior (remove and report; that is a finding, not a citation).
4. Replace an absent claim with the coverage-limit form, not with a weaker synonym of the same claim. "The boundary is equality-only; whether a nested binding can be constructed is not established by this review" tells the reader exactly what is unknown. "The registry seals overlapping roots" tells the reader something false.
5. Keep the lookup evidence (command, revision, result) in session notes so the correction survives a checkpoint. A digest-bound carrier makes post-publication correction expensive.

### Failure Shapes to Recognize

- A convention-shaped name passes review: `disallow_lanes_that_overlap_public` fits the codebase vocabulary, so no reader flags it, and grep over the tree finds nothing.
- Justification-by-seal: a scope decision ("stay equality-only") leans on a seal that does not exist, silently weakening the cited rationale for a boundary that ships.
- Stale-but-real citations: the identifier exists on an older checkout and was renamed, so memory is almost right; the lookup must target the exact reviewed revision.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Draft from memory, publish directly | Write the rationale section from remembered architecture and publish the carrier. | A convention-shaped but nonexistent seal identifier nearly shipped inside an evidence-bound review; only a pre-publication lookup caught it. | Bind the lookup to the same revision as the publish step; memory of a codebase's vocabulary is the fabrication hazard itself. |

## Results & Parameters

### Configuration

- One symbol lookup per cited identifier, run at the exact reviewed revision, immediately before publication.
- On lookup failure: claim removal plus a coverage-limit sentence in the same section; no substitute claim.

### Verification

Proven on a live review round: one fabricated-style seal citation was removed pre-publication after its lookup returned nothing, the corrected coverage-limit text was bound and published, and the review's terminal state merged. The pattern entry itself is a discipline rule; its verification level is verified-local because the incident and recovery are documented from one bound deliverable.
