# Notes — github-release-board-realignment

Evidence for `github-release-board-realignment.md`. Generalized per the
privacy rules; repository identity, issue numbers, and internal identifiers
are withheld.

## Measured pass (2026-10-23/24)

Environment: GitHub repository with ~700 open issues and ~21–30 open PRs;
pre-existing release-automation wave machinery; `gh` CLI without a
`milestone` subcommand (REST fallback required).

Starting state: 5 milestones partially populated from a first-pass plan;
~430 issues unmilestoned; every open PR unmilestoned; a restated calendar
arriving in two amendments (a typoed date, then a three-way split of the
nearest cut).

### Pass results

1. Retitled and re-dated the 5 existing milestones by `PATCH` on their
   numeric IDs. Zero membership loss; the renamed milestones kept all
   assignments through the retitle.
2. Created 8 additional milestones through the REST API fallback.
3. Swept ~430 unmilestoned issues with the ordered bucket rules
   (pins > labels > title prefixes > keyword families > catch-all).
   Per-item failure capture: zero failures across ~600 `gh issue edit`
   calls when run with a tolerant loop; missing or closed numbers land in
   the failure log instead of aborting the batch.
4. Title-prefix missort found on review: one `[bug]:`-titled issue with no
   label had fallen into a keyword bucket; moved to the bug milestone
   before applying. Lesson preserved in the main skill's rule order.
5. Midnight-UTC due dates rendered one day early in the milestone list;
   corrected by re-setting `due_on` with `T12:00:00Z` and reading back.
6. Three-way split of one cut (~150 issues) applied by explicit ID-pin
   lists; 5 items missed by the lists defaulted into the nearest cut and
   were reviewed before final assignment.
7. Overnight arrivals (~7 issues, ~11 PRs, created by wave automation) were
   re-swept by linked-issue classification; one review mistake (a docs PR
   assigned to the CI milestone instead of the docs milestone) was caught
   on read-back and corrected.
8. Two self-declaring arrivals (an issue naming a target engine version in
   its title that overlapped an existing planning issue) were kept and
   cross-linked rather than closed; the linkage comment is the conflict
   record.

### Board after the realignment

- Zero unassigned issues, zero unassigned PRs (verified by both queries).
- 13 milestones, one tracker epic each, labels `epic` + `state:skip` so
  dispatch automation ignores them.
- Transfer and split records appended to the affected tracker bodies as
  history sections; no roster lines deleted.

## Provenance

- Delivery base: `8cdb8d577bc7e984bfcd295b855a91e77cc5a65d` (main, refresh
  verified at write time).
- Duplicates checked at write time: `audit-epic-sequencing-milestone-attachment`
  (different intent: one known child list, one new milestone, wave
  sequencing — no retitle, no board sweep, no PR sweep), plus non-matching
  hits for milestone, board, sweep, and due-date keywords
  (`github-issue-workflow-and-preflight-gates`,
  `github-issue-blockedby-bulk-linking`, `track-implementation-progress`,
  `atlas-go-dashboard-milestone-delivery`).
- Open PRs at write time: 3, none touching a milestone- or board-intent
  skill.
