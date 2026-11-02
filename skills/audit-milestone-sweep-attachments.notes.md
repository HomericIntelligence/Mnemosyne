# audit-milestone-sweep-attachments — supporting notes

Supporting evidence for
[audit-milestone-sweep-attachments.md](audit-milestone-sweep-attachments.md).
The main entry holds every rule needed to operate. This file holds the
measurements that justify those rules.

## Case 1 — cluster shape

A release board was swept onto a restated release calendar. A later audit of
one patch-cut milestone found a group of tracker issues that entered together:

```text
#A: 2026-11-02T17:49:09Z
#B: 2026-11-02T17:49:09Z
#C: 2026-11-02T17:49:10Z
#D: 2026-11-02T17:49:11Z
#E: 2026-11-02T17:49:11Z
#F: 2026-11-02T17:49:12Z
#G: 2026-11-02T17:49:12Z
#H: 2026-11-02T17:49:13Z
```

Eight unrelated items entered in five seconds. Each had exactly one
`milestoned` event and no `demilestoned` event. The milestone's plan roster
named none of them: `grep -c` against the plan body returned `0` for every
one.

All eight were opened by the same closing documentation-remediation work,
about one hour before the sweep. That provenance explains the cluster: the
items arrived as one batch and were swept as one batch, without a scope test.

## Case 2 — horizon mismatch

The same milestone was a patch cut with roughly two days left. Every cluster
member required a capability that its own body marked as not started or not
deployed, for example: no transition reducer exists, no executor dispatches
the command, the pass has no implementation, and the gate is not deployed.

Such items cannot fit a two-day cut regardless of effort. The horizon test in
the main entry replaces a subjective "this looks big" judgment with a stated
comparison.

## Case 3 — the title-token false positive

Two items were proposed for moving because their bodies named later
releases. Neither was an artifact of the sweep:

- One item named a head release and an intermediate release, and its body
  stated that two specific features "stay in" the later release. It was a
  correctly scoped design program, not a misplacement.
- Another item's title read "rebuild on vX.Y.Z". That token was the version of
  a third-party engine inside the product's own image line, not a milestone.
  The item was correctly placed in the current cut.

Neither carried a clustered attach time. This is the reason the workflow
requires two signals instead of one. A title or body token alone produced a
confident but wrong proposal.

## Case 4 — planned trackers with a similar shape

The same milestone held several tracker epics that the plan did not use as a
roster line, yet each tied directly to the live promotion state of the
current release. They were also created and attached in a single pass.

The two-signal rule keeps them in place: their work is genuinely required by
the cut, and the owner confirmed the placement. A single-signal rule would
have moved them.

## Measurement summary

| Signal | Cluster members | Correctly placed trackers |
| --- | --- | --- |
| Attach inside a tight cluster | yes | sometimes yes |
| Absent from the plan roster | yes | yes |
| Work fits the cut horizon | no | yes |

Only the third row separates the two groups reliably for horizon, and only
the first row reveals that a scope decision was never made. The conjunction
of rows one and two, then a horizon test, produced the correct set.

## Count verification pattern

Record `open_issues` for every milestone before the moves, then re-read them
after. A correct batch leaves each source and destination changed by exactly
its share, with no other milestone changed. This caught nothing in the
verified run, but it is the only cheap proof that a loop over
`gh issue edit --milestone` did not mis-target an item.

## Limits of this evidence

- Both cases are from one repository and two audit passes.
- The timestamps are the strongest signal, but a plan authored in one pass can
  produce a similar cluster. Always apply the roster test with them.
- Mention of `demilestoned` events does not appear in either verified case, so
  this approach does not prove the absence of an earlier intentional move. It
  only shows the current attach happened in a batch.