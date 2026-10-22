---
name: checkout-other-ref-silent-file-clobber
license: BSD-3-Clause
description: "Port changes across Git refs, or read content at another ref, without overwriting destination content or mutating the caller's index; use when whole-file checkout would hide per-hunk conflicts, stage an overlay, or destroy shared-checkout state."
category: tooling
date: 2026-10-22
version: "1.1.0"
user-invocable: false
verification: verified-local
tags:
  - git
  - checkout
  - silent-revert
  - file-clobber
  - cherry-pick
  - port-files-between-branches
  - strict-review-catch
  - pr-review
  - merge-conflict-adjacent
  - read-only-inspection
  - detached-head
  - index-overlay
  - homericintelligence
  - hephaestus
history-source: "https://github.com/HomericIntelligence/Mnemosyne/blob/1956c91d76867bc2e484eaf573a57051855186f8/skills/checkout-other-ref-silent-file-clobber.history"
history-cleanup-date: "2026-09-20"
---

# `git checkout <other-ref> -- <path>` Silently Replaces the Whole File, Reverting Unrelated Committed Work

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-07-19 |
| **Objective** | Port a small, targeted change (a couple of `CLAUDE.md`→`AGENTS.md` reference fixes) from one Hephaestus PR branch (`pr2327`) into another (`docs/agents-md-single-source`, PR #2334) by running `git checkout pr2327 -- scripts/README.md .github/workflows/_required.yml`. |
| **Outcome** | The command replaced BOTH files wholesale with `pr2327`'s versions, silently deleting the "Disaster recovery" section of `scripts/README.md` and the `persist-credentials: false` line in `.github/workflows/_required.yml` — both unrelated, already-landed changes (via separately-merged PR #2332) that existed on the destination branch but not on `pr2327`. The regression was caught by an independent strict-review agent (graded F / NO-GO, 2 CRITICAL findings), not by the author. Fixed by amending the commit to restore both sections. |
| **Verification** | verified-local — reproduced the failure mode directly (the committed diff showed the deleted sections), root-caused via `git diff pr2327...docs/agents-md-single-source -- <path>` (confirmed the two branches diverged on unrelated hunks of the same files), and confirmed the fix by amending the commit and having a second independent review pass with no findings on those files. |

## When to Use

- You want to bring a specific change from another branch/ref into your current branch, and you
  reach for `git checkout <ref> -- <path>` as a shortcut because it's fast and doesn't require
  resolving a real merge/rebase.
- The destination file has ALSO been edited independently since the two branches diverged — e.g. a
  third PR landed unrelated changes to the same file on `main` after your source ref's branch point.
  This is the exact condition under which the clobber is invisible: there's no conflict to trigger a
  warning, because git isn't merging anything — it's an unconditional whole-file overwrite.
  Two-dot/three-dot diff review against `main` from the DESTINATION branch's tip won't surface it
  either, since after the checkout the file legitimately differs from main in the intended way too.
- Reviewing a PR (yours or an agent's) that includes a `git checkout <other-ref> -- <path>` step, or
  whose diff shows an unexplained deletion of content unrelated to the PR's stated purpose in a file
  it also legitimately modifies.
- A strict-review pass flags "this PR reverts already-merged section X" in a file that the PR
  otherwise has a legitimate reason to touch — that pattern is the fingerprint of this failure mode,
  not necessarily a merge/rebase mistake.
- You only want to READ content at another ref (evidence, review, comparison) from a checkout you
  share with other work — above all a detached-HEAD checkout. There is nothing to port, so the
  whole-file overwrite buys nothing: the read-only commands (`git show <ref>:<path>`,
  `git archive <ref> | tar -x`) leave the index and working tree untouched. On a shared checkout an
  accidental `checkout <ref> -- .` can destroy another actor's uncommitted state, and no PR review
  net exists to catch an ad-hoc shell read.
- You verify command output against `HEAD` after any earlier `checkout <ref> -- .`-class operation:
  the whole-tree dot form STAGES an overlay (new and modified entries relative to HEAD), so later
  reads answer against the overlay ref, not HEAD. Results look valid for the wrong tree while the
  checkout is silently mutated.

## Verified Workflow

### Quick Reference

```bash
# WRONG — replaces the ENTIRE file with <other-ref>'s version, silently discarding any content
# on the current branch that <other-ref> doesn't have (even unrelated, already-committed work):
git checkout <other-ref> -- path/to/file.md

# READ-ONLY INTENT — never use checkout to look at another ref's content. Both commands leave the
# caller's index and working tree byte-identical:
git show <other-ref>:path/to/file.md | sed -n '570,576p'      # one file / excerpt
git -C <repo> archive <other-ref> | tar -x -C <scratch-dir>   # many files or a build

# WRONG for reads on shared checkouts — the whole-tree form stages an overlay AND can destroy
# uncommitted state owned by other actors; recovery needs a verified-clean pre-state:
git checkout <other-ref> -- .

# RIGHT — before doing ANY checkout-from-another-ref, diff the two versions first to see the
# FULL scope of what would change, not just the hunk you intend to port:
git diff HEAD <other-ref> -- path/to/file.md

# If the diff shows ONLY your intended hunk: checkout -- is safe, proceed.
# If the diff shows unrelated sections (present on HEAD, absent on <other-ref>, or vice versa):
# do NOT use checkout --. Instead, apply just the intended hunk:

# Option A: cherry-pick the exact commit that introduced the change on <other-ref>
git log --oneline <other-ref> -- path/to/file.md      # find the introducing commit
git cherry-pick -n <that-commit>                        # stage without committing
git diff --cached -- path/to/file.md                    # verify ONLY the intended hunk changed
git commit

# Option B: hand-edit the specific lines after inspecting both versions
git show <other-ref>:path/to/file.md > /tmp/other-version.md
diff HEAD:path/to/file.md /tmp/other-version.md          # see exactly what differs
# manually apply only the wanted lines with Edit, leaving the rest of the file untouched
```

### Detailed Steps

1. **Never treat `git checkout <ref> -- <path>` as a "merge this one change in" operation.** It is
   a whole-file overwrite: the destination file becomes byte-for-byte identical to the source ref's
   version of that path. There is no partial application, no conflict detection, and no warning —
   it behaves the same whether the two versions differ by one line or by an entire unrelated section.
2. **Before running it, always diff the two full versions of the file first**, not just the hunk you
   intend to port: `git diff HEAD <other-ref> -- <path>`. If anything appears in that diff beyond
   your intended change, `checkout --` will silently destroy it. This is the single check that would
   have caught the incident: `scripts/README.md`'s "Disaster recovery" section and
   `_required.yml`'s `persist-credentials: false` line were both landed on the destination branch
   via a separately-merged PR (#2332) AFTER the source branch (`pr2327`) had branched off — so they
   existed on `HEAD` but not on `pr2327`, and the diff would have shown them as about to be deleted.
3. **Prefer `git cherry-pick -n <commit>` when the intended change is an isolated commit** on the
   source ref — it applies only that commit's diff, and a real conflict will surface (loudly) if it
   touches lines your branch has also changed, rather than silently discarding one side.
4. **When the intended change isn't a clean standalone commit**, use `git show <ref>:<path>` to view
   the source version and hand-apply just the wanted lines with a normal edit — slower, but it cannot
   destroy unrelated content because it never replaces the file wholesale.
5. **Standard two-dot (`origin/main...HEAD`) or three-dot diff review will not catch this class of
   regression** if the destination branch legitimately differs from main elsewhere in the same file —
   the deleted section simply appears as "not present in this PR's diff from main" rather than as an
   explicit revert, which reads as unremarkable unless the reviewer already knows that section landed
   via a different, already-merged PR. Catching it requires either the targeted pre-checkout diff in
   step 2, or an independent reviewer cross-referencing the file's recent merged history.
6. **If the damage has already landed in a commit**, fix it by amending that commit to restore the
   deleted content (re-adding the missing section verbatim, e.g. via `git show <good-ref>:<path>`)
   rather than by a fresh follow-up commit, when the offending commit hasn't been merged yet — keeps
   the branch's history honest about what each commit actually contains.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|----------------|-----------------|
| `git checkout pr2327 -- scripts/README.md .github/workflows/_required.yml` to port a small doc/workflow fix between two PR branches | Assumed the command would only bring in the intended lines since both files were "mostly the same" between branches | Replaced both files wholesale; silently deleted the "Disaster recovery" section of `scripts/README.md` and `persist-credentials: false` from `_required.yml`, both landed independently via already-merged PR #2332 after `pr2327` branched | Always diff-before-checkout (`git diff HEAD <ref> -- <path>`) to see the FULL scope of the replacement, not just the intended hunk, before running `checkout <ref> -- <path>` |
| Relied on the PR's own two-dot diff against `origin/main` to self-verify before pushing | Read the PR's diff top to bottom, looked plausible since the file still differed from main in the intended way | The deletion of already-merged content doesn't look anomalous in a diff against main — it just looks like "this section isn't part of this PR's changes," which is true and unremarkable on its face | Cross-reference recently-merged PRs that touched the same files, or diff against the specific ref you copied from, not just against main |
| Assumed a strict-review pass would need to be told exactly what to look for | Ran an independent review agent generically ("review this PR") | It still caught the issue because it diffed the PR against main's actual recent history and noticed the vanished section, without being told the specific failure mode | A generic independent strict-review pass on a diff CAN catch whole-file-clobber regressions even without knowing this failure mode by name — but don't rely on it as the only safety net; prevent it at the source per steps 2-4 above |
| `git checkout origin/main -- .` in a shared detached checkout to grep merged files for diagnosis | Needed read-only content at the merged ref and reached for checkout by habit | The whole-tree form staged the ref tree as an index overlay (A/M vs HEAD); follow-on greps quietly answered against the overlay while the checkout was silently mutated; on a dirty shared checkout the same command destroys other actors' uncommitted work with no review net | Read-only intent uses `git show <ref>:<path>` or `git archive`, never checkout; recovery is `git reset --hard HEAD` only after the pre-overlay state is verified clean — otherwise the loss is unrecoverable |

## Results & Parameters

- **Reproduced on:** Hephaestus PR #2334 (`docs/agents-md-single-source` branch), files
  `scripts/README.md` and `.github/workflows/_required.yml`.
- **Command that caused it:** `git checkout pr2327 -- scripts/README.md .github/workflows/_required.yml`
  run from a clean working tree on the destination branch (no conflict, no rebase in progress).
- **What was silently lost:** the "Disaster recovery" section of `scripts/README.md` (already-landed
  via merged PR #2332) and the `persist-credentials: false` line in `_required.yml` (same PR).
- **Detection:** an independent strict-review agent graded the PR F/NO-GO with 2 CRITICAL findings
  identifying the reverted sections; not caught by the author's own two-dot diff review.
- **Fix:** `git commit --amend -S -s` to restore both deleted sections plus 3 additional dangling
  `CLAUDE.md`→`AGENTS.md` reference fixes that were also part of the intended scope; force-pushed
  with `--force-with-lease`.
- **General rule verified:** `git diff HEAD <other-ref> -- <path>` run BEFORE the checkout reliably
  shows the full scope of what a subsequent `git checkout <other-ref> -- <path>` would change,
  including anything it would delete — this is the cheap, always-available guard.
- **Read-only alternative verified:** `git show <ref>:<path>` (one file) and
  `git -C <repo> archive <ref> | tar -x -C <scratch>` (many files) answer against the target ref
  while the caller's index and working tree stay byte-identical.
- **Whole-tree overlay observed:** `git checkout <other-ref> -- .` on a shared detached checkout
  staged the full tree as new+modified index entries relative to HEAD (no user content was lost
  only because the tree was clean); follow-on evidence reads silently answered against the overlay.
  Recovery `git reset --hard HEAD` restores index and worktree exactly when — and only when — the
  pre-overlay state carried no uncommitted changes; on a dirty shared checkout the same command is
  unrecoverable destruction of other actors' work. Detection came from an operator self-catch at run
  time: ad-hoc shell reads have no review net.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| Hephaestus PR #2334 | Porting CLAUDE.md→AGENTS.md reference fixes between two sibling PR branches during an ecosystem-wide doc-consolidation campaign | verified-local; regression caught by independent strict-review (F/NO-GO, 2 CRITICAL), fixed via commit amend restoring both deleted sections, force-pushed with `--force-with-lease`, confirmed clean on a second independent review pass |
| Private monorepo qualification drive (generalized) | Read-only evidence gathering at a merged release ref from a shared detached checkout | verified-local; whole-tree overlay staging reproduced, evidence-provenance confusion observed, full recovery via `git reset --hard HEAD` under a verified-clean pre-state |
