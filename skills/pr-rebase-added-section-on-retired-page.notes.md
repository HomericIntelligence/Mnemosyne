# Notes: pr-rebase-added-section-on-retired-page

Supporting evidence and provenance for
[pr-rebase-added-section-on-retired-page](pr-rebase-added-section-on-retired-page.md).
This file is outside normal retrieval.

## Source evidence

Session: a pull-request drive task with rebase-only authority on a feature branch that
added a new core module, its tests, a layer-registry row, and a layout docstring entry.
The same commit added one prose section to an architecture page.

During the rebase, trunk had deleted the architecture page set in a documentation
closeout that absorbed content into component pages. Git reported the conflicted path
as deleted in HEAD and modified in the replayed commit (`DU`). The rebase stopped with
a modify/delete conflict.

## Resolution record

- Trunk side: the closeout deleted the page and stated its absorber set.
- Branch side: one added section titled for runtime write authority.
- Decision: keep the deletion (`git rm <path>`), continue the rebase, report the
  dropped section as a scope delta, and name the re-review as the owner.
- Rejected relocation: the absorber pages use a template with fixed sections, prose
  denies repository paths and code file names, and a catalog allowlist entry exists
  per allowed span. Any of those four is a docs change outside the reviewed scope.

## Contrast with `pr-rebase-conflict-resolution-patterns`

That canonical entry covers modify/delete in general ("verify stale base before
deletion"), which assumes the branch should probably delete. The branch that *added*
content to the deleted page has the opposite default, so the decision rule differs:

| Case | Branch side | Default |
| --- | --- | --- |
| Branch deletes, trunk edits | deletion | keep deletion after confirming the edit is stale |
| Branch adds, trunk deletes | addition | keep deletion, report the dropped content |

A related open change added the "union of both guards" branch to that entry. That
branch is about a resolution that keeps both sides of a competing design. This entry is
about content with no valid host after a retirement. Different decision, different
default, so they stay separate.

## Generalization limits

- The rule assumes the deleting change is newer information architecture. If the
  deletion was accidental or reverted, restore the page and re-apply the section.
- The rule assumes relocation changes decisions outside the review. If the delivery
  authorization already names the target page and its shape, relocate instead.
- A documentation drop is a scope delta, not a blocking conflict, unless the reviewed
  behavior depends on the prose, for example a security contract stated only there.