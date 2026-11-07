---
name: doc-claim-drift-liveness-and-provenance-gate
license: BSD-3-Clause
description: "Repair documentation whose prose claims drifted from forge state or from its own rules while structure gates stayed green. Use when a docs review finds stale status markers, citations to deleted stores, closed-issue references, false counts, or a template rule that no test enforces."
category: documentation
date: 2026-11-01
version: "1.1.0"
user-invocable: false
verification: verified-local
tags:
  - documentation-drift
  - prose-vs-structure-gates
  - link-liveness
  - issue-ownership
  - deleted-store-citation
  - template-rule-enforcement
  - offline-drift-gate
  - closed-tracking-epic
  - claim-inventory-first
---

# Repair Documentation Claim Drift Behind Green Structure Gates

## Overview

| Field | Value |
| ------- | ----- |
| **Date** | 2026-11-01 |
| **Objective** | Repair documentation that no longer matches the live forge state or its own rules, after link, navigation, and build gates all passed. |
| **Outcome** | A claim-by-claim inventory with a liveness rule for each claim class, a per-page decision procedure for ownership markers, and an offline gate that fails when a claim class returns. |
| **Verification** | `verified-local` — inventory counts, the marker census, and the inactive-interface vocabulary were produced by direct `git grep` and `gh api` runs at one bound revision. The remediation PR was not merged at capture time. |

Structure gates answer a narrow question: does every page resolve and appear in navigation? They
do not answer whether a page tells the truth. A documentation tree can pass a strict build, a link
check, a navigation check, and a template-shape test, and still carry claims that the forge
contradicts. Plan claim repair as its own work item, not as a follow-up to a green gate run.

## When to Use

- A review finds status markers, ownership links, or "planned" statements that no longer match
  the live tracker.
- Live pages cite a decision store, directory, or process step that the repository deleted.
- An agent-instructions file or contributor guide contradicts the same repository's own policy.
- A page states a fixed count, or claims a mapping that its own markers do not show.
- A template states a rule, and a passing test only checks the shape of the rule's example.
- A prior docs closeout claimed "zero live references" and counted links or navigation entries
  only.

## Verified Workflow

### Quick Reference

```bash
REV=<bound full SHA>   # every count is a receipt at one revision

# 1. Inventory each claim class at the bound revision. Record the count.
git grep -cE '<claim-pattern>' "$REV" -- <live-paths>

# 2. Resolve liveness against the live forge, not the reference text.
gh api "repos/<owner>/<repo>/issues?state=open&per_page=100&page=1" --jq '.[].number'

# 3. Find the tree's own vocabulary for the incomplete state before you touch a marker.
git grep -hoE '(is not active|are not active|is Planned\.|no implementing issue)' \
  "$REV" -- <live-paths> | sort | uniq -c

# 4. Gate offline with a committed allowlist; never call the network from the test.
```

### Detailed Steps

1. **Bound the review to one revision and make every count a receipt.** Record the full SHA. Each
   finding states a `file:line` and a count that a reader can reproduce with one command at that
   SHA. Re-verify at the current default-branch SHA before you file the issue; a moved base
   invalidates every coordinate.

2. **Build a claim inventory per class, and give each class a liveness rule.** A link that
   resolves is not a claim that is true. Sort the findings into these classes:

   | Claim class | Liveness question |
   | --- | --- |
   | Ownership or status marker | Does the linked record still exist and still own the work? |
   | Citation to a record store | Does the referenced store or number still resolve in the tree? |
   | Tracking or tracker reference | Is the referenced tracker still open? |
   | Fixed count or mapping claim | Does a command on the tree produce that number? |
   | Command or path in a runbook | Does the file, unit, or subcommand exist in the tree? |
   | Coverage claim about named paths | Does the pattern set name a path that every writer of that class writes, and does it leave no covered class out? |

3. **Read the template rule before you change a marker.** The template states what the marker
   carries. In the captured case the rule required a link to "the issue that owns the remaining
   work", and the shape test enforced a linked issue number. A repair that replaces the link with
   plain text violates both. Confirm the rule and the test regex first; then decide only between
   "correct owner" and "correct status word".

4. **Classify incomplete status by the tree's own vocabulary, not by intuition.** A page is
   Partial or Planned when it names an incomplete part. Find the exact phrases the tree already
   uses, then apply the rule mechanically:

   - count the incomplete-part phrases on the page;
   - zero count: the page is Active, so the status word may be wrong;
   - nonzero count: the status word is correct, and only the owner may be wrong.

   Read one page before you generalize. A page can look fully implemented at the top and name a
   planned gate 120 lines down.

5. **Verify a coverage claim against the writers, not against the pattern list.** When prose says a
   pattern set covers a class, for example "every log family", list the code sites that write a
   path of that class, and compare them with the patterns. A covered path proves one match. It does
   not prove coverage. A class with no pattern stays unrotated or unbounded, and no gate fails,
   because a pattern set with a missing entry is still valid syntax. When a range is wider than a
   constant (`{digits}` followed by a `*` tail), also confirm that the narrow reject case is a
   different length from the minimum. If the tail absorbs the case, the minimum is untested.

