---
name: identifier-citations-source-lookup
description: "Verify every implementation identifier a deliverable cites as existing evidence against the live source before publication, and convert a failed lookup to an explicit coverage limit instead of a substitute claim. Use when (1) review prose, a review carrier, a PR body, or a plan asserts that a named function, guard, seal, validator, or policy table exists and does something, (2) the citation comes from memory, naming conventions, or adjacent code rather than a fresh lookup, (3) the text will be bound as evidence (for example a digest-bound exchange carrier or a terminal review), or (4) you audit your own already-delivered text and a lookup contradicts a term you used, because a term can resolve to a real but different concept and then needs revocation, not a silent rewrite."
category: architecture
date: 2026-10-30
version: "1.1.0"
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
- You audit text you already delivered, and a lookup shows that a term you used names a real but different concept. That is a separate branch from an absent identifier: see [Revoke a real-but-wrong identifier](#revoke-a-real-but-wrong-identifier).

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

### Revoke a real-but-wrong identifier

An identifier misses in three ways, not two. "Absent" and "verified" are the
obvious ends. The middle case is a term that is real in the domain, so a
lookup succeeds on the string while the text uses the wrong concept. A
near-miss token is the usual sign: a correct term with one character
substituted, a plural where the domain uses a singular, or a standard term
from the neighbouring field.

1. Treat a near-miss token as unverified. Do not accept it because the string
   resolves or because the reader will "know what it means".
2. Look up the token and the intended term together, on the exact bound
   revision, before you write the sentence.
3. If the intended term is real and correct, use it. If no term is correct,
   apply the absent-identifier recovery.
4. Audit delivered text for the same branch. Extract the tokens that carry
   technical meaning, then compare each one with the source vocabulary. A
   spelling variant that is also a real token will not fail any schema, diff,
   or readback check, because the output stayed machine-valid.
5. When the text is already published or byte-bound, correct it explicitly:
   name the wrong term, name the correct term, and state that the earlier
   text held the defect. Do not rewrite the sentence silently; downstream
   consumers may already have quoted it.

The failure mode: no gate catches this class. A schema check accepts any
string, an exact readback proves byte fidelity and not correctness, and a
reviewer who shares the author's vocabulary reads the term as intended. Only
a deliberate term audit finds it.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Draft from memory, publish directly | Write the rationale section from remembered architecture and publish the carrier. | A convention-shaped but nonexistent seal identifier nearly shipped inside an evidence-bound review; only a pre-publication lookup caught it. | Bind the lookup to the same revision as the publish step; memory of a codebase's vocabulary is the fabrication hazard itself. |
| Accept a token because the string is real | Delivered a structured report that used a one-character variant of a standard term. The string resolved as a genuine domain token, the structure validated, and the echo-back matched byte for byte. | No gate checks term choice: the schema accepts any string, readback proves fidelity and not correctness, and the self-review shared the author's vocabulary. | A near-miss token that resolves to a different real concept is still an error. Audit technical terms against the source vocabulary, and correct published text explicitly. |

## Results & Parameters

### Configuration

- One symbol lookup per cited identifier, run at the exact reviewed revision, immediately before publication.
- On lookup failure: claim removal plus a coverage-limit sentence in the same section; no substitute claim.
- On a near-miss token: look up the token and the intended term together before you accept either.
- On a defect in published text: name the wrong term, name the correct term, and mark the earlier text as defective.

### Verification

Proven on a live review round: one fabricated-style seal citation was removed pre-publication after its lookup returned nothing, the corrected coverage-limit text was bound and published, and the review's terminal state merged. The revocation branch comes from a later session that found the defect only in its own post-publication audit. The pattern entry itself is a discipline rule; its verification level is verified-local because the incidents and recoveries are documented from bound deliverables.
