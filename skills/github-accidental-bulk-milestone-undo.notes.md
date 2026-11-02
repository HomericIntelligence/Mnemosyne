# Notes: Undo an Accidental Bulk GitHub Milestone Move

Supporting evidence for [github-accidental-bulk-milestone-undo](github-accidental-bulk-milestone-undo.md).
All identifiers below are generalized; the source repository, milestone titles, and issue
numbers stay private.

## Provenance

- Learned 2026-11-01 from an operator-reported incident on a private repository: one
  open backlog milestone's entire open membership was accidentally reassigned to a
  different open milestone. The session recovered the batch the same day.
- Delivery base: Mnemosyne default branch at 188d710bc0b0bc1ba873402133fea0d79c61a300
  (freshness verified by upstream refresh at lesson time). No open PR touched the
  related entries at discovery time.

## Why a new entry and not an amendment

The closest corpus entries were inspected in full before the disposition decision:

- `github-label-mass-mislabel-forensics` uses the same core technique (timeline events
  survive cleanup; histogram timestamps; each tight cluster is one mechanism run), but
  its intent is ATTRIBUTING unexplained labels to automation code paths. It has no
  decision branch for "the operator caused the move, so bind the accidental window and
  revert only inside it", and no milestone or PR-trap material. Same mechanism,
  different trigger, outcome, and failure modes.
- `github-milestone-gh-cli-release-sweep` and `github-release-board-realignment`
  cover PLANNED board moves and sweep completeness. They share the PR-visibility trap
  (which this entry restates briefly and links), but nothing about selective undo.

The new entry adds: (a) the accident-undo trigger, (b) the inside/outside-cluster
decision branch as a revert gate, (c) the verify-counts end state, and (d) the
`gh pr list --milestone` failure evidence.

## Incident evidence (generalized)

- Destination milestone open count examined first; source milestone had zero open
  members, which already suggested the bulk move consumed everything.
- 25 open issues in the destination had a source-milestone entry in the timeline
  (last `milestoned` event title = source). Timeline pattern per item:
  `milestoned:SOURCE <earlier> ; demilestoned:SOURCE <t> ; milestoned:DEST <t>`.
- Timestamps for 24 of 25 fell inside one ~20-second window on the accidental day
  (16:09:47Z–16:10:06Z). One item moved ~4 days earlier in an isolated event — excluded
  from the batch and reported to the operator.
- `gh issue list --milestone DEST --state open` returned 64 items; only the 24 inside
  the window were candidates for the restore loop.
- `gh pr list --milestone DEST` failed with `unknown flag: --milestone` (gh CLI has no
  milestone filter for PRs). The working query:
  `gh pr list --state open --limit 200 --json milestone --jq
  '.[] | select(.milestone != null and .milestone.title == "DEST") | .number'`,
  followed by the same timeline check per number. No PRs had a source-milestone
  history.
- Restore loop: `gh issue edit N --milestone SOURCE` for each of the 24 items; all 24
  reported success. Post-check: source milestone open count went 0 → 24, destination
  went 64 → 40 (= 64 − 24). Closed items were out of the requested scope and untouched.

## Parameters used

- Timeline read: `gh api repos/OWNER/REPO/issues/N/timeline --paginate --jq
  '[.[] | select(.event=="milestoned" or .event=="demilestoned")] '` — `milestoned`
  events carry `.milestone.title`; use `?` on the title for events without milestone
  payload.
- Milestone numbers and counts: `gh api repos/OWNER/REPO/milestones` (list) and
  `repos/OWNER/REPO/milestones/NUM` (single milestone verification).
- `gh issue edit --milestone` matches milestone TITLES; if milestones were retitled
  between the accident and the undo, resolve by number from the list output first.

## Edge cases noted but not hit

- If the accidental move included CLOSED items and the scope includes them, repeat the
  procedure with `--state closed` (or `--state all`) on both issue and PR lists.
- Timeline pagination matters on hot issues: `--paginate` is required or events can be
  silently truncated past the first page.
- If the actor evidence matters (who ran the bulk move), timeline events carry
  `.actor.login`; automation tokens show the token owner, so timestamps remain the
  reliable discriminator.
