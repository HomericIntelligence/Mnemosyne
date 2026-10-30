---
name: author-response-provable-authority-binding
description: "Answer a review finding whose closure condition demands named evidence — an accepted artifact, an owning authority, an approved substitute — by binding only provable, re-derivable authority. Use when: (1) a required finding asks the plan to name an artifact that does not exist yet, (2) the honest answer to a closure condition is 'nothing today satisfies this', (3) a closure condition offers named arms (authority or substitute, supersede or re-map) and you must pick and complete exactly one, (4) restating an unexecutable criterion requires naming an operator-prerequisite owner with an in-band fail-closed gate, or (5) a reconciliation reference predates a decision that has since landed and must re-bind to the accepted record."
category: tooling
date: 2026-10-30
version: "1.0.0"
user-invocable: false
tags:
  - review-exchange
  - author-response
  - plan-review
  - evidence-binding
  - honest-gap
  - future-delivery
  - admission-gate
---

# Author Response Provable Authority Binding

## Overview

| Field | Value |
| --- | --- |
| Date | 2026-10-30 |
| Objective | Close findings that demand named evidence with answers a reviewer can re-derive, never with invented artifacts. |
| Outcome | Required findings close on the first author round; honesty claims survive independent review verification; no falsifiable existence assertions are published. |

## When to Use

- A required finding's closure condition says "name the accepted X" or "provide the verifiable substitute" and no such X exists today.
- An author response cites an artifact, issue, record, or gate, and every citation must withstand a hostile re-derivation.
- A closure condition names alternative arms and you must complete one arm fully instead of half-answering all of them.
- A criterion is unexecutable as written and the fix involves moving ownership to a named operator prerequisite.

## Verified Workflow

1. Prefer proving the negative over asserting the positive. When the demanded artifact does not exist, prove the absence by enumerated search, not by claim:
   - build or registry manifest search (for example an entry-point group declared in the package manifest; a clean grep miss);
   - call or registration site search across the source tree (every hit enumerated, each classified as production or test fake);
   - sibling issue and record search (the most plausible delivery venue, with its actual scope quoted).
   Write the enumeration into the response as the evidence: what was searched, where, and the exact result.
2. Bind the future delivery instead of inventing the artifact. Name: the delivery record (issue or change identifier) plus its contract child, the loading contract (entry point group name, loader function with file:line pins), the fail-closed admission path (the require-check that keeps the system closed until delivery lands), and the executable admission checkpoint (the command that succeeds only after exactly one delivery is installed). Record explicitly that nothing exists at the pinned base, so the current behavior remains fail-closed.
3. Pick exactly one closure arm and complete it. When closure offers arms (for example "name the authority whose acceptance applies" versus "specify the approved verifiable substitute"), choose one, say which arm, and satisfy its full checklist: the authority verbatim from its source, the exact evidence location with pins, and the verification command. Judge the arm against the code path that executes it — trace the gate yourself before citing it.
4. Move unexecutable criteria to named operator prerequisites, never to silent weakening. A criterion that cannot run inside CI becomes: named owner of enrollment and reimage, a documented operator-prerequisite procedure, an in-band fail-closed preflight gate that runs before first dispatch, and the unchanged criterion re-executed downstream of that gate. Diff the restated criteria against the originals; zero text changes to passing commands is the provable no-weakening property.
5. Re-bind reconciliation references that landed after authoring. When a referenced decision reached its terminal state between plan authoring and the author response (a sibling plan that reached GO, an accepted ADR slot), update the binding to the accepted record with exact citations (decision record, comment identifier, date) and name the single owner of any overlapping authority so two services never claim one contract.
6. Disclose your own anomalies. A mechanical imprecision you found in your own evidence (a count, a default flag firing, a digest-form mismatch) goes in the response with your analysis. Reviewers resolve a disclosed imprecision as a nit at worst; an undisclosed one reads as a trust defect and can re-open the finding.
7. Expect the reviewer mirror. Every existence claim receives an independent re-derivation (the same greps re-run, the named records fetched, the traced gate re-traced). The closure strength named in such reviews — future-delivery contract plus loading contract plus fail-closed admission plus executable checkpoint — closes "the central blocker lacks an executable path". Anything weaker does not.

