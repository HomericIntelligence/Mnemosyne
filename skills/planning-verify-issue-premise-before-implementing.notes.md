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

## 2026-11: Correct the doc anchors, then dispose per ask (v3.8.0 source case)

A planning probe for a "warn instead of fail closed" issue checked four kinds of
anchor against the tree before it proposed any file:

- Source sites. Two of the three named refusal sites still refused; one already
  warned under an existing drift mechanism. The plan reused that mechanism and
  forbade a second warning framework.
- The named documentation page. It does not exist as a tracked file. The page is
  retired and survives only as a section ledger in another document. The plan
  replaced the target with the owning release-operations pages and named the one
  ledger row that still points to the retired path.
- The named decision record. It has no file. The decision survives only as prose
  references from component pages. The plan cited those pages and did not treat
  the missing record as proof that the direction is wrong.
- The mechanism the issue asked to build. A merged change had already removed the
  last acceptance gate of that kind. The plan read the issue's "one acceptance
  path" as one warning shape over the existing seal record, not as new approval
  storage.

The disposition was not "obsolete". Part of the behavior already shipped, one
named site still refused, an opt-in flag still gated the warning, and the actor
that closed the superseded issues was a forge action that the tree cannot prove.
The prompt output enumerated the criteria that already held and the criteria that
remained. The prompt output also stated the two stale issue facts as uncertain
rather than restating them.

Rule applied: date a zero-match anchor for source sites, but for a documentation
page or decision record that the store retirement removed, name the owning page
that absorbed the content and plan against it. Then dispose per ask, not per
issue.

## 3.9.0 — a local load-path patch is not durable (source case)

Source evidence: a planning hand-off for a consumer issue whose code lives in a
separate repository. Before the plan, three premises were re-checked:

- All four named target pull requests were already merged. The alternate acceptance
  form (report each block with its cause) applied, and no delivery run was needed.
- The consumer-side supersession patch was closed without a merge. The owner fix was
  an open pull request in the owning repository.
- A local install had been patched by hand and reported active the day before. The
  installed copy held none of the change: a later sync from the owning repository
  replaced it. The installed digest equalled the owning default branch.

Rules the case supports:

1. Report an installed or deployed copy's state from a digest check against the
   required owning revision, never from an earlier report. Do not hand-apply a
   patch to the load path as the durable route.
2. A closed supersession patch in the consumer, plus an open owner fix, leaves the
   plan with a tracking action, not a code action in the consumer.
3. An accepted alternate acceptance form discharges the delivery criterion by
   evidence, not by a mock run.

## Retrieval note

This file is a companion and is not part of normal retrieval. Keep rules in the main
entry.

## v3.9.0 evidence: clause ledger, authority conflict, paired commits (2026-11-07)

Source: one planning session on an issue that was deferred and replanned. The issue cited
four later issues. Two merged commits names its own issue id in the subject line, so the
issue id itself was a valid search key.

Findings, in a generic form:

1. A commit that cites the issue id discharged two of six named clauses: one script that
   called a CLI verb without its required positional argument, and one refusal message
   that named only the accepted values and not the observed one. The other four clauses
   stayed live, and the primary ask stayed open. A later, broadened design record kept
   the issue as an input.
2. A second commit in the same area relaxed one admission check and kept another refusal
   fatal. Read alone, the pair looks inconsistent. Read as a classification, it is the
   rule: one identity class is informational and one is enforced. The residual work is then
   to apply that classification to the gates the first commit did not cover, not to pick
   one of the two commit behaviors.
3. The issue's own proposal said to replace an allowlist refusal with a warning. The live
   decision record listed authentication and permissions as the classes that stay
   enforced. The plan kept the refusal and adopted only the proposal's clause about the
   message content.

Checklist that produced the finding:

    git log --oneline --all --grep='#<issue>' -5          # the issue id as a search key
    git log --oneline --all --grep='#<cited>' -5          # each cited issue
    gh issue view <issue> --json state,labels,comments    # deferral and planner comments
    git show <sha> -- <files>                             # clause-by-clause discharge

Limit: no implementation outcome follows from this session. The lesson records the
planning decision support only.
