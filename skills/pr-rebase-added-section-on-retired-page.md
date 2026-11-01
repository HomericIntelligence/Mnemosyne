---
name: pr-rebase-added-section-on-retired-page
description: "Resolve a rebase modify/delete conflict where the pull request added a prose section to a page that main deleted during a documentation restructuring. Use when: (1) an approved pull request gains a documentation section on an architecture, runbook, or design page, (2) main deletes that page in a closeout or reorganization that absorbs its content into component or owning pages, (3) the rebase reports the conflicted path as deleted in HEAD and modified in the replayed commit, (4) the branch carries a delivery authorization that covers code and tests but not a documentation restructuring, and (5) you must decide whether to keep the deletion, relocate the section, or stop."
category: documentation
date: 2026-11-01
version: "1.0.0"
user-invocable: false
license: BSD-3-Clause
verification: verified-ci
tags: [git, rebase, merge-conflict, modify-delete, documentation, doc-reorg, content-absorption, review-scope, pr-drive]
---

# Rebase: Section Added to a Page That Main Retired

## Overview

| Field | Value |
| --- | --- |
| **Date** | 2026-11-01 |
| **Objective** | Resolve a documentation modify/delete conflict without silently discarding reviewed prose or smuggling an unauthorized docs reorganization into a rebase. |
| **Outcome** | Successful; the pull request rebased, reached a clean merge state, and passed every required check with the dropped prose reported as an explicit scope delta. |
| **Verification** | verified-ci; the resolution passed the full hosted check set after the rebase. |

A rebase of a branch that *added* a section to a page is not the same conflict as a
branch that *edited* a page. When main deleted the page, the deleted side is the newer
information architecture, and the branch side is content that has no home. The
mechanical resolution (`git rm`) is easy; the hard part is deciding what happens to the
reviewed prose and reporting that decision honestly.

## When to Use

- `git status` shows `DU <path>` or "deleted in HEAD and modified in `<commit>`".
- The conflicted path is a documentation page, and main removed it in a closeout,
  absorption, or reorganization change.
- The branch's commit message and pull request description name one artifact as the
  place for this prose.
- Delivery authorization covers the feature and its tests, not a docs restructuring.
- You must report old head, new head, conflicts, and behavior change after the rebase.

## Verified Workflow

### Quick Reference

```bash
git show :2:<path> 2>/dev/null || echo "stage 2 absent: deleted on trunk side"
git show :3:<path> | git diff --no-index -- /dev/null -   # the replayed addition
git log --oneline <base>..origin/main -- <path>          # the deleting commit
git show <deleting-commit> --stat | head -40             # what it did to the page set
```

### Suggested Approach

1. Confirm which side deleted the file and why. Read the deleting commit's message for
   its absorption or retirement statement. The page set is the newer design; do not
   resurrect a retired page to keep a branch happy.
2. Extract the branch's unique delta (`git diff <base> <pr-head> -- <path>`) before any
   resolution. You need it for the report even if you drop it.
3. Check whether relocating the section is in scope. Hosting the prose on another page
   can require decisions the review never saw: which page owns the topic, the template
   shape, catalog allowlist entries, and navigation registration. If those decisions
   change, relocation is a docs change, not a rebase.
4. Keep the deletion when relocation is out of scope, and continue the rebase. Do not
   stop for a documentation relocation alone when the code and tests still apply
   cleanly; a stop is for a conflict you cannot resolve without altering reviewed
   behavior.
5. State the dropped section in the delivery report as a behavior or scope change with
   the page name. A reader must not learn about it from an empty `git diff`.
6. Name one owner for the lost prose: the re-review, or a follow-up that gives it a
   registered home. Do not leave it unowned.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --- | --- | --- | --- |
| Restore the deleted page to keep the section | Re-added the retired page with only the new section | Resurrects a retired information architecture and contradicts the closeout | The deleting side owns the structure |
| Silently relocate the section | Moved the prose to a nearby component page inside the rebase | Needs page-ownership, template, allowlist, and nav decisions the review never approved | Relocation is a docs change, not conflict mechanics |
| Silently drop the section | Ran `git rm` and pushed without a note | The reviewed prose vanished with no record | Report the delta, name the owner, state it cannot be inferred from the diff |

## Results & Parameters

### Configuration

```yaml
trunk_side: deleted (retired page, newer information architecture)
branch_side: added section (no valid host page after the closeout)
resolution: keep deletion, continue rebase, report dropped prose
relocation: only when page ownership and template decisions are in scope
```

### Expected Output

- A clean rebase whose merge state returns to mergeable.
- A report line that names the dropped page and the section title.
- One named owner for the prose: the re-review or a follow-up.

## Verified On

| Project | Context | Details |
| --- | --- | --- |
| Internal project | PR drive rebase of a documentation-bearing pull request | See [notes](pr-rebase-added-section-on-retired-page.notes.md) for the contrast with the both-sides-guards branch. |

## References

- [PR rebase and conflict resolution patterns](pr-rebase-conflict-resolution-patterns.md)
- [ASD-STE100](../docs/asd-ste100.md)