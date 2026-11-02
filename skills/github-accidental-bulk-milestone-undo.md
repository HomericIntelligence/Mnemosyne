---
name: github-accidental-bulk-milestone-undo
description: "Undo an accidental bulk GitHub milestone reassignment with timeline time-window clustering. Use when issues or pull requests were moved to the wrong milestone and only the accidental batch must move back, because earlier intentional moves into the same destination milestone must stay there."
category: tooling
date: 2026-11-01
version: "1.0.0"
user-invocable: false
tags:
  - github
  - gh-cli
  - milestone
  - timeline-events
  - bulk-undo
  - accidental-move
  - time-window-clustering
  - issue-sweep
  - pr-sweep
  - recovery
---

# Undo an Accidental Bulk GitHub Milestone Move

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Restore only the items that an accidental bulk milestone reassignment moved, without touching items that were moved to the same destination on purpose. |
| **Outcome** | Successful. The destination milestone held 25 items with a source-milestone history; the timeline showed the accidental batch as one 20-second cluster (24 open issues) and one intentional move from days earlier. The 24 items moved back with zero failures; the intentional move was excluded; milestone member counts verified before and after. |

Two API facts drive every decision in this skill:

1. The `issues/N/timeline` endpoint records each `demilestoned`/`milestoned`
   pair with the milestone title and a timestamp. Current membership alone
   cannot tell an accidental move from an earlier intentional one.
2. `gh issue list --milestone` never returns pull requests, and
   `gh pr list` has no `--milestone` flag. Check both sets or an accidental
   move of open PRs is missed.

## When to Use

- A user reports, or you notice, that many issues or pull requests were moved
  to the wrong milestone in one operation, and asks to move them back.
- The destination milestone already contained correctly assigned items, so
  "move everyone back" would revert work that was never part of the accident.
- Some items were moved to the same destination on purpose BEFORE the
  accidental operation and must not be touched.
- The requested scope covers only open items, only closed items, or only one
  of issues/PRs, so the undo must respect the stated boundary.

Do not use this skill for planned whole-board moves; for that see
[github-release-board-realignment](github-release-board-realignment.md). For
attributing unexpected LABELS to an automation mechanism (not undoing a known
accident), see
[github-label-mass-mislabel-forensics](github-label-mass-mislabel-forensics.md).

## Verified Workflow

### Quick Reference

```bash
# 1. Milestone numbers and member counts (the before picture).
gh api repos/OWNER/REPO/milestones \
  --jq '.[] | "\(.number) \(.title) open:\(.open_issues) closed:\(.closed_issues)"'

# 2. For each open member of the destination milestone, extract move events.
gh issue list --milestone "DEST" --state open --limit 500 --json number --jq '.[].number' | \
while read n; do
  gh api "repos/OWNER/REPO/issues/$n/timeline" --paginate \
    --jq '[.[] | select(.event=="milestoned" or .event=="demilestoned")
           | "\(.event):\(.milestone.title?):\(.created_at)"] | @tsv'
done

# 3. Pull requests separately: no --milestone on gh pr list.
gh pr list --state open --limit 500 --json number,milestone \
  --jq '.[] | select(.milestone != null and .milestone.title == "DEST") | .number'

# 4. Restore only the inside-window batch and re-check counts.
gh issue edit N --milestone "SOURCE"
gh api repos/OWNER/REPO/milestones/NUM --jq '.open_issues'
```

### Suggested Approach

1. **Record the before state.** Read every milestone's number and
   open/closed counts first. These numbers are the verification target at
   the end.
2. **Enumerate candidates in both sets.** List current members of the
   destination milestone: issues through `gh issue list --milestone`, pull
   requests through `gh pr list --json milestone` with a select, because the
   `--milestone` filter does not exist for `gh pr list`. Apply the requested
   scope (open/closed) to both lists.
3. **Derive prior state from timeline pairs, not membership.** For each
   candidate, read the timeline and keep `demilestoned`/`milestoned` events.
   An item belongs to the accidental batch only if it left the SOURCE
   milestone and entered the DESTINATION inside the accidental window.
4. **Cluster by timestamp.** An accidental bulk move forms one tight
   timestamp cluster (the verified case: 24 moves within 20 seconds, all on
   one day). Move events days or hours outside the cluster are intentional
   and must be excluded and reported, not reverted. One event per item, one
   actor, and one minute-wide window is the signature of a bulk edit.
5. **Restore only the inside-window items.** Move each identified item back
   to the source milestone. A simple loop with `gh issue edit --milestone`
   works; record each item's result.
6. **Verify counts after.** Re-read both milestone counts and compare with
   step 1; the source should gain exactly the restored count and the
   destination should lose exactly that count.

If a user description of the accident disagrees with the timeline (for
example, the timestamp cluster occurred on a different day than remembered),
trust the timeline evidence and report the difference.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| `gh pr list --milestone DEST` | Filter open PRs by milestone with the same flag `gh issue list` accepts | `unknown flag: --milestone` — PR milestone filtering is unsupported | Fetch `--json milestone` and select on `.milestone.title` instead |
| Restore every destination member with a source-milestone history | Skip the timeline read and treat each match as part of the accident | One issue had moved to the destination days BEFORE the accidental cluster; a blind restore would have reverted an intentional move | Cluster by timestamp and restore only the accidental window; report excluded items with their timestamps |

## Results & Parameters

### Verification

```text
Before: source milestone open:0  closed:2   destination open:64 closed:127
Batch:  24 open issues in one 20-second window; 1 issue moved 4 days earlier (excluded)
After:  source milestone open:24 closed:2   destination open:40 closed:127
PRs:    0 destination-member PRs had a source-milestone history
```

### Expected Output

- Every restored item carries a `demilestoned`/new-`milestoned` pair back to
  the source milestone.
- The destination milestone open count decreases by exactly the restored
  number; the source milestone open count increases by the same number.
- Items moved outside the accidental window are listed and left unchanged.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A private release-board repository | Operator-reported accidental bulk move between two open milestones | 24 open issues restored, 1 intentional move excluded, 0 failures, counts verified |

## References

- [github-label-mass-mislabel-forensics](github-label-mass-mislabel-forensics.md) — the same timestamp-cluster technique applied to label attribution
- [github-release-board-realignment](github-release-board-realignment.md) — planned board-wide milestone moves, with the `gh issue list` PR trap
- [audit-milestone-sweep-attachments](audit-milestone-sweep-attachments.md) — the forward case: items a sweep attached to the wrong release with no plan entry; uses the same timeline evidence
- [GitHub issue timeline events API](https://docs.github.com/en/rest/issues/timeline)