### Quick Reference

| Situation | Binding move |
| --- | --- |
| Demanded artifact does not exist | Prove absence by enumerated search; bind the named future delivery + loading contract + fail-closed admission |
| Closure offers alternative arms | Choose exactly one arm; complete its full checklist with verbatim authority and verification command |
| Criterion unexecutable in CI | Named owner + operator prerequisite + in-band fail-closed preflight + unchanged criteria downstream |
| Referenced decision landed after authoring | Re-bind to the accepted record with exact citations; name the single authority owner |
| Own evidence imprecision found | Disclose it with analysis in the author response |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| 1 | Leave the central blocker's acceptance path as a conditional placeholder ("only if accepted") | Two consecutive review rounds kept the gate closed: a conditional with no authority has no executable path | Convert the placeholder into a named arm: either the authority's verbatim acceptance text or the approved substitute plus its verification command |
| 2 | Assert a due-to-exist artifact by name alone with a delivery promise | An existence assertion without a re-derivable path is a falsifiable claim; the reviewer standard rejects it and the finding re-opens | Enumerate the absence proof instead, and transfer the claim to a named future delivery with an executable admission checkpoint |
| 3 | Quietly restate blocking criteria in weaker form so they pass | Weakening disguised as restatement is detected by a before-and-after diff of the criteria text and becomes a required finding | Restate around unchanged criterion text; move the unexecutable part to a named operator prerequisite with a fail-closed preflight |
| 4 | Keep the reconciliation text that predates a landed sibling decision | The plan read as superseding a design that had since been accepted, so the review treated the reconciliation as stale | Re-bind the reconciliation to the accepted record and name the single owner of the overlapping authority |

## Results & Parameters

- Absence enumeration output per claim: the manifest search, the call-site search (production versus test fakes), and the sibling-scope quote — all reproducible.
- Future-delivery binding fields: delivery identifier, contract child, entry-point group, loader pin, fail-closed require pin, admission checkpoint command, acceptance-evidence location.
- Closure-arm output: chosen arm name, verbatim authority quote, evidence pins, verification command.
- No-weakening property: byte-identical criterion commands across the restatement, with only ownership and gating text added around them.
- Citation minimum for landed-after-authoring references: record identifier, comment or revision identifier, and date.

## Verified On

- A two-round plan/review exchange on a stage-gated host-integration blocker: the demanded reviewed adapter existed nowhere (manifest group absent, registration only in runtime plus two test fakes, sibling delivery issue scoped to a different harness); the response bound the named delivery record plus contract child, loader and fail-closed require pins, and an executable admission command. Independent review re-ran every search, fetched both named issues, judged the future-delivery contract as closing, and verified the approval.
- The same exchange's comparison-finding closure: the author chose the documented substitute arm with authority quoted from the parent issue ("where practical"), pinned the disposition record and its manifest default, and the reviewer executed the gate trace to confirm a drifted disposition fails closed.
- A runner-contract finding on a fast-moving automation repository: all 40+ workflow `runs-on` values recounted, zero self-hosted targets, criteria re-executed unchanged downstream of a named operator-owned runner group and a fail-closed clean-preflight with attestation; reviewer confirmed executability-by-construction by diffing the revisions for disguised weakening and finding none.
- An ADR acceptance-clause finding whose named gate test existed only in the ADR text: resolved by the closure's re-map arm with intent preserved (non-skipping, fail-closed identity gate) and a superseded-in-part marking planned; the reviewer verified the re-map's anchors.
- Two author self-disclosures (an incidental default-flag firing and a digest-form mismatch) resolved by reviewers as accurate or as analyst error, with no trust impact.

## References

- Companion view from the reviewer side: `planning-verify-issue-premise-before-implementing` (premise checks against authoritative sources, the zero-match-grep three-explanations trap) — this entry is the author-side doctrine for producing answers that pass such verification.
- `debugging-absence-of-evidence-verify-with-authority` covers the debugging-direction absence trap for conclusion claims in shared threads.
