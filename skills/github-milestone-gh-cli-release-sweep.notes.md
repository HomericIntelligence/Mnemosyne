# Notes: GitHub Milestones with the gh CLI and Release-Board Sweeps

Supporting evidence for `github-milestone-gh-cli-release-sweep`. All
organization, repository, project, and issue identifiers are withheld per the
Mnemosyne privacy rules; the mechanics below are the reusable residue.

## Source session (2026-10-23 to 2026-10-24)

A release-train setup for a private multi-service monorepo:

1. Operator direction set a release calendar spanning one bugfix stream and a
   major release with two release candidates.
2. Initial pass created milestones for the first two releases with
   `due_on="...T00:00:00Z"`. Follow-up queries through
   `gh api repos/{owner}/{repo}/milestones` returned each `due_on` rendered one
   day earlier than the intended calendar date; the viewing account timezone
   is behind UTC.
3. Repair pass ran
   `gh api -X PATCH repos/{owner}/{repo}/milestones/{number} -F due_on="YYYY-MM-DDT12:00:00Z"`
   for each milestone. Subsequent reads returned the intended calendar dates.
   No recreation was required.
4. A later operator correction expanded the calendar to 13 milestones and
   split one overloaded bugfix milestone into three daily cuts, then
   rebalanced two later milestones. Total open issues at sweep time:
   approximately 700 (273 already assigned, remainder bucketed by labels and
   title theme from a disk snapshot of
   `gh issue list --state open --limit 1000 --json number,title,labels,milestone`).
5. Batch assignment used `gh issue edit {n} --milestone "{title}"` per issue,
   with a failure log. First pass: zero failures; verification counts per
   milestone matched the assignment lists.
6. Next-day re-sweep found 7 newly arrived unassigned issues and 11
   unassigned pull requests. Pull requests were assigned with
   `gh pr edit {n} --milestone "{title}"`; classification leaned on linked
   parent issues (a PR inherits the milestone of the issue it closes). One
   mis-assignment was found only by re-reading the parent issue of each PR:
   the PR had been placed in a code-release milestone while its parent issue
   lived in a documentation milestone. Corrected with a second `gh pr edit`.
7. Final verification: both zero-unassigned queries returned `0`, failure log
   empty. Board rendered per-milestone open/closed counts from the milestone
   API (`open_issues`/`closed_issues`), which matches the web UI progress
   bars.

## Observations worth keeping

- The CLI-gap discovery cost real time: `gh milestone create` prints a usage
  error, and a `cmd1 || cmd2` fallback chain made the session log ambiguous
  about which command had executed. Picking the REST path directly avoids the
  ambiguity.
- The `T12:00:00Z` rule has one edge: accounts ahead of UTC by more than 12
  hours do not exist on standard maps (max offset is UTC+14, Line Islands).
  At UTC+13/UTC+14 a noon-UTC timestamp renders as the intended date plus one
  early-morning hour of the *next* day only between 12:00 and 14:00 UTC+13/14
  — practically irrelevant for due-date semantics, and strictly better than
  midnight UTC, which is wrong for every account behind UTC.
- `audit-epic-sequencing-milestone-attachment` predates this lesson and uses
  `due_on="...T00:00:00Z"` in its examples. Under this rule those examples
  render one day early for accounts behind UTC; that skill was left unchanged
  here (single-create disposition), but the discrepancy is recorded for a
  future amendment.
- Tracker-epic bodies were edited by fetching to disk
  (`gh issue view {n} --json body -q .body > body.md`), appending, and
  re-uploading (`gh issue edit {n} --body-file body.md`). Append-only in a
  disk file keeps the operation restart-safe and reviewable before upload.
- Enumeration without an explicit `--limit` truncated the first inventory
  silently; the discrepancy surfaced only because the per-milestone counts
  did not add up. Always reconcile counts before claiming completeness.
