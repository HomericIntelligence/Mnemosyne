# Notes: Planning — Verify Premises Before Implementing

Supporting cases for `planning-verify-issue-premise-before-implementing`. Rules that the
skill requires for operation live in the skill itself, not here.

## 2026-10: Self-produced reproduction on a stale checkout (v3.4.0 source case)

A production service logged a code-level
`ValueError` on a recurring scheduler state. The responder ran the same live inputs against
the source tree and reproduced the failure, then filed an issue with a root-cause analysis,
a proposed predicate fix, and started the plan-review round.

Days later, a fresh fetch for an unrelated change showed the default branch already
contained the predicate fix with regression tests. The earlier reproduction had run from a
local checkout that lagged the default branch by multiple merges. The deployed release
artifact also predated the branch, so the production errors were real at the deployed
version but already remediated upstream. The issue closed as already-fixed; the only
remaining action was a routine deployment. The verification that would have prevented the
cycle took thirty seconds: the same live inputs run against a throwaway worktree at the
fetched default-branch head all passed, and a `-S` history search on the fixed predicate
named the upstream change.

Cost classification: the issue, plan draft, and one review round were recoverable but
wasted. Two cheap checks would have prevented them:

1. Re-run the reproduction at the fetched default-branch head (throwaway worktree), not
   the checkout as-found. A stale checkout proves a defect existed, not that it exists.
2. For a deployed service, compare the deployed artifact's version with the default
   branch. Fixed upstream plus a lagging deployment means operational remediation, and a
   second implementation of the same code is a redundant fix.

Outcome classification applied: `already_fixed_on_branch` with deployment currency as the
remaining action.

## 2026-10: Prescribed-fallback close on an overtaken plan (v3.6.0 source case)

A minor documentation-consistency issue planned eight one-line edits to a frozen
decision-record store. Its plan carried a verified baseline, a review GO, and one
gating condition plus a matching fallback: the store was frozen pending a retirement
epic, and the plan prescribed that if the retirement's closeout deletes the store
first, the implementer records the verified findings on the owning record and closes
the issue as subsumed.

During the dwell, the closeout change merged and deleted the entire store directory
(78 files), closing the retirement epic. At dispatch the anchor sweep found:

1. `git ls-files <store-dir>` returned zero tracked files; the store guard test no
   longer named the store.
2. `git log --full-history --oneline -- <store-dir>` dated the removal to the
   closeout change, and its PR body carried a deliberate deletion inventory.
3. The owning epic issue was closed seconds after the closeout merged.

Because the GO'd plan itself prescribed the disposition for this exact trigger, the
implementer executed the fallback instead of re-planning:

1. Re-verified the plan's baseline findings at the plan's own commit
   (`git grep -l '^Status:' <plan-sha> -- '<store-dir>/*.md'` returned the same six
   files; `git show <plan-sha>:<store-dir>/index.md` re-read the cited rows).
2. Recorded the findings and the per-ask discharge map (all asks discharged by the
   deletion; two of the issue's four claims had already been refuted at plan time)
   as a comment on the closed owning record.
3. Closed the issue as subsumed with the trigger evidence in the closing comment.

Cost: zero source edits, no PR, no new review round. The verdict attached to the
reviewed prescription plus fresh trigger evidence. Without the prescribed-fallback
branch, the same dispatch would have produced either a blocked report or a re-plan
round spent authorizing a zero-work close.

## 2026-11: Converted checks need a per-check load path (v3.7.0 source case)

A review of a plan that converted many configuration checks from fatal raises
to logged warnings found one structural defect. The plan named a single post-load
validation pass behind the loader of the main settings model. Most listed checks
did not belong to that model. They hung off nested models of a second, larger
record type, and those records have their own loader and their own production
call sites (a supervisor and a validation module).

Effects the review named:

- The listed checks could not run through the chosen hook in production: no
  raise, no drift event. The conversion would have removed them silently.
- The plan named a fair-share validator family as converted, but only
  test modules construct that family; the live surface is a different model
  owned by another work stream. A hook on the main loader can never fire for it.

The revision split the conversion by load root, gave the second loader its own
optional log directory and standard-error fallback, and stated the disposition
of the family with no production load path. The review also required each
behavior test to load through the real loader rather than a private helper.
