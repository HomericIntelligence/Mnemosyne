---
name: github-release-board-realignment
description: "Realign a whole GitHub repository board when a release calendar changes after issues and PRs are already milestoned. Use when: (1) a release schedule is restated and hundreds of items must move between milestones, (2) already-milestoned members must be re-classified under restated scope rules by topical ownership, not token mention, (3) milestone titles and due dates change but assignments must survive, (4) the sweep must cover pull requests, which `gh issue list` never returns, (5) the board must end with zero unassigned items and stay that way as automation adds work."
category: tooling
date: 2026-11-16
version: "1.1.0"
license: BSD-3-Clause
user-invocable: false
tags: [github, milestone, release-board, triage, gh-api, bulk-edit, catch-all, tracker-epic, due-date, realignment]
---

# GitHub Release Board Realignment

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-16 |
| **Objective** | Move an entire open-issue and open-PR board onto a restated release calendar without losing existing assignments, silently dropping items, or leaving new arrivals unswept. Re-classify already-milestoned members when the owner restates cut scope rules. |
| **Outcome** | Operational. One realignment pass retitled and re-dated 5 milestones, created 8 more, swept ~700 issues and ~21 PRs across 13 milestones, verified zero unassigned in both sets, and absorbed a dozen automation-created arrivals on a re-sweep. A later pass re-classified a 270-member release cut under restated scope rules and moved 32 members across two destination cuts with zero failures. |

## When to Use

- The owner restates a release calendar (new versions, splits, or dates) after
  milestones already exist and carry members.
- A large open-issue set is mostly or partly unmilestoned and must be mapped
  onto a new calendar in one pass.
- Milestone titles change while their membership must survive unchanged.
- Automation or other actors keep opening issues and PRs during the realignment,
  so a single sweep cannot be the last check.
- A team uses one tracker epic per milestone and needs transfer history recorded
  without rewriting prior scope.
- The owner restates cut scope rules (a lane, engine feature, or model family
  defers to a later cut) and already-milestoned members must be re-classified
  against the new rules.

## Verified Workflow

### Quick Reference

```bash
# Retitle + re-date keeps every member: milestones bind by number, not title.
gh api -X PATCH repos/OWNER/REPO/milestones/NUM \
  -F title="v0.3.x" -F due_on="2026-11-13T12:00:00Z" --jq '.title,.due_on'

# Verify coverage in BOTH sets; gh issue list never returns PRs.
gh issue list --state open --limit 1000 --json milestone \
  --jq '[.[] | select(.milestone == null)] | length'
gh pr list --state open --limit 100 --json milestone \
  --jq '[.[] | select(.milestone == null)] | length'
```

### Suggested Approach

Sequence the pass as four stages; each has its own failure mode.

1. **Change the calendar, not the membership.** Existing milestones are bound
   by numeric ID. `PATCH` title and `due_on` keeps every assignment; only
   create new milestones, never delete-and-recreate one that has members.
   After a retitle, resolve the milestone by its new title: `gh issue edit
   --milestone "<title>"` matches titles, so do membership edits after the
   rename.
2. **Sweep unassigned items with ordered rules on title plus labels.** Fetch
   every open issue once (`--limit 1000` or paging), then bucket in priority
   order: explicit ID pins > typed labels > title prefix tokens > keyword
   family > a catch-all milestone. The catch-all milestone (for example a
   late "triage" cut) is load-bearing: without it, unmatched items stay
   unassigned and the board lies. Title prefixes matter because labeled rules
   alone miss items like a `[bug]:`-titled issue that carries no `bug` label.
3. **Sweep PRs separately and classify by linked issue.** PRs are invisible to
   `gh issue list`. Milestone each open PR to the milestone of the issue its
   title or branch references; default active gate/promotion PRs to the
   currently cutting milestone.
4. **Verify, then re-verify after arrests.** Print per-milestone counts and
   the two zero-unassigned queries, fix any misses, and re-run the queries.
   Expect new issues and PRs to arrive from wave automation between passes;
   schedule a re-sweep and classify arrivals by their linked issue.

Record every move set (ID → milestone) in a file before applying it; apply
with per-item failure capture instead of aborting the batch.

### Classify members for a scope transfer

Re-classifying already-milestoned members against restated scope rules is a
decision pass, not a keyword sweep. A keyword-family rule that buckets on
token presence alone mis-sorts members that merely mention the deferred
subject. Apply these rules in order:

1. **Scan with untruncated bodies.** A first classification scan over length-capped
   body fields (list previews or snippet truncation) silently misses members whose
   token appears past the cap. Run the same member query with full, untruncated
   bodies before applying, and reconcile the two result sets. A measured pass found
   six additional candidates only on the untruncated re-scan.
2. **Read the match context for every hit.** A member belongs to the destination
   cut only when it is about the deferred subject. Incidental mentions stay:
   rollout-target lists, incident examples, revision-pin tables, cluster-id
   enumerations, and mechanism descriptions that name the subject once. Print the
   surrounding text of every match and decide on that context, not on hit count.
