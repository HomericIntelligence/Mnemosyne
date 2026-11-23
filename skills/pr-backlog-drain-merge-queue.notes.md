# Notes: PR Backlog Drain Under a Merge Queue

Supporting evidence for `pr-backlog-drain-merge-queue.md`. Counts and paths are
generalized. No tokens or private host identifiers appear in this file.

## Additive overlap in a 32-PR drain (2026-11-23)

A drain started with 32 open skill PRs. A changed-path comparison before
enqueue found one overlap: two PRs changed the same main skill file and the
same notes companion, and both raised the same frontmatter version to the same
value. A merge-tree probe against the default branch reported content
conflicts in both files.

The first PR entered the queue. The second PR stayed out of the queue. After
the first PR squash-merged, the second PR was rebased onto the new default
branch.

The resolution combined both lessons in one artifact set:

- The shared version moved past both candidate versions.
- The two new table rows became consecutive rows.
- Cross-references in failed-attempt lessons and notes section titles were
  renumbered to the new row order.
- Both run-evidence sections were kept.
- The description, tags, and trigger lists included both additions.

The rebased commit was signed, validated at 1122/1122 skill files, and
force-pushed with a lease bound to the old head. The held PR diff against the
new default branch held only its own delta. The queue merged the remaining PRs,
the open count reached zero, and the default branch was checked for both rows,
both notes sections, and the combined version.

## Failure mode that the hold avoids

If both PRs enter the queue, the first squash merge can make the second
`DIRTY`. GitHub then builds no merge commit for the second PR, and no
pull-request checks start. The drain loop must remove that entry, rebase the
branch, and enqueue it again.