---
name: promotion-start-body-evidence-and-epic-tag-set
description: "Open a source-to-deployed release promotion with every body claim re-derived from live refs and current merge policy, and reconcile the release epic to the full version-tagged set before the cut. Use at promotion start: opening or refreshing the promotion pull request, syncing the release epic checklist with milestone-tagged items, or restating merge gates that can drift between promotions."
category: ci-cd
date: 2026-10-30
version: "1.0.0"
user-invocable: false
verification: verified-local
license: BSD-3-Clause
tags: [promotion, release-train, release-epic, tracker-epic, milestone, title-tag, tagged-set-completeness, promotion-policy, merge-policy-drift, schema-component, snapshot-drift, gh-cli, verified-local]
---

# Promotion Start: Live Body Evidence and Epic Tagged-Set Reconciliation

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Start a release promotion: open the source-to-deployed promotion pull request and bring the release epic to closure-condition completeness in one ceremony. |
| **Outcome** | Successful. The promotion pull request opened with refs, counts, migration-tree state, and merge gate all re-derived from live evidence. The epic received the missing version-tagged items as a dated section with live checkbox state. The schema-component gate passed on first CI run. |

The promotion record is an authorization document. Every claim in it
(commit range, counts, tree diffs, merge method, label gate) authorizes
behavior, so each claim must be re-derived from live state at promotion
time, never copied from a predecessor record. The release epic's closure
condition — every item closed or deferred with a named follow-up — is
auditable only when the checklist holds every item tagged for the version.

## When to Use

- Opening the periodic or version-source `source` to `deployed` branch
  promotion pull request on its hosted forge.
- A promotion pipeline that gates on a declared schema component: a policy
  CI job compares the two migration trees and refuses a change that the
  body does not declare.
- The merge method or merge gate can change between promotions (ruleset,
  validation policy, or label-gate changes), so the predecessor promotion
  body is stale at its next reuse.
- The release epic's closure condition is "every item closed or deferred",
  and version-tagged work items arrive in the milestone after the epic body
  was written. A prompt to "add tagged items to the epic" resolves to this
  tagged-set reconciliation.
- A parent tracker groups the tagged work under one inventory issue whose
  children are tagged for the version but absent from the release epic.

Do not use this skill to merge a structurally red candidate; see
[promotion-candidate-cannot-go-green-merge-record](promotion-candidate-cannot-go-green-merge-record.md).
For the config-completeness diff that must accompany the scope record, see
[promotion-scope-branch-config-diff](promotion-scope-branch-config-diff.md).
For milestone creation and assignment sweeps upstream of this ceremony, see
[github-milestone-gh-cli-release-sweep](github-milestone-gh-cli-release-sweep.md).

## Verified Workflow

### Quick Reference

1. Duplicate guard: `gh pr list --base <deployed-branch> --head
   <source-branch> --state open` must be empty before creation.
2. Derive head, base, and commit count from live refs. Record the base as
   the newest deployed merge (`#N` of the predecessor promotion).
3. Migration-tree gate: `git diff --name-only origin/<deployed> origin/<source>
   -- <migration-root>/`. Non-empty result: the body declares the schema
   component in the documented one-line marker (`<marker-key>: <component>`).
   Empty result: the body records the verified empty diff, with the command.
4. Restate the merge gate from current validation documentation and
   branch rules: method, required checks, label gate. Never copy the
   predecessor body's gate text.
5. Tagged-set reconciliation: tagged set = milestone issues whose title
   carries the version tag. Missing set = tagged set minus issue refs in
   the epic body. Append the missing set as one dated section; checkbox
   state mirrors the live issue state.

```bash
git fetch origin <source-branch> <deployed-branch>
gh pr list -R <repo> --base <deployed-branch> --head <source-branch> --state open
git rev-list --count origin/<deployed-branch>..origin/<source-branch>
git log --oneline --no-merges origin/<deployed-branch>..origin/<source-branch>
git diff --name-only origin/<deployed-branch> origin/<source> -- <migration-root>/

gh issue list -R <repo> --milestone "<version>" --state all --limit 500 \
  --json number,title,state \
  --jq '.[] | select(.title | contains("[" + "<version>" + "]")) | [.number, .state] | @tsv'
gh issue view <epic> -R <repo> --json body --jq .body > epic-body.md
grep -oE '#[0-9]+' epic-body.md | tr -d '#' | sort -u > epic-refs.txt
comm -23 <(tagged-numbers-set) <(epic-refs.txt)   # items to attach

gh pr create -R <repo> --base <deployed-branch> --head <source-branch> \
  --title "Promote <source> (<short-sha>) to <deployed> — <version> <themes>" \
  --body-file promotion-body.md
```