3. **Consumer-scoped markers keep shared mechanisms in place.** A member whose
   body scopes a shared mechanism to a named consumer only (for example "these
   source requirements apply to the consumer only; the shared mechanism keeps its
   existing general scope") stays when the consumer family defers. Only
   family-owned members — enablement, qualification, staging, pinned images and
   configuration, and the family epic — move with the family.
4. **Verify member counts as a sum.** Record before counts per milestone, apply
   the move set, then check that every destination gained exactly the moved count
   and the source lost exactly that count before running the zero-unassigned
   queries. A re-scan of the residual source membership for the deferred tokens
   confirms that every remaining mention is a verified incidental one.

Supporting detail, including the measured floor of this pass, is in
[github-release-board-realignment.notes.md](github-release-board-realignment.notes.md).

### Tracker epics and due dates

- One tracker epic per milestone, labeled so dispatch automation skips it, in
  its own milestone. The body holds the roster, ordering, closure condition,
  and a deferral section. Transfers between milestones are recorded as body
  sections; do not silently delete roster lines; GitHub renders the milestone
  progress bar from assignment, and the body is the explainable record.
- GitHub issues have no per-issue due-date field. The milestone `due_on` is
  the date of record; repeat the date in the tracker body text.
- A past due date marks the milestone overdue in the UI. That can be a
  deliberate "cut this now" signal, but set it deliberately and tell the
  owner, not by accident.
- If a transfer supersedes a dated operator direction recorded in the tracker
  epic body, reconcile the epic in the same pass: post a supersession comment
  that names the new direction date and the full move list, rewrite the affected
  body section to record which members moved and which stayed, and retitle the
  epic when its title asserts the superseded scope. An unreconciled epic keeps
  claiming the transferred scope and the release plan lies.

### Housekeeping on arrival

Mid-sweep arrivals sometimes self-declare scope (a new issue that names its
target version in the title, or a PR opened against an existing milestone's
issue). Assign by that declaration and cross-link overlapping work instead
of closing either side; the linkage is the conflict-resolution record.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| `gh milestone create` | The `gh` CLI milestone subcommand. | Not present in the installed CLI version. | Keep a REST fallback: `gh api repos/OWNER/REPO/milestones -F title=... -F due_on=... -F state=open`; extract the number for later edits. |
| Midnight-UTC due dates | `due_on="YYYY-MM-DDT00:00:00Z"`. | The rendered milestone showed one day earlier than the intended date (display-zone conversion against midnight). | Set `due_on` with a midday-UTC time (for example `T12:00:00Z`) and read back the displayed date. |
| Single combined sweep | Sweep open issues once and report zero unassigned. | Unassigned PRs remained; `gh issue list` excludes PRs, so the board looked complete while wave PRs were unmilestoned. | Run both zero-unassigned queries (issues and PRs) after every pass; sweep PRs separately in the same batch. |
| Label-only bucket rules | Bucket by labels only. | A real defect with a `[bug]:` title prefix and no label fell into the catch-all. | Order rules as pins > labels > title prefixes > keywords > catch-all; the prefix pass catches unlabeled-but-titled items. |
| Snippet-field classification scan | Classify already-milestoned members from length-capped body snippets. | The scan missed members whose token appears past the cap; the same query with untruncated bodies found additional candidates, so the move set was silently incomplete. | Re-run the classification scan with full untruncated bodies and reconcile both result sets before applying; a keyword hit is ownership only when the member is about the deferred subject. |

## Results & Parameters

### Configuration

```yaml
bucket_rule_order:
  - explicit ID pins            # operator-directed placements
  - typed labels                # type: bug, documentation, type: design, ...
  - title prefix tokens         # "[bug]:", "test:", "[docs]" without labels
  - keyword families            # ci/test, docs, access/edge, perf/capacity
  - catch-all milestone         # never leave an item unmilestoned
due_on_format: "YYYY-MM-DDTHH:MM:SSZ  # use midday UTC; read back the date"
scope_transfer_scan:
  bodies: full_untruncated      # re-scan with untruncated bodies; reconcile both sets
  ownership: about_the_subject  # read match context; incidental mentions stay
  consumer_marker_stays: true   # shared mechanisms keep general scope on family deferral
```

### Expected Output

- Every open issue assigned to exactly one milestone; both zero-unassigned
  queries return `0`.
- Per-milestone open/closed counts that sum to the board totals.
- New arrivals classified on re-sweep by linked-issue milestone; a mistake
  found on review is moved and re-verified, not described as covered.
- One tracker epic per milestone; transfer notes recorded on the bodies.
- A scope transfer leaves every residual token mention in the source cut
  verified as incidental, and the tracker epic reconciled to the new direction.

## Verified On

List the projects in which you tested this skill:

| Project | Context | Details |
| --------- | --------- | --------- |
| Large internal inference-platform repository | Three-pass realignment of ~700 issues and ~21 PRs onto a restated 13-cut calendar, 2026-10-23/24 | Measured pass detail in [github-release-board-realignment.notes.md](github-release-board-realignment.notes.md) |
| Large internal inference-platform repository | Scope-rule restatement audit of a 270-member release cut; 32 member moves to two deferred cuts, zero failures; counts verified before and after, 2026-11-16 | Measured pass detail in [github-release-board-realignment.notes.md](github-release-board-realignment.notes.md) |

## References

- [audit-epic-sequencing-milestone-attachment.md](audit-epic-sequencing-milestone-attachment.md) — one known child list into one fresh milestone; this skill covers the repo-wide re-map of an existing board, retitling, PR sweep, and re-sweep of arrivals.
- [github-issue-blockedby-bulk-linking.md](github-issue-blockedby-bulk-linking.md) — bulk GraphQL issue-dependency linking once the board is aligned.
