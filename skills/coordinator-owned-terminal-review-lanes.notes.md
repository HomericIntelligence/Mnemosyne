# Notes: coordinator-owned-terminal-review-lanes

Supporting evidence for the main skill. Generalized from one coordination
window; identifiers are omitted under the privacy rules.

## Case chronology (2026-11-01)

A multi-lane backlog program ran on a shared delivery forge with a
coordinator and up to six concurrent background lanes (the measured
admission ceiling of the host). Two work items needed independent reviews
after their implementation lanes delivered.

### Item A: the orphan that published, then stalled

The implementation lane (background) self-launched two background review
children before its session ended. Both children survived:

- Child A1 completed and published a round-1 review on the pull request.
  The coordinator only learned of the publication through a manual artifact
  read — the completion notification had gone to the ended parent.
- Child A2 never signalled. The artifact state (round-2 unanswered, head
  stable) stayed unchanged for hours.

Classification at discovery: A1 orphan-completed (accept with audit), A2
orphan-stalled (candidate for replacement after enumeration).

### Item B: the degenerate orphan

The implementation lane for item B spawned a background review child and
ended. The child's only observable output was a degenerate completion
message — a verbatim source dump, no review publication. The parent was
gone; the coordinator found the state by reading the artifact. A genuine
review for the same head had meanwhile arrived from an unrelated lane.

Classification: orphan-stalled; no replacement needed because enumeration
showed the review gap already closed by the unrelated lane — launch would
have created a race, not coverage.

### The three-reviewer race

On a third pull request, a stale terminal signal (an orphaned review lane
whose parent was dead) tempted a replacement launch. Before enumeration ran,
three lanes had each launched a reviewer for the same head:

- all three published round-1 reviews;
- the verdicts converged, so no rework of the artifact was needed;
- the review spend tripled and the verdict reconciliation needed an extra
  audit step to bind one canonical review to the head.

After this window, the coordinator adopted the rule: every terminal launch
is coordinator-owned, gated on a forge readback of the artifact, and
preceded by enumeration. No further races or silent stalls occurred in the
remainder of the program (several more terminal launches, each with a live
notification owner).

## Case chronology (2026-11-07): a shared checkout with two live reviewers

A launcher started the same review task twice, minutes apart, into one shared
review checkout. Both processes ran the same command against the same
directory. The checkout was bound to one artifact head.

- The first process detected the second by process enumeration, a claim
  record that named one owning process, and files whose modification times no
  command of the first process produced.
- The second process had made uncommitted edits to two shipped files and one
  test file. The first process had edited only the test file.
- One of the foreign edits was an incomplete repair. It skipped a validation
  for the alternate revision, so the derived document kept value set B while
  it claimed the digest of value set A. The edited check then passed, and the
  later promotion consumer refused the document.
- The first process had already reproduced two required defects by execution
  at the bound head. It posted one verdict with the reproduction evidence, an
  ownership note with both process identifiers, and one decision request for
  the repair choice. It set no gate label.
- The first process restored the two shipped files that the second process had
  edited. It left the second process's untracked test file in place.

Outcome evidence at the bound head: the required check passed, the focused
suite passed before any edit, and the two required defects reproduced by
execution.

## Decision points the evidence supports

| Decision | Evidence |
| -------- | -------- |
| Coordinator owns terminal launches | Both orphans traced to author-spawned children; every coordinator-owned launch afterwards kept its notification owner alive |
| Gate launches on forge readback | One orphan's completion report arrived without a published artifact; readback distinguished it from a real publication |
| Enumerate before replacement | The race cost triple review spend; in item B enumeration showed the gap already closed and prevented a redundant launch |
| Classify orphans by artifact state | A1 (publish present) vs A2 (nothing) vs B (degenerate): three states, three different correct actions |
| A reviewer stops writing when ownership of one checkout is split | Two live processes in one checkout left uncommitted edits mid-review, so the head under review could not be stated as one author's work |
| Screen foreign in-flight edits as evidence, not as a fix | A foreign edit that skipped one validation let a document claim the digest of one value set while carrying another; only the later consumer refused it |
| Restore foreign tracked edits, leave foreign untracked files | Restoring prevents a later push from carrying a half-applied repair; deleting the untracked file would discard the other process's work |

## Limits

- Evidence is one coordination window on one host with one forge; the rule
  set generalizes (notification routing and enumeration are mechanics, not
  site policy), but the "stable for hours" wait bound is program-specific.
- The entry does not cover reviewer verdict reconciliation after a race
  beyond flagging the audit need; the review-loop skill owns that.
- Foreground children (parent awaits them) were not exercised in this
  window; the permission for them follows from the notification-lifetime
  argument, not from observed cases.
- The two-live-reviewer case is one observation. It shows that a shared
  checkout can acquire a second writer after launch. It does not measure how
  often that happens, and it did not follow the second process to its end; the
  coordinator stopped one process off this session.

## Privacy note

Source identifiers (organization, repositories, issue, pull-request and
discussion numbers, comment identifiers, branch names, commit identifiers,
session and shell identifiers) are deliberately omitted. The decision rules
are stated against the general mechanism.