6. **Separate "owner missing" from "status wrong".** These are different repairs with different
   risk. An ownership repair re-points a link. A status repair changes a claim about the product.
   Report the split before you plan. Do not classify every closed-issue marker as a defect: an
   Active page can link the delivery record that closed its work, and that is not drift. Only a
   marker whose page names remaining work, but which links a closed record, is a defect.

7. **Confirm that the parent tracker is closed before you promise a re-point.** When the page's
   component epic, tracker, or delivery issue is also closed, there is no open owner to link. Then
   the choice is: open one tracking issue for the remaining work (record it in the pull-request
   body), or correct the status word. Never invent an owner.

8. **Resolve citations to a deleted store by re-homing, not by deleting.** For each citation,
   replace the dead number with the live page that now carries the rule, or inline the rule when
   no page carries it. Keep the one citation that the tree itself preserves and explains, and
   make that the only entry in the gate allowlist. Do not reintroduce the store.

9. **Treat an agent-instructions contradiction as the highest-priority finding.** When one
   section of the repository rules says a store is retired, and another section of the same file
   says it is "frozen pending" a closed issue, the file teaches both rules. Repair the
   contradictory text to the rule the repository already adopted. Do not soften it into advice.

10. **Make count and mapping claims reproducible.** Replace a stated number with a number that a
   command produces, or make the claim true by changing the tree. Run the command inside the test
   so the next change fails visibly.

11. **Gate each repaired class offline with a committed allowlist.** Follow the repository's
    existing registry style: a set of accepted values with a comment naming why each entry is
    accepted. Prove the gate fails by reintroducing one instance of each class, run the gate,
    confirm the failure, and revert. Record the proof runs in the pull-request body.

12. **Prove the class is visible to no other gate.** Run the strict build, the structural tests,
    and the link check on the unrepaired tree. If they pass, state that in the issue, so the
    reviewer accepts that a new gate is necessary and not duplicated.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Treated every closed-issue marker as drift | Counted all markers that link a closed issue as defects | Active pages legitimately link the record that delivered them; the count overstated the defect set | Split ownership defects from historical references before planning |
| Planned a link swap for every defective marker | Re-point each marker to an open owner | The component trackers were also closed, so no open owner existed | Check tracker state before you promise a re-point; open a tracking issue or correct the word |
| Replaced a status marker with plain text | Used a non-link status form when no owner existed | The template and the shape test both require a linked issue | Read the template rule and the test regex before changing the marker |
| Relabeled all owned-marker pages Active | Assumed the status words were stale after the trackers closed | Sampled pages named a planned gate deep in the body, so the word was correct | Classify by the tree's incomplete-part vocabulary, not by a reading of the opening section |

## Results & Parameters

Captured receipts at one bound revision of a large documentation tree:

- Status markers: 75 total. 51 Partial, of which 24 link a closed issue. 2 Planned, none closed.
  22 Active, of which 21 link a closed issue and only the delivery record.
- Citation to a deleted decision store: 114 lines across 32 live pages, 32 distinct numbers, and
  one number preserved with an explanation in a live page.
- Contradictory policy statements: 3 lines across 2 agent-facing files, against 1 correct
  statement in the same file.
- Component-area coverage of a template gate: 11 registered roots against 15 existing directories.
- Incomplete-part vocabulary in the tree: `is Planned.` 20, `is not active` 3, `are not active` 2,
  `no implementing issue` 1.
- Structure gates on the unrepaired tree: strict build exit 0, structural tests all pass, broken
  internal links 0 across 219 files.

### Verified On

| Project / Issue | What was observed (locally, this session) |
| --------------- | ----------------------------------------- |
| LLM360/comet, docs alignment review and issue #3866 | Full review at a bound SHA found 11 findings behind green gates. The plan was corrected three times before review: the non-link form was invalid, the trackers were closed, and the status words were mostly correct. The per-page procedure in step 4 made the work decidable. |
| LLM360/comet, review of PR #3863 | A log-rotation config claimed to cover every production log family. The pattern set was valid and the dry run passed, but one writer class had no pattern and grew without bound. Step 5 converted the claim into a check on the writers. |

## Related Skills

- `audit-doc-consistency-fix-verify-coordinates-on-disk` re-anchors drifted `file:line`
  coordinates against tracking source. This skill assumes the coordinates are correct and checks
  whether the claim itself is still true.
- `code-quality-enforcement-gates` §9 verifies audit findings before remediation and §6 asserts
  properties rather than prose. Both apply to the gate in step 10.

## Risks for the plan reviewer

- **A status repair changes a product claim.** A reviewer must check each Partial-to-Active flip
  for residual incomplete-part language, and compare it with any per-area status list on the
  system page. A wrong flip is not a link fix.
- **A committed allowlist goes stale.** Each entry names why it is accepted. An entry with a
  closed record and no comment is a defect in the gate.
- **The inventory is bound to one revision.** Any count in the issue is evidence at a SHA, not a
  contract. Recompute at the implementation base.
- **A prose gate can regress into prose-pinning.** Assert the claim class, for example that
  a citation number resolves, not the wording of a sentence.