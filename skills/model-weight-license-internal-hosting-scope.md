---
name: model-weight-license-internal-hosting-scope
description: "Decide whether an open-weight model license permits a specific hosting arrangement. Use when: (1) a request asks if a license allows hosting, serving, or deploying model weights, (2) the service is described as internal, private, or behind a VPN, (3) revenue, user-count, branding, or agreement thresholds are visible in the text, or (4) two model versions ship the same license text under different names."
category: tooling
date: 2026-11-04
version: "1.0.0"
user-invocable: false
tags: [license, model-weights, open-weight, hosting, inference-service, internal-use, third-party, threshold, term-diff]
---

# Model-Weight License Scope for Internal Hosting

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-04 |
| **Objective** | Answer a hosting-permission question from the exact license text, not the model card, and test "internal" against the license definition instead of the network topology. |
| **Outcome** | Successful — direct text comparison resolved both questions in one pass. |

Model cards state the license *name*, not its *scope*. A permissive opening grant ("deal in the
Software without restriction") usually has later conditions on top. Read those conditions before you
answer. Many weight licenses publish an exemption for internal use, and that exemption often decides
the whole question.

## When to Use

- A request asks whether a license permits hosting, serving, deploying, or fine-tuning open weights.
- The requester says the arrangement is "internal only", "private", "behind a VPN", or "for staff".
- The license text contains revenue, monthly-active-user, branding, or separate-agreement thresholds.
- Two versions or tags of one model family ship nearly identical licenses, and the requester needs
  to know if the choice between them is a licensing decision.
- Some outputs of the service leave the organization, for example in delivered work products.

## Verified Workflow

### Quick Reference

Fetch the license file itself, not the rendered card. On a model hub, the restructured
`.../raw/main/<LICENSE>` URL returns the plain text.

```bash
# Fetch the license text, not the model card
curl -fsSL "<hub>/<org>/<model>/raw/main/LICENSE" -o k_a.txt
curl -fsSL "<hub>/<org>/<model2>/raw/main/LICENSE" -o k_b.txt

# Compare two family licenses, ignoring the model-name literal
diff <(sed -E 's/Kimi [K0-9.]+(-Pro)?/<MODEL>/g' k_a.txt) \
     <(sed -E 's/Kimi [K0-9.]+(-Pro)?/<MODEL>/g' k_b.txt)
```

### Suggested Approach

1. **Fetch the license file.** Use the raw file path. The card's "License: x" badge and its link
   label are not the terms, and the card can contradict the license file about which terms apply
   to the weights as opposed to the code.
2. **Read the opening grant and then every numbered condition.** Separate the grant from the
   conditions in your answer. A wide grant with a narrow-conditioned carve-out is common.
3. **Compare family versions by normalizing the model-name literal, not by title.** Two "different"
   licenses that differ only in the branding string make the version choice a capability decision,
   not a licensing decision. State this result explicitly, because a two-row table of terms is
   often all the requester needs.
4. **Bind "internal" to the license definition.** Find the definition sentence. Test three things
   separately: the software, its outputs, and its underlying capabilities. A private network does
   not make a service internal when outputs reach a third party.
5. **Identify what still applies inside the exemption.** A typical internal-use carve-out removes
   only the threshold and branding clauses. The notice, attribution, law-compliance, and
   no-warranty clauses usually stay. List these as the remaining obligations.
6. **Resolve "third party".** If the license does not define it, use the conservative reading:
   anyone who is not the licensee or its affiliates. Contractors, partners, and customers are
   candidates for a non-internal classification. Mark the boundary as an interpretation, not a
   certainty.
7. **Trace threshold clauses to their exact triggers.** Record the metric (revenue, monthly active
   users, revenue per month), the window (consecutive 12 months), and the required remedy
   (separate agreement, visible branding, nothing). Do not merge two thresholds with different
   metrics into one row.
8. **Separate the internal case from the output-leaving case in the answer.** Give one verdict for
   internal-only use, then one for the moment an output becomes a deliverable. This is the point
   where requesters usually leave the exemption without noticing.
9. **State that this is not legal advice** when the boundary is interpretive. Name the license
   contact for edge cases if the text gives one.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | --------------- |
| Answering from the model card | Used the card's license name and repository framing | The card named the code and weight terms together and did not describe the thresholds | The badge and the card prose do not carry the operative conditions. Read the license file |
| Treating "internal" as a network property | Assumed private access made the service internal | The definition keys on outputs and capabilities reaching third parties, not on routing | Test the software, outputs, and capabilities separately against the definition sentence |
| Assuming a new license name means new terms | Compared the two models only by license title | The texts differed only in the branding literal | Normalize the model-name literal and diff the body before you report a difference |
| Several obligations under the carve-out | Planned to mark the arrangement "no conditions apply" | The internal-use exemption covers only the threshold and branding clauses | Always list the notice, law-compliance, and warranty clauses that remain |

## Results & Parameters

### Configuration

```yaml
review_steps:
  - fetch: "<hub>/<org>/<model>/raw/main/LICENSE"
  - diff_family: "normalize model-name literal, compare body text"
  - classify: "internal-use exemption present? yes/no"
test_axes:
  - who_receives_the_software: "inside | outside"
  - who_receives_the_outputs: "inside | outside"
  - who_uses_the_capabilities: "inside | outside"
threshold_fields:
  - metric: "aggregate revenue | monthly active users | monthly revenue"
  - window: "consecutive 12 months | per month"
  - remedy: "separate agreement | visible branding | none"
still_applies_under_exemption:
  - "copyright and permission notice on all copies"
  - "comply with applicable law"
  - "as-is, no warranty"
```

### Expected Output

- One verdict per scenario: internal-only use, and output used in delivered work.
- A short terms table for the family comparison, with the normalization called out.
- A list of the obligations that survive the internal exemption.
- The interpretive boundaries named as such, with the license contact if published.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Mnemosyne | Analysis of two open-weight model-family licenses | Model and vendor identifiers are withheld. See [notes.md](model-weight-license-internal-hosting-scope.notes.md) for the generic term pattern. |

## References

- [ASD-STE100 writing policy](../docs/asd-ste100.md)
- [License scan marker excluded fallback](license-scan-marker-excluded-fallback.md)
- [Model version retarget for issue-tracked enablement](model-version-retarget-issue-tracked-enablement.md)