### Suggested Approach

1. **Re-derive every recorded claim; the merge gate is a live claim.**
   In the observed drift, the predecessor promotion body stated that any
   merge method was permitted. Between promotions the deployed branch
   moved to merge-commit-only policy through a separate change. A body
   copied from the predecessor template would have authorized a forbidden
   merge method on the record. Restate the gate from the validation
   documentation and the branch protection state of the deployed branch
   every time: the permitted method, the required checks, and the label
   that gates CI start.
2. **Record verified absence, not silence.** When the migration tree is
   unchanged, an unstated schema component is indistinguishable from an
   unchecked one. The body names the verified empty diff with its command.
   The mirror rule applies to the scope record: cite
   `promotion-scope-branch-config-diff` evidence — additive-only entries,
   each deletion with its tracking issue — instead of claiming "nothing
   but tracked issues".
3. **Complete the tagged set before the cut, not at epic close.** Items
   tagged for the version continue to arrive after the epic body is
   written; children of an inventory tracker are tagged without being
   listed. Detect them by set difference, not by a status sweep: a status
   refresh cannot find an item the body never listed. Attach the missing
   set as one dated section so the addition is auditable; the checkbox
   mirrors the live issue state, which keeps the closure condition
   truthful.
4. **Keep one promotion record.** Refresh the table values (`Source`,
   `Target`, `Commits promoted` at last refresh) and the themes from the
   live commit range. Title names the head short-SHA and the two or three
   dominant themes of the range.
5. **State the boundary.** The promotion pull request mutates no
   deployment. The cut, the cluster install, and the deployment validation
   are the separate steps named in their runbook.
6. For live-status freshness of listed epic items before planning or
   closing, use
   [planning-epic-verify-live-child-state](planning-epic-verify-live-child-state.md).
   The tagged-set completeness check here precedes that status sweep: the
   set must be complete before any refresh is meaningful.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| N/A | The direct approach was successful: one live-evidence derivation per claim, one set-difference reconciliation, first-CI-run pass of the schema-component gate. | N/A | The failure modes this skill guards were observed as drift in predecessor records (a merge-method claim invalidated by a later policy change) and in tracker structure (version-tagged children absent from the release epic). Restate live; complete the set. |

## Results & Parameters

### Configuration

| Parameter | Value | Notes |
| --------- | ------- | ------- |
| Issue-ref extraction | `grep -oE '#[0-9]+'` over the epic body | Body refs include cross-section duplicates; deduplicate with `sort -u`. |
| Tagged-set selector | title contains `[<version>]` | Search the milestone, not the whole tracker; search text-matching titles across bodies returns body mentions as false positives. |
| Listing limit | 500+ on `gh issue list` | Default page size truncates large milestones silently. |
| Epic section marker | `## <section>. <scope> (attached <date> at the promotion start)` | One dated section per reconciliation; keep prior dated sections. |
| Checkbox mapping | closed issue -> `- [x]`, open issue -> `- [ ]` | Mirror the live state at attach time. |

### Expected Output

- An open promotion pull request whose record table, migration-tree
  verdict, scope evidence, and merge gate all trace to fresh commands or
  current validation documentation.
- The schema-component declaration present exactly when the migration
  tree changed; the policy job accepts the declared change.
- The epic holds every version-tagged milestone item in one dated
  section, with checkbox state equal to live issue state.
- No open duplicate promotion pull request for the same lane.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A release-train monorepo | Version patch promotion start: source-to-deployed promotion pull request opened for a 41-commit range; two added migrations declared; deployed branch move to merge-commit-only since the predecessor promotion; 14 version-tagged milestone items (2 closed, 12 open) attached to the release epic | Unnamed repository; live forge evidence. |

## References

- [promotion-scope-branch-config-diff](promotion-scope-branch-config-diff.md) — the config-completeness diff gate that complements these body claims.
- [promotion-candidate-cannot-go-green-merge-record](promotion-candidate-cannot-go-green-merge-record.md) — the merge-on-the-record path when a check cannot pass on the candidate branch.
- [github-milestone-gh-cli-release-sweep](github-milestone-gh-cli-release-sweep.md) — milestone creation, assignment sweeps, and tracker-epic primitives upstream of this ceremony.
- [planning-epic-verify-live-child-state](planning-epic-verify-live-child-state.md) — per-item live-state refresh of an epic checklist after set completeness holds.
