# Premise Checks: Notes

## 3.5.0 — a collect-all report cannot use a validating reader

Source evidence: a plan review of a deployment-install issue. The plan promised one
report that lists every metadata mismatch below a deployment root, and named the
module's existing open helpers as the reader.

Observed in the reviewed source (generalized):

- The leaf reader took an expected mode parameter, and the plan read that parameter as
  "no mode check". The body still checked the owner, the expected group, and the node
  type, and raised before it returned any value.
- The directory reader raised a not-found or not-a-directory error for an absent or
  replaced item, which are exactly the states the report had to list.
- One premise row said an absent fixed directory "already reports cleanly". That held
  only for the write path, which creates the directory. It did not hold for the
  collecting pass, which must report absence as a row.
- The plan then contradicted itself: one section said an absent item is not reported,
  and another said every item reports presence.

Repair that the reviewer accepted: one local read loop that opens each path component
with `O_RDONLY | O_NOFOLLOW | O_DIRECTORY` from a retained directory descriptor, then
calls `fstat`. It returns presence, owner, group, mode, and type without enforcing any
of them. The plan records this as the only non-validating reader for the report, so the
validation owner stays single.

## 3.5.0 — policy facts the plan must read

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

Observed pattern:

- A path-policy table set an exact mode for some entries and left the field unset for
  others. The plan attributed the mode tuple to the entries that had no policy mode.
- The publisher module held the only mode authority for the unset entries.
- Several entries shared a group rule that resolved to an administrator group, not to
  the running user's primary group.

Rule applied: name one authority per expected value, and state which entries have no
policy rule. A test built on an unset policy field encodes a value that no owner states.

## 3.5.0 — report order against the protected stage

Observed pattern: the caller staged dependencies before it called the authorize step,
and the new report lived inside the final publisher. The report therefore arrived after
the expensive stage, which is the serial-discovery cost the issue reported. Repair:
a cheap read-only preview with the same field names in the caller before staging, with
the publisher check kept as the authority for identity.

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

## 2026-11: Per-ask triage then vehicle selection (v3.9.0 source case)

Source: one planning session on an open bug issue in a fast-moving repository.
The issue body listed six asks. The issue was still open after the primary defect
was repaired.

Discharge map measured against the default-branch tip:

- A merged CI-repair change had already updated the five stale test assertions
  (found by `git log --oneline <merge-commit>..origin/main -- <test files>`),
  removed the dead selector write, and threaded an explicit selector into the
  rendered calls that the issue cited.
- One documentation example and one error-wrapper call site were still open; no
  default-branch commit after the merge touched either file.
- A merged CI repair also rewrote the selection page the issue flagged.

Vehicle selection: the repository had an open PR whose body closed the same
issue. Reading its diff (`git diff --stat origin/main...<branch>`) showed the
code fix, the documentation fix, and the dead-write removal, but no test pinned
the new precedence and no wrapper around the failing call. Reading its merge base
(`git merge-base`) showed the branch was cut before the CI repair, and its test
shards failed in the same modules that repair had touched. The plan therefore
reused the open PR: rebase, add the missing test and the wrapper, rebind checks.

Limitations: planning only. The disposition was not implemented or merged in this
session, so the rule is recorded as unverified and the example is illustrative.

## Retrieval note

This file is a companion and is not part of normal retrieval. Keep rules in the main
entry.
